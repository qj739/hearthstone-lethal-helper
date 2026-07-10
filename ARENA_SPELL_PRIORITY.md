# 本赛季 Underground Arena 法术实现优先级

> 数据来源: HSReplay `card_stats/free/?ArenaTimestampRangeFilter=LAST_4_DAYS`  
> 模式: `['ArenaGameTypeFilter.BGT_UNDERGROUND_ARENA', 'ArenaTimestampRangeFilter.LAST_4_DAYS']`  
> 卡牌文本: hearthstonejson `zhCN` / `enUS`  
> 已排除: `SPELL_DAMAGE_DB` + `BOARD_CLEAR_SPELLS` 已收录卡；P3 含全体清场 4 张（邪爆、布洛克斯加的奋战、怪异触手、屠灭）  

## 优先级定义

| 级别 | 条件 (num_games) | 数量 | 建议 |
|------|------------------|------|------|
| **P0** | HSReplay games ≥ 500 | 102 | 第一阶段核心 |
| **P1** | games 100–499 | 16 | 第二阶段补充 |
| **P2** | games < 100 | 2 | 可暂缓 |
| **P3** | 手动降级（与斩杀无关） | 17 | 暂不实现 |

**待做合计: 137 张**（其中 P3 暂不实现 **17** 张）

## 第一阶段：P0 直伤法术（`spell_p0_direct` / `BOARD_CLEAR_SPELLS`）

共 **21** 张已接入 `BOARD_CLEAR_SPELLS`。

| card_id | 中文名 | 费 | games | 状态 | 中文描述 |
|---------|--------|----|-------|------|----------|
| `CATA_785` | 暮光祭礼 | 2 | 48572 | ✅ | <b>兆示</b>{0}。<b>连击：</b>造成$3点伤害。 |
| `BAR_319` | 邪恶挥刺（等级1） | 2 | 26226 | ✅ | 造成$2点伤害。<i>（当你有5点法力值时升级。）</i> |
| `CORE_CATA_007` | 吞噬 | 4 | 10481 | ✅ | 随机对两个敌方随从造成$3点伤害。每有一个随从死亡，抽一张牌。 |
| `AV_259` | 冰霜撕咬 | 2 | 9406 | ✅ | 造成$3点伤害。<b>荣誉消灭：</b>你对手的下一个法术法力值消耗增加（2）点。 |
| `RLK_512` | 冰川突进 | 3 | 8518 | ✅ | 造成$4点伤害。在本回合中，你的下一个法术法力值消耗减少（2）点。 |
| `SW_040` | 邪能弹幕 | 2 | 7611 | ✅ | 对生命值最低的敌人造成$2点伤害两次。 |
| `CORE_AT_064` | 怒袭 | 2 | 6306 | ✅ | 造成$3点伤害。获得3点 护甲值。 |
| `CORE_CS2_062` | 地狱烈焰 | 3 | 5422 | ✅ | 对所有角色造成$3点伤害。 |
| `WW_405` | 迅疾连射 | 4 | 4692 | ✅ | 造成$6点伤害，分配到生命值最低的敌人身上。 |
| `TIME_855` | 奥术弹幕 | 3 | 4577 | ✅ | 对一个敌人造成$3点伤害，并随机对两个其他敌人造成$2点伤害。 |
| `GDB_851` | 星域相变射线 | 2 | 3991 | ✅ | <b>抉择：</b>随机对两个敌方随从造成$2点伤害；或者使一个敌方随从<b>休眠</b>2回合。 |
| `CATA_485` | 激寒急流 | 1 | 3909 | ✅ | 造成$2点伤害。随机对一个敌方随从造成$1点伤害。 |
| `CATA_303` | 净化吐息 | 2 | 2541 | ✅ | 对一个随从造成$5点伤害。如果该随从死亡，则为敌方英雄恢复#5点生命值。 |
| `CATA_498` | 拉法姆的奋战 | 3 | 2453 | ✅ | 随机对两个敌方随从造成$2点伤害。<i>（每回合都会升级！）</i> |
| `TIME_611` | 时间停滞 | 2 | 2335 | ✅ | 造成$3点伤害。随机<b>冻结</b>两个敌方随从。 |
| `FIR_909` | 爆裂射击 | 2 | 1063 | ✅ | 随机对三个敌人造成$2点伤害。 |
| `TLC_227` | 熔岩涌流 | 3 | 868 | ✅ | 对生命值最低的敌人造成$2点伤害，触发三次。<b>过载：</b>（1）。 |
| `AV_212` | 法力虹吸 | 2 | 814 | ✅ | 造成$2点伤害。<b>荣誉消灭：</b>使你手牌中所有法术牌的法力值消耗减少（1）点。 |
| `JAM_002` | 星辰能量 | 5 | 804 | ✅ | 随机对一个敌方随从造成$5点伤害。重复此效果，每次伤害减少1点。 |
| `EDR_255` | 复苏烈焰 | 7 | 799 | ✅ | <b>吸血</b>。对生命值最低的敌人造成$5点伤害，触发两次。 |
| `REV_601` | 冰冻之触 | 2 | 787 | ✅ | 造成$3点伤害。<b>注能（3）：</b>将一张冰冻之触置入你的 手牌。 |

## P3 手动降级清单（与斩杀无关）

| card_id | 中文名 | 原 games | 降级原因 |
|---------|--------|----------|----------|
| `TIME_711` | 闪回 | 14446 | 铺场/连击加攻，无当回合伤害 |
| `CORE_RLK_035` | 邪爆 | 5808 | 邪爆：全体清场循环，非场攻 |
| `CATA_526` | 布洛克斯加的奋战 | 5569 | 布洛克斯加的奋战：全体清场，非场攻 |
| `RLK_730` | 血液沸腾 | 4172 | 感染后回合结束才伤害，与斩杀无关 |
| `CATA_202` | 能量窃取 | 3886 | 仅获取裂变牌，无伤害 |
| `CATA_134` | 荒林怪圈 | 3664 | 铺场树人/亡语，非斩杀 |
| `CATA_491` | 怪异触手 | 3503 | 怪异触手：全体清场递减，非场攻 |
| `CATA_567` | 升腾 | 3201 | 变形铺场，非斩杀 |
| `EX1_407` | 绝命乱斗 | 2971 | 乱斗仅解场，清嘲后不一定增加当回合打脸 |
| `OG_027` | 异变 | 1971 | 异变提升己方随从，非斩杀 |
| `CATA_581` | 屠灭 | 1899 | 屠灭：全体清场，非场攻 |
| `WORK_026` | 失火 | 1714 | 失火：抽牌点燃，无当回合伤害 |
| `SCH_235` | 衰变飞弹 | 1515 | 衰变飞弹，衰变机制暂不模拟 |
| `FIR_902` | 燃薪咒符 | 1117 | 燃薪咒符，下回合开始才伤害 |
| `CATA_820` | 运输补给 | 837 | 运输补给：抽牌+buff手牌，非斩杀 |
| `WW_092` | 液力压裂 | 714 | 液力压裂：检视牌库抽牌，非斩杀 |
| `AV_330` | 纳鲁的赐福 | 587 | 纳鲁的赐福：回血，非斩杀 |

---

## 完整清单（含中文名与效果描述）

