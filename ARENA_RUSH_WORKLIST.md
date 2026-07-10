# 竞技场突袭随从清单

> **筛选规则**：HSReplay 竞技场池内 `MINION` + `RUSH`（与网页 Advanced View 一致）。
> 网页: [https://hsreplay.net/arena/cards/#view=advanced&tableSort=popularity&cardType=MINION&mechanics=RUSH](https://hsreplay.net/arena/cards/#view=advanced&tableSort=popularity&cardType=MINION&mechanics=RUSH)
> 数据来源: HSReplay `ArenaTimestampRangeFilter=LAST_4_DAYS`
> 模式: `['ArenaGameTypeFilter.BGT_UNDERGROUND_ARENA', 'ArenaTimestampRangeFilter.LAST_4_DAYS']`
> 卡牌文本: hearthstonejson `zhCN`（`HS_new/json/cards_zhCN.json`）；
> enUS 来源 `HS_new/json/cards.json`
> 竞技场统计: 本地缓存或 HSReplay API（20s 超时）；卡牌 JSON 仅读本地

> 接入: `hdt_python/rush_board.py` + `rush_p0.py`（手牌打出、当回合突袭解场规则）

## 概览

**合计: 59 张**（按 `games` 降序，与 HSReplay 热度排序一致）

---

## 全部突袭随从

| # | card_id | 中文名 | 英文名 | 费 | 身材 | games | 其他机制 | 场攻 | 中文描述 |
|---|---------|--------|--------|----|------|-------|----------|------|----------|
| 1 | `VAC_514` | 恐惧猎犬训练师 | Dreadhound Handler | 2 | 2/2 | 33012 | DEATHRATTLE | ✅ | <b>突袭</b>。<b>亡语：</b>召唤一只1/1并具有<b>复生</b>的恐惧猎犬。 |
| 2 | `TOY_516` | 折价区海盗 | Bargain Bin Buccaneer | 3 | 3/2 | 29177 | - | ✅ | <b>突袭</b>。<b>连击：</b>召唤一个本随从的复制。 |
| 3 | `TOY_312` | 恋旧的侏儒 | Nostalgic Gnome | 4 | 4/4 | 17572 | - | ✅ | <b>微缩</b> <b>突袭</b>。在本随从在你的回合中造成了刚好消灭目标的伤害后，抽一张牌。 |
| 4 | `CATA_525` | 装甲放血纳迦 | Armored Bloodletter | 3 | 3/1 | 17501 | BATTLECRY | ✅ | <b>突袭</b>。<b>战吼：</b><b>兆示</b>{0}。 |
| 5 | `CS3_020` | 伊利达雷审判官 | Illidari Inquisitor | 8 | 8/8 | 8573 | - | ✅ | <b>突袭</b> 在你的英雄攻击一个敌人后，本随从也会攻击该敌人。 |
| 6 | `MIS_314` | 积木魔像 | Building-Block Golem | 5 | 6/3 | 7862 | DEATHRATTLE | ✅ | <b>突袭</b>。<b>亡语：</b>随机召唤三个法力值消耗为（1）的随从。 |
| 7 | `DRG_076` | 无面腐蚀者 | Faceless Corruptor | 5 | 5/4 | 7279 | BATTLECRY | 战吼✅ | <b>突袭</b>。<b>战吼：</b>将你的一个随从变形成为本随从的复制。 |
| 8 | `WW_418` | 食人魔帮歹徒 | Ogre-Gang Outlaw | 3 | 4/4 | 6773 | - | ✅ | <b>突袭。</b>50%几率攻击错误的敌人。 |
| 9 | `WORK_015` | 精魂商贩 | Spirit Peddler | 6 | 6/6 | 6764 | DEATHRATTLE | ✅ | <b>突袭</b>。<b>亡语：</b>随机使你手牌中的一张随从牌的法力值消耗减少（6）点。 |
| 10 | `BAR_896` | 石槌掌锚手 | Stonemaul Anchorman | 5 | 4/6 | 6493 | - | ✅ | <b>突袭</b>，<b>暴怒：</b>抽一张牌。 |
| 11 | `TSC_645` | 积雷母舰 | Stormcoil Mothership | 6 | 5/4 | 5770 | DEATHRATTLE | ✅ | <b>突袭</b>。<b>亡语：</b>随机召唤两个法力值消耗小于或等于（3）点的 机械。 |
| 12 | `SW_431` | 花园猎豹 | Park Panther | 4 | 4/4 | 5306 | - | ✅ | <b>突袭</b> 每当本随从攻击时，使你的英雄在本回合中获得+3攻击力。 |
| 13 | `ETC_357` | 铜管元素 | Brass Elemental | 4 | 3/3 | 4815 | TAUNT,DIVINE_SHIELD,WINDFURY | ✅ | <b>突袭</b>，<b>圣盾</b>，<b>嘲讽</b>，<b>风怒</b> |
| 14 | `TTN_713` | 生气的冥狱之犬 | Angry Helhound | 4 | 2/5 | 4172 | - | ✅ | <b>突袭</b> 在你的回合拥有+4攻击力。 |
| 15 | `DAL_047` | 活动喷泉 | Walking Fountain | 8 | 4/8 | 4153 | LIFESTEAL,WINDFURY | ✅ | <b>吸血，突袭，风怒</b> |
| 16 | `WW_326` | 矿车巡逻兵 | Minecart Cruiser | 3 | 4/5 | 3661 | BATTLECRY | ✅ | <b>突袭</b>。<b>过载：</b>（2）。<b>战吼：</b>如果你在上个回合使用过元素牌，则本牌不会<b>过载</b>。 |
| 17 | `CATA_469` | 多彩龙巢母 | Chromatic Broodmother | 4 | 2/5 | 3530 | - | ✅ | <b>突袭</b>。每当本随从 攻击时，复原等同于本随从攻击力的法力水晶。 |
| 18 | `CORE_BT_156` | 被禁锢的邪犬 | Imprisoned Vilefiend | 2 | 3/5 | 3078 | - | ✅ | <b>休眠</b>2回合。 <b>突袭</b> |
| 19 | `TTN_042` | 独眼突击者 | Cyclopian Crusher | 3 | 3/3 | 2995 | FORGE | ✅ | <b>突袭</b>。<b>锻造：</b>获得+3/+2。 |
| 20 | `TLC_630` | 格里什异种虫 | Gorishi Wasp | 5 | 2/7 | 2962 | - | ✅ | <b>突袭</b>。每当本随从受到伤害，获取一张法力值消耗为（1）的格里什毒刺虫。 |
| 21 | `CORE_DRG_079` | 辟法巨龙 | Evasive Wyrm | 6 | 5/4 | 2729 | DIVINE_SHIELD | ✅ | <b>突袭</b>。<b>圣盾</b>。<b>扰魔</b> |
| 22 | `CATA_153` | 奥拉基尔，风暴之主 | Al'Akir, Lord of Storms | 8 | 2/8 | 2689 | WINDFURY | ✅ | <b>巨型+2 <b>突袭。</b>风怒。</b><b>战吼：</b>获取2张法力值消耗等同于本随从攻击力的随从牌，这两张牌的法力值消耗为（1）点。 |
| 23 | `VAC_527` | 龙族美餐 | Draconic Delicacy | 8 | 6/6 | 2674 | - | ✅ | <b>突袭</b>。<b>扰魔</b>。每次只能受到1点伤害。 |
| 24 | `WW_043` | 轮式淤泥怪 | Sludge on Wheels | 3 | 2/5 | 2601 | - | ✅ | <b>突袭</b>。每当本随从受到伤害时，获取一张淤泥桶并将一张淤泥桶置于你的牌库底。 |
| 25 | `RLK_955` | 银月城军备官 | Silvermoon Armorer | 4 | 4/4 | 2541 | - | ✅ | <b>突袭</b>。<b>法力渴求（7）：</b>获得+2/+2。 |
| 26 | `RLK_604` | 索利贝洛尔 | Thori'belore | 4 | 4/4 | 2256 | DEATHRATTLE | ✅ | <b>突袭</b>。<b>亡语：</b>进入<b>休眠</b>状态。施放一个火焰法术以复活索利贝 洛尔！ |
| 27 | `TIME_209` | 高山之王穆拉丁 | Muradin, High King | 5 | 3/2 | 2211 | BATTLECRY,DEATHRATTLE | ✅ | <b>奇闻</b> <b>突袭</b>。<b>战吼：</b>为本随从装备高山之王的战锤！<b>亡语：</b>将该战锤置入你的手牌。 |
| 28 | `BT_761` | 盘牙督军 | Coilfang Warlord | 8 | 9/5 | 1967 | DEATHRATTLE | ✅ | <b>突袭，亡语：</b>召唤一个5/9并具有<b>嘲讽</b> 的督军。 |
| 29 | `TLC_243` | 涡流风暴幼龙 | Whirling Stormdrake | 9 | 8/8 | 1964 | WINDFURY | ✅ | <b>突袭</b>。<b>风怒</b> <b>延系：</b>在本回合中获得<b>免疫</b>。 |
| 30 | `CORE_WC_701` | 邪能响尾蛇 | Felrattler | 3 | 3/2 | 1909 | DEATHRATTLE | ✅ | <b>突袭</b>，<b>亡语：</b>对所有敌方随从造成 1点伤害。 |
| 31 | `BT_720` | 锈骑劫匪 | Ruststeed Raider | 5 | 1/8 | 1817 | TAUNT,BATTLECRY | ✅ | <b>嘲讽，突袭， 战吼：</b>在本回合获得+4攻击力。 |
| 32 | `GDB_322` | 光注魔刃豹 | Lightfused Manasaber | 6 | 6/6 | 1674 | SPELLBURST | ✅ | <b>突袭</b>。<b><b>法术迸发</b>：</b>获得<b>圣盾</b>。 |
| 33 | `TOY_811` | 绒绒虎 | Tigress Plushy | 3 | 3/2 | 1672 | DIVINE_SHIELD,LIFESTEAL | ✅ | <b>微缩</b> <b>突袭</b>，<b>吸血</b>，<b>圣盾</b> |
| 34 | `EDR_421` | 年兽 | Omen | 10 | 6/12 | 1645 | WINDFURY,DEATHRATTLE | ✅ | <b>突袭</b>。<b>风怒</b> <b>亡语：</b>对所有敌人造成1点伤害。<i>（在本随从攻击后提升！）</i> |
| 35 | `TSC_007` | 潜水跳板船员 | Gangplank Diver | 5 | 6/4 | 1518 | - | ✅ | <b>休眠</b>1回合。<b>突袭</b>。攻击时具有<b>免疫</b>。 |
| 36 | `VAC_950` | 抱石伙伴 | Bouldering Buddy | 7 | 6/7 | 1412 | TAUNT | ✅ | <b>突袭。嘲讽</b> 如果你拥有至少十个法力水晶，则法力值消耗为（1）点。 |
| 37 | `WW_825` | 落日灵龙菲伊 | Fye, the Setting Sun | 9 | 4/12 | 1333 | TAUNT,LIFESTEAL | ✅ | <b>突袭</b>。<b>吸血</b>。<b>嘲讽</b>。在本局对战中，你每召唤一条龙，本牌的法力值消耗便减少（1）点。 |
| 38 | `YOG_506` | 扭曲的霜翼龙 | Twisted Frostwing | 4 | 3/3 | 1297 | DEATHRATTLE | ✅ | <b>突袭</b>。<b>亡语：</b>召唤一只属性值等同于本随从攻击力的奇美拉。 |
| 39 | `EDR_486` | 纵火眼魔 | Scorching Observer | 9 | 7/9 | 1292 | LIFESTEAL | ✅ | <b>突袭</b>。<b>吸血</b> |
| 40 | `REV_352` | 石缚加尔贡 | Stonebound Gargon | 4 | 3/5 | 1280 | INFUSE | ✅ | <b>突袭</b>，<b>注能（3）：</b>同时对其攻击目标相邻的随从造成伤害。 |
| 41 | `TTN_466` | 米诺陶牛头人 | Minotauren | 6 | 5/5 | 1039 | - | ✅ | <b>突袭</b> 每当本随从造成伤害时，获得等量的护甲值。 |
| 42 | `REV_375` | 石裔干将 | Stoneborn General | 10 | 8/8 | 918 | DEATHRATTLE | ✅ | <b>突袭</b>，<b>亡语：</b>召唤一只8/8并具有<b>突袭</b>的墓翼蝠。 |
| 43 | `JAM_004` | 镂骨恶犬 | Hollow Hound | 6 | 3/4 | 898 | LIFESTEAL | ✅ | <b>吸血</b>，<b>突袭</b>。同时对其攻击目标相邻的随从造成伤害。 |
| 44 | `ONY_004` | 团本首领奥妮克希亚 | Raid Boss Onyxia | 10 | 8/8 | 880 | BATTLECRY | ✅ | <b>突袭</b>。当你控制着雏龙时<b>免疫</b>。<b>战吼：</b>召唤六条2/1并具有<b>突袭</b>的雏龙。 |
| 45 | `SW_062` | 闪金镇豺狼人 | Goldshire Gnoll | 10 | 5/4 | 853 | - | ✅ | <b>突袭</b> 你每有一张其他手牌，本牌的法力值消耗便减少（1）点。 |
| 46 | `WW_808` | 银蛇 | Silver Serpent | 3 | 2/3 | 846 | POISONOUS | ✅ | <b><b>突袭</b>。<b>剧毒</b> 快枪：</b>在本回合中获得<b>免疫</b>。 |
| 47 | `TIME_850` | 血斗士洛戈什 | Lo'Gosh, Blood Fighter | 7 | 7/7 | 714 | DEATHRATTLE | ✅ | <b>奇闻</b> <b>突袭</b>。<b>亡语：</b>从你的手牌中召唤一位血斗士，使其获得+5/+5并随机攻击一个敌人。 |
| 48 | `DINO_401` | 伟岸的德拉克雷斯 | The Great Dracorex | 8 | 5/12 | 544 | - | ✅ | <b>突袭</b>。在本随从攻击一个敌方随从后，还会对所有其他敌方随从造成伤害。 |
| 49 | `RLK_913` | 达库鲁大王 | Overlord Drakuru | 9 | 6/8 | 487 | WINDFURY | ✅ | <b>突袭</b>，<b>风怒</b>。 在本随从攻击并消灭随从后，为你复活被消灭的随从。 |
| 50 | `RLK_916` | 胆大的幼龙 | Daring Drake | 4 | 4/4 | 472 | BATTLECRY | ✅ | <b>突袭</b>。<b>战吼：</b>如果你的手牌中有龙牌，便获得+1/+1。 |
| 51 | `TOY_356` | 玩具暴龙 | Toyrannosaurus | 7 | 7/7 | 427 | DEATHRATTLE | ✅ | <b>突袭</b> <b>亡语：</b>随机对一个敌人造成7点伤害。 |
| 52 | `TLC_240` | 填鳃暴龙 | Tyrannogill | 6 | 6/3 | 397 | DEATHRATTLE | ✅ | <b>突袭</b>。<b>亡语：</b> 召唤三个2/1的鱼人，使其各获得一项随机<b>额外效果</b>。 |
| 53 | `TSC_945` | 艾萨拉的刃豹 | Azsharan Saber | 4 | 4/3 | 287 | DEATHRATTLE | ✅ | <b>突袭</b>，<b>亡语：</b>将一张沉没的刃豹置于你的牌库底。 |
| 54 | `TLC_366` | 掠食飞翼龙 | Pterrorwing Ravager | 6 | 7/5 | 257 | - | ✅ | <b>突袭</b>。<b>延系：</b>法力值消耗减少（2）点。 |
| 55 | `GDB_141` | 伊瑞尔，希望信标 | Yrel, Beacon of Hope | 3 | 3/3 | 240 | DEATHRATTLE | ✅ | <b>突袭</b>。<b>亡语：</b>获取来自更早时间线的三张不同圣契牌！ |
| 56 | `BT_487` | 巨型大恶魔 | Hulking Overfiend | 8 | 5/10 | 209 | - | ✅ | <b>突袭</b> 在本随从攻击并消灭一个随从后，可再次攻击。 |
| 57 | `SW_323` | 鼠王 | The Rat King | 5 | 5/5 | 108 | DEATHRATTLE | ✅ | <b>突袭</b>，<b>亡语：</b>进入<b>休眠</b>状态。在5个友方随从死亡后复活。 |
| 58 | `TIME_029` | 灾毁迅疾幼龙 | Ruinous Velocidrake | 5 | 5/5 | 75 | BATTLECRY | ✅ | <b>突袭</b>。<b>战吼：</b>从你的牌库中施放一张时空撕裂以召唤一个本随从的复制。 |
| 59 | `CATA_493` | 地狱公爵 | Duke of Below | 4 | 2/2 | 29 | - | ✅ | <b>突袭</b>。在本局对战中，你每弃掉一张牌，便拥有+2/+2。 |

---

重新生成: `python scripts/generate_arena_rush_worklist.py`
