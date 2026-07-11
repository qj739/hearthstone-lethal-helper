# 炉石传说辅助工具 - HDT Python版

## 🎯 项目简介

> **这是竞技场模式专用，用于斩杀计算和提示，让你永不错斩！**

这是一个**仿照 Hearthstone Deck Tracker (HDT) 实现方式**的 Python 版炉石传说**竞技场**辅助工具。

核心功能：
- ✅ 实时监控游戏状态
- ✅ 自动检测斩杀机会
- ✅ 显示手牌和场面信息
- ✅ 基于官方日志解析（和HDT一样）

## 🏗️ 架构设计

### 仿照HDT的模块化架构

```
hdt_tracker.py (主程序)
    ↓
hdt_python/
    ├── log_watcher.py        # 日志监控系统 (仿 LogWatcherManager)
    ├── power_parser.py       # Power.log 解析器 (仿 PowerHandler)
    ├── lethal_checker.py     # 斩杀检测器
    └── __init__.py
```

### 核心组件

#### 1. LogWatcherManager（日志监控管理器）
- 管理多个日志监控器
- 实时读取日志文件新增内容
- 多线程异步处理
- 自动处理日志重置（游戏重启）

#### 2. PowerLogParser（Power.log解析器）
- **预编译正则表达式**（性能优化）
- 解析游戏实体和事件
- 事件驱动架构
- 完整的标签系统

#### 3. GameState（游戏状态管理）
- 实体管理（Entity）
- 玩家识别（本地/对手）
- 区域追踪（手牌/场面/墓地）
- 实时状态更新

#### 4. LethalChecker（斩杀检测器）
- 计算场面攻击伤害
- 计算法术伤害
- 计算武器伤害
- 计算冲锋随从伤害
- 考虑法力值限制

## 📦 文件结构

```
HS/
├── hdt_tracker.py              # ⭐ 主程序（从这里启动）
├── log.config                  # 炉石日志配置文件
├── hdt_python/                 # 核心模块
├── docs/                       # 文档（本文档位于 docs/）
├── tests/                      # 回归测试
├── tools/                      # 日志分析 / 调试脚本
└── json/                       # 卡牌数据
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.7+
- Windows 系统
- 已安装炉石传说

### 2. 首次设置

```bash
# 克隆或下载项目
cd C:\Users\zqinjie\Desktop\HS

# 运行主程序
python hdt_tracker.py
```

### 3. 首次运行会自动

1. ✅ 检查并安装 `log.config` 到炉石目录
2. ✅ 查找炉石日志文件位置
3. ✅ 启动日志监控系统

### 4. 重启炉石传说

⚠️ **重要**: 首次运行后需要**重启炉石传说**以应用日志配置！

## 📖 使用方法

### 基本使用

```bash
python hdt_tracker.py
```

### 预期输出

```
============================================================
HDT风格的炉石传说辅助工具
仿照 Hearthstone Deck Tracker 实现
============================================================

[1/3] 检查 log.config...
[Config] 已安装 log.config 到: C:\Users\...\log.config

[2/3] 查找炉石传说日志...
[Finder] 找到日志目录: C:\Program Files (x86)\Hearthstone\Logs

[3/3] 设置日志监控器...
[Manager] 注册监控器: Power

✅ 设置完成！

============================================================
开始监控游戏...
提示: 按 Ctrl+C 停止
============================================================

[Manager] 启动日志监控系统...
[Power] 开始监控: C:\Program Files (x86)\Hearthstone\Logs\Power.log
[Manager] 监控线程已启动
```

### 游戏中的输出

#### 普通状态

```
------------------------------------------------------------
玩家ID: 我方=1 | 对手=2
我方: 25+0血 | 6/10法力
对手: 18+2血

场面: 我方 3 随从 | 对手 2 随从
手牌: 5 张

我方场面:
  [✓] CS2_124 (3/1)  # 可攻击
  [✗] EX1_506 (4/5)  # 不可攻击
  [✓] CS2_189 (2/2)

手牌:
  (4) CS2_029  # 火球术
  (3) CS2_012
  (2) CS2_024
  (1) CS2_025
  (0) CS2_072
------------------------------------------------------------
```

#### 斩杀提示

```
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯
⚔️  斩杀提示！检测到斩杀机会！ ⚔️
🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯🎯

============================================================
⚔️  斩杀！有斩杀机会！ ⚔️
============================================================
对手血量: 15 + 护甲: 0 = 总计: 15
我方总伤害: 18

