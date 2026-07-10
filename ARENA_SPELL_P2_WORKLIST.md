# P2 法术实施清单（2 张，1 张已完成）

> **实施顺序**：按下方 2 个分类依次完成，类内按 `games` 降序。  
> **入选条件**：HSReplay `num_games` < 100（P0 ≥500，P1 100–499）；尚未接入 `SPELL_DAMAGE_DB` / `BOARD_CLEAR_SPELLS`。  
> 数据来源: HSReplay `card_stats/free/?ArenaTimestampRangeFilter=LAST_4_DAYS`  
> 模式: `['ArenaGameTypeFilter.BGT_UNDERGROUND_ARENA', 'ArenaTimestampRangeFilter.LAST_4_DAYS']`  
> 卡牌文本: hearthstonejson `zhCN`  
> 已排除: `SPELL_DAMAGE_DB` + `BOARD_CLEAR_SPELLS` 已收录卡；P3 手动降级见 `ARENA_SPELL_PRIORITY.md`  
> **默认规则**：单体法术点敌方随从时仅考虑嘲讽（卡牌另有说明的除外）。  

## 分类概览

| 序号 | 分类 | 数量 | 建议接入位置 |
|------|------|------|--------------|
| 1 | SPELL_DAMAGE 直伤 | 1 | `spell_p2_direct.py` / `BOARD_CLEAR_SPELLS` ✅ |
| 2 | spell_board 复杂 AOE | 1 | `spell_p2_aoe.py` / `BOARD_CLEAR_SPELLS` |

**P2 合计: 2 张**（1 + 1）

---

## 1. SPELL_DAMAGE 直伤（1 张）

接入: `spell_p2_direct.py` / `SPELL_DAMAGE_DB`

| # | card_id | 中文名 | 英文名 | 费 | games | 状态 | 标签 | 中文描述 |
|---|---------|--------|--------|----|-------|------|------|----------|
| 1 | `TIME_600` | 精确射击 | Precise Shot | 2 | 97 | ✅ | 直伤 | 造成$3点伤害。如果本牌位于你手牌的正中间，改为造成 $5点。 |

### 实现说明（`spell_p2_direct.py`）

| 项 | 规则 |
|----|------|
| 伤害 | `POWERED_UP` 亮边 **5** 点，否则 **3** 点 |
| 目标 | `_apply_optimal_single_target_damage`：无嘲打脸，有嘲仅点嘲讽随从 |
| 注册 | `BOARD_CLEAR_SPELLS` |

---

## 2. spell_board 复杂 AOE（1 张）

接入: `spell_p2_aoe.py` / `BOARD_CLEAR_SPELLS`

| # | card_id | 中文名 | 英文名 | 费 | games | 状态 | 标签 | 中文描述 |
|---|---------|--------|--------|----|-------|------|------|----------|
| 2 | `RLK_534` | 灵魂弹幕 | Soul Barrage | 4 | 50 | 待做 | 直伤,解场伤,敌AOE | 当你使用或弃掉这张牌时，造成$5点伤害，随机分配到所有敌人身上。 |

### 实现要点

| 项 | 说明 |
|----|------|
| 打出触发 | **使用**时：对「所有敌人」（英雄 + 敌方随从）随机分配共 **5** 点伤害 |
| 弃牌触发 | v1 **不模拟**弃牌路径（场攻/斩杀仅枚举「打出」序列） |
| 随机分配 | 复用 `_apply_random_split_damage` 或同类；斩杀取 **MC / 乐观上界**（与 `TLC_249` 等一致） |
| 解嘲关系 | 随机可打随从，通常不单独枚举「先解嘲再弹幕」；与 P0 随机直伤法术同策略 |
| 注册 | `BOARD_CLEAR_SPELLS`；`uses_random=True` |

---

## 实施说明

- 模块命名仿 P0/P1：`spell_p2_direct.py`、`spell_p2_aoe.py`（本批仅 2 张，可不拆更多文件）。
- 注册方式与 P0 相同：直伤进 `SPELL_DAMAGE_DB`，场面法术进 `BOARD_CLEAR_SPELLS`；在 `spell_board.py` 或 `lethal_checker` 导入链中 `import spell_p2_*` 触发注册。
- 测试建议：`test_p2_spells_registered`；`TIME_600` 手牌 3/5/7 张正中/非正中；`RLK_534` 无嘲直伤 5、有嘲随机上界。
- P0（126 张）与 P1（14 张）已完成；P3（17 张）与斩杀无关，暂不实现。

---

## 与 P0/P1 对照

| 级别 | games 条件 | 数量 | 状态 |
|------|------------|------|------|
| P0 | ≥ 500 | 126 | ✅ 已完成 |
| P1 | 100–499 | 14 | ✅ 已完成 |
| **P2** | **< 100** | **2** | **1/2 已完成** |
| P3 | 手动降级 | 17 | 暂不实现 |

重新生成总表: `python scripts/generate_arena_spell_priority.py`
