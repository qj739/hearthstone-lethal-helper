# 测试用例审核目录

> **用途**：整理项目内复杂回归用例，供审核后发布到 GitHub。  
> **统计**：`tests/` 下 **82** 个文件、约 **555** 个 `test_*` 函数（2026-07-11 扫描）。

**场面明细（对手血 / 双方场面 / 手牌）** → [`TEST_CASES_SCENARIOS.md`](TEST_CASES_SCENARIOS.md)  
（由 `python tools/extract_test_scenarios.py` 从测试代码自动生成，可重复执行更新）

---

## 审核说明

| 列 | 含义 |
|----|------|
| **优先级** | P0=核心回归必留 · P1=复杂斩杀/场攻 · P2=单卡注册 · P3=基础设施 |
| **类型** | `unit` 纯构造场面 · `replay` 回放 Power.log · `regress` 修过的历史 bug |
| **审核** | 留空供你勾选：✅ 保留 / ❌ 删除 / 📝 需补说明 |

---

## 一、P0 · 核心回归（建议必留）

这些用例直接对应用户可见的误报/漏报，与 Overlay 变红、斩杀提示强相关。

### 1.1 Overlay 斩杀显示

| 审核 | 文件 | 用例 | 场景摘要 | 防什么 |
|------|------|------|----------|--------|
| | `test_overlay_lethal_diff_display.py` | `test_overlay_red_prompt_ok_on_opponent_turn` | 对方回合场攻 13、对手 13 血 | 下回合斩预览不变红 |
| | | `test_overlay_diff_damage_not_inflated_when_not_lethal` | MC 抬高 total 但 has_lethal=False | 差 0 却不亮红 |
| | | `test_apply_overlay_board_lethal_does_not_inflate_total_when_mana_fails` | 场攻够但法力不够 | 虚报斩杀 |
| | `test_opponent_fatigue_lethal.py` | `test_opponent_turn_fatigue_lowers_lethal_threshold` | 牌库空、疲劳 3、15 血、场攻 12 | 下回合斩未计疲劳 |
| | | `test_local_turn_fatigue_not_counted` | 我方回合同场面 | 疲劳双重扣减 |
| | `test_taunt_false_lethal.py` | `test_taunt_blocks_board_lethal_when_not_enough_face` | 5/5 嘲 + 8 场攻 vs 6 血 | 场攻绕过嘲讽误斩 |
| | | `test_red_card_dormant_enemy_not_counted_as_taunt` | 红牌休眠嘲 | 休眠嘲挡脸 |
| | `test_lifesteal_taunt_lethal.py` | `test_lifesteal_taunt_gdb_320_not_false_lethal` | 吸血嘲讽抬高有效血 | 场攻不足误报斩 |
| | `test_forgefiend_armor_lethal.py` | `test_forgefiend_deathrattle_blocks_false_lethal` | 换熔魔亡语 +8 甲 | 未清场误斩 |
| | `test_chogall_lethal_regress.py` | `test_chogall_turn_start_not_lethal_on_18` | 加尔手臂附魔重复叠攻 | 18 血假斩杀 |
| | `test_opponent_lethal_threat.py` | `test_opponent_imps_threat_when_player_id_swapped` | PlayerID 颠倒 | 敌斩威胁漏报 / 误报我能斩 |
| | `test_dubious_no_combo_face.py` | `test_dubious_without_combo_does_not_inflate_face_to_21` | 可疑交易未连击 | 场攻虚增到 21 |
| | `test_toy601_end_turn_double_count.py` | `test_toy601_end_turn_not_double_counted_in_overlay` | 工厂装配机回合结束 | 回合结束伤害双计 |
| | `test_overlay_false_dormant_et.py` | `test_spell_clear_no_false_dormant_et` | 活体根须+潮起潮落 | 误显示「回 X」回合结束 |

**运行**：
```powershell
python tests/test_overlay_lethal_diff_display.py
python tests/test_opponent_fatigue_lethal.py
python tests/test_taunt_false_lethal.py
python tests/test_chogall_lethal_regress.py
```