| 优先级 | card_id | 中文名 | 英文名 | 费 | games | 实现类型 | 标签 | 备注 | 中文描述 |
|--------|---------|--------|--------|----|-------|----------|------|------|----------|
| P0 | `DAL_716` | 宿敌 | Vendetta | 4 | 44297 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$4点伤害。如果你的手牌中有另一职业的卡牌，则法力值消耗为（0）点。 |
| P0 | `ONY_032` | 奈法利安的牙 | Tooth of Nefarian | 2 | 41649 | spell_board其他 | - | - | 造成$3点伤害。<b>荣誉消灭：</b><b>发现</b>一张另一职业的法术牌。 |
| P0 | `EDR_814` | 感染吐息 | Infested Breath | 2 | 32944 | spell_board其他 | - | - | 造成$2点伤害。召唤一条0/2的水蛭。 |
| P0 | `MIS_903` | 可疑交易 | Dubious Purchase | 4 | 32294 | spell_board消灭 | 移除 | - | 抽三张牌。<b>连击：</b>随机消灭一个敌方随从。 |
| P0 | `REV_939` | 锯齿骨刺 | Serrated Bone Spike | 2 | 22503 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$3点伤害。如果该随从死亡，在本回合中，你的下一张牌法力值消耗减少（2）点。 |
| P0 | `EX1_129` | 刀扇 | Fan of Knives | 2 | 22437 | spell_board复杂AOE | 解场伤,敌AOE | - | 对所有敌方随从造成$1点伤害，抽一张牌。 |
| P0 | `CATA_156` | 试验演示 | Experimental Animation | 6 | 22360 | spell_board复杂AOE | 解场伤,敌AOE | - | <b>兆示</b>{0}。对所有敌方随从造成$4点伤害。 |
| P0 | `FIR_939` | 影焰晕染 | Shadowflame Suffusion | 2 | 19766 | spell_board解场伤 | 解场伤 | - | 造成$2点伤害。<b>发现</b>一张具有<b>黑暗之赐</b>的战士随从牌。 |
| P0 | `CATA_585` | 烈火炙烤 | Torch | 1 | 18033 | spell_board解场伤 | 解场伤 | - | 对一个受伤的随从造成$8点伤害。如果伤害超过目标生命值，将能造成剩余伤害的本牌移回手牌。 |
| P0 | `WW_354` | 残骸遍野 | Fistful of Corpses | 1 | 18020 | spell_board解场伤 | 解场伤 | - | 对一个随从造成等同于你的<b>残骸</b>数量的伤害。 |
| P0 | `TIME_712` | 诛灭暴君 | Dethrone | 7 | 17774 | spell_board消灭 | 移除 | - | 消灭一个随从。<b>连击：</b>随机召唤一个法力值消耗为（8）的随从。 |
| P0 | `ETC_394` | 混乱品味 | Taste of Chaos | 1 | 16169 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$2点伤害。<b>压轴：</b><b>发现</b>一张邪能法术牌。 |
| P0 | `VAC_323` | 麦芽岩浆 | Malted Magma | 2 | 15740 | spell_board复杂AOE | 直伤,敌AOE | - | 对所有敌人造成$1点伤害。<i>（还剩3杯！）</i> |
| P0 | `RLK_018` | 凋零打击 | Plague Strike | 2 | 15354 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$3点伤害。如果该随从死亡，召唤一个2/2并具有<b>突袭</b>的僵尸。 |
| P0 | `CORE_EX1_246` | 妖术 | Hex | 3 | 15274 | spell_board消灭 | 移除 | - | 使一个随从变形成为一只0/1并具有<b>嘲讽</b>的青蛙。 |
| P0 | `WW_006` | 飞镖投掷 | Dart Throw | 2 | 14009 | spell_board其他 | - | - | 随机向敌方随从投掷两枚造成$2点伤害的飞镖。<i>（如果两枚击中同一个随从，获取一张幸运币！）</i> |
| P0 | `RLK_709` | 冷酷严冬 | Remorseless Winter | 4 | 12847 | spell_board复杂AOE | 直伤,敌AOE | - | 对所有敌人造成$2点伤害。抽一张牌。 |
| P0 | `TIME_750` | 先行打击 | Precursory Strike | 2 | 12585 | spell_board解场伤 | 解场伤 | - | 造成$3点伤害。如果你的手牌中有法力值消耗大于或等于（5）点的随从牌，抽一张随从牌。 |
| P0 | `BT_490` | 吞噬魔法 | Consume Magic | 1 | 12219 | spell_board消灭 | 移除 | - | <b>沉默</b>一个敌方随从。<b>流放：</b>抽一张牌。 |
| P0 | `TTN_753` | 鼓动火焰 | Bellowing Flames | 3 | 11477 | spell_board复杂AOE | 解场伤,敌AOE | - | 对一个随从造成$5点伤害。<b>锻造：</b>然后造成$5点伤害，随机分配到所有敌方随从身上。 |
| P0 | `TLC_902` | 虫害侵扰 | Infestation | 2 | 11282 | spell_board其他 | - | - | 获取两张法力值消耗为（1）的格里什毒刺虫。毒刺虫可以造成$2点伤害并召唤一只2/1具有<b>突袭</b>的异种虫幼体。 |
| P0 | `GDB_902` | 潜入 | Infiltrate | 3 | 11277 | spell_board解场伤 | 解场伤 | - | 选择一个随从。对所有其他随从造成$3点伤害。 |
| P0 | `EDR_813` | 病变虫群 | Morbid Swarm | 1 | 11184 | spell_board解场伤 | 解场伤 | - | <b>抉择：</b>召唤两只1/1的蚂蚁；或者消耗2份<b>残骸</b>，对一个随从造成$4点伤害。 |
| P0 | `GDB_445` | 陨石风暴 | Meteor Storm | 6 | 11169 | spell_board复杂AOE | 解场伤,全场AOE | - | 对所有随从造成$5点伤害。将5张小行星洗入你的牌库。 |
| P0 | `CATA_582` | 灼热裂隙 | Searing Fissure | 2 | 11098 | spell_board复杂AOE | 解场伤,全场AOE | - | 对所有随从造成$1点伤害。在本回合中，使你的英雄获得+3攻击力。 |
| P0 | `JAM_018` | 混搭狂想曲 | Remixed Rhapsody | 5 | 10477 | spell_board复杂AOE | 解场伤,全场AOE | - | 对所有随从造成$3点伤害。在你的手牌中时会获得一项额外效果，该效果每回合都会改变。 |
| P0 | `TIME_433` | 抹除存在 | Cease to Exist | 3 | 9742 | spell_board消灭 | 移除 | - | <b>回溯</b>。<b>沉默</b>并消灭一个随机敌方随从。 |
| P0 | `WW_393` | 影叶入侵 | Invasive Shadeleaf | 4 | 9721 | spell_board解场伤 | 解场伤 | - | 对一个敌方随从造成$10点伤害。将超过目标生命值的伤害存入法力值消耗为（1）的瓶子。 |
| P0 | `CORE_CS1_112` | 神圣新星 | Holy Nova | 3 | 9077 | spell_board复杂AOE | 解场伤,敌AOE | - | 对所有敌方随从造成$2点伤害，为所有友方角色恢复#2点 生命值。 |
| P0 | `TOY_500` | 苏打火山 | Baking Soda Volcano | 4 | 8991 | spell_board复杂AOE | 解场伤,全场AOE | - | <b>吸血</b>。造成$10点伤害，随机分配到所有随从身上。<b>过载：</b>（1） |
| P0 | `BAR_314` | 罪罚（等级1） | Condemn (Rank 1) | 2 | 8808 | spell_board复杂AOE | 解场伤,敌AOE | - | 对所有敌方随从造成$1点伤害。<i>（当你有5点法力值时升级。）</i> |
| P0 | `REV_307` | 自然死亡 | Natural Causes | 2 | 8703 | spell_board其他 | - | - | 造成$2点伤害。召唤一个2/2的树人。 |
| P0 | `TOY_508` | 立体书 | Pop-Up Book | 1 | 8683 | spell_board其他 | - | - | 造成$2点伤害。召唤两只0/1并具有<b>嘲讽</b>的青蛙。 |
| P0 | `CORE_EX1_259` | 闪电风暴 | Lightning Storm | 3 | 8619 | spell_board解场伤 | 解场伤 | - | 对所有敌方随从造成$3点伤害，<b>过载：</b>（1） |
| P0 | `CORE_EX1_391` | 猛击 | Slam | 1 | 8487 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$2点伤害，如果 它依然存活，则抽一张牌。 |
| P0 | `REV_249` | 炽燃圣光 | The Light! It Burns! | 1 | 8293 | spell_board解场伤 | 解场伤 | - | 对一个随从造成等同于其攻击力的伤害。 |
| P0 | `CORE_BT_035` | 混乱打击 | Chaos Strike | 2 | 7453 | spell_board加攻 | - | - | 在本回合中，使你的英雄获得+2攻击力。抽一张牌。 |
| P0 | `VAC_414` | 炽热火炭 | Hot Coals | 3 | 7123 | spell_board复杂AOE | 直伤,敌AOE | - | 对所有敌人造成$2点伤害。如果你的英雄在本回合受到过伤害，再造成$1点。 |
| P0 | `CFM_696` | 衰变 | Devolve | 2 | 7118 | spell_board消灭 | 移除 | - | 随机将所有 敌方随从变形成为法力值消耗减少（1）点的随从。 |
| P0 | `CORE_AT_037` | 活体根须 | Living Roots | 1 | 6628 | spell_board其他 | - | - | <b>抉择：</b>造成$2点伤害；或者召唤两个1/1的树苗。 |
| P0 | `TIME_702` | 潮起潮落 | Ebb and Flow | 2 | 6354 | spell_board解场伤 | 解场伤 | - | 造成$3点伤害。如果你在本牌在你手中时使用过随从牌，获得5点护甲值。 |
| P0 | `TSC_932` | 血染大海 | Blood in the Water | 6 | 6114 | spell_board解场伤 | 解场伤 | - | 对一个敌人造成$3点伤害。召唤一条5/5并具有<b>突袭</b>的鲨鱼。 |
| P0 | `CORE_RLK_087` | 窒息 | Asphyxiate | 3 | 5553 | spell_board消灭 | 移除 | - | 消灭攻击力最高的敌方随从。 |
| P0 | `EDR_460` | 新月祈愿 | Wish of the New Moon | 3 | 5294 | spell_board解场伤 | 解场伤 | - | 对一个随从 造成$6点伤害。 <i>（施放3个法术 以获得<b>吸血</b>。）</i> |
| P0 | `CATA_533` | 涣漫洪流 | Flash Flood | 5 | 5206 | spell_board解场伤 | 解场伤 | - | 对你的对手最左边和最右边的随从造成$5点伤害。<b>流放：</b>重复一次。 |
| P0 | `GVG_015` | 暗色炸弹 | Darkbomb | 2 | 5170 | spell_board其他 | - | - | 对一个角色造成$3点伤害。如果该角色死亡，抽一张暗影法术牌。 |
| P0 | `WORK_014` | 恶魔交易 | Demonic Deal | 2 | 5117 | spell_board解场伤 | 解场伤 | - | <b>吸血</b> 对一个随从造成$4点伤害。将一张法力值消耗大于或等于（5）点的随机恶魔牌置于你的牌库顶。 |
| P0 | `ICC_041` | 亵渎 | Defile | 2 | 4721 | spell_board复杂AOE | 解场伤,全场AOE | - | 对所有随从造成$1点伤害，如果有随从死亡，则再次施放该法术。 |
| P0 | `GDB_460` | 神圣之星 | Divine Star | 2 | 4696 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$3点伤害。随机使你手牌中的一张随从牌获得+3生命值。 |
| P0 | `VAC_404` | 夜影花茶 | Nightshade Tea | 1 | 4618 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$2点伤害。对你的英雄造成$2点伤害。<i>（还剩3杯！）</i> |
| P0 | `WW_427` | 夕阳漫射 | Sunset Volley | 9 | 4557 | spell_board复杂AOE | 直伤,解场伤,敌AOE | - | 造成$10点伤害，随机分配到所有敌人身上。随机召唤一个法力值消耗为（10）的随从。 |
| P0 | `ULD_714` | 苦修 | Penance | 2 | 4314 | spell_board解场伤 | 解场伤 | - | <b>吸血</b> 对一个随从造成$3点伤害。 |
| P0 | `TIME_215` | 雷霆动地 | Thunderquake | 2 | 4021 | spell_board复杂AOE | 解场伤,全场AOE | - | 对所有随从造成$1点伤害。获取一张静电震击。 |
| P0 | `TIME_619t2` | 赞达拉的惨象 | What Befell Zandalar | 3 | 3820 | spell_board复杂AOE | 直伤,敌AOE | - | 对所有敌人造成$2点伤害。选择并使邦桑迪获得一项恩泽。 |
| P0 | `WORK_022` | 打卡 | Punch Card | 3 | 3802 | spell_board加攻 | - | - | 在本回合中，使你的英雄获得+3攻击力和“同时对相邻随从造成伤害”。 |
| P0 | `TTN_460` | 致命诛灭 | Mortal Eradication | 3 | 3797 | spell_board复杂AOE | 解场伤,敌AOE | - | 造成$5点伤害，随机分配到所有敌方随从身上。每消灭一个随从，为你的英雄恢复#2点生命值。 |
| P0 | `KAR_076` | 火焰之地传送门 | Firelands Portal | 7 | 3785 | spell_board解场伤 | 解场伤 | - | 造成$6点伤害。随机召唤一个法力值消耗为（6）的随从。 |
| P0 | `TOY_377` | 霜巫十字绣 | Frost Lich Cross-Stitch | 4 | 3774 | spell_board其他 | - | - | 对一个角色造成$3点伤害。如果该角色死亡，召唤一个3/6的可以<b><b>冻结</b></b>攻击目标的水元素。 |
| P0 | `DMF_701` | 深水炸弹 | Dunk Tank | 4 | 3585 | spell_board复杂AOE | 解场伤,敌AOE | - | 造成$4点伤害。<b>腐蚀：</b>再对所有敌方随从造成$2点伤害。 |
| P0 | `SW_107` | 火热促销 | Fire Sale | 4 | 3559 | spell_board复杂AOE | 解场伤,全场AOE | - | <b>可交易</b> 对所有随从造成 $3点伤害。 |
| P0 | `TTN_932` | 混乱吞噬 | Chaotic Consumption | 1 | 3472 | spell_board消灭 | 移除 | - | 消灭一个友方随从以消灭一个敌方随从。 |
| P0 | `DMF_117` | 连环灾难 | Cascading Disaster | 4 | 3470 | spell_board消灭 | 移除 | - | 随机消灭一个敌方随从。<b>腐蚀：</b>消灭两个。<b>再次腐蚀：</b>消灭三个。 |
| P0 | `CORE_EX1_309` | 灵魂虹吸 | Siphon Soul | 4 | 3287 | spell_board消灭 | 移除 | - | 消灭一个随从，为你的英雄恢复#3点生命值。 |
| P0 | `VAC_951` | “健康”饮品 | "Health" Drink | 3 | 3276 | spell_board解场伤 | 解场伤 | - | <b>吸血</b> 对一个随从造成$3点伤害。<i>（还剩3杯！）</i> |
| P0 | `ETC_363` | 主歌乐句 | Verse Riff | 1 | 3247 | spell_board加攻 | - | - | 在本回合中，使你的英雄获得+2攻击力。获得2点护甲值。<b>压轴：</b>演奏你的上一个乐句。 |
| P0 | `CATA_489` | 奥术涌流 | Arcane Flow | 4 | 2573 | spell_board复杂AOE | 直伤,移除,敌AOE | - | <b>裂变</b> 造成$4点伤害。对所有敌人造成$2点伤害。123743造成$4点伤害。对所有敌人造成$2点伤害。 |
| P0 | `TIME_209t2` | 天神下凡形态 | Avatar Form | 3 | 2523 | spell_board复杂AOE | 直伤,敌AOE | - | 在本回合中，使一个友方角色获得+2攻击力和“在本角色攻击后，对所有敌人造成2点伤害”。 |
| P0 | `SW_090` | 纳斯雷兹姆之触 | Touch of the Nathrezim | 1 | 2500 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$2点伤害。如果该随从死亡，则为你的英雄恢复#3点生命值。 |
| P0 | `CATA_203` | 迦罗娜的奋战 | Garona's Last Stand | 2 | 2494 | spell_board消灭 | 移除 | - | <b>可交易</b> 消灭一个<b>传说</b> 随从。 |
| P0 | `NX2_020` | 野蛮残食 | Cannibalize | 4 | 2465 | spell_board消灭 | 移除 | - | 消灭一个随从。为所有友方角色恢复生命值，数值相当于该随从的生命值。 |
| P0 | `TIME_216` | 新生闪电 | Nascent Bolt | 3 | 2291 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$5点伤害。如果该随从依然存活，抽两张牌。 |
| P0 | `VAC_953` | 浪潮涌起 | Rising Waves | 3 | 2242 | spell_board复杂AOE | 解场伤,全场AOE | - | 对所有随从造成 $2点伤害。如果没有随从死亡，再造成$2点。 |
| P0 | `CORE_BAR_541` | 符文宝珠 | Runed Orb | 2 | 2232 | spell_board其他 | - | - | 造成$2点伤害。<b>发现</b>一张法术牌。 |
| P0 | `ETC_069` | 渐强声浪 | Crescendo | 2 | 1760 | spell_board复杂AOE | 直伤,敌AOE | - | 受到疲劳伤害。对所有敌人造成等量的伤害。0受到{0}点疲劳伤害。对所有敌人造成等量的伤害。 |
| P0 | `CATA_306` | 教派分歧 | Schism | 4 | 1726 | spell_board消灭 | 移除 | - | <b>裂变</b> 使一个友方随从获得+2/+3和<b>扰魔</b>。召唤一个它的复制。122876使一个友方随从获得+2/+3和<b>扰魔</b>。召唤一个它的复制。 |
| P0 | `TTN_726` | 焦油飞溅 | Tar Slick | 1 | 1717 | spell_board其他 | - | - | 在本回合中，随从受到的伤害翻倍。造成$1点伤害。 |
| P0 | `FIR_954` | 焚烧 | Conflagrate | 1 | 1689 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$5点伤害，其拥有者抽一张牌。 |
| P0 | `TLC_221` | 炽火缠身 | Sizzling Swarm | 6 | 1630 | spell_board其他 | - | - | 造成$3点伤害，召唤相同数量的2/1的炽烈烬火。 |
| P0 | `UNG_955` | 陨石术 | Meteor | 6 | 1564 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$15点伤害，并对其相邻的随从造成 $4点伤害。 |
| P0 | `RLK_063` | 冰霜巨龙之怒 | Frostwyrm's Fury | 7 | 1539 | spell_board复杂AOE | 解场伤,敌AOE | - | 造成$5点伤害。<b>冻结</b>所有敌方随从。召唤一条5/5的冰霜巨龙。 |
| P0 | `CFM_662` | 龙息药水 | Dragonfire Potion | 5 | 1516 | spell_board复杂AOE | 解场伤,全场AOE | - | 对所有非龙随从造成$5点伤害。 |
| P0 | `CORE_SW_108` | 初始之火 | First Flame | 1 | 1498 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$2点伤害。将“传承之火”置入你的手牌。 |
| P0 | `GVG_010` | 维伦的恩泽 | Velen's Chosen | 3 | 1495 | spell_board其他 | - | - | 使一个随从获得+2/+4和<b>法术伤害+1</b>。 |
| P0 | `GDB_305` | 阳炎耀斑 | Solar Flare | 5 | 1458 | spell_board复杂AOE | 直伤,敌AOE | - | 对所有敌人造成$2点伤害。你每控制一个元素，本牌的法力值消耗便减少（1）点。 |
| P0 | `CORE_CS2_093` | 奉献 | Consecration | 3 | 1433 | spell_board复杂AOE | 直伤,敌AOE | - | 对所有敌人造成$2点伤害。 |
| P0 | `BT_117` | 剑刃风暴 | Bladestorm | 2 | 1307 | spell_board复杂AOE | 解场伤,全场AOE | - | 对所有随从造成$1点伤害。重复此效果，直到某个随从 死亡。 |
| P0 | `CATA_452` | 织法者的光辉 | Spellweaver's Brilliance | 10 | 1300 | spell_board其他 | - | - | 召唤一条6/6的龙。在本回合中，你每用法术造成一点伤害，本牌的法力值消耗便减少（1）点。 |
| P0 | `DED_517` | 奥术溢爆 | Arcane Overflow | 5 | 1258 | spell_board解场伤 | 解场伤 | - | 对一个敌方随从造成$8点伤害。召唤一滩残渣，属性值等同于超过目标生命值的伤害。 |
| P0 | `BT_011` | 正义圣契 | Libram of Justice | 5 | 1208 | spell_board加攻 | - | - | 装备一把1/4的武器。将所有敌方随从的生命值变为1。 |
| P0 | `YOG_502` | 清理污染 | Sanitize | 4 | 1182 | spell_board复杂AOE | 全场AOE | - | 对所有随从造成等同于你的护甲值的伤害。<b>锻造：</b>先获得3点护甲值。 |
| P0 | `ETC_314` | 悦耳流行歌 | Harmonic Pop | 6 | 1135 | spell_board复杂AOE | 解场伤,全场AOE | - | 对所有随从造成$3点伤害。召唤一个6/6的流行歌星。<i>（每回合切换。）</i> |
| P0 | `REV_239` | 窒息暗影 | Suffocating Shadows | 3 | 1109 | spell_board消灭 | 移除 | - | 当你使用或弃掉这张牌时，随机消灭一个敌方随从。 |
| P0 | `CATA_479` | 飞龙机动 | Flight Maneuvers | 4 | 980 | spell_board消灭 | 移除 | - | <b>裂变</b> 召唤两条4/2的幼龙。使你的随从获得+1攻击力和<b>圣盾</b>。123141召唤两条4/2的幼龙。使你的随从获得+1攻击力和<b>圣盾</b>。 |
| P0 | `TLC_901` | 烟雾熏蒸 | Fumigate | 2 | 966 | spell_board解场伤 | 解场伤 | - | 对一个随从及所有相同类型的其他随从造成$3点伤害。 |
| P0 | `SW_441` | 纳鲁碎片 | Shard of the Naaru | 1 | 951 | spell_board消灭 | 移除 | - | <b>可交易</b> <b>沉默</b>所有敌方随从。 |
| P0 | `CATA_557` | 希尔瓦娜斯的胜利 | Sylvanas's Triumph | 2 | 800 | spell_board复杂AOE | 直伤,敌AOE | - | 造成$3点伤害。如果你使用过本牌的其他复制，改为对所有敌人造成伤害。 |
| P0 | `CATA_978` | 辛达苟萨的胜利 | Sindragosa's Triumph | 5 | 780 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$8点伤害。使你手牌中一张随机牌的法力值消耗减少，减少的量等于超过目标生命值的伤害。 |
| P0 | `TTN_853` | 审判恶徒 | Judge Unworthy | 4 | 756 | spell_board复杂AOE | 直伤,敌AOE | - | 将一个敌方随从的生命值变为1，然后对所有敌人造成$1点 伤害。 |
| P0 | `REV_507` | 处理证据 | Dispose of Evidence | 0 | 697 | spell_board加攻 | - | - | 在本回合中，使你的英雄获得+3攻击力。从你的3张手牌中选择一张洗入你的牌库。 |
| P0 | `SCH_512` | 通窍 | Initiation | 6 | 636 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$4点伤害。如果该随从死亡，召唤一个新的复制。 |
| P0 | `CORE_CS2_028` | 暴风雪 | Blizzard | 6 | 575 | spell_board复杂AOE | 解场伤,敌AOE | - | 对所有敌方随从造成$2点伤害，并使其<b>冻结</b>。 |
| P0 | `CORE_GVG_061` | 作战动员 | Muster for Battle | 3 | 547 | spell_board加攻 | - | - | 召唤三个1/1的白银之手新兵，装备一把1/4的武器。 |
| P1 | `SCH_138` | 威能祝福 | Blessing of Authority | 5 | 475 | spell_board其他 | - | - | 使一个随从获得+8/+8，在本回合中无法攻击英雄。 |
| P1 | `ONY_010` | 灭龙射击 | Dragonbane Shot | 2 | 466 | SPELL_DAMAGE直伤 | 直伤 | - | 造成$2点伤害。<b>荣誉消灭：</b>将一张灭龙射击置入你的手牌。 |
| P1 | `ETC_082` | 绝望哀歌 | Dirge of Despair | 6 | 453 | spell_board其他 | - | - | 对一个角色造成$3点伤害。如果该角色死亡，从你的牌库中召唤一个恶魔。 |
| P1 | `VAC_416` | 死亡翻滚 | Death Roll | 5 | 445 | spell_board复杂AOE | 直伤,移除,敌AOE | - | 消灭一个敌方随从。造成等同于其攻击力的伤害，随机分配到所有敌人身上。 |
| P1 | `TSC_006` | 多重打击 | Multi-Strike | 2 | 384 | spell_board加攻 | - | - | 在本回合中使你的英雄获得+2攻击力，并可以额外攻击一次敌方随从。 |
| P1 | `EDR_874` | 星体平衡 | Stellar Balance | 2 | 345 | spell_board其他 | - | - | 获取一张月火术和一张星火术，使其获得<b>法术伤害+1</b>。 |
| P1 | `FIR_910` | 灼烧之风 | Scorching Winds | 3 | 345 | SPELL_DAMAGE直伤 | 直伤,解场伤 | - | 造成$3点伤害。随机弃掉一张火焰法术牌以再造成$3点。 |
| P1 | `DINO_406` | 喷吐火焰 | Fire Breath | 3 | 338 | SPELL_DAMAGE直伤 | 直伤 | - | 造成$4点伤害。使你的元素获得+1/+1。 |
| P1 | `TOY_883` | 掀桌子 | Table Flip | 10 | 300 | spell_board复杂AOE | 解场伤,敌AOE | - | 对所有敌方随从造成$3点伤害。你每有一张其他手牌，本牌的法力值消耗便减少（1）点。 |
| P1 | `RLK_918` | 为了奎尔萨拉斯！ | For Quel'Thalas! | 2 | 274 | spell_board加攻 | - | - | 使一个友方随从获得+3攻击力。在本回合中，使你的英雄获得+2攻击力。 |
| P1 | `LOOT_417` | 大灾变 | Cataclysm | 5 | 216 | spell_board消灭 | 移除 | - | 消灭所有随从。弃两张牌。 |
| P1 | `EDR_262` | 灵魂联结 | Spirit Bond | 3 | 189 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$3点伤害。如果该随从死亡，召唤一只3/2并具有<b>突袭</b>的狼。 |
| P1 | `VAC_944` | 咒怨纪念品 | Cursed Souvenir | 2 | 179 | spell_board其他 | - | - | 使一个随从获得+3/+3和“在你的回合开始时，对你的英雄造成3点伤害”。 |
| P1 | `WC_021` | 不稳定的暗影震爆 | Unstable Shadow Blast | 2 | 165 | spell_board解场伤 | 解场伤 | - | 对一个随从造成$6点伤害，超过目标生命值的伤害会命中你的英雄。 |
| P1 | `SW_088` | 恶魔来袭 | Demonic Assault | 4 | 138 | spell_board其他 | - | - | 造成$3点伤害。召唤两个1/3并具有<b>嘲讽</b>的虚空行者。 |
| P1 | `TIME_027` | 超光子弹幕 | Tachyon Barrage | 2 | 111 | spell_board复杂AOE | 直伤,解场伤,敌AOE | - | 造成$6点伤害，随机分配到所有敌人身上。将2张时空撕裂洗入你的牌库。 |
| P2 | `TIME_600` | 精确射击 | Precise Shot | 2 | 97 | SPELL_DAMAGE直伤 | 直伤 | - | 造成$3点伤害。如果本牌位于你手牌的正中间，改为造成 $5点。 |
| P2 | `RLK_534` | 灵魂弹幕 | Soul Barrage | 4 | 50 | spell_board复杂AOE | 直伤,解场伤,敌AOE | - | 当你使用或弃掉这张牌时，造成$5点伤害，随机分配到所有敌人身上。 |
| P3 | `TIME_711` | 闪回 | Flashback | 2 | 14446 | spell_board其他 | - | 铺场/连击加攻，无当回合伤害 | 随机召唤两个来自过去的法力值消耗为（1）的随从。<b>连击：</b>并具有+1攻击力。 |
| P3 | `CORE_RLK_035` | 邪爆 | Corpse Explosion | 5 | 5808 | spell_board复杂AOE | 解场伤,全场AOE | 邪爆：全体清场循环，非场攻 | 引爆一份<b>残骸</b>，对所有随从造成$1点伤害。如果有随从存活，重复此效果。 |
| P3 | `CATA_526` | 布洛克斯加的奋战 | Broxigar's Last Stand | 2 | 5569 | spell_board复杂AOE | 解场伤,全场AOE | 布洛克斯加的奋战：全体清场，非场攻 | 对所有随从造成$1点伤害。每有一个随从死亡，抽一 张牌。 |
| P3 | `RLK_730` | 血液沸腾 | Blood Boil | 5 | 4172 | spell_board复杂AOE | 解场伤,敌AOE | 感染后回合结束才伤害，与斩杀无关 | <b>吸血</b>。感染所有敌方随从。在你的回合结束时，使其受到2点伤害。 |
| P3 | `CATA_202` | 能量窃取 | Stolen Power | 3 | 3886 | spell_board消灭 | 移除 | 仅获取裂变牌，无伤害 | 随机获取一张另一职业的<i>已拼合的</i><b>裂变</b>牌。 |
| P3 | `CATA_134` | 荒林怪圈 | Wildwood Circle | 4 | 3664 | spell_board消灭 | 移除 | 铺场树人/亡语，非斩杀 | <b>裂变</b> 召唤两个2/2的树人。使你的随从获得“<b>亡语：</b>召唤一个2/2的树人。”122972召唤两个2/2的树人。使你的随从获得“<b>亡语：</b>召唤一个2/2的树人。” |
| P3 | `CATA_491` | 怪异触手 | Eldritch Tentacles | 6 | 3503 | spell_board复杂AOE | 解场伤,全场AOE | 怪异触手：全体清场递减，非场攻 | 对所有随从造成$3点伤害。重复 此效果，每次伤害减少1点。 |
| P3 | `CATA_567` | 升腾 | Ascendance | 4 | 3201 | spell_board消灭 | 移除 | 变形铺场，非斩杀 | 将所有友方随从变形成为法力值消耗增加（1）点的随从。当这些随从死亡时，召唤原随从。 |
| P3 | `EX1_407` | 绝命乱斗 | Brawl | 5 | 2971 | spell_board消灭 | 移除 | 乱斗仅解场，清嘲后不一定增加当回合打脸 | 随机选择一个随从，消灭除了该随从外的所有其他随从。 |
| P3 | `OG_027` | 异变 | Evolve | 1 | 1971 | spell_board消灭 | 移除 | 异变提升己方随从，非斩杀 | 随机将你的 所有随从变形成为法力值消耗增加（1）点的随从。 |
| P3 | `CATA_581` | 屠灭 | Decimation | 6 | 1899 | spell_board复杂AOE | 解场伤,全场AOE | 屠灭：全体清场，非场攻 | 对所有随从造成$1点伤害<i>（战场上每有一个随从都会提高）</i>。 |
| P3 | `WORK_026` | 失火 | Burndown | 3 | 1714 | spell_board消灭 | 移除 | 失火：抽牌点燃，无当回合伤害 | 抽三张牌并将其点燃。3回合后，摧毁其中仍在手中的牌。 |
| P3 | `SCH_235` | 衰变飞弹 | Devolving Missiles | 1 | 1515 | spell_board消灭 | 移除 | 衰变飞弹，衰变机制暂不模拟 | 随机向敌方随从发射三枚飞弹，使其变形成为法力值消耗减少（1）点的随从。 |
| P3 | `FIR_902` | 燃薪咒符 | Sigil of Cinder | 2 | 1117 | spell_board复杂AOE | 直伤,解场伤,敌AOE | 燃薪咒符，下回合开始才伤害 | 在你的下回合开始时，造成$6点伤害，随机分配到所有敌人身上。 |
| P3 | `CATA_820` | 运输补给 | Supply Run | 4 | 837 | spell_board消灭 | 移除 | 运输补给：抽牌+buff手牌，非斩杀 | <b>裂变</b> 抽三张随从牌。使你手牌中的随从牌获得+2/+2。121758抽三张随从牌。使你手牌中的随从牌获得+2/+2。 |
| P3 | `WW_092` | 液力压裂 | Fracking | 1 | 714 | spell_board消灭 | 移除 | 液力压裂：检视牌库抽牌，非斩杀 | 检视你的牌库底的三张牌，抽其中一张，摧毁其余牌。 |
| P3 | `AV_330` | 纳鲁的赐福 | Gift of the Naaru | 1 | 587 | spell_board复杂AOE | 全场AOE | 纳鲁的赐福：回血，非斩杀 | 为所有角色恢复#3点生命值。如果有角色仍处于受伤状态，抽一张牌。 |

