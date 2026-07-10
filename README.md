# HS Lethal Helper / 炉石斩杀助手

[中文](#中文) | [English](#english)

---

## 中文

### 简介

> **这是竞技场模式专用，用于斩杀计算和提示，让你永不错斩！**

**HS Lethal Helper** 是一款基于 **Power.log 日志解析** 的《炉石传说》**竞技场**辅助工具，思路与 [Hearthstone Deck Tracker (HDT)](https://github.com/HearthSim/Hearthstone-Deck-Tracker) 类似：不读取游戏内存，只监听官方日志，安全、轻量、易于维护。

主要能力：

- 实时监控竞技场对局场面、手牌、法力与回合信息
- **斩杀检测**：自动搜索可斩杀对手的出牌顺序，并估算成功率
- **游戏内浮层**：在炉石窗口上显示推荐连招、场攻与关键提示
- 针对竞技场卡池优化，覆盖大量法术、战吼、武器、冲锋、地标等效果模拟
- 可用 `Power.log` 回放验证，便于回归测试与排错

> 本项目为个人学习与研究用途，与暴雪娱乐无关，也不保证覆盖全部卡牌机制。

### 快速开始

**环境要求：** Windows 10+、Python 3.10+、已安装《炉石传说》

```bash
# 1. 克隆仓库
git clone https://github.com/qj739/hearthstone-lethal-helper.git
cd hearthstone-lethal-helper

# 2. 启动主程序（首次运行会自动安装 log.config）
python hdt_tracker.py

# 3. 打开浮层设置界面（可选）
python hdt_tracker.py --settings
```

首次运行后，若日志未生效，请**重启炉石客户端**一次。

炉石日志默认路径：

```
C:\Program Files (x86)\Hearthstone\Logs\
```

### 项目结构

```
HS/
├── hdt_tracker.py          # 主程序入口
├── overlay_win.py          # Windows 游戏内浮层
├── overlay_settings_ui.py  # 浮层设置界面
├── hdt_python/             # 核心逻辑
├── docs/                   # 文档与竞技场清单
├── tests/                  # 回归测试
├── scripts/                # 工具脚本
└── json/                   # 卡牌数据
```

### 常用命令

| 命令 | 说明 |
|------|------|
| `python hdt_tracker.py` | 启动追踪与斩杀提示 |
| `python hdt_tracker.py --settings` | 打开浮层主题/位置设置 |
| `python tests/test_hdt.py` | 基础功能自检 |
| `quick_test.bat` | 快速跑核心测试 |
| `build_exe.bat` | 打包为 Windows 可执行文件 |

### 工作原理

```
炉石客户端 → 写入 Power.log → LogWatcher 实时 tail
          → PowerLogParser 解析场面 → LethalChecker 搜索斩杀
          → Overlay 在游戏窗口显示推荐连招
```

与 HDT 相同，推荐使用**无边框窗口化**显示模式，浮层叠加效果更稳定。

### 免责声明

- 仅供学习、研究与单机体验辅助，请勿用于任何违反游戏服务条款的行为。
- 卡牌机制复杂且版本更新频繁，检测结果可能存在误报或漏报。
- 作者不对使用本工具造成的任何后果负责。

### 相关文档

- [docs/HDT_PYTHON_README.md](docs/HDT_PYTHON_README.md) — 完整使用说明
- [docs/README_INDEX.md](docs/README_INDEX.md) — 文档索引
- [docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md) — 技术改进记录

### 许可证

本项目以学习研究为目的开源。炉石传说及相关资产归暴雪娱乐所有。

---

## English

### Overview

> **Built for Arena mode — lethal calculation and hints so you never miss lethal!**

**HS Lethal Helper** is an **Arena-focused** *Hearthstone* assistant built on **Power.log parsing**, following the same approach as [Hearthstone Deck Tracker (HDT)](https://github.com/HearthSim/Hearthstone-Deck-Tracker): it does not read game memory, only official log files—keeping things safe, lightweight, and maintainable.

**Features:**

- Real-time Arena board, hand, mana, and turn tracking
- **Lethal detection** — searches for winning play sequences and estimates success probability
- **In-game overlay** — shows recommended combos, board damage, and key hints on top of the Hearthstone window
- Optimized for the Arena card pool; simulates spells, battlecries, weapons, Rush minions, locations, and more
- Replay validation via `Power.log` for regression testing and debugging

> For personal learning and research only. Not affiliated with Blizzard Entertainment. Not all card mechanics are guaranteed to be covered.

### Quick Start

**Requirements:** Windows 10+, Python 3.10+, Hearthstone installed

```bash
# 1. Clone the repository
git clone https://github.com/qj739/hearthstone-lethal-helper.git
cd hearthstone-lethal-helper

# 2. Run the tracker (installs log.config on first launch)
python hdt_tracker.py

# 3. Open overlay settings (optional)
python hdt_tracker.py --settings
```

After the first run, **restart the Hearthstone client** if logging is not active yet.

Default log location:

```
C:\Program Files (x86)\Hearthstone\Logs\
```

### Project Layout

```
HS/
├── hdt_tracker.py          # Main entry point
├── overlay_win.py          # Windows in-game overlay
├── overlay_settings_ui.py  # Overlay settings UI
├── hdt_python/             # Core logic
├── docs/                   # Documentation & Arena worklists
├── tests/                  # Regression tests
├── scripts/                # Utility scripts
└── json/                   # Card data
```

### Common Commands

| Command | Description |
|---------|-------------|
| `python hdt_tracker.py` | Start tracking and lethal hints |
| `python hdt_tracker.py --settings` | Overlay theme/position settings |
| `python tests/test_hdt.py` | Basic self-check |
| `quick_test.bat` | Run core tests quickly |
| `build_exe.bat` | Build Windows executable |

### How It Works

```
Hearthstone client → writes Power.log → LogWatcher tails in real time
                   → PowerLogParser builds game state → LethalChecker searches lines
                   → Overlay displays recommended combos on the game window
```

Like HDT, **borderless windowed** display mode gives the most reliable overlay behavior.

### Disclaimer

- For learning, research, and offline-style assistance only. Do not use in ways that violate the game's Terms of Service.
- Card mechanics are complex and change frequently; false positives and missed lethals are possible.
- The authors are not responsible for any consequences of using this tool.

### Further Reading

- [docs/HDT_PYTHON_README.md](docs/HDT_PYTHON_README.md) — full usage guide (Chinese)
- [docs/README_INDEX.md](docs/README_INDEX.md) — documentation index
- [docs/IMPROVEMENTS.md](docs/IMPROVEMENTS.md) — technical improvement notes

### License

Open source for educational purposes. *Hearthstone* and related assets are property of Blizzard Entertainment.