---

### 1.2 嘲讽最优解

| 审核 | 文件 | 用例 | 场景摘要 |
|------|------|------|----------|
| | `test_taunt.py` | `test_scenario_1` ~ `5` | 无嘲 / 小嘲 / 大嘲 / 法术绕过 / 圣盾嘲 |
| | `test_optimal_taunt.py` | `test_case_1` ~ `6` | 贪心劣于最优、多嘲、圣盾、风怒、剧毒 |
| | `test_deathrattle_taunt_summon_face.py` | 4 个用例 | 淤泥/山岭野熊/邪鬼皇后/盘牙督军亡语嘲 |

**运行**：`python tests/test_taunt.py` · `python tests/test_optimal_taunt.py`

---

### 1.3 玩家识别 / 回放

| 审核 | 文件 | 用例 | 场景摘要 | 防什么 |
|------|------|------|----------|--------|
| | `test_player_id_replay.py` | `test_begin_new_game_clears_stale_player_names` | 新局 CREATE_GAME | 沿用上一局 PlayerID |
| | | `test_lethal_game_player2_and_lethal_mid_turn` | 6/29 对局回放 | 我方 Player2 时算错斩杀 |
| | | `test_penultimate_turn_cataclysm_lethal_line` | 火球/喷吐后大灾变线 | 组合线漏算 |
| | `test_board_player_id.py` | `test_full_replay_local_is_player1_with_yog` | YOG vs TTN 对手场面 | 敌我场面颠倒 |
| | `test_zero_config_identity.py` | 2 个用例 | DebugPrintGame / FRIENDLY_PLAYER | 零配置识别 |

---

### 1.4 法力与斩杀资格

| 审核 | 文件 | 用例 | 场景摘要 |
|------|------|------|----------|
| | `test_lethal_mana.py` | `test_no_lethal_when_starfire_unaffordable` | 剩 2 费打不出 6 费星火 |
| | | `test_lethal_when_starfire_affordable` | 剩 7 费可星火斩 15 |
| | | `test_lethal_turn_start_despite_zero_mc_prob_replay_10656` | 确定性 13≥13，MC p=0 仍提示 |
| | `test_infestation_lethal_mana.py` | 3 个用例 | 虫害侵扰 + 武器法力边界 |
| | `test_lethal_prefers_simpler_line.py` | `test_dubious_purchase_alone_not_stacked_with_natural_causes` | 单卡可斩不叠复杂线 |

---

## 二、P1 · 复杂斩杀场景（按机制分类）

### 2.1 回合结束伤害（41 用例）

**文件**：`test_end_turn_board.py`

| 子类 | 代表用例 | 卡牌/机制 |
|------|----------|-----------|
| 休眠 | `test_magtheridon_dormant_end_turn` | 玛瑟里顿 +3 |
| 随机 MC | `test_factory_bot_prob_lethal_at_six_hp` | 工厂装配机 6 攻随机 |
| 最低血目标 | `test_masticator_*`（4 个） | 侏儒嚼嚼怪打最低血 |
| 手牌打出 ET | `test_masticator_hand_opp_turn_overlay` | 对方回合下回合打出嚼嚼怪 |
| 光环离场 | `test_mograine_aura_without_minion` | RLK_706e3 英雄 +3 |
| 溢出攻击 | `test_thornmantle_*`（10+ 个） | 棘嗣幼龙 EDR_453 溢出 |
| 刚上场 pure | `test_pure_board_face_includes_end_turn_on_summon` | 当回合不能攻仍计 ET |
| 回合切换 | `test_current_player_handoff_at_turn_start` | CURRENT_PLAYER 交接 |

**运行**：`python tests/test_end_turn_board.py`（部分用例需完整 pytest 或单独函数）

---

### 2.2 法术组合 / 穿插（100 用例）

**文件**：`test_spell_board.py`（最大单文件）

#### 2.2.1 月亮井线（高频回归）