---

## 按优先级分组（详细条目）

### P0（102 张）

#### spell_board解场伤（33 张）

- **`DAL_716`** 宿敌 / Vendetta  （4费 · games=44297 · 解场伤）
  - 中文：**对一个随从造成$4点伤害。如果你的手牌中有另一职业的卡牌，则法力值消耗为（0）点。**
  - 英文：Deal $4 damage to a minion. Costs (0) if you're holding a card from another class.

- **`REV_939`** 锯齿骨刺 / Serrated Bone Spike  （2费 · games=22503 · 解场伤）
  - 中文：**对一个随从造成$3点伤害。如果该随从死亡，在本回合中，你的下一张牌法力值消耗减少（2）点。**
  - 英文：[x]Deal $3 damage to a minion. If it dies, your next card this turn costs (2) less.

- **`FIR_939`** 影焰晕染 / Shadowflame Suffusion  （2费 · games=19766 · 解场伤）
  - 中文：**造成$2点伤害。<b>发现</b>一张具有<b>黑暗之赐</b>的战士随从牌。**
  - 英文：[x]Deal $2 damage. <b>Discover</b> a Warrior minion with a <b>Dark Gift</b>.

- **`CATA_585`** 烈火炙烤 / Torch  （1费 · games=18033 · 解场伤）
  - 中文：**对一个受伤的随从造成$8点伤害。如果伤害超过目标生命值，将能造成剩余伤害的本牌移回手牌。**
  - 英文：[x]Deal $8 damage to a damaged minion. Return this to hand with any excess damage.

