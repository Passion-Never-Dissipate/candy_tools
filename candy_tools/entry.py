import threading
import candy_tools as root
from mcdreforged.api.all import *
from candy_tools.server_data_getter import ServerDataGetter


def on_load(server: PluginServerInterface, prev):
    """
	插件加载时调用
	"""
    if hasattr(prev, 'command_getter'):
        # 从之前的实例恢复查询
        root.command_getter = prev.command_getter
        root.has_carpet = prev.has_carpet
    else:
        # 首次加载，创建新实例
        root.command_getter = ServerDataGetter(server)


def on_info(server: PluginServerInterface, info):
    """
	处理服务器输出
	"""
    root.command_getter.on_info(info)


def on_server_start(server: PluginServerInterface):
    has_carpet_on_server_start()


@new_thread
def has_carpet_on_server_start():
    results = {
        'has_fabric': False,
        'has_carpet': False
    }

    def check_fabric():
        result = root.listen_and_wait(
            r'^Loading Minecraft .+ with Fabric Loader .+$',
            10,
            return_match=False
        )
        results['has_fabric'] = result is not None

    def check_carpet():
        result = root.listen_and_wait(
            r'^\s*-\s+carpet\s+\d+\.\d+',
            10,
            return_match=False
        )
        results['has_carpet'] = result is not None

    # 创建并启动线程
    fabric_thread = threading.Thread(target=check_fabric, daemon=True)
    carpet_thread = threading.Thread(target=check_carpet, daemon=True)

    fabric_thread.start()
    carpet_thread.start()

    # 等待两个线程完成
    fabric_thread.join(timeout=10)
    carpet_thread.join(timeout=10)

    root.has_carpet = results['has_fabric'] and results['has_carpet']