| 用例 | 场景 |
|------|------|
| `test_moonwell_clears_taunt_and_face` | 月亮井清嘲 + 场面打脸 |
| `test_moonwell_lifesteal_minion_still_lethal_from_log` | 吸血龙不应阻止斩杀 |
| `test_moonwell_play_animation_keeps_lethal_overlay` | 月亮井 PLAY 动画期间保持红 |
| `test_moonwell_dragon_breath_*`（`test_moonwell_dragon_breath.py` 5 个） | 月亮井 + 龙息 + 沉默问题学生 |
| `test_huntress_board_line_not_lethal_at_17_from_log` | 女猎手线不应误斩 17 血 |

#### 2.2.2 先法后攻 / 穿插

| 用例 | 场景 |
|------|------|
| `test_hellfire_attack_first_face`（`test_hellfire_attack_first_face.py`） | 地狱烈焰前先随从攻 |
| `test_p1_broxigar_interleave_face` | 布洛克斯加奋战穿插 |
| `test_potion_sludge_interleave_face`（`test_potion_of_madness.py`） | 疯狂药水 + 淤泥 |
| `test_p0_hostile_invader_interleaved_*` | 入侵者战吼清场穿插 |

#### 2.2.3 随机 / MC

| 用例 | 场景 |
|------|------|
| `test_p0_bursting_shot_mc_stats` | 爆裂射击随机直伤 |
| `test_p0_devolving_missiles_sludge_three_taunts_mc_overlay` | 衰变飞弹 + 淤泥 MC |
| `test_p0_baking_soda_volcano_deterministic_clear_at_10_hp` | 苏打火山确定性清场 |
| `test_remixed_rhapsody_emotional_hero_buff_not_overwritten_by_random_spell` | 动情狂想曲不被 MC 覆盖 |

#### 2.2.4 英雄技能 / 武器 / 变形

| 用例 | 场景 |
|------|------|
| `test_p0_hero_power_dh_claws_opp_turn_next_turn` | 对方回合下回合恶魔之爪刷新 |
| `test_p0_deathwing_turn_start_from_split_log` | 手牌灭世者推断无情 +5 |
| `test_p0_reborn_taunt_*` | 复生嘲讽挡脸 |
| `test_p0_buffed_bear_mace_*` | BUFF 武器 479 滞后 |

#### 2.2.5 注册覆盖（CI 门禁）

| 用例 | 覆盖 |
|------|------|
| `test_p0_minion_spells_registered` | P0 解场伤 33 张 |
| `test_p0_aoe_spells_registered` | P0 复杂 AOE 33 张 |
| `test_p0_remove_spells_registered` | 消灭/变形 17 张 |
| `test_p1_spells_registered` | P1 法术 14 张 |
| `test_p2_spells_registered` | P2 法术 |
| `test_eudora_loot_registered` | 尤朵拉战利品 11 张 |

---

### 2.3 疯狂药水（15 用例）

**文件**：`test_potion_of_madness.py`

| 用例 | 场景 |
|------|------|
| `test_potion_steal_2_1_face` | 偷 2/1 当回合打脸 2 |
| `test_potion_sludge_and_22_taunt_interleave_face` | 淤泥 + 2/2 嘲穿插 |
| `test_potion_steal_does_not_drop_friendly_board_slot` | 偷取不挤掉友方槽位 |
| `test_potion_stolen_deathrattle_summons_friendly` | 被偷亡语算我方 |
| `test_decimation_not_recommended_when_attack_first_lethal_without_it` | 先攻够斩不推荐屠灭 |

---

### 2.4 突袭 / 冲锋 / 手牌场攻

| 文件 | 代表场景 |
|------|----------|
| `test_rush_board.py` | 突袭当回合不打脸、下回合预览可打脸 |
| `test_face45_hand_charge_display.py` | 场攻主数字不含手牌冲锋 |
| `test_army_of_the_dead_lethal.py` | 亡者大军 RLK_060 突袭空场斩 |
| `test_call_of_the_wild_lethal.py` | 兽群呼唤霍弗 + 雷欧克 |
| `test_fire_elemental_lethal.py` | 火元素战吼直伤 |