- **`WW_354`** 残骸遍野 / Fistful of Corpses  （1费 · games=18020 · 解场伤）
  - 中文：**对一个随从造成等同于你的<b>残骸</b>数量的伤害。**
  - 英文：Deal damage to a minion equal to your <b>Corpses</b>.

- **`ETC_394`** 混乱品味 / Taste of Chaos  （1费 · games=16169 · 解场伤）
  - 中文：**对一个随从造成$2点伤害。<b>压轴：</b><b>发现</b>一张邪能法术牌。**
  - 英文：Deal $2 damage to a minion. <b>Finale:</b> <b>Discover</b> a Fel spell.

- **`RLK_018`** 凋零打击 / Plague Strike  （2费 · games=15354 · 解场伤）
  - 中文：**对一个随从造成$3点伤害。如果该随从死亡，召唤一个2/2并具有<b>突袭</b>的僵尸。**
  - 英文：Deal $3 damage to a minion. If it dies, summon a 2/2 Zombie with <b>Rush</b>.

- **`TIME_750`** 先行打击 / Precursory Strike  （2费 · games=12585 · 解场伤）
  - 中文：**造成$3点伤害。如果你的手牌中有法力值消耗大于或等于（5）点的随从牌，抽一张随从牌。**
  - 英文：Deal $3 damage. If you're holding a minion that costs (5) or more, draw a minion.

