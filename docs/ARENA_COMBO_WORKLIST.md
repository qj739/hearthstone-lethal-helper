# 竞技场连击随从清单

> **筛选规则**：HSReplay 竞技场池内 `MINION` + `COMBO`（与网页 Advanced View 一致）。
> 网页: [https://hsreplay.net/arena/cards/#view=advanced&tableSort=popularity&cardType=MINION&mechanics=COMBO](https://hsreplay.net/arena/cards/#view=advanced&tableSort=popularity&cardType=MINION&mechanics=COMBO)
> 数据来源: HSReplay `ArenaTimestampRangeFilter=LAST_4_DAYS`
> 模式: `['ArenaGameTypeFilter.BGT_UNDERGROUND_ARENA', 'ArenaTimestampRangeFilter.LAST_4_DAYS']`
> 卡牌文本: hearthstonejson `zhCN`（`HS_new/json/cards_zhCN.json`）；
> enUS 来源 `HS_new/json/cards.json`
> 竞技场统计: 本地缓存或 HSReplay API（20s 超时）；卡牌 JSON 仅读本地

> 接入: `hdt_python/combo_board.py` + `combo_p0.py`（亮边 `POWERED_UP` = 连击已激活）
> 含 **突袭+连击** 的随从（如折价区海盗）由 `rush_p0.py` 处理。

## 概览

**合计: 6 张**（按 `games` 降序，与 HSReplay 热度排序一致）

---

## 全部连击随从

| # | card_id | 中文名 | 英文名 | 费 | 身材 | games | 其他机制 | 场攻 | 中文描述 |
|---|---------|--------|--------|----|------|-------|----------|------|----------|
| 1 | `TOY_516` | 折价区海盗 | Bargain Bin Buccaneer | 3 | 3/2 | 29177 | RUSH | 突袭✅ | <b>突袭</b>。<b>连击：</b>召唤一个本随从的复制。 |
| 2 | `UNG_064` | 邪脊吞噬者 | Vilespine Slayer | 5 | 3/4 | 20289 | - | ✅ | <b>连击：</b> 消灭一个随从。 |
| 3 | `TSC_933` | 镣铐水鬼 | Bootstrap Sunkeneer | 5 | 4/4 | 18902 | - | ✅ | <b>连击：</b>将一个敌方随从置于你对手的牌库底。 |
| 4 | `DAL_415` | 怪盗恶霸 | EVIL Miscreant | 3 | 1/5 | 13799 | - | ✅ | <b>连击：</b>随机将两张<b>跟班</b>牌置入你的手牌。 |
| 5 | `TLC_516` | 尼斐塞特武器匠 | Neferset Weaponsmith | 4 | 5/4 | 5065 | BATTLECRY | ✅ | <b>战吼：</b>随机获取一张另一职业的武器牌。<b>连击：</b>使其获得+2攻击力。 |
| 6 | `GDB_870` | 艾瑞达潜藏者 | Eredar Skulker | 2 | 1/3 | 3638 | SPELLBURST | ✅ | <b>连击，<b>法术迸发</b>：</b>获得+2攻击力和<b>潜行</b>。 |

---

## 实现说明

| card_id | 亮边连击效果 | v1 建模 |
|---------|--------------|---------|
| `TOY_516` | 召唤复制 | 见 `rush_p0` 折价区海盗 |
| `UNG_064` | 消灭一个随从 | 最优消灭（含友方）+ 召唤 3/4 |
| `TSC_933` | 敌方随从置入牌库底 | 最优移出敌方随从 + 召唤 4/4 |
| `DAL_415` | 获取 2 张跟班 | 召唤 1/5；跟班入手牌不计入当回合场攻 |
| `TLC_516` | 武器 +2 攻 | 召唤 5/4；亮边且装备武器时 +2 临时英雄攻 |
| `GDB_870` | +2 攻与潜行 | 亮边召唤 3/3（无突袭，当回合不攻击） |

重新生成: `python scripts/generate_arena_combo_worklist.py`
