# P1 法术实施清单（14 张 ✅ 全部已完成）

> **实施顺序**：按下方 6 个分类依次完成，类内按 `games` 降序。  
> **入选条件**：HSReplay `num_games` 100–499（P0 为 ≥500）；`FORCE_P1` 手动划入（如 `CATA_526`）。  
> 数据来源: HSReplay `card_stats/free/?ArenaTimestampRangeFilter=LAST_4_DAYS`  
> 模式: `['ArenaGameTypeFilter.BGT_UNDERGROUND_ARENA', 'ArenaTimestampRangeFilter.LAST_4_DAYS']`  
> 卡牌文本: hearthstonejson `zhCN`  
> 已排除: `SPELL_DAMAGE_DB` + `BOARD_CLEAR_SPELLS` 已收录卡；`LOOT_417` 大灾变 → P3  
> **默认规则**：单体法术点敌方随从时仅考虑嘲讽（卡牌另有说明的除外）。  

## 分类概览

| 序号 | 分类 | 数量 | 接入位置 |
|------|------|------|----------|
| 1 | SPELL_DAMAGE 直伤 | 2 | `spell_p1_direct.py` / `BOARD_CLEAR_SPELLS` ✅ |
| 2 | spell_board 解场伤 | 2 | `spell_p1_minion.py` / `BOARD_CLEAR_SPELLS` ✅ |
| 3 | spell_board 复杂 AOE | 3 | `spell_p1_aoe.py` / `BOARD_CLEAR_SPELLS` ✅ |
| 4 | spell_board 加攻 | 2 | `spell_p1_buff.py` / 场攻模块 ✅ |
| 5 | spell_board 其他 | 5 | `spell_p1_other.py` ✅ |

**P1 合计: 14 张**（2 + 2 + 3 + 2 + 5；另含星体平衡衍生 `CS2_008`/`CS2_009`）

---

## 1. SPELL_DAMAGE 直伤（2 张 ✅）

接入: `spell_p1_direct.py` / `BOARD_CLEAR_SPELLS`

| # | card_id | 中文名 | 英文名 | 费 | games | 状态 | 标签 | 中文描述 |
|---|---------|--------|--------|----|-------|------|------|----------|
| 1 | `ONY_010` | 灭龙射击 | Dragonbane Shot | 2 | 494 | ✅ | 直伤 | 造成$2点伤害。<b>荣誉消灭：</b>将一张灭龙射击置入你的手牌。 |
| 2 | `DINO_406` | 喷吐火焰 | Fire Breath | 3 | 283 | ✅ | 直伤 | 造成$4点伤害。使你的元素获得+1/+1。 |

---

## 2. spell_board 解场伤（2 张 ✅）

接入: `spell_p1_minion.py` / `BOARD_CLEAR_SPELLS`

| # | card_id | 中文名 | 英文名 | 费 | games | 状态 | 标签 | 中文描述 |
|---|---------|--------|--------|----|-------|------|------|----------|
| 3 | `EDR_262` | 灵魂联结 | Spirit Bond | 3 | 169 | ✅ | 解场伤 | 对一个随从造成$3点伤害。如果该随从死亡，召唤一只3/2并具有<b>突袭</b>的狼。 |
| 4 | `WC_021` | 不稳定的暗影震爆 | Unstable Shadow Blast | 2 | 158 | ✅ | 解场伤 | 对一个随从造成$6点伤害，超过目标生命值的伤害会命中你的英雄。 |

---

## 3. spell_board 复杂 AOE（3 张 ✅）

接入: `spell_p1_aoe.py` / `BOARD_CLEAR_SPELLS`

| # | card_id | 中文名 | 英文名 | 费 | games | 状态 | 标签 | 中文描述 |
|---|---------|--------|--------|----|-------|------|------|----------|
| 5 | `CATA_526` | 布洛克斯加的奋战 | Broxigar's Last Stand | 2 | 5080 | ✅ | 解场伤,全场AOE | 对所有随从造成$1点伤害。每有一个随从死亡，抽一 张牌。 |
| 6 | `VAC_416` | 死亡翻滚 | Death Roll | 5 | 366 | ✅ | 直伤,移除,敌AOE | 消灭一个敌方随从。造成等同于其攻击力的伤害，随机分配到所有敌人身上。 |
| 7 | `TOY_883` | 掀桌子 | Table Flip | 10 | 280 | ✅ | 解场伤,敌AOE | 对所有敌方随从造成$3点伤害。你每有一张其他手牌，本牌的法力值消耗便减少（1）点。 |

---

## 4. spell_board 加攻（2 张 ✅）

接入: `spell_p1_buff.py` / 场攻模块

| # | card_id | 中文名 | 英文名 | 费 | games | 状态 | 标签 | 中文描述 |
|---|---------|--------|--------|----|-------|------|------|----------|
| 8 | `TSC_006` | 多重打击 | Multi-Strike | 2 | 388 | ✅ | - | 在本回合中使你的英雄获得+2攻击力，并可以额外攻击一次敌方随从。 |
| 9 | `RLK_918` | 为了奎尔萨拉斯！ | For Quel'Thalas! | 2 | 239 | ✅ | - | 使一个友方随从获得+3攻击力。在本回合中，使你的英雄获得+2攻击力。 |

---

## 5. spell_board 其他（5 张 ✅）

接入: `spell_p1_other.py`

| # | card_id | 中文名 | 英文名 | 费 | games | 状态 | 标签 | 中文描述 |
|---|---------|--------|--------|----|-------|------|------|----------|
| 10 | `ETC_082` | 绝望哀歌 | Dirge of Despair | 6 | 457 | ✅ | - | 对一个角色造成$3点伤害。如果该角色死亡，从你的牌库中召唤一个恶魔。 |
| 11 | `SCH_138` | 威能祝福 | Blessing of Authority | 5 | 429 | ✅ | - | 使一个随从获得+8/+8，在本回合中无法攻击英雄。 |
| 12 | `EDR_874` | 星体平衡 | Stellar Balance | 2 | 398 | ✅ | - | 获取一张月火术和一张星火术，使其获得<b>法术伤害+1</b>。 |
| 13 | `VAC_944` | 咒怨纪念品 | Cursed Souvenir | 2 | 169 | ✅ | - | 使一个随从获得+3/+3和“在你的回合开始时，对你的英雄造成3点伤害”。 |
| 14 | `SW_088` | 恶魔来袭 | Demonic Assault | 4 | 132 | ✅ | - | 造成$3点伤害。召唤两个1/3并具有<b>嘲讽</b>的虚空行者。 |

---

## 已从 P1 移出 → P3

| card_id | 中文名 | games | 原因 |
|---------|--------|-------|------|
| `LOOT_417` | 大灾变 | 206 | 消灭所有随从，与当回合场攻/斩杀无关 |

---

## v1 简化说明

| 卡牌 | 简化 |
|------|------|
| `ONY_010` | 荣誉消灭回手未模拟 |
| `DINO_406` | 元素 +1/+1 已模拟（card_id / CARDRACE 判定） |
| `CATA_526` | 抽牌未模拟；机制同亵渎循环；已注册穿插法术 `interleave_board` |
| `TOY_883` | 减费未模拟 |
| `ETC_082` | 击杀召唤固定 3/3 突袭恶魔 |
| `VAC_944` | 回合开始自伤未模拟 |
| `SCH_138` | 被 buff 随从本回合 `can_face=False` |

重新生成: `python scripts/generate_arena_spell_priority.py`