- **`GDB_902`** 潜入 / Infiltrate  （3费 · games=11277 · 解场伤）
  - 中文：**选择一个随从。对所有其他随从造成$3点伤害。**
  - 英文：Choose a minion. Deal $3 damage to all other minions.

- **`EDR_813`** 病变虫群 / Morbid Swarm  （1费 · games=11184 · 解场伤）
  - 中文：**<b>抉择：</b>召唤两只1/1的蚂蚁；或者消耗2份<b>残骸</b>，对一个随从造成$4点伤害。**
  - 英文：<b>Choose One -</b> Summon two 1/1 Ants; or Spend 2 <b>Corpses</b> to deal $4 damage to a minion.

- **`WW_393`** 影叶入侵 / Invasive Shadeleaf  （4费 · games=9721 · 解场伤）
  - 中文：**对一个敌方随从造成$10点伤害。将超过目标生命值的伤害存入法力值消耗为（1）的瓶子。**
  - 英文：Deal $10 damage to an enemy minion. Save any excess in a 1-Cost Bottle.

- **`CORE_EX1_259`** 闪电风暴 / Lightning Storm  （3费 · games=8619 · 解场伤）
  - 中文：**对所有敌方随从造成$3点伤害，<b>过载：</b>（1）**
  - 英文：Deal $3 damage to all enemy minions. <b>Overload:</b> (1)

- **`CORE_EX1_391`** 猛击 / Slam  （1费 · games=8487 · 解场伤）
  - 中文：**对一个随从造成$2点伤害，如果 它依然存活，则抽一张牌。**
  - 英文：Deal $2 damage to a minion. If it survives, draw a card.

- **`REV_249`** 炽燃圣光 / The Light! It Burns!  （1费 · games=8293 · 解场伤）
  - 中文：**对一个随从造成等同于其攻击力的伤害。**
  - 英文：[x]Deal damage to a minion equal to its Attack.

- **`TIME_702`** 潮起潮落 / Ebb and Flow  （2费 · games=6354 · 解场伤）
  - 中文：**造成$3点伤害。如果你在本牌在你手中时使用过随从牌，获得5点护甲值。**
  - 英文：Deal $3 damage. If you played a minion while holding this, gain 5 Armor.

- **`TSC_932`** 血染大海 / Blood in the Water  （6费 · games=6114 · 解场伤）
  - 中文：**对一个敌人造成$3点伤害。召唤一条5/5并具有<b>突袭</b>的鲨鱼。**
  - 英文：Deal $3 damage to an enemy. Summon a 5/5 Shark with <b>Rush</b>.

- **`EDR_460`** 新月祈愿 / Wish of the New Moon  （3费 · games=5294 · 解场伤）
  - 中文：**对一个随从 造成$6点伤害。 <i>（施放3个法术 以获得<b>吸血</b>。）</i>**
  - 英文：Deal $6 damage to a minion. <i>(Cast 3 spells to gain <b>Lifesteal</b>.)</i>

- **`CATA_533`** 涣漫洪流 / Flash Flood  （5费 · games=5206 · 解场伤）
  - 中文：**对你的对手最左边和最右边的随从造成$5点伤害。<b>流放：</b>重复一次。**
  - 英文：[x]Deal $5 damage to your opponent's left  and right-most minions. <b>Outcast:</b> Do it again.

- **`WORK_014`** 恶魔交易 / Demonic Deal  （2费 · games=5117 · 解场伤）
  - 中文：**<b>吸血</b> 对一个随从造成$4点伤害。将一张法力值消耗大于或等于（5）点的随机恶魔牌置于你的牌库顶。**
  - 英文：[x]<b>Lifesteal</b>. Deal $4 damage to a minion. Put a random Demon that costs (5) or more on top of your deck.

- **`GDB_460`** 神圣之星 / Divine Star  （2费 · games=4696 · 解场伤）
  - 中文：**对一个随从造成$3点伤害。随机使你手牌中的一张随从牌获得+3生命值。**
  - 英文：Deal $3 damage to a minion. Give a random minion in your hand +3 Health.

- **`VAC_404`** 夜影花茶 / Nightshade Tea  （1费 · games=4618 · 解场伤）
  - 中文：**对一个随从造成$2点伤害。对你的英雄造成$2点伤害。<i>（还剩3杯！）</i>**
  - 英文：Deal $2 damage to a minion. Deal $2 damage to your hero. <i>(3 Drinks left!)</i>

- **`ULD_714`** 苦修 / Penance  （2费 · games=4314 · 解场伤）
  - 中文：**<b>吸血</b> 对一个随从造成$3点伤害。**
  - 英文：<b>Lifesteal</b> Deal $3 damage to a minion.

- **`KAR_076`** 火焰之地传送门 / Firelands Portal  （7费 · games=3785 · 解场伤）
  - 中文：**造成$6点伤害。随机召唤一个法力值消耗为（6）的随从。**
  - 英文：Deal $6 damage. Summon a random 6-Cost minion.

- **`VAC_951`** “健康”饮品 / "Health" Drink  （3费 · games=3276 · 解场伤）
  - 中文：**<b>吸血</b> 对一个随从造成$3点伤害。<i>（还剩3杯！）</i>**
  - 英文：<b>Lifesteal</b>. Deal $3 damage to a minion. <i>(3 Drinks left!)</i>

- **`SW_090`** 纳斯雷兹姆之触 / Touch of the Nathrezim  （1费 · games=2500 · 解场伤）
  - 中文：**对一个随从造成$2点伤害。如果该随从死亡，则为你的英雄恢复#3点生命值。**
  - 英文：[x]Deal $2 damage to a minion. If it dies, restore #3 Health to your hero.

- **`TIME_216`** 新生闪电 / Nascent Bolt  （3费 · games=2291 · 解场伤）
  - 中文：**对一个随从造成$5点伤害。如果该随从依然存活，抽两张牌。**
  - 英文：Deal $5 damage to a minion. If it survives, draw 2 cards.

- **`FIR_954`** 焚烧 / Conflagrate  （1费 · games=1689 · 解场伤）
  - 中文：**对一个随从造成$5点伤害，其拥有者抽一张牌。**
  - 英文：Deal $5 damage to a minion. Its owner draws a card.

- **`UNG_955`** 陨石术 / Meteor  （6费 · games=1564 · 解场伤）
  - 中文：**对一个随从造成$15点伤害，并对其相邻的随从造成 $4点伤害。**
  - 英文：Deal $15 damage to a minion and $4 damage to adjacent ones.

- **`CORE_SW_108`** 初始之火 / First Flame  （1费 · games=1498 · 解场伤）
  - 中文：**对一个随从造成$2点伤害。将“传承之火”置入你的手牌。**
  - 英文：Deal $2 damage to a minion. Add a Second Flame to your hand.

- **`DED_517`** 奥术溢爆 / Arcane Overflow  （5费 · games=1258 · 解场伤）
  - 中文：**对一个敌方随从造成$8点伤害。召唤一滩残渣，属性值等同于超过目标生命值的伤害。**
  - 英文：[x]Deal $8 damage to an enemy minion. Summon a Remnant with stats equal to the excess damage.

- **`TLC_901`** 烟雾熏蒸 / Fumigate  （2费 · games=966 · 解场伤）
  - 中文：**对一个随从及所有相同类型的其他随从造成$3点伤害。**
  - 英文：Deal $3 damage to a minion and all others of the same minion type.

- **`CATA_978`** 辛达苟萨的胜利 / Sindragosa's Triumph  （5费 · games=780 · 解场伤）
  - 中文：**对一个随从造成$8点伤害。使你手牌中一张随机牌的法力值消耗减少，减少的量等于超过目标生命值的伤害。**
  - 英文：[x]Deal $8 damage to a minion. Reduce the Cost of a random card in your hand by the excess damage.

- **`SCH_512`** 通窍 / Initiation  （6费 · games=636 · 解场伤）
  - 中文：**对一个随从造成$4点伤害。如果该随从死亡，召唤一个新的复制。**
  - 英文：Deal $4 damage to a minion. If it dies, summon a new copy.

#### spell_board复杂AOE（33 张）

- **`EX1_129`** 刀扇 / Fan of Knives  （2费 · games=22437 · 解场伤,敌AOE）
  - 中文：**对所有敌方随从造成$1点伤害，抽一张牌。**
  - 英文：Deal $1 damage to all enemy minions. Draw a card.

- **`CATA_156`** 试验演示 / Experimental Animation  （6费 · games=22360 · 解场伤,敌AOE）
  - 中文：**<b>兆示</b>{0}。对所有敌方随从造成$4点伤害。**
  - 英文：<b>Herald</b> {0}. Deal $4 damage to all enemy minions.

- **`VAC_323`** 麦芽岩浆 / Malted Magma  （2费 · games=15740 · 直伤,敌AOE）
  - 中文：**对所有敌人造成$1点伤害。<i>（还剩3杯！）</i>**
  - 英文：Deal $1 damage to all enemies. <i>(3 Drinks left!)</i>

- **`RLK_709`** 冷酷严冬 / Remorseless Winter  （4费 · games=12847 · 直伤,敌AOE）
  - 中文：**对所有敌人造成$2点伤害。抽一张牌。**
  - 英文：Deal $2 damage to all enemies. Draw a card.

- **`TTN_753`** 鼓动火焰 / Bellowing Flames  （3费 · games=11477 · 解场伤,敌AOE）
  - 中文：**对一个随从造成$5点伤害。<b>锻造：</b>然后造成$5点伤害，随机分配到所有敌方随从身上。**
  - 英文：Deal $5 damage to a minion. <b>Forge:</b> Then deal $5 damage split among all enemy minions.

- **`GDB_445`** 陨石风暴 / Meteor Storm  （6费 · games=11169 · 解场伤,全场AOE）
  - 中文：**对所有随从造成$5点伤害。将5张小行星洗入你的牌库。**
  - 英文：Deal $5 damage to all minions. Shuffle 5 Asteroids into your deck.

- **`CATA_582`** 灼热裂隙 / Searing Fissure  （2费 · games=11098 · 解场伤,全场AOE）
  - 中文：**对所有随从造成$1点伤害。在本回合中，使你的英雄获得+3攻击力。**
  - 英文：Deal $1 damage to all minions. Give your hero +3 Attack this turn.

- **`JAM_018`** 混搭狂想曲 / Remixed Rhapsody  （5费 · games=10477 · 解场伤,全场AOE）
  - 中文：**对所有随从造成$3点伤害。在你的手牌中时会获得一项额外效果，该效果每回合都会改变。**
  - 英文：Deal $3 damage to all minions. Gains an extra effect in your hand that changes each turn.