---

### 2.5 亡语 / 吸血 / 法强

| 文件 | 代表场景 |
|------|----------|
| `test_deathrattle.py` | ARENA 亡语表 14 张 + 机制 |
| `test_spell_power_lethal.py` | 英雄法强 + 激寒急流斩 16 |
| `test_moonwell_lifesteal_lethal.py` | 挂刀前 5 血应斩 |
| `test_denathrius_lethal.py` | 注能 TAG_SCRIPT + 随机分配 |
| `test_climactic_necrotic_lethal.py` | 通灵最强音动态伤害 |

---

### 2.6 单卡斩杀回归（精选）

| 审核 | 文件 | 卡牌 | 要点 |
|------|------|------|------|
| | `test_putricide_potion_lethal.py` | 普崔塞德药剂 | 回放 L61400 斩杀回合 |
| | `test_end_022_lethal.py` | END_022 时光扭曲先知 | 先知 + 火焰冲击 + 法强 |
| | `test_fel_barrage_hero_first_lethal.py` | 邪能弹幕 | 先英雄攻再法术 |
| | `test_supernova_cathedral_lethal.py` | 超新星 + 赎罪教堂 | 20 血斩杀 |
| | `test_hip_hop_lethal.py` | ETC_717 嘻哈双形态 | 刺耳/悦耳 + 武器 |
| | `test_hold_them_off_lethal.py` | 拦住他们！ | +5/+5 buff 启用斩杀 |
| | `test_holy_nova_hold_lethal.py` | 神圣新星 + 拦住他们 | 清嘲后 buff 斩 |
| | `test_corpsicle_lethal.py` | VAC_427 甜筒 | 残骸法术 3 伤 |
| | `test_crusader_aura_lethal.py` | 十字军光环 | 攻击时 +2 伤 |
| | `test_reliable_companion_lethal.py` | 可靠陪伴 | buff + 麦芽岩浆 |
| | `test_clear_conscience_lethal.py` | 问心无愧 | 友方 +2/+3 |
| | `test_transform_lethal.py` | CHANGE_ENTITY | 变形后 ET / 攻击资格 |

---

### 2.7 地标 / 战吼 / 特殊

| 文件 | 场景 |
|------|------|
| `test_location_board.py` | 赎罪教堂目标选择、喷发火山档位 |
| `test_ball_hog.py` | 球霸野猪人打最低血 |
| `test_banana_bunch.py` | 一串香蕉连打 3 次 |
| `test_boneblade_flurry.py` | 骨刃乱舞亮边 +3 |
| `test_collaborative_spark.py` | 协作火花杀随从 buff |
| `test_frozen_touch_infuse.py` | 注能之触回手双次 |
| `test_arcane_arrow_manathirst.py` | 奥术箭法力渴求 8 水晶 |

---

## 三、P2 · 注册与数据完整性

**文件**：`test_arena_season_registered.py`

| 用例 | 检查内容 |
|------|----------|
| `test_gap_spells_registered` | 缺口报告法术已注册 |
| `test_gap_battlecries_registered` | 战吼表 |
| `test_gap_rush_registered` | 突袭表 |
| `test_gap_weapons_registered` | 武器表 |
| `test_gap_combo_registered` | 连击表 |
| `test_gap_deathrattle_registered` | 亡语表 |
| `test_gap_end_turn_registered` | 回合结束表 |

**文件**：`test_end_turn_board.py` · `test_end_turn_p1_registered` · `test_end_turn_registered_cards_in_card_db`

---

## 四、P3 · 解析 / 场攻 / UI 基础设施

