# Candy Tools 文档

## 概述

本插件主要作为前置api用于FRUITS_CANDY开发的MCDR插件，如果你有兴趣使用推荐下载源码查看完整功能。

本插件有些功能依赖carpet mod

## 功能特性

- ✅ 执行任意命令并根据正则表达式匹配结果
- ✅ 监听服务器输出中的特定消息
- ✅ 支持返回完整字符串或正则匹配对象
- ✅ 自动检测服务端上是否有 Carpet mod
- ✅ 获取指定区域内玩家的 NBT 属性
- ✅ 线程安全，支持插件热重载

## 安装

### 前置要求

- MCDReforged >= 2.7.0
- Minecraft 服务器（支持 Fabric 服务端）（可选）

### 安装步骤

将插件放入 MCDR 的 `plugins` 目录 或使用指令 `!!MCDR plugin install candy_tools` 来安装插件

## API 使用指南

### 基本导入

```python
import candy_tools
# 或者只导入需要的函数
from candy_tools import execute_and_wait, listen_and_wait
```

### 1. 执行命令并等待结果（命令执行超时返回None）

#### 1.1 返回完整字符串

```python
# 获取玩家列表
result = candy_tools.execute_and_wait_str(
    command="list",
    pattern=r"There are \d+ of a max of \d+ players online:.*",
    timeout=5.0
)

if result:
    print(f"服务器返回: {result}")
```

#### 1.2 返回正则匹配对象

```python
# 获取玩家列表并提取数字信息
match = candy_tools.execute_and_wait_match(
    command="list",
    pattern=r"There are (\d+) of a max of (\d+) players online:(.*)",
    timeout=5.0
)

if match:
    current_players = match.group(1)  # 当前在线玩家数
    max_players = match.group(2)      # 最大玩家数
    player_list = match.group(3)      # 玩家名字列表
    print(f"在线: {current_players}/{max_players}")
    print(f"玩家: {player_list}")
```

#### 1.3 使用命名分组

```python
match = candy_tools.execute_and_wait_match(
    command="time query daytime",
    pattern=r"The time is (?P<time>\d+)",
    timeout=3.0
)

if match:
    world_time = match.group('time')
    print(f"世界时间: {world_time}")
```

### 2. 监听服务器消息

#### 2.1 监听玩家加入

```python
# 监听玩家加入消息
message = candy_tools.listen_and_wait_str(
    pattern=r"Player (\w+) joined the game",
    timeout=30.0
)

if message:
    print(f"有玩家加入: {message}")
```

#### 2.2 监听服务器启动

```python
# 监听服务器启动完成
match = candy_tools.listen_and_wait_match(
    pattern=r"Done \((\d+\.\d+)s\)! For help, type \"help\"",
    timeout=60.0
)

if match:
    startup_time = match.group(1)
    print(f"服务器启动完成，耗时: {startup_time}秒")
```

### 3. 高级功能

#### 3.1 检测 Carpet 模组

```python
# 检测服务器是否安装了 Carpet 模组
has_carpet = candy_tools.query_carpet()
print(f"服务器是否安装 Carpet 模组: {has_carpet}")

```

#### 3.2 获取区域内的玩家信息（需要carpet mod）

```python
# 定义要监控的区域
regions = {
    'overworld': [
        {'x1': -100, 'x2': 100, 'y1': 0, 'y2': 255, 'z1': -100, 'z2': 100},
        {'x1': 200, 'x2': 300, 'y1': 0, 'y2': 255, 'z1': 200, 'z2': 300}
    ],
    'the_nether': [
        {'x1': -50, 'x2': 50, 'y1': 0, 'y2': 127, 'z1': -50, 'z2': 50}
    ]
}

# 获取区域内玩家的 UUID
players = candy_tools.get_players_nbt_in_regions(
    region_dict=regions,
    nbt_attribute='uuid',  # 可以是 'uuid', 'gamemode', 'health' 等
    timeout=10.0
)

if players is None:
    print("查询超时")
elif players == {}:
    print("区域内没有玩家")
else:
    for player_name, uuid in players.items():
        print(f"{player_name}: {uuid}")
```

## 事件处理

### 自动 Carpet 检测

Candy Tools 会在以下事件中自动检测 Carpet 模组：

- `on_server_start`：服务器启动时检测
- 检测结果存储在 `candy_tools.has_carpet` 中

## 错误处理

### 超时处理

所有 API 函数都有 `timeout` 参数，超时会返回 `None`：

```python
result = candy_tools.execute_and_wait_str("list", r"players online", timeout=2.0)
if result is None:
    print("命令执行超时")
```

### 正则表达式错误

如果提供的正则表达式无效，会记录错误并返回 `None`：

```python
# 错误的正则表达式
result = candy_tools.execute_and_wait_str("list", r"invalid[regex", timeout=2.0)
# result 为 None，控制台会输出错误日志
```

## 故障排除

### 常见问题

1. **API 返回 None**
   - 检查命令是否正确执行
   - 检查正则表达式是否匹配命令输出
   - 增加超时时间

2. **插件加载失败**
   - 检查 MCDReforged 版本是否 >= 2.7.0
   - 检查插件文件是否完整
   - 查看 MCDR 日志中的错误信息

## 许可证

本项目基于 MIT 许可证开源，详见 [LICENSE](LICENSE) 文件。

## 贡献与反馈

- 项目地址：https://github.com/Passion-Never-Dissipate/candy_tools
- 问题反馈：在 GitHub Issues 中提交问题
- 功能建议：欢迎提交 Pull Request

---