- **`CORE_CS1_112`** 神圣新星 / Holy Nova  （3费 · games=9077 · 解场伤,敌AOE）
  - 中文：**对所有敌方随从造成$2点伤害，为所有友方角色恢复#2点 生命值。**
  - 英文：Deal $2 damage to all enemy minions. Restore #2 Health to all friendly characters.

- **`TOY_500`** 苏打火山 / Baking Soda Volcano  （4费 · games=8991 · 解场伤,全场AOE）
  - 中文：**<b>吸血</b>。造成$10点伤害，随机分配到所有随从身上。<b>过载：</b>（1）**
  - 英文：<b>Lifesteal</b>. Deal $10 damage randomly split among all minions. <b>Overload:</b> (1)

- **`BAR_314`** 罪罚（等级1） / Condemn (Rank 1)  （2费 · games=8808 · 解场伤,敌AOE）
  - 中文：**对所有敌方随从造成$1点伤害。<i>（当你有5点法力值时升级。）</i>**
  - 英文：[x]Deal $1 damage to all enemy minions. <i>(Upgrades when you have 5 Mana.)</i>

- **`VAC_414`** 炽热火炭 / Hot Coals  （3费 · games=7123 · 直伤,敌AOE）
  - 中文：**对所有敌人造成$2点伤害。如果你的英雄在本回合受到过伤害，再造成$1点。**
  - 英文：[x]Deal $2 damage to all enemies. If your hero took damage this turn, deal $1 more.

- **`ICC_041`** 亵渎 / Defile  （2费 · games=4721 · 解场伤,全场AOE）
  - 中文：**对所有随从造成$1点伤害，如果有随从死亡，则再次施放该法术。**
  - 英文：Deal $1 damage to all minions. If any die, cast this again.

- **`WW_427`** 夕阳漫射 / Sunset Volley  （9费 · games=4557 · 直伤,解场伤,敌AOE）
  - 中文：**造成$10点伤害，随机分配到所有敌人身上。随机召唤一个法力值消耗为（10）的随从。**
  - 英文：Deal $10 damage randomly split among all enemies. Summon a random 10-Cost minion.

- **`TIME_215`** 雷霆动地 / Thunderquake  （2费 · games=4021 · 解场伤,全场AOE）
  - 中文：**对所有随从造成$1点伤害。获取一张静电震击。**
  - 英文：[x]Deal $1 damage to all minions. Get a Static Shock.

- **`TIME_619t2`** 赞达拉的惨象 / What Befell Zandalar  （3费 · games=3820 · 直伤,敌AOE）
  - 中文：**对所有敌人造成$2点伤害。选择并使邦桑迪获得一项恩泽。**
  - 英文：[x]Deal $2 damage to all enemies. Choose a Boon to give to Bwonsamdi.

- **`TTN_460`** 致命诛灭 / Mortal Eradication  （3费 · games=3797 · 解场伤,敌AOE）
  - 中文：**造成$5点伤害，随机分配到所有敌方随从身上。每消灭一个随从，为你的英雄恢复#2点生命值。**
  - 英文：[x]Deal $5 damage randomly split among all enemy minions. Restore #2 Health to your hero for each killed.

- **`DMF_701`** 深水炸弹 / Dunk Tank  （4费 · games=3585 · 解场伤,敌AOE）
  - 中文：**造成$4点伤害。<b>腐蚀：</b>再对所有敌方随从造成$2点伤害。**
  - 英文：Deal $4 damage. <b>Corrupt:</b> Then deal $2 damage to all enemy minions.

- **`SW_107`** 火热促销 / Fire Sale  （4费 · games=3559 · 解场伤,全场AOE）
  - 中文：**<b>可交易</b> 对所有随从造成 $3点伤害。**
  - 英文：<b>Tradeable</b> Deal $3 damage to all minions.

- **`CATA_489`** 奥术涌流 / Arcane Flow  （4费 · games=2573 · 直伤,移除,敌AOE）
  - 中文：**<b>裂变</b> 造成$4点伤害。对所有敌人造成$2点伤害。123743造成$4点伤害。对所有敌人造成$2点伤害。**
  - 英文：[x]<b>Shatter</b> Deal $4 damage.  Deal $2 damage to  all enemies.

- **`TIME_209t2`** 天神下凡形态 / Avatar Form  （3费 · games=2523 · 直伤,敌AOE）
  - 中文：**在本回合中，使一个友方角色获得+2攻击力和“在本角色攻击后，对所有敌人造成2点伤害”。**
  - 英文：[x]Give a friendly character +2 Attack and "After this attacks, deal 2 damage to all enemies" this turn.

- **`VAC_953`** 浪潮涌起 / Rising Waves  （3费 · games=2242 · 解场伤,全场AOE）
  - 中文：**对所有随从造成 $2点伤害。如果没有随从死亡，再造成$2点。**
  - 英文：Deal $2 damage to all minions. If none die, deal $2 more.

- **`ETC_069`** 渐强声浪 / Crescendo  （2费 · games=1760 · 直伤,敌AOE）
  - 中文：**受到疲劳伤害。对所有敌人造成等量的伤害。0受到{0}点疲劳伤害。对所有敌人造成等量的伤害。**
  - 英文：[x]Take Fatigue damage. Deal that much damage to all enemies.

- **`RLK_063`** 冰霜巨龙之怒 / Frostwyrm's Fury  （7费 · games=1539 · 解场伤,敌AOE）
  - 中文：**造成$5点伤害。<b>冻结</b>所有敌方随从。召唤一条5/5的冰霜巨龙。**
  - 英文：Deal $5 damage. <b>Freeze</b> all enemy minions. Summon a 5/5 Frostwyrm.

- **`CFM_662`** 龙息药水 / Dragonfire Potion  （5费 · games=1516 · 解场伤,全场AOE）
  - 中文：**对所有非龙随从造成$5点伤害。**
  - 英文：[x]Deal $5 damage to all minions except Dragons.

- **`GDB_305`** 阳炎耀斑 / Solar Flare  （5费 · games=1458 · 直伤,敌AOE）
  - 中文：**对所有敌人造成$2点伤害。你每控制一个元素，本牌的法力值消耗便减少（1）点。**
  - 英文：Deal $2 damage to all enemies. Costs (1) less for each Elemental you control.

- **`CORE_CS2_093`** 奉献 / Consecration  （3费 · games=1433 · 直伤,敌AOE）
  - 中文：**对所有敌人造成$2点伤害。**
  - 英文：Deal $2 damage to all enemies.

- **`BT_117`** 剑刃风暴 / Bladestorm  （2费 · games=1307 · 解场伤,全场AOE）
  - 中文：**对所有随从造成$1点伤害。重复此效果，直到某个随从 死亡。**
  - 英文：Deal $1 damage to all minions. Repeat until one dies.

- **`YOG_502`** 清理污染 / Sanitize  （4费 · games=1182 · 全场AOE）
  - 中文：**对所有随从造成等同于你的护甲值的伤害。<b>锻造：</b>先获得3点护甲值。**
  - 英文：[x]Deal damage equal to your Armor to all minions. <b>Forge:</b> Gain 3 Armor first.

- **`ETC_314`** 悦耳流行歌 / Harmonic Pop  （6费 · games=1135 · 解场伤,全场AOE）
  - 中文：**对所有随从造成$3点伤害。召唤一个6/6的流行歌星。<i>（每回合切换。）</i>**
  - 英文：Deal $3 damage to all minions. Summon a 6/6 Popstar. <i>(Swaps each turn.)</i>

- **`CATA_557`** 希尔瓦娜斯的胜利 / Sylvanas's Triumph  （2费 · games=800 · 直伤,敌AOE）
  - 中文：**造成$3点伤害。如果你使用过本牌的其他复制，改为对所有敌人造成伤害。**
  - 英文：[x]Deal $3 damage. If you've played another copy of this, hit all enemies instead.

- **`TTN_853`** 审判恶徒 / Judge Unworthy  （4费 · games=756 · 直伤,敌AOE）
  - 中文：**将一个敌方随从的生命值变为1，然后对所有敌人造成$1点 伤害。**
  - 英文：Set an enemy minion's Health to 1, then deal $1 damage to all enemies.

- **`CORE_CS2_028`** 暴风雪 / Blizzard  （6费 · games=575 · 解场伤,敌AOE）
  - 中文：**对所有敌方随从造成$2点伤害，并使其<b>冻结</b>。**
  - 英文：Deal $2 damage to all enemy minions and <b>Freeze</b> them.

#### spell_board消灭（16 张）

- **`MIS_903`** 可疑交易 / Dubious Purchase  （4费 · games=32294 · 移除）
  - 中文：**抽三张牌。<b>连击：</b>随机消灭一个敌方随从。**
  - 英文：Draw 3 cards. <b>Combo:</b> Destroy a random enemy minion.

- **`TIME_712`** 诛灭暴君 / Dethrone  （7费 · games=17774 · 移除）
  - 中文：**消灭一个随从。<b>连击：</b>随机召唤一个法力值消耗为（8）的随从。**
  - 英文：Destroy a minion. <b>Combo:</b> Summon a random 8-Cost minion.

- **`CORE_EX1_246`** 妖术 / Hex  （3费 · games=15274 · 移除）
  - 中文：**使一个随从变形成为一只0/1并具有<b>嘲讽</b>的青蛙。**
  - 英文：Transform a minion into a 0/1 Frog with <b>Taunt</b>.

- **`BT_490`** 吞噬魔法 / Consume Magic  （1费 · games=12219 · 移除）
  - 中文：**<b>沉默</b>一个敌方随从。<b>流放：</b>抽一张牌。**
  - 英文：<b>Silence</b> an enemy minion. <b>Outcast:</b> Draw a card.

- **`TIME_433`** 抹除存在 / Cease to Exist  （3费 · games=9742 · 移除）
  - 中文：**<b>回溯</b>。<b>沉默</b>并消灭一个随机敌方随从。**
  - 英文：<b>Rewind</b> <b>Silence</b> and destroy a random enemy minion.

- **`CFM_696`** 衰变 / Devolve  （2费 · games=7118 · 移除）
  - 中文：**随机将所有 敌方随从变形成为法力值消耗减少（1）点的随从。**
  - 英文：Transform all enemy minions into random ones that cost (1) less.

- **`CORE_RLK_087`** 窒息 / Asphyxiate  （3费 · games=5553 · 移除）
  - 中文：**消灭攻击力最高的敌方随从。**
  - 英文：Destroy the highest Attack enemy minion.

- **`TTN_932`** 混乱吞噬 / Chaotic Consumption  （1费 · games=3472 · 移除）
  - 中文：**消灭一个友方随从以消灭一个敌方随从。**
  - 英文：Destroy a friendly minion to destroy an enemy minion.