| 分类 | 文件 | 要点 |
|------|------|------|
| 攻击力标签 | `test_attack_tags.py` | ATK / 479 / 4472 滞后 |
| BUFF 场攻 | `test_buff_board_atk.py` | 加尔手臂不双叠、法老猫 script |
| 武器 | `test_weapon_board.py` | 埃提耶识、双武器不计、敲狼锤 |
| 休眠 | `test_dormant_magtheridon_overlay.py` | 场攻展示 vs 斩杀计入 |
| 回合刷新 | `test_turn_refresh_stale_attacks.py` | NUM_ATTACKS 残留 |
| Overlay UI | `test_overlay.py` | 白底/半透明/窗口检测 |
| Combo 文案 | `test_overlay_target_label.py` | 步骤目标「嘲讽」标签 |
| 玩家身份 | `test_player_identity.py` | 战网名匹配 |
| 终局 | `test_playstate_end.py` | LOSING 不结束对局 |
| 基础 | `test_hdt.py` | 导入、日志路径、GameState |

---

## 五、Power.log 回放用例索引

以下用例依赖 `Logs/` 或环境变量，**缺日志时自动 SKIP**：

| 文件 | 用例 | 日志场景 |
|------|------|----------|
| `test_player_id_replay.py` | `test_penultimate_turn_cataclysm_lethal_line` | 6/29 雄鹿大灾变 |
| `test_putricide_potion_lethal.py` | `test_putricide_potion_lethal_from_power_log` | L61400 |
| `test_infestation_lethal_mana.py` | `test_lethal_penultimate_turn_replay_91587` | 虫害侵扰 7 血斩 |
| `test_lethal_mana.py` | `test_lethal_turn_start_despite_zero_mc_prob_replay_10656` | 13≥13 MC p=0 |
| `test_spell_board.py` | `test_moonwell_lifesteal_minion_still_lethal_from_log` | 最后一局 9 血 |
| `test_spell_board.py` | `test_hellfire_then_hot_coals_lethal_from_log_093429` | 地狱烈焰+炽热火炭 |
| `test_spell_board.py` | `test_p0_deathwing_lethal_from_log_before_relentless_played` | 灭世者发现前 |
| `test_banana_bunch.py` | `test_from_power_log` | 一串香蕉 |
| `test_frozen_touch_infuse.py` | `test_infused_play_from_power_log` | 注能之触 |
| `test_hold_them_off_prepare_cost.py` | `test_prepared_hold_from_power_log` | PREPARED 减费 |
| `test_holy_nova_hold_lethal.py` | `test_holy_nova_hold_lethal_from_power_log` | 神圣新星+拦住 |
| `test_simulate_line_outcome_unpack.py` | `test_overlay_face_no_unpack_error_on_moonwell_board` | 月亮井+龙息 unpack |

> **发布建议**：回放用例在 README 注明「需放置 anonymized log 片段」或保留 SKIP 逻辑。

---

## 六、按文件完整索引

<details>
<summary>点击展开 82 个测试文件清单</summary>

| 文件 | 用例数 | 模块说明 |
|------|--------|----------|
| `test_spell_board.py` | 100 | 法术模拟主集 |
| `test_end_turn_board.py` | 41 | 回合结束场攻 |
| `test_deathrattle.py` | 14 | 亡语机制 |
| `test_potion_of_madness.py` | 15 | 疯狂药水 |
| `test_location_board.py` | 10 | 地标 |
| `test_denathrius_lethal.py` | 7 | 德纳修斯 |
| `test_weapon_board.py` | 7 | 武器场攻 |
| `test_arena_season_registered.py` | 7 | 注册门禁 |
| `test_attack_tags.py` | 7 | ATK 标签 |
| `test_player_id_replay.py` | 7 | 回放 PlayerID |
| `test_taunt_false_lethal.py` | 6 | 嘲讽误斩 |
| `test_boneblade_flurry.py` | 6 | 骨刃乱舞 |
| `test_frozen_touch_infuse.py` | 6 | 注能之触 |
| `test_optimal_taunt.py` | 6 | 嘲讽最优 |
| `test_moonwell_dragon_breath.py` | 5 | 月亮井+龙息 |
| `test_buff_board_atk.py` | 5 | BUFF 攻 |
| `test_banana_bunch.py` | 5 | 香蕉 |
| `test_overlay_lethal_diff_display.py` | 5 | Overlay 斩杀 UI |
| `test_taunt.py` | 5 | 嘲讽基础 |
| `test_army_of_the_dead_lethal.py` | 4 | 亡者大军 |
| `test_ball_hog.py` | 4 | 球霸 |
| `test_collaborative_spark.py` | 4 | 协作火花 |
| `test_deathrattle_taunt_summon_face.py` | 4 | 亡语嘲挡脸 |
| `test_hdt.py` | 4 | 基础冒烟 |
| `test_rush_board.py` | 4 | 突袭 |
| *(其余 58 个文件各 1~3 用例)* | | 见仓库 `tests/` |

