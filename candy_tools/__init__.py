import re
from typing import Optional, Union
from candy_tools.server_data_getter import ServerDataGetter

__all__ = [
    'execute_and_wait',
    'listen_and_wait',
    'execute_and_wait_str',
    'execute_and_wait_match',
    'listen_and_wait_str',
    'listen_and_wait_match',
    'query_carpet',
    'get_players_nbt_in_regions',
    'get_online_players',
    'get_online_fake_players',
    'get_online_players_in_regions'
]

DEFAULT_TIME_OUT = 5.0  # seconds
has_carpet: Optional[bool] = None
command_getter: Optional[ServerDataGetter] = None


# ------------------
#   API Interfaces
# ------------------

def execute_and_wait(
        command: str,
        pattern: str,
        timeout: float = DEFAULT_TIME_OUT,
        return_match: bool = False
) -> Union[Optional[str], Optional[re.Match]]:
    """
    执行命令并等待匹配结果

    Args:
        command: 要执行的Minecraft命令,也可以是MCDR命令
        pattern: 正则表达式，用于匹配命令输出
        timeout: 超时时间（秒）
        return_match: 如果为True，返回re.Match对象；否则返回完整字符串

    Returns:
        如果return_match=True: 返回re.Match对象或None
        如果return_match=False: 返回匹配的完整字符串或None

    示例:
        # 返回完整字符串
        text = execute_and_wait("list", r"There are \d+ of a max of \d+ players")

        # 返回re.Match对象，方便提取分组
        match = execute_and_wait("list", r"There are (\d+) of a max of (\d+) players", return_match=True)
        if match:
            current = match.group(1)  # 当前玩家数
            max_players = match.group(2)  # 最大玩家数
    """

    return command_getter.execute_and_wait(command, pattern, timeout, return_match)