- **`DMF_117`** 连环灾难 / Cascading Disaster  （4费 · games=3470 · 移除）
  - 中文：**随机消灭一个敌方随从。<b>腐蚀：</b>消灭两个。<b>再次腐蚀：</b>消灭三个。**
  - 英文：[x]Destroy a random enemy minion. <b>Corrupt:</b> Destroy 2. <b>Corrupt Again:</b> Destroy 3.

- **`CORE_EX1_309`** 灵魂虹吸 / Siphon Soul  （4费 · games=3287 · 移除）
  - 中文：**消灭一个随从，为你的英雄恢复#3点生命值。**
  - 英文：Destroy a minion. Restore #3 Health to your hero.

- **`CATA_203`** 迦罗娜的奋战 / Garona's Last Stand  （2费 · games=2494 · 移除）
  - 中文：**<b>可交易</b> 消灭一个<b>传说</b> 随从。**
  - 英文：[x]<b>Tradeable</b> Destroy a <b>Legendary</b> minion.

- **`NX2_020`** 野蛮残食 / Cannibalize  （4费 · games=2465 · 移除）
  - 中文：**消灭一个随从。为所有友方角色恢复生命值，数值相当于该随从的生命值。**
  - 英文：Destroy a minion. Restore its Health to all friendly characters.

- **`CATA_306`** 教派分歧 / Schism  （4费 · games=1726 · 移除）
  - 中文：**<b>裂变</b> 使一个友方随从获得+2/+3和<b>扰魔</b>。召唤一个它的复制。122876使一个友方随从获得+2/+3和<b>扰魔</b>。召唤一个它的复制。**
  - 英文：[x]<b>Shatter</b> Give a friendly minion +2/+3 and <b>Elusive</b>. Summon a copy of it.

- **`REV_239`** 窒息暗影 / Suffocating Shadows  （3费 · games=1109 · 移除）
  - 中文：**当你使用或弃掉这张牌时，随机消灭一个敌方随从。**
  - 英文：[x]When you play or discard this, destroy a random enemy minion.

- **`CATA_479`** 飞龙机动 / Flight Maneuvers  （4费 · games=980 · 移除）
  - 中文：**<b>裂变</b> 召唤两条4/2的幼龙。使你的随从获得+1攻击力和<b>圣盾</b>。123141召唤两条4/2的幼龙。使你的随从获得+1攻击力和<b>圣盾</b>。**
  - 英文：[x]<b>Shatter</b>. Summon two 4/2 Drakes. Give your minions +1 Attack and <b>Divine Shield</b>.

- **`SW_441`** 纳鲁碎片 / Shard of the Naaru  （1费 · games=951 · 移除）
  - 中文：**<b>可交易</b> <b>沉默</b>所有敌方随从。**
  - 英文：<b>Tradeable</b> <b>Silence</b> all enemy minions.

#### spell_board加攻（6 张）

- **`CORE_BT_035`** 混乱打击 / Chaos Strike  （2费 · games=7453 · -）
  - 中文：**在本回合中，使你的英雄获得+2攻击力。抽一张牌。**
  - 英文：Give your hero +2 Attack this turn. Draw a card.

- **`WORK_022`** 打卡 / Punch Card  （3费 · games=3802 · -）
  - 中文：**在本回合中，使你的英雄获得+3攻击力和“同时对相邻随从造成伤害”。**
  - 英文：Give your hero +3 Attack and "Also damages adjacent minions" this turn.

- **`ETC_363`** 主歌乐句 / Verse Riff  （1费 · games=3247 · -）
  - 中文：**在本回合中，使你的英雄获得+2攻击力。获得2点护甲值。<b>压轴：</b>演奏你的上一个乐句。**
  - 英文：[x]Give your hero +2 Attack this turn. Gain 2 Armor. <b>Finale:</b> Play your last Riff.

- **`BT_011`** 正义圣契 / Libram of Justice  （5费 · games=1208 · -）
  - 中文：**装备一把1/4的武器。将所有敌方随从的生命值变为1。**
  - 英文：Equip a 1/4 weapon. Change the Health of all enemy minions to 1.

- **`REV_507`** 处理证据 / Dispose of Evidence  （0费 · games=697 · -）
  - 中文：**在本回合中，使你的英雄获得+3攻击力。从你的3张手牌中选择一张洗入你的牌库。**
  - 英文：Give your hero +3 Attack this turn. Pick from 3 cards in your hand to shuffle into your deck.

- **`CORE_GVG_061`** 作战动员 / Muster for Battle  （3费 · games=547 · -）
  - 中文：**召唤三个1/1的白银之手新兵，装备一把1/4的武器。**
  - 英文：Summon three 1/1 Silver Hand Recruits. Equip a 1/4 Weapon.

#### spell_board其他（14 张）

- **`ONY_032`** 奈法利安的牙 / Tooth of Nefarian  （2费 · games=41649 · -）
  - 中文：**造成$3点伤害。<b>荣誉消灭：</b><b>发现</b>一张另一职业的法术牌。**
  - 英文：[x]Deal $3 damage. <b>Honorable Kill:</b> <b>Discover</b> a spell from another class.

- **`EDR_814`** 感染吐息 / Infested Breath  （2费 · games=32944 · -）
  - 中文：**造成$2点伤害。召唤一条0/2的水蛭。**
  - 英文：Deal $2 damage. Summon a 0/2 Leech.

- **`WW_006`** 飞镖投掷 / Dart Throw  （2费 · games=14009 · -）
  - 中文：**随机向敌方随从投掷两枚造成$2点伤害的飞镖。<i>（如果两枚击中同一个随从，获取一张幸运币！）</i>**
  - 英文：[x]Throw two $2 damage darts at random enemy minions. <i>(If both hit the same minion, get a Coin!)</i>

- **`TLC_902`** 虫害侵扰 / Infestation  （2费 · games=11282 · -）
  - 中文：**获取两张法力值消耗为（1）的格里什毒刺虫。毒刺虫可以造成$2点伤害并召唤一只2/1具有<b>突袭</b>的异种虫幼体。**
  - 英文：[x]Get two 1-Cost Gorishi Stingers. Each one deals $2 damage and summons a 2/1 Grub with <b>Rush</b>.

- **`REV_307`** 自然死亡 / Natural Causes  （2费 · games=8703 · -）
  - 中文：**造成$2点伤害。召唤一个2/2的树人。**
  - 英文：Deal $2 damage. Summon a 2/2 Treant.

- **`TOY_508`** 立体书 / Pop-Up Book  （1费 · games=8683 · -）
  - 中文：**造成$2点伤害。召唤两只0/1并具有<b>嘲讽</b>的青蛙。**
  - 英文：Deal $2 damage. Summon two 0/1 Frogs with <b>Taunt</b>.

- **`CORE_AT_037`** 活体根须 / Living Roots  （1费 · games=6628 · -）
  - 中文：**<b>抉择：</b>造成$2点伤害；或者召唤两个1/1的树苗。**
  - 英文：<b>Choose One -</b> Deal $2 damage; or Summon two 1/1 Saplings.

- **`GVG_015`** 暗色炸弹 / Darkbomb  （2费 · games=5170 · -）
  - 中文：**对一个角色造成$3点伤害。如果该角色死亡，抽一张暗影法术牌。**
  - 英文：Deal $3 damage to a character. If it dies, draw a Shadow spell.

- **`TOY_377`** 霜巫十字绣 / Frost Lich Cross-Stitch  （4费 · games=3774 · -）
  - 中文：**对一个角色造成$3点伤害。如果该角色死亡，召唤一个3/6的可以<b><b>冻结</b></b>攻击目标的水元素。**
  - 英文：Deal $3 damage to a character. If it dies, summon a 3/6 Water Elemental that <b><b>Freeze</b>s</b>.

- **`CORE_BAR_541`** 符文宝珠 / Runed Orb  （2费 · games=2232 · -）
  - 中文：**造成$2点伤害。<b>发现</b>一张法术牌。**
  - 英文：Deal $2 damage. <b>Discover</b> a spell.

- **`TTN_726`** 焦油飞溅 / Tar Slick  （1费 · games=1717 · -）
  - 中文：**在本回合中，随从受到的伤害翻倍。造成$1点伤害。**
  - 英文：Minions take double damage this turn. Deal $1 damage.

- **`TLC_221`** 炽火缠身 / Sizzling Swarm  （6费 · games=1630 · -）
  - 中文：**造成$3点伤害，召唤相同数量的2/1的炽烈烬火。**
  - 英文：Deal $3 damage. Summon that many 2/1 Sizzling Cinders.

- **`GVG_010`** 维伦的恩泽 / Velen's Chosen  （3费 · games=1495 · -）
  - 中文：**使一个随从获得+2/+4和<b>法术伤害+1</b>。**
  - 英文：Give a minion +2/+4 and <b>Spell Damage +1</b>.

- **`CATA_452`** 织法者的光辉 / Spellweaver's Brilliance  （10费 · games=1300 · -）
  - 中文：**召唤一条6/6的龙。在本回合中，你每用法术造成一点伤害，本牌的法力值消耗便减少（1）点。**
  - 英文：[x]Summon a 6/6 Dragon. Costs (1) less for each damage you dealt with spells this turn.

---

### P1（16 张）

#### SPELL_DAMAGE直伤（3 张）

- **`ONY_010`** 灭龙射击 / Dragonbane Shot  （2费 · games=466 · 直伤）
  - 中文：**造成$2点伤害。<b>荣誉消灭：</b>将一张灭龙射击置入你的手牌。**
  - 英文：[x]Deal $2 damage. <b>Honorable Kill:</b> Add a Dragonbane Shot to your hand.

- **`FIR_910`** 灼烧之风 / Scorching Winds  （3费 · games=345 · 直伤,解场伤）
  - 中文：**造成$3点伤害。随机弃掉一张火焰法术牌以再造成$3点。**
  - 英文：Deal $3 damage. Discard a random Fire spell to deal $3 more.

- **`DINO_406`** 喷吐火焰 / Fire Breath  （3费 · games=338 · 直伤）
  - 中文：**造成$4点伤害。使你的元素获得+1/+1。**
  - 英文：Deal $4 damage. Give your Elementals +1/+1.

#### spell_board解场伤（2 张）

- **`EDR_262`** 灵魂联结 / Spirit Bond  （3费 · games=189 · 解场伤）
  - 中文：**对一个随从造成$3点伤害。如果该随从死亡，召唤一只3/2并具有<b>突袭</b>的狼。**
  - 英文：Deal $3 damage to a minion. If it dies, summon a 3/2 Wolf with <b>Rush</b>.

- **`WC_021`** 不稳定的暗影震爆 / Unstable Shadow Blast  （2费 · games=165 · 解场伤）
  - 中文：**对一个随从造成$6点伤害，超过目标生命值的伤害会命中你的英雄。**
  - 英文：[x]Deal $6 damage to a minion. Excess damage hits your hero.

#### spell_board复杂AOE（3 张）

