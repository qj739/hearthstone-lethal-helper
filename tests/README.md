# 测试说明

本项目 `tests/` 目录包含 **约 555 个** 自动化用例，覆盖斩杀判定、场攻计算、法术模拟、嘲讽最优解、Power.log 回放等。

**完整分类与审核表** → [`docs/TEST_CASES_REVIEW.md`](../docs/TEST_CASES_REVIEW.md)  
**每个用例场面明细（对手血/场面/手牌）** → [`docs/TEST_CASES_SCENARIOS.md`](../docs/TEST_CASES_SCENARIOS.md)

重新生成场面明细：

```powershell
python tools/extract_test_scenarios.py
```

---

## 快速开始

```powershell
# 基础冒烟
python tests/test_hdt.py
python tests/test_taunt.py

# 核心斩杀回归
python tests/test_overlay_lethal_diff_display.py
python tests/test_opponent_fatigue_lethal.py
python tests/test_taunt_false_lethal.py
python tests/test_chogall_lethal_regress.py
```

安装 pytest 后一键运行：

```powershell
pip install pytest
python -m pytest tests/ -q
```

---

## 目录结构（按机制）

| 类型 | 代表文件 | 说明 |
|------|----------|------|
| **斩杀回归** | `test_*_lethal.py` | 单卡/组合能否正确判斩 |
| **场攻/回合结束** | `test_end_turn_board.py` | 嚼嚼怪、棘嗣幼龙、工厂机器人等 |
| **法术模拟** | `test_spell_board.py` | 最大集：月亮井、穿插、MC、技能 |
| **嘲讽** | `test_taunt.py`, `test_optimal_taunt.py`, `test_taunt_false_lethal.py` | 最优解 + 误报回归 |
| **Overlay UI** | `test_overlay_lethal_diff_display.py` | 变红、差值、下回合预览 |
| **解析/身份** | `test_player_id_replay.py`, `test_attack_tags.py` | PlayerID、ATK 标签 |
| **注册门禁** | `test_arena_season_registered.py` | 竞技场卡牌表完整性 |
| **回放** | `test_*_from_power_log*` | 依赖 `Logs/`，缺文件则 SKIP |

---

## 优先级

1. **P0** — Overlay 误报/漏报、嘲讽误斩、PlayerID 颠倒、法力虚斩  
2. **P1** — 复杂法术线、回合结束 MC、手牌冲锋、亡语有效血  
3. **P2** — 卡牌注册表是否齐全  
4. **P3** — 解析细节、UI 冒烟  

详见 [`docs/TEST_CASES_REVIEW.md`](../docs/TEST_CASES_REVIEW.md) 第九节审核清单。

---

## 回放用例

部分测试读取 `Logs/split_games/` 下的 Power.log。本地无日志时会跳过，不影响其它用例。

环境变量（可选）：

```powershell
$env:HS_PLAYER_NAME="你的战网昵称#1234"
```

---

## 贡献新用例

1. 文件名：`test_<机制或卡牌>_lethal.py`  
2. 每个 `test_*` 写清 **中文 docstring**（场面、期望、防什么回归）  
3. 优先 **构造最小 GameState**，避免依赖完整 log  
4. 必须依赖 log 时，用 `if not log_path.exists(): return` 或 `pytest.skip`