伤害来源:
  • 场面攻击 [CS2_124(3), CS2_189(2)]: 5伤害
  • 武器 CS2_091: 3伤害
  • 法术 CS2_029: 7伤害 (4费)  # 火球术+1法伤
  • 冲锋 CS2_124: 3伤害 (3费)
============================================================
```

## 🔧 核心原理

### HDT 的工作原理（我们的实现基础）

根据对 HDT 源码的调研，我们了解到：

1. **主要方式：日志解析**
   - HDT 主要通过解析 `Power.log`、`Zone.log` 等获取游戏状态
   - 这是最准确、最稳定的方式
   - 暴雪官方支持的数据源

2. **辅助方式：内存读取**
   - 仅用于获取日志中没有的信息（任务、卡组收藏等）
   - 不是获取场面信息的主要方式

### 我们的实现

✅ **完全基于日志解析**
- 和 HDT 的核心方法一致
- 纯 Python 实现
- 无需复杂的内存操作

### log.config 配置

我们使用和 HDT 相同的日志配置：

```ini
[Power]
LogLevel=1        # 启用详细日志
FilePrinting=False
ConsolePrinting=True
ScreenPrinting=False

[Zone]
LogLevel=1
...
```

这会让炉石传说输出详细的游戏事件日志。

## 🎮 功能特性

### 已实现功能

**基础解析**
- [x] 自动查找日志文件
- [x] 实时监控游戏状态（Power.log）
- [x] 识别我方/对手（战网名、FRIENDLY_PLAYER、零配置）
- [x] 追踪手牌（已知卡牌）、场面、英雄血甲、武器、法力

**斩杀与场攻**
- [x] 斩杀检测与提示（含法力校验）
- [x] **嘲讽最优解**（回溯，非贪心）
- [x] 圣盾 / 风怒 / 剧毒 / 突袭 / 冲锋
- [x] 法术直伤、法伤、英雄技能
- [x] **AOE / 解场 / 消灭变形** 法术模拟（竞技场 P0/P1/P2，见 `docs/ARENA_SPELL_*`）
- [x] **战吼**直伤与场面 buff（`battlecry_board`）
- [x] **连击 / 流放 / 亮边**（`combo_board`）
- [x] **回合结束**伤害（嚼嚼怪、棘嗣幼龙、工厂机器人 MC 等）
- [x] **地标**、武器、手牌武器/冲锋
- [x] **亡语**（有效血、嘲讽召唤挡脸）
- [x] **先法后攻 / 穿插攻击**（疯狂药水、战吼清场等）
- [x] 随机线路 **蒙特卡洛** 概率斩杀
- [x] 对手**下回合疲劳**计入斩杀阈值
- [x] 对手**斩杀威胁**预警

**界面与工具**
- [x] **游戏内浮层** Overlay（场攻、斩杀、连招步骤）
- [x] 浮层**设置面板**（主题、缩放、显示项）
- [x] Power.log **回放验证**与 HDT 对比（可选插件）
- [x] **555+** 回归测试（见 `docs/TEST_CASES_REVIEW.md`）

### 待扩展功能

以下尚未完成或仅部分支持：

- [ ] **Zone.log** 解析（起手 unknown 手牌识别更准；当前与 HDT 一样主要依赖 Power.log）
- [ ] **完整牌库追踪**（已知张数/疲劳；未知具体牌序与对手牌库内容）
- [ ] **对手手牌内容**（仅可见/已知卡，无法读未揭示牌）
- [ ] **非竞技场**模式全面覆盖（当前卡池与逻辑以竞技场为主）
- [ ] **独立桌面 GUI**（现有为游戏内浮层，非 HDT 式主窗口）
- [ ] 牌组导入/导出
- [ ] 自动出牌 / ML 预测（不在当前范围）

## 📊 性能优化

仿照 HDT 的优化策略：

1. **预编译正则表达式**
   ```python
   class PowerRegex:
       FULL_ENTITY = re.compile(r"FULL_ENTITY...")  # 只编译一次
   ```

2. **异步日志处理**
   - 独立线程读取日志
   - 避免阻塞主程序

3. **增量读取**
   - 只读取新增内容
   - 记录文件位置

4. **智能防抖**
   - 2秒内只检查一次斩杀
   - 避免频繁输出

## 🐛 故障排除

### 问题1: 找不到日志文件

**解决方案:**
1. 确保炉石传说已安装
2. 至少启动过一次游戏
3. 检查安装路径是否正常

### 问题2: 没有输出游戏状态

**解决方案:**
1. 确保已重启炉石传说（应用 log.config）
2. 检查 `log.config` 是否正确安装
3. 进入一局游戏测试

### 问题3: 手牌识别不全

**说明:**
- 起手留牌在日志中显示为空
- 只有抽到的牌会显示完整信息
- 这是日志解析的固有限制
- HDT 也有同样的限制

### 问题4: 斩杀计算不准确

**解决方案:**
1. 检查卡牌是否在数据库中
2. 在 `lethal_checker.py` 中添加缺失的卡牌
3. 提交 Issue 或 PR

## 🔍 代码架构详解

### 1. 日志监控流程

```
炉石传说游戏
    ↓ 写入日志