def listen_and_wait(
        pattern: str,
        timeout: float = DEFAULT_TIME_OUT,
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

    示例:
        # 监听玩家加入消息
        message = listen_and_wait(r"Player (\w+) joined the game", timeout=30.0)
        if message:
            print(f"玩家加入消息: {message}")
    """

    return command_getter.listen_and_wait(pattern, timeout, return_match)


def execute_and_wait_str(command: str, pattern: str, timeout: float = DEFAULT_TIME_OUT) -> Optional[str]:
    """执行命令并返回完整字符串"""
    return execute_and_wait(command, pattern, timeout, return_match=False)


def execute_and_wait_match(command: str, pattern: str, timeout: float = DEFAULT_TIME_OUT) -> Optional[re.Match]:
    """执行命令并返回re.Match对象"""
    return execute_and_wait(command, pattern, timeout, return_match=True)


def listen_and_wait_str(pattern: str, timeout: float = DEFAULT_TIME_OUT) -> Optional[str]:
    """监听消息并返回完整字符串"""
    return listen_and_wait(pattern, timeout, return_match=False)


def listen_and_wait_match(pattern: str, timeout: float = DEFAULT_TIME_OUT) -> Optional[re.Match]:
    """监听消息并返回re.Match对象"""
    return listen_and_wait(pattern, timeout, return_match=True)


def query_carpet():
    """向服务端控制台执行指令以判断是否装有carpet mod"""
    global has_carpet
    if has_carpet is None:
        has_carpet = execute_and_wait(
            "script run logger('[candy_tools] carpet mod has been loaded on the server'); dummy = '[candy_tools] get carpet status done'",
            r'^\[candy_tools] carpet mod has been loaded on the server$',
            DEFAULT_TIME_OUT,
            return_match=False
        )
        has_carpet = True if has_carpet else False

    return has_carpet


def get_online_players(timeout: float = 5.0):
    """
    获取服务器所有在线玩家真实id列表，排除称号，前后缀对玩家id的影响（需要carpet mod）

    Returns:
        - 超时: 返回None
        - 无玩家: 返回空列表[]
        - 有玩家: 返回列表[玩家名1, 玩家名2, ...]
    """

    if has_carpet is None:
        query_carpet()

    if not has_carpet:
        return

    command = "script run players=player('all'); names=map(players, _~'name'); logger('online_player_list: '+str(names)); dummy='[CT] online player list done'"
    pattern = r"online_player_list:\s*\[(.*?)\]"

    try:
        match_result = execute_and_wait(
            command,
            pattern,
            timeout=timeout,
            return_match=True
        )

        if match_result is None:
            return None

        content = match_result.group(1).strip()

        if not content:
            return []

        # 解析玩家列表，去除引号和空格
        players = []
        for player_str in content.split(','):
            player_name = player_str.strip().strip("'").strip('"')
            if player_name:
                players.append(player_name)

        return players

    except Exception:
        return None


def get_online_fake_players(timeout: float = 5.0):
    """
    获取服务器所有在线的Carpet假人玩家真实id列表，排除称号，前后缀对玩家id的影响（需要carpet mod）

    Args:
        timeout: 命令超时时间（秒）

    Returns:
        - 超时: 返回None
        - 无假人: 返回空列表[]
        - 有假人: 返回列表[假人名1, 假人名2, ...]
    """

    if has_carpet is None:
        query_carpet()

    if not has_carpet:
        return

    command = "script run all_players=player('all'); fake_players=filter(all_players, _~'player_type'=='fake'); names=map(fake_players, _~'name'); logger('online_fake_player_list: '+str(names)); dummy='[CT] fake player list done'"
    pattern = r"online_fake_player_list:\s*\[(.*?)\]"

    try:
        match_result = execute_and_wait(
            command,
            pattern,
            timeout=timeout,
            return_match=True
        )

        if match_result is None:
            return None

        content = match_result.group(1).strip()

        if not content:
            return []

        # 解析假人名称列表
        fake_players_list = []
        for player_str in content.split(','):
            player_name = player_str.strip().strip("'").strip('"')
            if player_name:
                fake_players_list.append(player_name)

        return fake_players_list

    except Exception:
        return None


def __convert_to_scarpet_dict(py_dict):
    """
    将Python区域字典转换为Scarpet字典字符串（仅字典部分）。

    Args:
        py_dict: 区域定义字典

    Returns:
        Scarpet字典字符串
    """

    def convert_value(value):
        """递归转换值"""
        if isinstance(value, dict):
            items = []
            for k, v in value.items():
                if v is None:
                    continue
                items.append(f"'{k}' -> {convert_value(v)}")
            return '{' + ', '.join(items) + '}'
        elif isinstance(value, list):
            items = [convert_value(item) for item in value]
            return '[' + ', '.join(items) + ']'
        elif isinstance(value, str):
            return f"'{value}'"
        elif isinstance(value, (int, float)):
            return str(value)
        elif value is None:
            return 'null'
        else:
            return str(value)

    # 构建外部字典
    scarpet_items = []
    for dimension, regions in py_dict.items():
        scarpet_items.append(f"'{dimension}' -> {convert_value(regions)}")

    return '{' + ', '.join(scarpet_items) + '}'


def get_players_nbt_in_regions(
        region_dict: dict,
        nbt_attribute: str = 'uuid',
        timeout: float = 10.0
):
    """
    获取指定区域内所有玩家的NBT属性。（需要carpet mod）

    Args:
        region_dict: 区域定义字典:
        这里原版维度之所以不用minecraft:overworld是因为在scarpet指令系统里，原版三个维度没有minecraft:
        但是非原版的维度则不受此限制
        {
        'overworld': [
        {'x1': -100, 'x2': 100, 'y1': 0, 'y2': 255, 'z1': -100, 'z2': 100},
        {'x1': 200, 'x2': 300, 'z1': 200, 'z2': 300}
        ],
        'the_nether': [{'x1': -50, 'x2': 50, 'y1': 0, 'y2': 127, 'z1': -50, 'z2': 50}],
        'twilightforest:twilight_forest': [{'x1': -50, 'x2': 50}]
        }
        nbt_attribute: 玩家NBT属性名，如 'uuid', 'health', 'gamemode' 等
        timeout: 超时时间（秒）

    Returns:
        - 超时: 返回None
        - 无玩家: 返回空字典{}
        - 有玩家: 返回字典{玩家名: 属性值}
    """

    if has_carpet is None:
        query_carpet()

    if not has_carpet:
        return

    # 1. 生成区域字典字符串
    region_map_str = __convert_to_scarpet_dict(region_dict)

    # 2. 修改Scarpet指令模板：确保无玩家时也输出 {nbt_attribute}_dict: {}
    # 关键修改：将原来的条件判断改为总是输出字典，只是内容不同
    scarpet_template = f"""script run region_map = {region_map_str}; check_region(pos, region) -> ([x, y, z] = pos; if (has(region, 'x1') && has(region, 'x2'), min_x = min(region:'x1', region:'x2'); max_x = max(region:'x1', region:'x2'); if (x < min_x || x > max_x, return(false))); if (has(region, 'y1') && has(region, 'y2'), min_y = min(region:'y1', region:'y2'); max_y = max(region:'y1', region:'y2'); if (y < min_y || y > max_y, return(false))); if (has(region, 'z1') && has(region, 'z2'), min_z = min(region:'z1', region:'z2'); max_z = max(region:'z1', region:'z2'); if (z < min_z || z > max_z, return(false))); return(true)); all_players = entity_selector('@a'); unique_players = {{}}; for(all_players, p = _; dim = p~'dimension'; player_pos = pos(p); if (has(region_map, dim), regions = get(region_map, dim); for(regions, if (check_region(player_pos, _), unique_players:(p~'{nbt_attribute}') = p; break())))); filtered_players = values(unique_players); json_parts = map(filtered_players, str('"') + _~'name' + str('": "') + _~'{nbt_attribute}' + str('"')); logger('在多维度的指定区域内找到 ' + length(filtered_players) + ' 名玩家（已去重）'); dict_content = if (length(filtered_players) > 0, '{{' + join(', ', json_parts) + '}}', '{{}}'); logger('{nbt_attribute}_dict: ' + dict_content); dummy = '[candy_tools] get_player_nbt done'"""

    # 3. 压缩为单行指令
    scarpet_command = ' '.join(scarpet_template.split())

    # 4. 执行命令并处理结果 - 现在只需要匹配 {nbt_attribute}_dict: {...}
    result_pattern = rf'{re.escape(nbt_attribute)}_dict:\s*\{{(.*?)\}}'

    try:
        match_result = execute_and_wait(
            scarpet_command,
            result_pattern,
            timeout=timeout,
            return_match=True
        )

        # 情况1: 超时 - 没有匹配到任何输出
        if match_result is None:
            return None

        # 获取字典内容
        json_content = match_result.group(1).strip()

        # 情况2: 字典内容为空 {} - 没有玩家
        if json_content == "":
            return {}

        # 情况3: 有玩家数据 - 解析字典
        players_dict = {}
        key_value_pattern = r'"([^"]+)"\s*:\s*"([^"]*)"'
        matches = re.findall(key_value_pattern, json_content)

        for player_name, attribute_value in matches:
            players_dict[player_name] = attribute_value

        return players_dict

    except Exception:
        # 执行异常
        return None


def get_online_players_in_regions(region_dict: dict, timeout: float = 10.0):
    """
        获取指定区域内所有在线玩家的真实id列表，排除称号，前后缀对玩家id的影响。（需要carpet mod）

        Args:
            region_dict: 区域定义字典，格式同 get_players_nbt_in_regions 的 region_dict 参数
            timeout: 超时时间（秒）

        Returns:
            - 超时: 返回 None
            - 无玩家: 返回空列表 []
            - 有玩家: 返回玩家名称列表 [玩家名1, 玩家名2, ...]

        示例:
            regions = {
                "overworld": [{"x1": 50, "z1": 50, "x2": -50, "z2": -50}],
                "the_nether": [{"x1": 100, "z1": 100, "x2": 200, "z2": 200}]
            }

            # 获取指定区域内的在线玩家
            players = get_online_players_in_regions(regions)

            if players is None:
                print("查询超时")
            elif len(players) == 0:
                print("区域内没有玩家")
            else:
                print(f"区域内有 {len(players)} 名玩家: {players}")
        """

    if has_carpet is None:
        query_carpet()

    if not has_carpet:
        return

    result = get_players_nbt_in_regions(region_dict, 'name', timeout)
    # 情况1: 超时 - 没有匹配到任何输出
    if result is None:
        return None

    # 情况2: 字典内容为空 {} - 没有玩家
    if not result:
        return []

    # 情况3: 有玩家数据 - 返回满足要求的玩家列表
    return list(result.keys())
