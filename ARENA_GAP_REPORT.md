# 竞技场新赛季待接入卡牌清单

> 生成时间: 2026-07-02 06:55 UTC  
> 数据来源: [HSReplay Arena](https://hsreplay.net/api/v1/arena/card_stats/free/?ArenaTimestampRangeFilter=LAST_4_DAYS)  
> 模式: `BGT_UNDERGROUND_ARENA` + `LAST_4_DAYS`  
> **当季池规模: 1243 张**（上次文档约 1081–1243 张，以本次 API 为准）  
> 已注册集: `BOARD_CLEAR_SPELLS` / `SPELL_DAMAGE_DB` / `BOARD_BATTLECRY` / `BOARD_RUSH` / `BOARD_WEAPON` / 等  

## 总览

| 模块 | 池内相关 | 已接入 | 待接入 |
|------|----------|--------|--------|
| 法术 | 136 | 65 | **71** |
| 战吼随从 | 40 | 10 | **30** |
| 突袭随从 | 63 | 19 | **44** |
| 武器 | 41 | 15 | **26** |
| 连击随从 | 12 | 0 | **12** |
| 亡语随从 | 10 | 0 | **10** |
| 回合结束随从 | 5 | 2 | **3** |
| **合计** | — | — | **196** |

## 优先级说明

| 级别 | HSReplay games | 建议 |
|------|----------------|------|
| **P0** | ≥ 500 | 优先实现 |
| **P1** | 100–499 | 第二批 |
| **P2** | 1–99 | 可暂缓 |

## 代码内已知待做（旧清单）

| card_id | 说明 |
|---------|------|
| `RLK_534` | 灵魂弹幕 P2 |
| `YOP_034` | 窜逃的黑翼龙 |
| `CORE_YOP_034` | 窜逃的黑翼龙 |
| `BAR_063` | 沃坎诺斯 |
| `BAR_064` | 亮铜之翼 |

## 法术待接入（按优先级）

## 法术 P0（50 张）

**待接入 50 张**

| card_id | 中文名 | 费 | games | 优先级 | 效果摘要 |
|---------|--------|----|-------|--------|----------|
| `END_025` | 永时火焰箭 | 3 | 12658 | P0 | <b>Lifesteal</b> Deal $3 damage to a minion. If it dies, return this to your han |
| `JAM_022` | 致聋术 | 1 | 7848 | P0 | <b>Silence</b> a minion. <b>Combo:</b> Also deal $2 damage to it. 致聋术 |
| `CORE_CS2_032` | 烈焰风暴 | 7 | 4940 | P0 | Deal $5 damage to all enemy minions. 烈焰风暴 |
| `END_023` | 苦涩结局 | 5 | 4482 | P0 | <b>Freeze</b> a minion and its neighbors. Destroy any that are damaged. 苦涩结局 |
| `END_028` | 力敌万世 | 4 | 4320 | P0 | Destroy all minions with 4 or less Attack. <b>Overload:</b> (2) 力敌万世 |
| `REV_840` | 死神之躯 | 6 | 4222 | P0 | Deal $2 damage to all minions. Summon a 2/2 Volatile Skeleton  for each killed.  |
| `END_007` | 发挥优势 | 2 | 3823 | P0 | Deal $1 damage. Give your hero +1 Attack this turn. Draw 1 card. Gain 1 Armor. 发 |
| `END_014` | 协作火花 | 4 | 3382 | P0 | [x]Deal $3 damage to an enemy. If it dies, give a random friendly minion +3/+3.  |
| `REV_252` | 净场 | 5 | 3305 | P0 | Destroy all minions with 3 or less Attack. <b>Infuse (3):</b> 6 or less. 净场 |
| `REV_364` | 雄鹿冲锋 | 3 | 3284 | P0 | Deal $3 damage. Summon a random <b>Dormant</b> Wildseed. 雄鹿冲锋 |
| `CORE_BT_072` | 深度冻结 | 7 | 3173 | P0 | <b>Freeze</b> an enemy. Summon two 3/6 Water Elementals. 深度冻结 |
| `RLK_024` | 灵界打击 | 4 | 2988 | P0 | <b>Lifesteal</b> Deal $6 damage to a minion. 灵界打击 |
| `REV_369` | 间接伤害 | 8 | 2416 | P0 | [x]Deal $6 damage to three  random enemy minions.  Excess damage hits  the enemy |
| `CORE_CS1_130` | 神圣惩击 | 1 | 2348 | P0 | Deal $3 damage to a minion. 神圣惩击 |
| `CORE_BRM_013` | 快速射击 | 2 | 2137 | P0 | Deal $3 damage. If your hand is empty, draw a card. 快速射击 |
| `JAM_013` | 即兴演奏 | 2 | 2049 | P0 | [x]Give a friendly minion +3/+3. Deal $1 damage to all other minions. <b>Overloa |
| `MAW_019` | 谋杀指控 | 2 | 1897 | P0 | Choose a minion. Destroy it after another enemy minion dies. 谋杀指控 |
| `ETC_305` | 暗弦术：改 | 3 | 1840 | P0 | Give a minion -5/-5. If it has 0 Attack, destroy it. 暗弦术：改 |
| `CORE_LOOT_101` | 爆炸符文 | 3 | 1811 | P0 | <b>Secret:</b> After your opponent plays a minion, deal $6 damage to it and any  |
| `CATA_EVENT_402` | 致命贿赂 | 3 | 1660 | P0 | [x]Destroy a minion and give your opponent a Coin. <b>Combo:</b> You get one too |
| `TOY_714` | 飞速离架 | 3 | 1522 | P0 | Deal $1 damage to all enemy minions. Repeat for each Dragon you're holding. 飞速离架 |
| `CORE_CS2_076` | 刺杀 | 4 | 1400 | P0 | Destroy an enemy minion. 刺杀 |
| `END_020` | 永时困苦 | 1 | 1357 | P0 | [x]Deal $1 damage to a minion. If it survives, draw a card. If it dies, summon a |
| `RLK_025` | 冰霜打击 | 2 | 1334 | P0 | [x]Deal $3 damage to a  minion. If it dies, <b>Discover</b> a Frost Rune card. 冰 |
| `CORE_EX1_610` | 爆炸陷阱 | 2 | 1291 | P0 | <b>Secret:</b> When your hero is attacked, deal $2 damage to all enemies. 爆炸陷阱 |
| `REV_834` | 灭绝圣物 | 1 | 1269 | P0 | Deal $1 damage to a random enemy minion, twice. Improve your future Relics. 灭绝圣物 |
| `TOY_640` | 工坊事故 | 4 | 1220 | P0 | Deal $5 damage to a minion. Excess damages both neighbors. <b>Outcast:</b> Gain  |
| `TIME_001` | 时空飞刃 | 3 | 1193 | P0 | <b>Rewind</b> Throw 3 knives at random enemies that deal $2 damage each. 时空飞刃 |
| `CORE_BAR_801` | 击伤猎物 | 1 | 1102 | P0 | Deal $1 damage. Summon a 1/1 Hyena with <b>Rush</b>. 击伤猎物 |
| `TLC_365` | 乱翻库存 | 3 | 957 | P0 | Deal $3 damage to a minion. Costs (0) if you've <b>Discovered</b> this turn. 乱翻库 |
| `TIME_441` | 永世裂痕 | 4 | 931 | P0 | <b>Rewind</b> Deal $4 damage to two random enemies. 永世裂痕 |
| `MAW_023` | 盗窃指控 | 1 | 883 | P0 | [x]Choose a minion. Destroy it after you play a card copied from the opponent. 盗 |
| `MIS_701` | 恋旧风潮 | 5 | 876 | P0 | Transform ALL minions into random <b>Legendary</b> ones from the past. 恋旧风潮 |
| `CORE_EX1_197` | 暗言术：毁 | 4 | 868 | P0 | Destroy all minions with 5 or more Attack. 暗言术：毁 |
| `VAC_460` | 把经理叫来！ | 2 | 868 | P0 | Deal $2 damage. <b>Combo:</b> Get a Coin. 把经理叫来！ |
| `MIS_709` | 圣光荧光棒 | 4 | 864 | P0 | <b>Lifesteal</b> Deal $4 damage to a minion. Costs (1) if you've cast a Holy spe |
| `CORE_CS2_108` | 斩杀 | 1 | 842 | P0 | Destroy a damaged enemy minion. 斩杀 |
| `CORE_BAR_311` | 噬灵疫病 | 3 | 838 | P0 | [x]<b>Lifesteal</b>. Deal $4 damage randomly split among all enemy minions. 噬灵疫病 |
| `REV_920` | 可信的伪装 | 1 | 837 | P0 | [x]Transform a friendly minion into one that costs (2) more. <b>Infuse (4):</b>  |
| `JAM_008` | 直播事故 | 2 | 812 | P0 | Destroy your Undead. Resummon them. 直播事故 |
| `TIME_218` | 静电震击 | 0 | 763 | P0 | Deal $1 damage to a minion. Give your hero +1 Attack this turn. 静电震击 |
| `TIME_715` | 为了荣耀！ | 5 | 755 | P0 | Draw 2 cards. Costs (1) less for each minion your opponent controls. 为了荣耀！ |
| `ETC_528` | 灯光表演 | 3 | 733 | P0 | [x]Shoot 2 beams at enemies that each deal $2 damage. Your future Lightshows sho |
| `CORE_ICC_055` | 吸取灵魂 | 2 | 696 | P0 | <b>Lifesteal</b> Deal $3 damage to a minion. 吸取灵魂 |
| `MAW_010` | 否决动议 | 2 | 690 | P0 | [x]<b>Secret:</b> After your opponent plays three cards in a turn, deal $6 damag |
| `CORE_EX1_302` | 死亡缠绕 | 1 | 591 | P0 | [x]Deal $1 damage to a minion.  If it dies, draw a card. 死亡缠绕 |
| `TIME_027` | 超光子弹幕 | 2 | 583 | P0 | Deal $6 damage split among all enemies. Shuffle 2 Shreds of Time into your deck. |
| `MIS_027` | 多米诺效应 | 3 | 554 | P0 | Deal $2 damage to a minion. Repeat to the left or right, dealing 1 more damage e |
| `ETC_356` | 变音和弦 | 5 | 549 | P0 | <b>Lifesteal</b> Deal $6 damage to a minion. Costs (3) less if you're <b>Overloa |
| `MAW_001` | 纵火指控 | 2 | 533 | P0 | Choose a minion. Destroy it after your hero takes damage. 纵火指控 |

## 法术 P1（17 张）

**待接入 17 张**

| card_id | 中文名 | 费 | games | 优先级 | 效果摘要 |
|---------|--------|----|-------|--------|----------|
| `TIME_212` | 引雷针 | 1 | 449 | P1 | Deal $2 damage to a friendly minion to deal $4 damage to a random enemy minion.  |
| `CORE_SW_442` | 虚空碎片 | 4 | 439 | P1 | <b>Lifesteal</b> Deal $4 damage. 虚空碎片 |
| `REV_924` | 始源之潮 | 3 | 437 | P1 | [x]Transform enemy minions  into ones that cost (1) less  and friendly minions i |
| `REV_950` | 圣洁鸣钟 | 7 | 431 | P1 | [x]Shoot 5 rays at random minions. They give friendly minions +2/+2, and deal $2 |
| `TOY_384` | 净化之力 | 2 | 386 | P1 | <b>Silence</b> all friendly minions, then give them +1/+2. 净化之力 |
| `ONY_011` | 别站在火里！ | 5 | 349 | P1 | Deal $10 damage randomly split among all enemy minions. <b>Overload:</b> (1) 别站在 |
| `CORE_RLK_035` | 邪爆 | 5 | 326 | P1 | Detonate a <b>Corpse</b> to deal $1 damage to all minions. If any are still aliv |
| `MIS_707` | 批量生产 | 1 | 284 | P1 | Draw 2 cards. Deal $3 damage to your hero. Shuffle 2 copies of this into your de |
| `CORE_BOT_222` | 灵魂炸弹 | 1 | 276 | P1 | Deal $4 damage to a minion and your hero. 灵魂炸弹 |
| `EX1_312` | 扭曲虚空 | 8 | 243 | P1 | Destroy all minions and locations. 扭曲虚空 |
| `CORE_ULD_152` | 压感陷阱 | 2 | 224 | P1 | <b>Secret:</b> After your opponent casts a spell, destroy a random enemy minion. |
| `SCH_514` | 亡者复生 | 0 | 214 | P1 | Deal $3 damage to your hero. Return two friendly minions that died this game to  |
| `LOOT_504` | 不稳定的异变 | 1 | 135 | P1 | <b>Echo</b> Transform a friendly minion into one that costs (1) more. 不稳定的异变 |
| `ETC_413` | 低沉摇摆 | 4 | 128 | P1 | [x]Give your hero +2 Attack and <b>Immune</b> this turn, then  attack each enemy |
| `DEEP_011` | 灼燃之心 | 1 | 127 | P1 | Deal $2 damage to a minion. If it survives, give your hero +3 Attack this turn.  |
| `TOY_800` | 闪光试剂瓶 | 4 | 125 | P1 | [x]Deal $2 damage. Your next card this turn costs that much less. 闪光试剂瓶 |
| `ETC_362` | 跳吧，虫子！ | 5 | 120 | P1 | Transform a minion into Ragnaros the Firelord. <b>Overload:</b> (2) 跳吧，虫子！ |

## 法术 P2（4 张）

**待接入 4 张**

| card_id | 中文名 | 费 | games | 优先级 | 效果摘要 |
|---------|--------|----|-------|--------|----------|
| `TOY_602` | 化工泄漏 | 6 | 93 | P2 | Summon the highest Cost minion from your hand, then deal $5 damage to it. 化工泄漏 |
| `BT_134` | 沼泽射线 | 3 | 73 | P2 | Deal $3 damage to a minion. Costs (0) if you have at least 7 Mana Crystals. 沼泽射线 |
| `TOY_529` | 死亡轮盘 | 8 | 69 | P2 | Destroy your deck. In 5 turns, destroy the enemy hero. 死亡轮盘 |
| `CORE_EX1_407` | 绝命乱斗 | 5 | 5 | P2 | Destroy all minions except one. <i>(chosen randomly)</i> 绝命乱斗 |

## 战吼待接入

**待接入 30 张**

| card_id | 中文名 | 费 | games | 优先级 | 效果摘要 |
|---------|--------|----|-------|--------|----------|
| `TOY_520` | 秘迹观测者 | 3 | 5861 | P0 | <b>Battlecry:</b> Cast 2 random <b>Secrets</b>. At the start of your turn, destr |
| `TOY_375` | 滑冰元素 | 5 | 5636 | P0 | <b>Miniaturize</b> <b>Battlecry:</b> <b>Freeze</b> an enemy minion. Gain Armor e |
| `CORE_SW_072` | 锈烂蝰蛇 | 3 | 4958 | P0 | [x]<b>Tradeable</b> <b>Battlecry:</b> Destroy your opponent's weapon. 锈烂蝰蛇 |
| `CORE_UNG_205` | 冰川裂片 | 1 | 3549 | P0 | <b>Battlecry:</b> <b>Freeze</b> an enemy. 冰川裂片 |
| `CORE_REV_023` | 拆迁修理工 | 3 | 2611 | P0 | <b>Tradeable</b> <b>Battlecry:</b> Destroy  an enemy location. 拆迁修理工 |
| `END_034` | 碎裂扫荡者 | 8 | 2419 | P0 | [x]<b>Battlecry:</b> Destroy a random enemy minion, location, and weapon. 碎裂扫荡者 |
| `CORE_CFM_753` | 污手街供货商 | 2 | 1919 | P0 | <b>Battlecry:</b> Give all minions in your hand +1/+1. 污手街供货商 |
| `CORE_EX1_082` | 疯狂投弹者 | 2 | 1686 | P0 | <b>Battlecry:</b> Deal 3 damage randomly split between all other characters. 疯狂投 |
| `TIME_EVENT_301` | 灭世信徒 | 8 | 1208 | P0 | [x]<b>Battlecry:</b> Randomly destroy another minion. Repeat for each Dragon you |
| `TOY_388` | 粉笔美术家 | 4 | 1019 | P0 | [x]<b>Battlecry:</b> Draw a minion. Transform it into a random  <b>Legendary</b> |
| `TIME_875` | 半兽人迦罗娜 | 4 | 806 | P0 | [x]<b>Fabled</b>. <b>Battlecry:</b> If your opponent is holding King Llane, dest |
| `END_021` | 次元武器匠 | 3 | 786 | P0 | <b>Battlecry:</b> Give all minions and weapons in your hand +2 Attack. 次元武器匠 |
| `TIME_019` | 时间流具象 | 4 | 785 | P0 | <b>Battlecry:</b> If you control an Aura, deal 3 damage to all enemies. 时间流具象 |
| `CORE_EX1_005` | 王牌猎人 | 4 | 701 | P0 | [x]<b>Tradeable</b> <b>Battlecry:</b> Destroy a minion with 7 or more Attack. 王牌 |
| `ETC_110` | 封面艺人 | 4 | 557 | P0 | <b>Battlecry:</b> Transform into a 3/3 copy of a minion. 封面艺人 |
| `TOY_357` | 抱龙王噗鲁什 | 9 | 479 | P1 | [x]<b>Charge</b> <b>Battlecry:</b> Return all minions with less Attack than this |
| `CORE_UNG_848` | 始生幼龙 | 8 | 465 | P1 | [x]<b>Taunt</b> <b>Battlecry:</b> Deal 2 damage to all other minions. 始生幼龙 |
| `TOY_504` | 神秘女巫哈加莎 | 4 | 373 | P1 | [x]<b>Battlecry:</b> Draw 2 spells that cost (5) or more. Transform them into Sl |
| `TIME_EVENT_998` | 时光卫士露妮 | 5 | 323 | P1 | [x]<b>Battlecry:</b> Send all minions in your hand 2 turns into the future. They |
| `YOG_525` | 健身肌器人 | 3 | 310 | P1 | [x]<b>Battlecry:</b> Give all minions in your hand +1/+1. <b>Forge:</b> +2/+2 in |
| `RLK_593` | 洛瑟玛·塞隆 | 7 | 283 | P1 | <b>Battlecry:</b> Double the stats of all minions in your deck. 洛瑟玛·塞隆 |
| `LOOT_389` | 狗头人拾荒者 | 3 | 281 | P1 | <b>Battlecry:</b> Return one of your destroyed weapons to your hand. 狗头人拾荒者 |
| `CORE_OG_149` | 暴虐食尸鬼 | 3 | 260 | P1 | <b>Battlecry:</b> Deal 1 damage to all other minions. 暴虐食尸鬼 |
| `LOOT_161` | 食肉魔块 | 5 | 117 | P1 | <b>Battlecry:</b> Destroy a friendly minion. <b>Deathrattle:</b> Summon 2 copies |
| `MAW_000` | 冒牌小鬼 | 2 | 108 | P1 | <b>Battlecry:</b> Choose a friendly Imp. Transform into a copy of it. 冒牌小鬼 |
| `YOG_501` | 历战无面者 | 2 | 104 | P1 | <b>Battlecry:</b> Transform into a copy of a damaged minion. 历战无面者 |
| `CATA_EVENT_002` | 怨毒焰魔 | 3 | 93 | P2 | <b>Battlecry:</b> If you've played a Fire spell this turn, destroy a minion. 怨毒焰 |
| `CORE_ULD_165` | 裂隙屠夫 | 6 | 81 | P2 | <b>Battlecry:</b> Destroy a minion. Your hero takes damage equal to its Health.  |
| `NEW1_030` | 死亡之翼 | 10 | 39 | P2 | <b>Battlecry:</b> Destroy all other minions and discard your hand. 死亡之翼 |
| `END_035` | 末世之兆 | 5 | 29 | P2 | [x]<b>Battlecry:</b> If your deck is empty, destroy the top 5  cards of the enem |

## 突袭待接入

**待接入 44 张**

| card_id | 中文名 | 费 | games | 优先级 | 效果摘要 |
|---------|--------|----|-------|--------|----------|
| `TOY_894` | 折纸青蛙 | 5 | 7595 | P0 | [x]<b>Rush</b> <b>Battlecry:</b> Swap Attack with another minion. 折纸青蛙 |
| `JAM_033` | 混搭乐师 | 3 | 6408 | P0 | [x]<b>Rush</b> Gains an extra effect in your hand that changes each turn. 混搭乐师 |
| `ETC_325` | 音乐治疗师 | 2 | 5839 | P0 | <b>Rush</b> <b>Finale:</b> Gain <b>Lifesteal</b>. 音乐治疗师 |
| `JAM_027` | 饭圈迷弟 | 2 | 3601 | P0 | [x]<b>Choose One -</b> Give a friendly minion +2 Attack and <b>Rush</b>; or +2 H |
| `TOY_517` | 泼漆彩鳍鱼人 | 3 | 3520 | P0 | [x]<b>Poisonous</b> <b>Battlecry:</b> Draw a <b>Rush</b> minion. 泼漆彩鳍鱼人 |
| `END_032` | 飞翼畸变体 | 4 | 3492 | P0 | [x]<b>Rush</b> <b><b>Combo:</b> Overload</b> for (2) to gain <b>Immune</b> this  |
| `TOY_823` | 彩虹裁缝 | 3 | 3354 | P0 | [x]<b>Battlecry:</b> If your deck started with a Blood, Frost, or Unholy card, g |
| `ETC_742` | 摇滚巨石 | 2 | 3241 | P0 | [x]<b>Rush</b> <b>Battlecry:</b> If the last card you played costs (1), gain +1/ |
| `JAM_021` | 单曲流星 | 2 | 2858 | P0 | <b>Rush</b> <b>Combo:</b> Gain <b><b>Poisonous</b>.</b> 单曲流星 |
| `CS3_038` | 红鳃锋颚战士 | 2 | 2320 | P0 | <b>Rush</b> 红鳃锋颚战士 |
| `MAW_009` | 影犬 | 5 | 2202 | P0 | [x]Whenever this attacks, give your other Beasts +2/+2. <b>Infuse (3 Beasts):</b |
| `REV_015` | 假面狂欢者 | 6 | 1918 | P0 | [x]<b>Rush</b> <b>Deathrattle:</b> Summon a 2/2 copy of another minion in your d |
| `TLC_436` | 重生的翼手龙 | 5 | 1568 | P0 | <b><b>Rush</b>, Lifesteal</b> Costs <b>Corpses</b> instead of Mana. 重生的翼手龙 |
| `TIME_605` | 纪元追猎者 | 6 | 1284 | P0 | <b>Rush</b>, <b>Elusive</b> <b>Battlecry:</b> Summon a copy of this. 纪元追猎者 |
| `TOY_821` | 毛绒暴暴狗 | 3 | 1223 | P0 | <b>Rush</b> After you cast a Frost spell, gain <b>Reborn</b>. 毛绒暴暴狗 |
| `ETC_419` | 摇滚缝合怪 | 8 | 1215 | P0 | [x]<b>Rush</b> After this attacks, gain +1 Attack and attack a  random enemy min |
| `TIME_051` | 永恒龙士兵 | 5 | 1050 | P0 | <b>Rush</b> <b>Battlecry:</b> Double this minion's Attack. 永恒龙士兵 |
| `BOT_548` | 奇利亚斯 | 5 | 913 | P0 | <b>Magnetic</b> <b><b>Divine Shield</b>, <b>Taunt</b>, Lifesteal, Rush</b> 奇利亚斯 |
| `TIME_050` | 灵知沙漏 | 6 | 895 | P0 | [x]<b>Rush</b> After this minion survives damage, swap its stats. 灵知沙漏 |
| `ETC_035` | 鼓乐独演者 | 5 | 746 | P0 | [x]<b>Taunt</b> <b>Battlecry:</b> If you control no other minions, gain +2/+2 an |
| `REV_314` | 灌木巨龙托匹奥 | 7 | 657 | P0 | [x]<b>Battlecry:</b> For the rest of the game, after you cast a Nature spell, su |
| `CORE_RLK_657` | 地底虫王 | 7 | 642 | P0 | [x]<b>Rush</b> <b>Battlecry and Deathrattle:</b> Gain 6 Armor. 地底虫王 |
| `ETC_073` | 押韵狂人 | 3 | 641 | P0 | [x]<b>Rush</b> <b>Combo:</b> Gain +1/+1 for each other <b>Combo</b> card you've  |
| `MIS_306` | 火箭跳蛙 | 5 | 563 | P0 | <b>Rush</b> <b>Overload:</b> (4) 火箭跳蛙 |
| `TIME_022` | 累世巨蛇 | 8 | 509 | P0 | [x]<b>Rush</b> Costs (4) less if a minion is <b>Dormant</b>. 累世巨蛇 |
| `ETC_408` | 滑铲铁腿 | 3 | 486 | P1 | [x]<b>Rush</b>. <b>Battlecry:</b> Gain +1/+1 for each minion of a different type |
| `ETC_410` | 蛇啮鼓手 | 2 | 464 | P1 | <b>Rush</b> <b>Battlecry:</b> Gain +1/+1 for each minion that died this turn.@ < |
| `MAW_030` | 托加斯特管理员 | 8 | 448 | P1 | [x]<b>Battlecry:</b> For each enemy minion, randomly gain <b>Rush</b>, <b>Divine |
| `MAW_020` | 潦草的书记员 | 6 | 415 | P1 | <b>Rush</b>. Costs (1) less for each card you've played this turn. 潦草的书记员 |
| `MIS_711` | 安全专家 | 10 | 378 | P1 | <b>Rush</b>. <b>Deathrattle:</b> Shuffle three Bombs into your opponent's deck.  |
| `ETC_836` | 穆克拉先生 | 6 | 320 | P1 | [x]<b>Rush</b>. <b>Battlecry:</b> Fill your opponent's hand with Bananas. 穆克拉先生 |
| `AV_339` | 圣殿骑士队长 | 8 | 317 | P1 | [x]<b>Rush</b>. After this attacks a minion, summon a 5/5 Defender with <b>Taunt |
| `ETC_840` | 班卓龙 | 10 | 315 | P1 | [x]<b>Rush</b> Whenever this attacks, draw a Beast and gain its stats. 班卓龙 |
| `ETC_399` | 哈维利亚·墨鸦 | 4 | 297 | P1 | <b>Rush</b> After a friendly <b>Rush</b> minion attacks, give your minions +1 At |
| `BT_123` | 卡加斯·刃拳 | 4 | 291 | P1 | [x]<b>Rush</b> <b>Deathrattle:</b> Shuffle 'Kargath Prime' into your deck. 卡加斯·刃 |
| `REV_961` | 势利精英 | 5 | 241 | P1 | [x]<b>Battlecry:</b> For each Paladin card in your hand, randomly  gain <b>Divin |
| `CORE_TTN_843` | 艾瑞达欺诈者 | 4 | 206 | P1 | Whenever you draw a card, summon a 1/1 Demon with <b>Rush</b>. 艾瑞达欺诈者 |
| `RLK_212` | 安尼赫兰蛮魔 | 9 | 197 | P1 | [x]<b>Taunt</b>, <b>Rush</b> After this minion survives damage, deal that amount |
| `TOY_812` | 皮普希·彩蹄 | 7 | 193 | P1 | [x]<b>Deathrattle:</b> Summon a random <b>Divine Shield</b>, <b>Rush</b>, and <b |
| `DMF_226` | 刀锋舞娘 | 6 | 179 | P1 | [x]<b>Rush</b> Costs (1) if your hero has 6 or more Attack. 刀锋舞娘 |
| `REV_316` | 活体利刃蕾茉妮雅 | 7 | 149 | P1 | <b>Rush</b> After this attacks, equip it. 活体利刃蕾茉妮雅 |
| `TIME_872` | 不败冠军 | 8 | 69 | P2 | [x]<b>Rush</b>. <b>Battlecry:</b> Fill your opponent's board with   random 1-Cos |
| `DMF_523` | 碰碰车 | 2 | 57 | P2 | <b>Rush</b> <b>Deathrattle:</b> Add two 1/1 Riders with <b>Rush</b> to your hand |
| `TIME_063` | 时光之主诺兹多姆 | 3 | 41 | P2 | [x]<b>Dormant</b> for 5 turns. <b>Rush</b>. After you play a card from the newes |

## 武器待接入

**待接入 26 张**

| card_id | 中文名 | 费 | games | 优先级 | 效果摘要 |
|---------|--------|----|-------|--------|----------|
| `MIS_101` | 海绵斧 | 5 | 3488 | P0 | Whenever your hero attacks, spend 3 <b>Corpses</b> to gain +1 Durability. 海绵斧 |
| `CORE_TRL_111` | 猎头者之斧 | 2 | 2684 | P0 | [x]<b>Battlecry:</b> If you control a Beast, gain +1 Durability. 猎头者之斧 |
| `TIME_444` | 迷时战刃 | 1 | 2595 | P0 | <b>Deathrattle:</b> Get a random Demon from the past. 迷时战刃 |
| `ETC_317` | 迪斯科战槌 | 3 | 1804 | P0 | [x]<b>Deathrattle:</b> Give a random friendly minion +1/+1. <i>(Play minions whi |
| `TOY_522` | 水弹枪 | 4 | 1596 | P0 | After your hero attacks, summon a 1/1 Pirate that attacks a random enemy. 水弹枪 |
| `ETC_832` | 丛林弹唱琴 | 4 | 1281 | P0 | [x]<b>Deathrattle:</b> Summon a random 1-Cost Beast. <i>(Cast spells while     e |
| `ETC_388` | 实木手鼓 | 4 | 1172 | P0 | [x]<b>Deathrattle:</b> Summon 1 5/5 Ancient. <i>(Play cards that cost (5) or mor |
| `CORE_BT_921` | 奥达奇战刃 | 3 | 1057 | P0 | <b>Lifesteal</b> 奥达奇战刃 |
| `REV_917` | 石雕凿刀 | 2 | 1043 | P0 | After your hero attacks, summon a random basic Totem. 石雕凿刀 |
| `JAM_011` | 风领主的管号 | 6 | 1015 | P0 | [x]<b>Windfury</b> Whenever your hero attacks a minion, set its stats to 3/3. 风领 |
| `ETC_405` | 战刃吉他 | 4 | 896 | P0 | [x] <b>Deathrattle:</b> Draw 1 card.  <i>(Play <b>Outcast</b> cards while  equip |
| `TOY_604` | 砰砰扳手 | 3 | 795 | P0 | [x]<b>Miniaturize</b> <b>Deathrattle:</b> Trigger the <b>Deathrattle</b> of a ra |
| `END_012` | 无穷之手 | 3 | 738 | P0 | [x]Can't attack heroes. <b>Battlecry:</b> Set this weapon's Attack to INFINITY t |
| `JAM_015` | 混搭音叉 | 2 | 547 | P0 | Gains an extra effect in your hand that changes each turn. 混搭音叉 |
| `ETC_813` | 爵士贝斯 | 3 | 479 | P1 | [x]<b>Deathrattle:</b> Your next spell costs (1) less. <i>(<b>Overload</b> while |
| `ETC_312` | 爱豆的爱 | 1 | 446 | P1 | Your Hero Power costs (0). After you use it, lose 1 Durability. 爱豆的爱 |
| `CORE_GVG_059` | 齿轮光锤 | 3 | 390 | P1 | <b>Battlecry:</b> Give a random friendly minion <b>Divine Shield</b> and <b>Taun |
| `ETC_518` | 搓盘机 | 3 | 317 | P1 | [x]<b>Deathrattle:</b> Refresh 1 Mana Crystal. <i>(Play <b>Combo</b> cards while |
| `ETC_520` | 科多兽皮组鼓 | 4 | 298 | P1 | [x]<b>Deathrattle:</b> Deal 1 damage to all minions. <i>(Gain Armor while     eq |
| `END_016` | 时空之爪 | 4 | 259 | P1 | After your hero attacks, discard your highest Cost card. 时空之爪 |
| `ETC_084` | 邪弦竖琴 | 1 | 160 | P1 | [x]Whenever your hero would take damage on your turn, restore #2 Health instead. |
| `TLC_EVENT_402` | 末日使者之杖 | 3 | 145 | P1 | <b>Deathrattle:</b> Destroy all minions. 末日使者之杖 |
| `CORE_OG_031` | 暮光神锤 | 5 | 105 | P1 | <b>Deathrattle:</b> Summon a 4/2 Elemental. 暮光神锤 |
| `CORE_RLK_086` | 霜之哀伤 | 6 | 66 | P2 | <b>Deathrattle:</b> Summon every minion killed by this weapon. 霜之哀伤 |
| `CORE_LOOT_044` | 铁刃护手 | 2 | 31 | P2 | Has Attack equal to your Armor. Can't attack heroes. 铁刃护手 |
| `CORE_BT_781` | 埃辛诺斯壁垒 | 3 | 5 | P2 | [x]Whenever your hero would take damage, this loses  1 Durability instead. 埃辛诺斯壁 |

## 连击待接入

**待接入 12 张**

| card_id | 中文名 | 费 | games | 优先级 | 效果摘要 |
|---------|--------|----|-------|--------|----------|
| `END_032` | 飞翼畸变体 | 4 | 3492 | P0 | [x]<b>Rush</b> <b><b>Combo:</b> Overload</b> for (2) to gain <b>Immune</b> this  |
| `TOY_516` | 折价区海盗 | 3 | 3430 | P0 | <b>Rush</b> <b>Combo:</b> Summon a copy of this. 折价区海盗 |
| `JAM_021` | 单曲流星 | 2 | 2858 | P0 | <b>Rush</b> <b>Combo:</b> Gain <b><b>Poisonous</b>.</b> 单曲流星 |
| `ETC_077` | 八爪碟机 | 2 | 2392 | P0 | <b>Combo:</b> Add a random <b>Combo</b> card to your hand. 八爪碟机 |
| `ETC_072` | B-Box拳手 | 3 | 2114 | P0 | [x]<b>Combo:</b> Deal 4 damage randomly split among  all enemies. B-Box拳手 |
| `CORE_EX1_134` | 军情七处特工 | 3 | 1591 | P0 | <b>Combo:</b> Deal 3 damage. 军情七处特工 |
| `TIME_710` | 暴徒双人组 | 4 | 1157 | P0 | <b>Stealth</b> <b>Combo:</b> Summon a copy of this. 暴徒双人组 |
| `REV_826` | 私家眼线 | 4 | 885 | P0 | [x]<b>Battlecry:</b> Cast a <b>Secret</b> from your deck.  <b>Combo:</b> Cast 2  |
| `CORE_DMF_511` | 狐人老千 | 2 | 807 | P0 | <b>Battlecry:</b> Your next <b>Combo</b> card this turn costs (2) less. 狐人老千 |
| `ETC_073` | 押韵狂人 | 3 | 641 | P0 | [x]<b>Rush</b> <b>Combo:</b> Gain +1/+1 for each other <b>Combo</b> card you've  |
| `CORE_EX1_131` | 迪菲亚头目 | 2 | 621 | P0 | <b>Combo:</b> Summon a 2/1 Defias Bandit. 迪菲亚头目 |
| `CORE_BOT_576` | 疯狂的药剂师 | 5 | 122 | P1 | <b>Combo:</b> Give a friendly minion +4 Attack. 疯狂的药剂师 |

## 亡语待接入

**待接入 10 张**

| card_id | 中文名 | 费 | games | 优先级 | 效果摘要 |
|---------|--------|----|-------|--------|----------|
| `REV_356` | 狂蝠来宾 | 1 | 3561 | P0 | <b>Deathrattle:</b> Summon a 2/1 Bat. 狂蝠来宾 |
| `TOY_670` | 欢乐的玩具匠 | 4 | 2846 | P0 | <b>Deathrattle:</b> Summon two 1/2 Mechs with <b>Taunt</b> and <b>Divine Shield< |
| `TIME_017` | 坦克机械师 | 4 | 2135 | P0 | [x]<b>Divine Shield</b> <b>Deathrattle:</b> Summon a 7/7 Tank with <b>Divine Shi |
| `TLC_468` | 黏团焦油 | 5 | 1234 | P0 | [x]<b>Poisonous</b>, <b>Taunt</b> <b>Deathrattle:</b> Summon a 2/2 Blob with <b> |
| `REV_012` | 沼泽兽 | 6 | 989 | P0 | [x]<b><b>Taunt</b></b>  <b>Deathrattle:</b> Summon a 2/4  Muckmare with <b>Taunt |
| `TOY_814` | 玩具兵盒 | 3 | 973 | P0 | <b>Deathrattle:</b> Summon five 1/1 Soldiers with random <b>Bonus Effects</b>. 玩 |
| `GDB_331` | 分裂星岩 | 8 | 872 | P0 | <b>Deathrattle:</b> Summon two 4/4 Splitting Boulders. 分裂星岩 |
| `BOT_700` | 大铡蟹 | 3 | 870 | P0 | <b>Magnetic</b>, <b>Echo</b> <b>Deathrattle:</b> Summon two 1/1 Microbots. 大铡蟹 |
| `TOY_908` | 焰火机师 | 5 | 639 | P0 | <b>Deathrattle:</b> Summon two 1/1 Boom Bots. <i>WARNING: Bots may explode.</i>  |
| `CORE_SW_439` | 活泼的松鼠 | 1 | 490 | P1 | [x]<b>Deathrattle:</b> Shuffle 4 Acorns into your deck. When drawn, summon a 2/1 |

## 回合结束待接入

**待接入 3 张**

| card_id | 中文名 | 费 | games | 优先级 | 效果摘要 |
|---------|--------|----|-------|--------|----------|
| `TOY_824` | 黑棘针线师 | 4 | 2020 | P0 | [x]At the end of your turn, deal this minion's Attack damage randomly split    a |
| `TOY_820` | 废弃电子玩偶 | 5 | 1124 | P0 | At the end of your turn, destroy a minion with less Attack than this. 废弃电子玩偶 |
| `CORE_TTN_866` | 神秘恐魔 | 7 | 723 | P0 | [x]<b>Lifesteal</b> At the end of your turn, force all enemy minions to attack t |

## 法术 Top20 热度（建议先做）

**待接入 20 张**

| card_id | 中文名 | 费 | games | 优先级 | 效果摘要 |
|---------|--------|----|-------|--------|----------|
| `END_025` | 永时火焰箭 | 3 | 12658 | P0 | <b>Lifesteal</b> Deal $3 damage to a minion. If it dies, return this to your han |
| `JAM_022` | 致聋术 | 1 | 7848 | P0 | <b>Silence</b> a minion. <b>Combo:</b> Also deal $2 damage to it. 致聋术 |
| `CORE_CS2_032` | 烈焰风暴 | 7 | 4940 | P0 | Deal $5 damage to all enemy minions. 烈焰风暴 |
| `END_023` | 苦涩结局 | 5 | 4482 | P0 | <b>Freeze</b> a minion and its neighbors. Destroy any that are damaged. 苦涩结局 |
| `END_028` | 力敌万世 | 4 | 4320 | P0 | Destroy all minions with 4 or less Attack. <b>Overload:</b> (2) 力敌万世 |
| `REV_840` | 死神之躯 | 6 | 4222 | P0 | Deal $2 damage to all minions. Summon a 2/2 Volatile Skeleton  for each killed.  |
| `END_007` | 发挥优势 | 2 | 3823 | P0 | Deal $1 damage. Give your hero +1 Attack this turn. Draw 1 card. Gain 1 Armor. 发 |
| `END_014` | 协作火花 | 4 | 3382 | P0 | [x]Deal $3 damage to an enemy. If it dies, give a random friendly minion +3/+3.  |
| `REV_252` | 净场 | 5 | 3305 | P0 | Destroy all minions with 3 or less Attack. <b>Infuse (3):</b> 6 or less. 净场 |
| `REV_364` | 雄鹿冲锋 | 3 | 3284 | P0 | Deal $3 damage. Summon a random <b>Dormant</b> Wildseed. 雄鹿冲锋 |
| `CORE_BT_072` | 深度冻结 | 7 | 3173 | P0 | <b>Freeze</b> an enemy. Summon two 3/6 Water Elementals. 深度冻结 |
| `RLK_024` | 灵界打击 | 4 | 2988 | P0 | <b>Lifesteal</b> Deal $6 damage to a minion. 灵界打击 |
| `REV_369` | 间接伤害 | 8 | 2416 | P0 | [x]Deal $6 damage to three  random enemy minions.  Excess damage hits  the enemy |
| `CORE_CS1_130` | 神圣惩击 | 1 | 2348 | P0 | Deal $3 damage to a minion. 神圣惩击 |
| `CORE_BRM_013` | 快速射击 | 2 | 2137 | P0 | Deal $3 damage. If your hand is empty, draw a card. 快速射击 |
| `JAM_013` | 即兴演奏 | 2 | 2049 | P0 | [x]Give a friendly minion +3/+3. Deal $1 damage to all other minions. <b>Overloa |
| `MAW_019` | 谋杀指控 | 2 | 1897 | P0 | Choose a minion. Destroy it after another enemy minion dies. 谋杀指控 |
| `ETC_305` | 暗弦术：改 | 3 | 1840 | P0 | Give a minion -5/-5. If it has 0 Attack, destroy it. 暗弦术：改 |
| `CORE_LOOT_101` | 爆炸符文 | 3 | 1811 | P0 | <b>Secret:</b> After your opponent plays a minion, deal $6 damage to it and any  |
| `CATA_EVENT_402` | 致命贿赂 | 3 | 1660 | P0 | [x]Destroy a minion and give your opponent a Coin. <b>Combo:</b> You get one too |