Power.log
    ↓ 监控
LogWatcher (独立线程)
    ↓ 读取新行
PowerLogParser
    ↓ 解析
GameState (更新状态)
    ↓ 触发
LethalChecker (检测斩杀)
    ↓ 输出
控制台提示
```

### 2. 实体系统

```python
Entity (实体)
    - entity_id: 实体ID
    - card_id: 卡牌ID
    - controller: 控制者
    - zone: 区域
    - tags: 标签字典
    - 属性: atk, health, damage, cost...
    - 方法: can_attack(), current_health()...
```

### 3. 事件系统

```python
# 注册事件处理器
power_parser.on("tag_changed", handler)
power_parser.on("entity_updated", handler)

# 触发事件
power_parser.emit("tag_changed", entity, tag, value)
```

## 📚 扩展开发

### 添加新卡牌

在 `lethal_checker.py` 中：

```python
SPELL_DAMAGE_DB = {
    "CARD_ID": (cost, damage, needs_target),
    "CS2_029": (4, 6, True),  # 火球术
    # 添加你的卡牌...
}

CHARGE_MINIONS_DB = {
    "CARD_ID": (cost, attack),
    "CS2_124": (3, 3),  # 狼骑兵
    # 添加你的卡牌...
}
```

### 添加新的日志解析器

```python
from hdt_python.log_watcher import LogWatcher

class ZoneLogParser(LogWatcher):
    def process_line(self, line: str):
        # 解析 Zone.log
        pass

# 注册到管理器
zone_log = os.path.join(log_dir, "Zone.log")
zone_parser = ZoneLogParser(zone_log, game_state)
log_manager.register_watcher("Zone", zone_parser)
```

### 自定义事件处理

```python
def on_lethal_detected(total_damage, sources):
    # 自定义处理
    print(f"检测到斩杀！{total_damage}点伤害")
    # 播放声音、发送通知等...

power_parser.on("tag_changed", on_lethal_detected)
```

## 🤝 对比分析

### vs 原始实现 (hs_ai.py)

| 特性 | 原始版本 | HDT Python版 |
|-----|---------|-------------|
| 架构 | 单文件 | 模块化 |
| 日志监控 | 单线程阻塞 | 多线程异步 |
| 正则表达式 | 每次编译 | 预编译 |
| 事件系统 | 无 | 完整支持 |
| 可扩展性 | 低 | 高 |
| 性能 | 一般 | 优化 |
| 代码组织 | 较乱 | 清晰 |

### vs HDT (C#)

| 特性 | HDT (C#) | 我们的实现 (Python) |
|-----|----------|-------------------|
| 语言 | C# | Python |
| 日志解析 | ✅ | ✅ 完全一致 |
| 内存读取 | ✅ (HearthMirror) | ❌ 不需要 |
| GUI | ✅ WPF | ❌ 控制台 |
| 性能 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 开发难度 | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 可维护性 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🎓 学习资源

### HDT 源码

- GitHub: https://github.com/HearthSim/Hearthstone-Deck-Tracker
- 重点文件:
  - `LogWatcherManager.cs` - 日志监控
  - `PowerHandler.cs` - Power.log 解析
  - `Entity.cs` - 实体系统

### 相关资源

- HearthSim 组织: https://hearthsim.info/
- python-hearthstone: https://github.com/HearthSim/python-hearthstone
- 日志格式文档: https://github.com/jleclanche/fireplace/wiki/How-to-enable-logging

## 📝 更新日志

### v1.0.0 (2025-01)

- ✅ 完整的 HDT 风格架构
- ✅ Power.log 解析器
- ✅ 游戏状态管理
- ✅ 斩杀检测器
- ✅ 事件驱动系统
- ✅ 自动配置安装

## 📄 许可证

本项目基于 HearthSim/Hearthstone-Deck-Tracker 的实现思路，使用 Python 重写。

仅供学习和个人使用。

## 👨‍💻 作者

基于 Hearthstone Deck Tracker 的实现方式
Python 版本实现

---

**享受游戏，永不错过斩杀！ ⚔️**