</details>

---

## 七、推荐发布结构（GitHub）

审核通过后建议仓库结构：

```
tests/
  README.md                 ← 快速运行说明（已生成）
  regression/               ← 可选：将 P0 回归迁入子目录
  spells/                   ← 可选：spell_board 拆分
  replay/                   ← 可选：集中回放用例 + fixtures
docs/
  TEST_CASES_REVIEW.md      ← 本文档（审核用）
  ARENA_TURN_START_NO_LETHAL_REVIEW.md  ← 实战胜局复盘（已有）
```

### 建议 CI 分层

| 阶段 | 范围 | 耗时 |
|------|------|------|
| **smoke** | `test_hdt` + `test_taunt` + `test_overlay_lethal_diff_display` + `test_opponent_fatigue_lethal` | <5s |
| **core** | P0 全部 + `test_taunt_false_lethal` + `test_chogall_lethal_regress` | <30s |
| **full** | 全量 `tests/`（需 pytest 或统一 runner） | 数分钟 |

---

## 八、运行方式

### 单文件（当前多数文件支持 `python tests/xxx.py`）

```powershell
cd c:\Users\WIN10\Desktop\hs_claude\HS
python tests/test_opponent_fatigue_lethal.py
python tests/test_overlay_lethal_diff_display.py
python tests/test_taunt_false_lethal.py
```

### 批量冒烟（PowerShell）

```powershell
Get-ChildItem tests\test_*lethal*.py | ForEach-Object { python $_.FullName 2>&1 | Select-Object -Last 1 }
```

### 安装 pytest 后（推荐长期）

```powershell
pip install pytest
python -m pytest tests/ -q --tb=no
```

---

## 九、审核清单（请你勾选）

- [ ] **P0 Overlay/斩杀回归** — 第一节 1.1~1.4 全部保留？
- [ ] **回合结束** — `test_end_turn_board.py` 是否拆分发布（文件较大）？
- [ ] **法术主集** — `test_spell_board.py` 100 用例是否作为核心资产公开？
- [ ] **回放用例** — 是否附带 anonymized log，或文档标明 SKIP？
- [ ] **注册门禁** — `test_arena_season_registered.py` 是否进 CI？
- [ ] **文档** — 本文档 + `tests/README.md` 是否满足 GitHub 说明需求？
- [ ] **命名** — 是否需要中文用例说明进 README（当前 docstring 已多为中文）？

---

## 十、已知问题（审核时注意）

| 问题 | 影响 | 建议 |
|------|------|------|
| 未安装 pytest | 无法 `pytest tests/` 一键跑 | README 注明 `pip install pytest` |
| 部分文件 `python xxx.py` 报错 | 如 `test_spell_board.py` 需 pytest 收集 | 审核时标为 `pytest-only` |
| 回放 log 路径硬编码 | 缺 log 则 SKIP | 发布时改相对路径或 fixtures |
| `test_end_turn_board.py` 直接运行部分失败 | 个别用例参数/断言需 pytest fixture | 优先 pytest 运行 |

---

*生成工具：扫描 `tests/test_*.py` AST + docstring，结合 `ARENA_TURN_START_NO_LETHAL_REVIEW.md` 与历史修复记录整理。*