- **`VAC_416`** 死亡翻滚 / Death Roll  （5费 · games=445 · 直伤,移除,敌AOE）
  - 中文：**消灭一个敌方随从。造成等同于其攻击力的伤害，随机分配到所有敌人身上。**
  - 英文：[x]Destroy an enemy minion. Deal damage equal to its Attack randomly split among all enemies.

- **`TOY_883`** 掀桌子 / Table Flip  （10费 · games=300 · 解场伤,敌AOE）
  - 中文：**对所有敌方随从造成$3点伤害。你每有一张其他手牌，本牌的法力值消耗便减少（1）点。**
  - 英文：Deal $3 damage to all enemy minions. Costs (1) less for each other card in your hand.

- **`TIME_027`** 超光子弹幕 / Tachyon Barrage  （2费 · games=111 · 直伤,解场伤,敌AOE）
  - 中文：**造成$6点伤害，随机分配到所有敌人身上。将2张时空撕裂洗入你的牌库。**
  - 英文：Deal $6 damage split among all enemies. Shuffle 2 Shreds of Time into your deck.

#### spell_board消灭（1 张）

- **`LOOT_417`** 大灾变 / Cataclysm  （5费 · games=216 · 移除）
  - 中文：**消灭所有随从。弃两张牌。**
  - 英文：Destroy all minions. Discard 2 cards.

#### spell_board加攻（2 张）

- **`TSC_006`** 多重打击 / Multi-Strike  （2费 · games=384 · -）
  - 中文：**在本回合中使你的英雄获得+2攻击力，并可以额外攻击一次敌方随从。**
  - 英文：Give your hero +2 Attack this turn. They may attack an additional enemy minion.

- **`RLK_918`** 为了奎尔萨拉斯！ / For Quel'Thalas!  （2费 · games=274 · -）
  - 中文：**使一个友方随从获得+3攻击力。在本回合中，使你的英雄获得+2攻击力。**
  - 英文：[x]Give a friendly minion +3 Attack. Give your hero +2 Attack this turn.

#### spell_board其他（5 张）

- **`SCH_138`** 威能祝福 / Blessing of Authority  （5费 · games=475 · -）
  - 中文：**使一个随从获得+8/+8，在本回合中无法攻击英雄。**
  - 英文：Give a minion +8/+8. It can't attack heroes this turn.

- **`ETC_082`** 绝望哀歌 / Dirge of Despair  （6费 · games=453 · -）
  - 中文：**对一个角色造成$3点伤害。如果该角色死亡，从你的牌库中召唤一个恶魔。**
  - 英文：[x]Deal $3 damage to a character. If it dies, summon a Demon from your deck.

- **`EDR_874`** 星体平衡 / Stellar Balance  （2费 · games=345 · -）
  - 中文：**获取一张月火术和一张星火术，使其获得<b>法术伤害+1</b>。**
  - 英文：Get a Moonfire and a Starfire. Give them <b>Spell Damage +1</b>.

- **`VAC_944`** 咒怨纪念品 / Cursed Souvenir  （2费 · games=179 · -）
  - 中文：**使一个随从获得+3/+3和“在你的回合开始时，对你的英雄造成3点伤害”。**
  - 英文：Give a minion +3/+3 and "At the start of your turn, deal 3 damage to your hero."

- **`SW_088`** 恶魔来袭 / Demonic Assault  （4费 · games=138 · -）
  - 中文：**造成$3点伤害。召唤两个1/3并具有<b>嘲讽</b>的虚空行者。**
  - 英文：[x]Deal $3 damage. Summon two 1/3 Voidwalkers with <b>Taunt</b>.

---

### P2（2 张）

#### SPELL_DAMAGE直伤（1 张）

- **`TIME_600`** 精确射击 / Precise Shot  （2费 · games=97 · 直伤）
  - 中文：**造成$3点伤害。如果本牌位于你手牌的正中间，改为造成 $5点。**
  - 英文：Deal $3 damage. If this is EXACTLY in the center of your hand, deal $5 instead.

#### spell_board复杂AOE（1 张）

- **`RLK_534`** 灵魂弹幕 / Soul Barrage  （4费 · games=50 · 直伤,解场伤,敌AOE）
  - 中文：**当你使用或弃掉这张牌时，造成$5点伤害，随机分配到所有敌人身上。**
  - 英文：When you play or discard this, deal $5 damage randomly split among all enemies.

---

### P3（17 张）

#### spell_board复杂AOE（7 张）

- **`CORE_RLK_035`** 邪爆 / Corpse Explosion  （5费 · games=5808 · 解场伤,全场AOE · 邪爆：全体清场循环，非场攻）
  - 中文：**引爆一份<b>残骸</b>，对所有随从造成$1点伤害。如果有随从存活，重复此效果。**
  - 英文：Detonate a <b>Corpse</b> to deal $1 damage to all minions. If any are still alive, repeat this.

- **`CATA_526`** 布洛克斯加的奋战 / Broxigar's Last Stand  （2费 · games=5569 · 解场伤,全场AOE · 布洛克斯加的奋战：全体清场，非场攻）
  - 中文：**对所有随从造成$1点伤害。每有一个随从死亡，抽一 张牌。**
  - 英文：[x]Deal $1 damage to all minions. Draw a card for each that died.

- **`RLK_730`** 血液沸腾 / Blood Boil  （5费 · games=4172 · 解场伤,敌AOE · 感染后回合结束才伤害，与斩杀无关）
  - 中文：**<b>吸血</b>。感染所有敌方随从。在你的回合结束时，使其受到2点伤害。**
  - 英文：<b>Lifesteal</b> Infect all enemy minions. At the end of your turns, they take 2 damage.

- **`CATA_491`** 怪异触手 / Eldritch Tentacles  （6费 · games=3503 · 解场伤,全场AOE · 怪异触手：全体清场递减，非场攻）
  - 中文：**对所有随从造成$3点伤害。重复 此效果，每次伤害减少1点。**
  - 英文：Deal $3 damage to all minions. Repeat this with 1 less damage.

- **`CATA_581`** 屠灭 / Decimation  （6费 · games=1899 · 解场伤,全场AOE · 屠灭：全体清场，非场攻）
  - 中文：**对所有随从造成$1点伤害<i>（战场上每有一个随从都会提高）</i>。**
  - 英文：[x]Deal $1 damage to all minions. <i>(Improved for each minion on the battlefield.)</i>

- **`FIR_902`** 燃薪咒符 / Sigil of Cinder  （2费 · games=1117 · 直伤,解场伤,敌AOE · 燃薪咒符，下回合开始才伤害）
  - 中文：**在你的下回合开始时，造成$6点伤害，随机分配到所有敌人身上。**
  - 英文：[x]At the start of your next turn, deal $6 damage randomly split among all enemies.

- **`AV_330`** 纳鲁的赐福 / Gift of the Naaru  （1费 · games=587 · 全场AOE · 纳鲁的赐福：回血，非斩杀）
  - 中文：**为所有角色恢复#3点生命值。如果有角色仍处于受伤状态，抽一张牌。**
  - 英文：[x]Restore #3 Health to all characters. If any are still damaged, draw a card.

#### spell_board消灭（9 张）

- **`CATA_202`** 能量窃取 / Stolen Power  （3费 · games=3886 · 移除 · 仅获取裂变牌，无伤害）
  - 中文：**随机获取一张另一职业的<i>已拼合的</i><b>裂变</b>牌。**
  - 英文：Get a random <b>Shatter</b> card from another class. <i>(It's already combined).</i>

- **`CATA_134`** 荒林怪圈 / Wildwood Circle  （4费 · games=3664 · 移除 · 铺场树人/亡语，非斩杀）
  - 中文：**<b>裂变</b> 召唤两个2/2的树人。使你的随从获得“<b>亡语：</b>召唤一个2/2的树人。”122972召唤两个2/2的树人。使你的随从获得“<b>亡语：</b>召唤一个2/2的树人。”**
  - 英文：[x]<b>Shatter</b>. Summon two 2/2 Treants. Give your minions "<b>Deathrattle:</b> Summon a 2/2 Treant."

- **`CATA_567`** 升腾 / Ascendance  （4费 · games=3201 · 移除 · 变形铺场，非斩杀）
  - 中文：**将所有友方随从变形成为法力值消耗增加（1）点的随从。当这些随从死亡时，召唤原随从。**
  - 英文：[x]Transform all friendly minions into ones that cost (1) more. They summon the originals when they die.

- **`EX1_407`** 绝命乱斗 / Brawl  （5费 · games=2971 · 移除 · 乱斗仅解场，清嘲后不一定增加当回合打脸）
  - 中文：**随机选择一个随从，消灭除了该随从外的所有其他随从。**
  - 英文：Destroy all minions except one. <i>(chosen randomly)</i>

- **`OG_027`** 异变 / Evolve  （1费 · games=1971 · 移除 · 异变提升己方随从，非斩杀）
  - 中文：**随机将你的 所有随从变形成为法力值消耗增加（1）点的随从。**
  - 英文：Transform your minions into random minions that cost (1) more.

- **`WORK_026`** 失火 / Burndown  （3费 · games=1714 · 移除 · 失火：抽牌点燃，无当回合伤害）
  - 中文：**抽三张牌并将其点燃。3回合后，摧毁其中仍在手中的牌。**
  - 英文：[x]Draw 3 cards and light them on fire. In 3 turns, any still   in hand are destroyed!

- **`SCH_235`** 衰变飞弹 / Devolving Missiles  （1费 · games=1515 · 移除 · 衰变飞弹，衰变机制暂不模拟）
  - 中文：**随机向敌方随从发射三枚飞弹，使其变形成为法力值消耗减少（1）点的随从。**
  - 英文：[x]Shoot three missiles at random enemy minions that transform them into ones that cost (1) less.

- **`CATA_820`** 运输补给 / Supply Run  （4费 · games=837 · 移除 · 运输补给：抽牌+buff手牌，非斩杀）
  - 中文：**<b>裂变</b> 抽三张随从牌。使你手牌中的随从牌获得+2/+2。121758抽三张随从牌。使你手牌中的随从牌获得+2/+2。**
  - 英文：<b>Shatter</b> Draw 3 minions. Give minions in your hand +2/+2.

- **`WW_092`** 液力压裂 / Fracking  （1费 · games=714 · 移除 · 液力压裂：检视牌库抽牌，非斩杀）
  - 中文：**检视你的牌库底的三张牌，抽其中一张，摧毁其余牌。**
  - 英文：[x]Look at the bottom 3 cards of your deck. Draw one and destroy the others.

#### spell_board其他（1 张）

- **`TIME_711`** 闪回 / Flashback  （2费 · games=14446 · - · 铺场/连击加攻，无当回合伤害）
  - 中文：**随机召唤两个来自过去的法力值消耗为（1）的随从。<b>连击：</b>并具有+1攻击力。**
  - 英文：Summon two random 1-Cost minions from the past. <b>Combo:</b> With +1 Attack.

---

重新生成: `python scripts/generate_arena_spell_priority.py`