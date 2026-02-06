import re
import uuid
import time
from queue import Queue, Empty
from threading import RLock
from typing import Dict, Optional, Pattern, List, Union
from dataclasses import dataclass
from mcdreforged.api.types import PluginServerInterface, Info


@dataclass
class SimpleQuery:
    """简化的查询对象"""
    query_id: str
    pattern: Pattern
    command: Optional[str]  # None表示不执行命令，只监听
    queue: Queue
    start_time: float
    timeout: float
    return_match: bool = False  # 是否返回re.Match对象


class ServerDataGetter:
    """
    服务器数据获取器

    特性：
    1. 线程安全
    2. 插件重载后继续未完成的查询
    3. 灵活返回类型：完整字符串或re.Match对象
    4. 支持两种模式：命令模式和监听模式
    5. 自动清理超时查询
    6. 一条输出只匹配最早的一个查询
    """

    def __init__(self, server: PluginServerInterface):
        self.server = server
        self.lock = RLock()
        self.queries: Dict[str, SimpleQuery] = {}

    def execute_and_wait(
            self,
            command: Optional[str],
            pattern: str,
            timeout: float = 5.0,
            return_match: bool = False
    ) -> Union[Optional[str], Optional[re.Match]]:
        """
        执行命令并等待匹配结果（或只监听消息）

        Args:
            command: 要执行的Minecraft命令，None表示不执行命令，只监听匹配的消息
            pattern: 正则表达式，用于匹配命令输出或服务器消息
            timeout: 超时时间（秒）
            return_match: 如果为True，返回re.Match对象；否则返回完整字符串

        Returns:
            如果return_match=True: 返回re.Match对象或None
            如果return_match=False: 返回匹配的完整字符串或None
        """
        if self.server.is_on_executor_thread():
            raise RuntimeError('Cannot invoke execute_and_wait on the task executor thread')

        # 生成唯一ID
        query_id = f"q_{uuid.uuid4().hex[:8]}"

        # 编译正则表达式
        try:
            compiled_pattern = re.compile(pattern)
        except re.error as e:
            self.server.logger.error(f"Invalid regex pattern '{pattern}': {e}")
            return None

        # 创建队列
        queue = Queue()

        # 创建查询对象
        query = SimpleQuery(
            query_id=query_id,
            pattern=compiled_pattern,
            command=command,
            queue=queue,
            start_time=time.time(),
            timeout=timeout,
            return_match=return_match
        )

        # 保存查询
        with self.lock:
            self.queries[query_id] = query

        try:
            # 如果有命令，执行命令；否则只是等待监听
            if command:
                self.server.execute(command)
            else:
                self.server.logger.debug(f"开始监听模式，等待匹配: {pattern}")

            # 等待结果
            result = queue.get(timeout=timeout)

            # 根据return_match参数返回相应类型
            if return_match:
                # 用户期望re.Match对象，返回匹配对象
                return result
            else:
                # 用户期望字符串，返回完整行
                if isinstance(result, str):
                    return result  # 直接返回字符串
                else:
                    return None  # 超时返回None

        except Empty:
            if command:
                self.server.logger.debug(f"Command '{command}' timeout")
            else:
                self.server.logger.debug(f"监听模式超时，未匹配到: {pattern}")
            return None

        finally:
            # 清理查询（无论成功还是超时）
            with self.lock:
                if query_id in self.queries:
                    del self.queries[query_id]

    def listen_and_wait(
            self,
            pattern: str,
            timeout: float = 5.0,
            return_match: bool = False
    ) -> Union[Optional[str], Optional[re.Match]]:
        """
        监听服务器输出，等待匹配的消息

        Args:
            pattern: 正则表达式，用于匹配服务器消息
            timeout: 超时时间（秒）
            return_match: 如果为True，返回re.Match对象；否则返回完整字符串

        Returns:
            如果return_match=True: 返回re.Match对象或None
            如果return_match=False: 返回匹配的完整字符串或None
        """
        return self.execute_and_wait(None, pattern, timeout, return_match)

    def on_info(self, info: Info):
        """
        处理服务器输出，必须在MCDR的on_info中调用

        一条输出只匹配最早的一个查询（最先开始的查询）
        """
        if info.is_user:  # 忽略玩家消息
            return

        content = info.content
        current_time = time.time()

        # 清理超时的查询
        self._cleanup_timeouts(current_time)

        # 获取所有未超时的查询，并按开始时间排序（最早的在前）
        matching_queries = self._get_valid_queries_sorted(current_time)

        # 查找第一个匹配的查询
        matched_query = None
        matched_match = None
        for query in matching_queries:
            match = query.pattern.search(content)
            if match:
                matched_query = query
                matched_match = match
                break

        # 如果找到匹配的查询，处理它
        if matched_query and matched_match:
            # 根据查询的return_match参数决定放入队列的内容
            if matched_query.return_match:
                # 放入re.Match对象
                matched_query.queue.put(matched_match)
            else:
                # 放入完整字符串
                matched_query.queue.put(content)

            # 从查询字典中移除（防止重复匹配）
            with self.lock:
                if matched_query.query_id in self.queries:
                    del self.queries[matched_query.query_id]

            # 记录日志
            if matched_query.command:
                self.server.logger.debug(f"查询 {matched_query.query_id} 匹配成功，命令: {matched_query.command}")
            else:
                self.server.logger.debug(f"监听查询 {matched_query.query_id} 匹配成功，模式: {matched_query.pattern.pattern}")

    def _get_valid_queries_sorted(self, current_time: float) -> List[SimpleQuery]:
        """
        获取所有未超时的查询，并按开始时间排序（最早的在前）
        """
        with self.lock:
            # 收集未超时的查询
            valid_queries = []
            for query_id, query in self.queries.items():
                if current_time - query.start_time <= query.timeout:
                    valid_queries.append(query)

            # 按开始时间排序（最早的在前）
            valid_queries.sort(key=lambda q: q.start_time)

            return valid_queries

    def _cleanup_timeouts(self, current_time: float):
        """清理超时的查询"""
        with self.lock:
            # 找出超时的查询
            timeout_ids = []
            for query_id, query in self.queries.items():
                if current_time - query.start_time > query.timeout:
                    timeout_ids.append(query_id)

            # 移除超时查询，并给等待的线程发送None
            for query_id in timeout_ids:
                query = self.queries[query_id]

                # 如果队列为空，放入None表示超时
                if not query.queue.full():
                    query.queue.put(None)

                del self.queries[query_id]

                if query.command:
                    self.server.logger.debug(f"查询 {query_id} 已超时，命令: {query.command}")
                else:
                    self.server.logger.debug(f"监听查询 {query_id} 已超时，模式: {query.pattern.pattern}")

    def get_pending_count(self) -> int:
        """获取等待中的查询数量"""
        with self.lock:
            return len(self.queries)