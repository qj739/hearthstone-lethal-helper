# 致死模拟已支持卡牌总表

> 自动生成：运行 `python scripts/generate_supported_cards_table.py` 可更新本文件。

> 生成时间（UTC）：2026-07-13 03:28

## 总览

| 模块 | 数量 |
|------|------|
| 法术 | 339 |
| 战吼随从 | 102 |
| 突袭随从 | 102 |
| 武器 | 57 |
| 连击 | 17 |
| 英雄技能 | 11 |
| 地标 | 3 |
| 手牌回合结束 | 3 |
| 受伤法强 | 1 |
| 场面回合结束 | 20 |
| 亡语 | 33 |
| 法术快速估算 | 25 |
| 冲锋快速估算 | 5 |
| **合计** | **718** |

## 字段说明

| 列 | 含义 |
|----|------|
| card_id | 炉石卡牌 ID（含 CORE_ 变体） |
| 中文名 / 英文名 | 来自 `json/cards_zhCN.json` / `json/cards.json` |
| 费用 | 注册表 `base_cost` 优先，否则 JSON `cost` |
| 攻/血 | 随从攻击/生命；武器为攻击/耐久 |
| 类型 | MINION / SPELL / WEAPON / HERO_POWER 等 |
| 随机 | 模拟是否含随机结算 |
| 模拟说明 | 代码内效果摘要（docstring 或注册名） |
| 中文描述 / 英文描述 | 官方卡牌文本 |

## 法术

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| SCH_514 | 亡者复生 | Raise Dead | 0 | - | SPELL | 否 | 亡者复生 | 对你的英雄造成$3点伤害。将两个在本局对战中死亡的友方随从移回你的手牌。 | Deal $3 damage to your hero. Return two friendly minions that died this game to your hand. |
| REV_507 | 处理证据 | Dispose of Evidence | 0 | - | SPELL | 否 | 处理证据 | 在本回合中，使你的英雄获得+3攻击力。从你的3张手牌中选择一张洗入你的牌库。 | Give your hero +3 Attack this turn. Pick from 3 cards in your hand to shuffle into your deck. |
| CS2_008 | 月火术 | Moonfire | 0 | - | SPELL | 否 | 月火术 | 造成$1点伤害。 | Deal $1 damage. |
| DREAM_05 | 梦魇 | Nightmare | 0 | - | SPELL | 否 | 梦魇：+5/+5，下回合初消灭（v1 只模拟当回合 +5 攻）。 | 使一个随从获得+5/+5，在你的下个回合开始时，消灭该随从。 | Give a minion +5/+5. At the start of your next turn, destroy it. |
| DREAM_01 | 欢笑的姐妹 | Laughing Sister | 0 | 3/5 | MINION | 否 | 梦境：将一个随从移回其拥有者的手牌（v1 按移出场面处理；有嘲讽时仅嘲讽）。 | <b>扰魔</b> | <b>Elusive</b> |
| TIME_218 | 静电震击 | Static Shock | 0 | - | SPELL | 否 | 静电震击 | 对一个随从造成$1点伤害。在本回合中，使你的英雄获得+1攻击力。 | Deal $1 damage to a minion. Give your hero +1 Attack this turn. |
| ETC_201 | 一串香蕉 | Bunch of Bananas | 1 | - | SPELL | 否 | 一串香蕉：友方随从 +1/+1，回手可再打（共 3 根）。 | 使一个随从获得+1/+1。<i>（还剩3根香蕉！）</i> | Give a minion +1/+1. <i>(3 Bananas left!)</i> |
| ETC_201t | 一串香蕉 | Bunch of Bananas | 1 | - | SPELL | 否 | 一串香蕉：友方随从 +1/+1，回手可再打（共 3 根）。 | 使一个随从获得+1/+1。<i>（还剩2根香蕉！）</i> | Give a minion +1/+1. <i>(2 Bananas left!)</i> |
| ETC_201t2 | 一串香蕉 | Bunch of Bananas | 1 | - | SPELL | 否 | 一串香蕉：友方随从 +1/+1，回手可再打（共 3 根）。 | 使一个随从获得+1/+1。<i>（最后一根香蕉！）</i> | Give a minion +1/+1. <i>(Last Banana!)</i> |
| LOOT_504 | 不稳定的异变 | Unstable Evolution | 1 | - | SPELL | 否 | 不稳定的异变 | <b>回响</b> 将一个友方随从随机变形成为一个法力值消耗增加（1）点的随从。 | <b>Echo</b> Transform a friendly minion into one that costs (1) more. |
| ETC_363 | 主歌乐句 | Verse Riff | 1 | - | SPELL | 否 | 主歌乐句：+2 攻（护甲 / 压轴复奏 v1 不模拟）。 | 在本回合中，使你的英雄获得+2攻击力。获得2点护甲值。<b>压轴：</b>演奏你的上一个乐句。 | [x]Give your hero +2 Attack this turn. Gain 2 Armor. <b>Finale:</b> Play your last Riff. |
| SW_108t | 传承之火 | Second Flame | 1 | - | SPELL | 否 | 2 伤；打出后将链上下一张法术置入手牌（由 apply_spell_sequence 继续施放）。 | 对一个随从造成$2点伤害。 | Deal $2 damage to a minion. |
| CORE_BAR_801 | 击伤猎物 | Wound Prey | 1 | - | SPELL | 否 | 击伤猎物 | 造成$1点伤害。召唤一只1/1并具有<b>突袭</b>的土狼。 | Deal $1 damage. Summon a 1/1 Hyena with <b>Rush</b>. |
| CORE_SW_108 | 初始之火 | First Flame | 1 | - | SPELL | 否 | 2 伤；打出后将链上下一张法术置入手牌（由 apply_spell_sequence 继续施放）。 | 对一个随从造成$2点伤害。将“传承之火”置入你的手牌。 | Deal $2 damage to a minion. Add a Second Flame to your hand. |
| SW_108 | 初始之火 | First Flame | 1 | - | SPELL | 否 | 2 伤；打出后将链上下一张法术置入手牌（由 apply_spell_sequence 继续施放）。 | 对一个随从造成$2点伤害。将“传承之火”置入你的手牌。 | Deal $2 damage to a minion. Add a Second Flame to your hand. |
| REV_920 | 可信的伪装 | Convincing Disguise | 1 | - | SPELL | 否 | 可信的伪装 | 将一个友方随从变形成为法力值消耗增加（2）点的随从。<b>注能（4）：</b>改为变形所有友方随从。 | [x]Transform a friendly minion into one that costs (2) more. <b>Infuse (4):</b> Transform all friendly minions instead. |
| BT_490 | 吞噬魔法 | Consume Magic | 1 | - | SPELL | 否 | 吞噬魔法 | <b>沉默</b>一个敌方随从。<b>流放：</b>抽一张牌。 | <b>Silence</b> an enemy minion. <b>Outcast:</b> Draw a card. |
| VAC_404 | 夜影花茶 | Nightshade Tea | 1 | - | SPELL | 否 | 2 伤 + 自伤 2；剩余杯数>0 时由 apply_spell_sequence 回手再喝。 | 对一个随从造成$2点伤害。对你的英雄造成$2点伤害。<i>（还剩3杯！）</i> | Deal $2 damage to a minion. Deal $2 damage to your hero. <i>(3 Drinks left!)</i> |
| VAC_404t1 | 夜影花茶 | Nightshade Tea | 1 | - | SPELL | 否 | 2 伤 + 自伤 2；剩余杯数>0 时由 apply_spell_sequence 回手再喝。 | 对一个随从造成$2点伤害。对你的英雄造成$2点伤害。<i>（还剩2杯！）</i> | Deal $2 damage to a minion. Deal $2 damage to your hero. <i>(2 Drinks left!)</i> |
| VAC_404t2 | 夜影花茶 | Nightshade Tea | 1 | - | SPELL | 否 | 2 伤 + 自伤 2；剩余杯数>0 时由 apply_spell_sequence 回手再喝。 | 对一个随从造成$2点伤害。对你的英雄造成$2点伤害。<i>（最后一杯！）</i> | Deal $2 damage to a minion. Deal $2 damage to your hero. <i>(Last Drink!)</i> |
| RLK_843 | 奥术箭 | Arcane Bolt | 1 | - | SPELL | 否 | 奥术箭 RLK_843：2 伤；法力渴求(8 水晶) 3 伤。 | 造成$2点伤害。<b>法力渴求（8）：</b>改为造成$3点伤害。 | Deal $2 damage. <b>Manathirst (8):</b> Deal $3 damage instead. |
| TIME_212 | 引雷针 | Lightning Rod | 1 | - | SPELL | 否 | 引雷针 | 对一个友方随从造成$2点伤害，以随机对一个敌方随从造成$4点伤害。 | Deal $2 damage to a friendly minion to deal $4 damage to a random enemy minion. |
| MIS_707 | 批量生产 | Mass Production | 1 | - | SPELL | 否 | 批量生产 | 抽两张牌。对你的英雄造成$3点伤害。将两张本牌的复制洗入你的牌库。 | Draw 2 cards. Deal $3 damage to your hero. Shuffle 2 copies of this into your deck. |
| CORE_CS2_108 | 斩杀 | Execute | 1 | - | SPELL | 否 | 斩杀 | 消灭一个受伤的敌方随从。 | Destroy a damaged enemy minion. |
| TLC_630t | 格里什毒刺虫 | Gorishi Stinger | 1 | - | SPELL | 否 | 格里什毒刺虫：2 伤 + 2/1 突袭衍生物（当回合仅解场）。 | 造成$2点伤害。召唤一只2/1并具有<b>突袭</b>的异种虫幼体。 | Deal $2 damage. Summon a 2/1 Grub with <b>Rush</b>. |
| CORE_EX1_302 | 死亡缠绕 | Mortal Coil | 1 | - | SPELL | 否 | 死亡缠绕 | 对一个随从造成$1点伤害。如果该随从死亡，抽一张牌。 | [x]Deal $1 damage to a minion.  If it dies, draw a card. |
| WW_354 | 残骸遍野 | Fistful of Corpses | 1 | - | SPELL | 否 | 残骸遍野 | 对一个随从造成等同于你的<b>残骸</b>数量的伤害。 | Deal damage to a minion equal to your <b>Corpses</b>. |
| END_020 | 永时困苦 | Eternal Toil | 1 | - | SPELL | 否 | 永时困苦 | 对一个随从造成$1点伤害。如果该随从依然存活，抽一张牌。如果该随从死亡，随机召唤一个法力值消耗为（1）的随从。 | [x]Deal $1 damage to a minion. If it survives, draw a card. If it dies, summon a random 1-Cost minion. |
| CORE_AT_037 | 活体根须 | Living Roots | 1 | - | SPELL | 否 | 活体根须：抉择 — 2 伤或两个 1/1（选场攻更高分支）。 | <b>抉择：</b>造成$2点伤害；或者召唤两个1/1的树苗。 | <b>Choose One -</b> Deal $2 damage; or Summon two 1/1 Saplings. |
| TTN_932 | 混乱吞噬 | Chaotic Consumption | 1 | - | SPELL | 否 | 混乱吞噬：消灭一个友方随从以消灭一个敌方随从。 | 消灭一个友方随从以消灭一个敌方随从。 | Destroy a friendly minion to destroy an enemy minion. |
| ETC_394 | 混乱品味 | Taste of Chaos | 1 | - | SPELL | 否 | 混乱品味 | 对一个随从造成$2点伤害。<b>压轴：</b><b>发现</b>一张邪能法术牌。 | Deal $2 damage to a minion. <b>Finale:</b> <b>Discover</b> a Fel spell. |
| CATA_485 | 激寒急流 | Sleet Storm | 1 | - | SPELL | 是 | 激寒急流 | 造成$2点伤害。随机对一个敌方随从造成$1点伤害。 | [x]Deal $2 damage.  Deal $1 damage to a  random enemy minion. |
| REV_834 | 灭绝圣物 | Relic of Extinction | 1 | - | SPELL | 是 | 灭绝圣物 | 随机对一个敌方随从造成$1点伤害，触发两次。提升你此后的圣物效果。 | Deal $1 damage to a random enemy minion, twice. Improve your future Relics. |
| CORE_BOT_222 | 灵魂炸弹 | Spirit Bomb | 1 | - | SPELL | 否 | 灵魂炸弹 | 对一个随从和你的英雄各造成$4点伤害。 | Deal $4 damage to a minion and your hero. |
| DEEP_011 | 灼燃之心 | Burning Heart | 1 | - | SPELL | 否 | 灼燃之心 | 对一个随从造成$2点伤害，如果它依然存活，使你的英雄在本回合中获得+3攻击力。 | Deal $2 damage to a minion. If it survives, give your hero +3 Attack this turn. |
| REV_249 | 炽燃圣光 | The Light! It Burns! | 1 | - | SPELL | 否 | 炽燃圣光 | 对一个随从造成等同于其攻击力的伤害。 | [x]Deal damage to a minion  equal to its Attack. |
| CATA_585 | 烈火炙烤 | Torch | 1 | - | SPELL | 否 | 烈火炙烤 | 对一个受伤的随从造成$8点伤害。如果伤害超过目标生命值，将能造成剩余伤害的本牌移回手牌。 | [x]Deal $8 damage to a damaged minion. Return this to hand with any excess damage. |
| FIR_954 | 焚烧 | Conflagrate | 1 | - | SPELL | 否 | 焚烧 | 对一个随从造成$5点伤害，其拥有者抽一张牌。 | Deal $5 damage to a minion. Its owner draws a card. |
| TTN_726 | 焦油飞溅 | Tar Slick | 1 | - | SPELL | 否 | 焦油飞溅：随从受伤翻倍，法术 1 伤对随从视为 2 伤。 | 在本回合中，随从受到的伤害翻倍。造成$1点伤害。 | Minions take double damage this turn. Deal $1 damage. |
| CORE_EX1_391 | 猛击 | Slam | 1 | - | SPELL | 否 | 猛击 | 对一个随从造成$2点伤害，如果 它依然存活，则抽一张牌。 | Deal $2 damage to a minion. If it survives, draw a card. |
| CORE_GIFT_10 | 玛法里奥的礼物 | Malfurion's Gift | 1 | - | SPELL | 否 | 玛法里奥的礼物：三选一发现，取对斩杀最优的衍生法术并立刻视为入手。 | <b>发现</b>一张<b>临时</b>的野性之怒，野性成长或横扫。 | <b>Discover</b> a <b>Temporary</b> Feral Rage, Wild Growth, or Swipe. |
| GIFT_10 | 玛法里奥的礼物 | Malfurion's Gift | 1 | - | SPELL | 否 | 玛法里奥的礼物：三选一发现，取对斩杀最优的衍生法术并立刻视为入手。 | <b>发现</b>一张<b>临时</b>的野性之怒，野性成长或横扫。 | <b>Discover</b> a <b>Temporary</b> Feral Rage, Wild Growth, or Swipe. |
| WW_393t | 瓶装影叶 | Bottled Shadeleaf | 1 | - | SPELL | 否 | 瓶装影叶 WW_393t：对敌方随从造成等于存储伤害的伤。 | 对一个敌方随从造成余下的伤害。0对一个敌方随从造成${0}点伤害。 | [x]Deal the excess damage to an enemy minion. |
| CFM_603 | 疯狂药水 | Potion of Madness | 1 | - | SPELL | 否 | 疯狂药水：夺取攻≤2 敌方随从；未冰冻可当回合打脸；亡语按我方触发。 | 直到回合结束，获得一个攻击力小于或等于2的敌方随从的控制权。 | Gain control of an enemy minion with 2 or less Attack until end of turn. |
| EDR_813 | 病变虫群 | Morbid Swarm | 1 | - | SPELL | 否 | 病变虫群 | <b>抉择：</b>召唤两只1/1的蚂蚁；或者消耗2份<b>残骸</b>，对一个随从造成$4点伤害。 | <b>Choose One -</b> Summon two 1/1 Ants; or Spend 2 <b>Corpses</b> to deal $4 damage to a minion. |
| MAW_023 | 盗窃指控 | Theft Accusation | 1 | - | SPELL | 否 | 消灭最优敌方随从（有嘲讽时仅嘲讽；清场指向性无嘲讽时可点随从）。 | 选择一个随从。在你使用一张从对手处复制的卡牌后，将其消灭。 | [x]Choose a minion. Destroy it after you play a card copied from the opponent. |
| CORE_CS1_130 | 神圣惩击 | Holy Smite | 1 | - | SPELL | 否 | 神圣惩击 | 对一个随从造成$3点伤害。 | Deal $3 damage to a minion. |
| TOY_508 | 立体书 | Pop-Up Book | 1 | - | SPELL | 否 | 立体书：2 伤（0/1 嘲讽青蛙 v1 不计场攻）。 | 造成$2点伤害。召唤两只0/1并具有<b>嘲讽</b>的青蛙。 | Deal $2 damage. Summon two 0/1 Frogs with <b>Taunt</b>. |
| TOY_644 | 红牌 | Red Card | 1 | - | SPELL | 否 | 红牌：使一个随从休眠 2 回合；休眠随从本回合不计嘲讽、不参与交换。 | 使一个随从<b>休眠</b>2回合。 | Make a minion go <b>Dormant</b> for 2 turns. |
| SW_090 | 纳斯雷兹姆之触 | Touch of the Nathrezim | 1 | - | SPELL | 否 | 纳斯雷兹姆之触 | 对一个随从造成$2点伤害。如果该随从死亡，则为你的英雄恢复#3点生命值。 | [x]Deal $2 damage to a minion. If it dies, restore #3 Health to your hero. |
| SW_441 | 纳鲁碎片 | Shard of the Naaru | 1 | - | SPELL | 否 | 纳鲁碎片：沉默所有敌方随从。 | <b>可交易</b> <b>沉默</b>所有敌方随从。 | <b>Tradeable</b> <b>Silence</b> all enemy minions. |
| JAM_022 | 致聋术 | Deafen | 1 | - | SPELL | 否 | 致聋术 | <b>沉默</b>一个随从。<b>连击：</b>并对其造成$2点伤害。 | <b>Silence</b> a minion. <b>Combo:</b> Also deal $2 damage to it. |
| SCH_235 | 衰变飞弹 | Devolving Missiles | 1 | - | SPELL | 是 | 衰变飞弹：随机向敌方随从发射 3 枚飞弹，各衰变一次（5 费→4/4 白板）。 | 随机向敌方随从发射三枚飞弹，使其变形成为法力值消耗减少（1）点的随从。 | [x]Shoot three missiles at random enemy minions that transform them into ones that cost (1) less. |
| VAC_323 | 麦芽岩浆 | Malted Magma | 1 | - | SPELL | 否 | 麦芽岩浆：全体敌人 1 伤，连喝（VAC_323 衍生链）。 | 对所有敌人造成$1点伤害。<i>（还剩3杯！）</i> | Deal $1 damage to all enemies. <i>(3 Drinks left!)</i> |
| WC_021 | 不稳定的暗影震爆 | Unstable Shadow Blast | 2 | - | SPELL | 否 | 不稳定的暗影震爆：6 伤；溢出伤害命中我方英雄。 | 对一个随从造成$6点伤害，超过目标生命值的伤害会命中你的英雄。 | [x]Deal $6 damage to a minion. Excess damage hits your hero. |
| RLK_918 | 为了奎尔萨拉斯！ | For Quel'Thalas! | 2 | - | SPELL | 否 | 为了奎尔萨拉斯！：友方随从 +3 攻；英雄 +2 攻。魔免随从不可指定，无合法目标则不可打出。 | 使一个友方随从获得+3攻击力。在本回合中，使你的英雄获得+2攻击力。 | [x]Give a friendly minion +3 Attack. Give your hero +2 Attack this turn. |
| ICC_041 | 亵渎 | Defile | 2 | - | SPELL | 否 | 亵渎：全场 1 伤循环，有随从死亡则再施放。 | 对所有随从造成$1点伤害，如果有随从死亡，则再次施放该法术。 | Deal $1 damage to all minions. If any die, cast this again. |
| DREAM_02 | 伊瑟拉苏醒 | Ysera Awakens | 2 | - | SPELL | 否 | 伊瑟拉苏醒：除伊瑟拉外，对所有角色造成 5 点伤害。 | 对除了伊瑟拉之外的所有角色造成$5点伤害。 | Deal $5 damage to all characters except Ysera. |
| TIME_750 | 先行打击 | Precursory Strike | 2 | - | SPELL | 否 | 先行打击 | 造成$3点伤害。如果你的手牌中有法力值消耗大于或等于（5）点的随从牌，抽一张随从牌。 | Deal $3 damage. If you're holding a minion that costs (5) or more, draw a minion. |
| REV_601 | 冰冻之触 | Frozen Touch | 2 | - | SPELL | 否 | 冰冻之触 | 造成$3点伤害。<b>注能（3）：</b>将一张冰冻之触置入你的 手牌。 | Deal $3 damage. <b>Infuse (3):</b> Add a Frozen Touch to your hand. |
| REV_601t | 冰冻之触 | Frozen Touch | 2 | - | SPELL | 否 | 冰冻之触 | <b>已注能</b> 造成$3点伤害。将一张冰冻之触置入你的手牌。 | [x]<b>Infused</b> Deal $3 damage.  Add a Frozen Touch  to your hand. |
| RLK_025 | 冰霜打击 | Frost Strike | 2 | - | SPELL | 否 | 冰霜打击 | 对一个随从造成$3点伤害。如果该随从死亡，<b>发现</b>一张冰霜符文牌。 | [x]Deal $3 damage to a  minion. If it dies, <b>Discover</b> a Frost Rune card. |
| AV_259 | 冰霜撕咬 | Frostbite | 2 | - | SPELL | 否 | 冰霜撕咬 | 造成$3点伤害。<b>荣誉消灭：</b>你对手的下一个法术法力值消耗增加（2）点。 | Deal $3 damage. <b>Honorable Kill:</b> Your opponent's next spell costs (2) more. |
| TOY_384 | 净化之力 | Purifying Power | 2 | - | SPELL | 否 | 净化之力 | <b>沉默</b>所有友方随从，然后使其获得+1/+2。 | <b>Silence</b> all friendly minions, then give them +1/+2. |
| CATA_303 | 净化吐息 | Purifying Breath | 2 | - | SPELL | 否 | 净化吐息 | 对一个随从造成$5点伤害。如果该随从死亡，则为敌方英雄恢复#5点生命值。 | [x]Deal $5 damage to a minion. If it dies, restore #5 Health to the enemy hero. |
| RLK_018 | 凋零打击 | Plague Strike | 2 | - | SPELL | 否 | 凋零打击 | 对一个随从造成$3点伤害。如果该随从死亡，召唤一个2/2并具有<b>突袭</b>的僵尸。 | Deal $3 damage to a minion. If it dies, summon a 2/2 Zombie with <b>Rush</b>. |
| EX1_129 | 刀扇 | Fan of Knives | 2 | - | SPELL | 否 | 刀扇 | 对所有敌方随从造成$1点伤害，抽一张牌。 | Deal $1 damage to all enemy minions. Draw a card. |
| ETC_717t | 刺耳嘻哈 | Dissonant Hip Hop | 2 | - | SPELL | 否 | 悦耳嘻哈 / 刺耳嘻哈：直伤 + 武器加攻（每回合切换形态）。 | 造成$3点伤害。使你的武器获得+1攻击力。<i>（每回合切换。）</i> | Deal $3 damage. Give your weapon +1 Attack. <i>(Swaps each turn.)</i> |
| BT_117 | 剑刃风暴 | Bladestorm | 2 | - | SPELL | 否 | 剑刃风暴：全场 1 伤循环，直到某轮有随从死亡。 | 对所有随从造成$1点伤害。重复此效果，直到某个随从 死亡。 | Deal $1 damage to all minions. Repeat until one dies. |
| JAM_013 | 即兴演奏 | Jam Session | 2 | - | SPELL | 否 | 即兴演奏 | 使一个友方随从获得+3/+3。对所有其他随从造成$1点伤害。<b>过载：</b>（1） | [x]Give a friendly minion +3/+3. Deal $1 damage to all other minions. <b>Overload:</b> (1) |
| CORE_ULD_152 | 压感陷阱 | Pressure Plate | 2 | - | SPELL | 否 | 压感陷阱 | <b>奥秘：</b>在你的对手施放一个法术后，随机消灭一个敌方 随从。 | <b>Secret:</b> After your opponent casts a spell, destroy a random enemy minion. |
| END_007 | 发挥优势 | Press the Advantage | 2 | - | SPELL | 否 | 发挥优势 | 造成$1点伤害。在本回合中，使你的英雄获得+1攻击力。抽1张牌。获得1点护甲值。 | Deal $1 damage. Give your hero +1 Attack this turn. Draw 1 card. Gain 1 Armor. |
| NAX11_04 | 变异注射 | Mutating Injection | 2 | - | SPELL | 否 | 变异注射 | 使一个随从获得+4/+4和<b>嘲讽</b>。 | Give a minion +4/+4 and <b>Taunt</b>. |
| ONY_005ta2 | 变异注射 | Mutating Injection | 2 | - | SPELL | 否 | 变异注射 | 使一个随从获得+4/+4和<b>嘲讽</b>。 | Give a minion +4/+4 and <b>Taunt</b>. |
| VAC_464t3 | 变异注射 | Mutating Injection | 2 | - | SPELL | 否 | 变异注射 | 使一个随从获得+4/+4和<b>嘲讽</b>。 | Give a minion +4/+4 and <b>Taunt</b>. |
| WW_027 | 可靠陪伴 | Trusty Companion | 2 | - | SPELL | 否 | 可靠陪伴：使一个友方随从获得 +2/+3（抽牌 v1 不模拟）。 | 使一个随从获得+2/+3。如果该随从有随从类型，抽一张该类型的随从牌。 | [x]Give a minion +2/+3. If it has a minion type, draw one of that type. |
| MAW_010 | 否决动议 | Motion Denied | 2 | - | SPELL | 否 | 否决动议 | <b>奥秘：</b>在你的对手在一回合中使用三张牌后，对敌方英雄造成$6点伤害。 | [x]<b>Secret:</b> After your opponent plays three cards in a turn, deal $6 damage to the enemy hero. |
| CORE_ICC_055 | 吸取灵魂 | Drain Soul | 2 | - | SPELL | 否 | 吸取灵魂 | <b>吸血</b> 对一个随从造成 $3点伤害。 | <b>Lifesteal</b> Deal $3 damage to a minion. |
| VAC_944 | 咒怨纪念品 | Cursed Souvenir | 2 | - | SPELL | 否 | 咒怨纪念品：+3/+3（回合开始自伤 v1 不计）。 | 使一个随从获得+3/+3和“在你的回合开始时，对你的英雄造成3点伤害”。 | Give a minion +3/+3 and "At the start of your turn, deal 3 damage to your hero." |
| TSC_006 | 多重打击 | Multi-Strike | 2 | - | SPELL | 否 | 多重打击：+2 攻；额外一次仅能攻击敌方随从。 | 在本回合中使你的英雄获得+2攻击力，并可以额外攻击一次敌方随从。 | Give your hero +2 Attack this turn. They may attack an additional enemy minion. |
| ONY_032 | 奈法利安的牙 | Tooth of Nefarian | 2 | - | SPELL | 否 | 奈法利安的牙 | 造成$3点伤害。<b>荣誉消灭：</b><b>发现</b>一张另一职业的法术牌。 | [x]Deal $3 damage. <b>Honorable Kill:</b> <b>Discover</b> a spell from another class. |
| CATA_526 | 布洛克斯加的奋战 | Broxigar's Last Stand | 2 | - | SPELL | 否 | 布洛克斯加的奋战：全场 1 伤循环直至无死亡（抽牌 v1 不计）。 | 对所有随从造成$1点伤害。每有一个随从死亡，抽一 张牌。 | [x]Deal $1 damage to all minions. Draw a card for each that died. |
| CATA_557 | 希尔瓦娜斯的胜利 | Sylvanas's Triumph | 2 | - | SPELL | 否 | 希尔瓦娜斯的胜利：3 伤（简化：单目标最优）。 | 造成$3点伤害。如果你使用过本牌的其他复制，改为对所有敌人造成伤害。 | [x]Deal $3 damage. If you've played another copy of this,  hit all enemies instead. |
| FIR_939 | 影焰晕染 | Shadowflame Suffusion | 2 | - | SPELL | 否 | 影焰晕染 | 造成$2点伤害。<b>发现</b>一张具有<b>黑暗之赐</b>的战士随从牌。 | [x]Deal $2 damage. <b>Discover</b> a Warrior minion with a <b>Dark Gift</b>. |
| CORE_BRM_013 | 快速射击 | Quick Shot | 2 | - | SPELL | 否 | 快速射击 | 造成$3点伤害。 如果你没有其他手牌，则抽一张牌。 | Deal $3 damage. If your hand is empty, draw a card. |
| CORE_AT_064 | 怒袭 | Bash | 2 | - | SPELL | 否 | 怒袭 | 造成$3点伤害。获得3点 护甲值。 | Deal $3 damage. Gain 3 Armor. |
| WORK_014 | 恶魔交易 | Demonic Deal | 2 | - | SPELL | 否 | 恶魔交易 | <b>吸血</b> 对一个随从造成$4点伤害。将一张法力值消耗大于或等于（5）点的随机恶魔牌置于你的牌库顶。 | [x]<b>Lifesteal</b>. Deal $4 damage to a minion. Put a random Demon that costs (5) or more on top of your deck. |
| ETC_717 | 悦耳嘻哈 | Harmonic Hip Hop | 2 | - | SPELL | 否 | 悦耳嘻哈 / 刺耳嘻哈：直伤 + 武器加攻（每回合切换形态）。 | 造成$1点伤害。使你的武器获得+3攻击力。<i>（每回合切换。）</i> | Deal $1 damage. Give your weapon +3 Attack. <i>(Swaps each turn.)</i> |
| EDR_814 | 感染吐息 | Infested Breath | 2 | - | SPELL | 否 | 感染吐息：2 伤（0/2 水蛭 v1 不计场攻）。 | 造成$2点伤害。召唤一条0/2的水蛭。 | Deal $2 damage. Summon a 0/2 Leech. |
| VAC_460 | 把经理叫来！ | Oh, Manager! | 2 | - | SPELL | 否 | 把经理叫来！ | 造成$2点伤害。<b>连击：</b>获取一张幸运币。 | Deal $2 damage. <b>Combo:</b> Get a Coin. |
| TIME_611 | 时间停滞 | Timestop | 2 | - | SPELL | 否 | 时间停滞 | 造成$3点伤害。随机<b>冻结</b>两个敌方随从。 | Deal $3 damage. <b>Freeze</b> two random enemy minions. |
| EDR_874 | 星体平衡 | Stellar Balance | 2 | - | SPELL | 否 | 星体平衡：获得月火术、星火术（法术伤害+1 → 2/6 伤）。 | 获取一张月火术和一张星火术，使其获得<b>法术伤害+1</b>。 | Get a Moonfire and a Starfire. Give them <b>Spell Damage +1</b>. |
| GDB_851 | 星域相变射线 | Astral Phaser | 2 | - | SPELL | 是 | 星域相变射线：抉择 — 随机两随从 2 伤，或使一个敌方随从休眠 2 回合。 | <b>抉择：</b>随机对两个敌方随从造成$2点伤害；或者使一个敌方随从<b>休眠</b>2回合。 | <b>Choose One -</b> Deal $2 damage to two random enemy minions; or Make one <b>Dormant</b> for 2 turns. |
| GVG_015 | 暗色炸弹 | Darkbomb | 2 | - | SPELL | 否 | 暗色炸弹 | 对一个角色造成$3点伤害。如果该角色死亡，抽一张暗影法术牌。 | Deal $3 damage to a character. If it dies, draw a Shadow spell. |
| BAR_915 | 暗金教物资官 | Kabal Outfitter | 2 | 3/3 | MINION | 否 | 罪罚 | <b>战吼，亡语：</b>随机使另一个友方随从获得+1/+1。 | [x]<b>Battlecry and Deathrattle:</b> Give another random  friendly minion +1/+1. |
| CATA_785 | 暮光祭礼 | Rite of Twilight | 2 | - | SPELL | 否 | 暮光祭礼 | <b>兆示</b>{0}。<b>连击：</b>造成$3点伤害。 | <b>Herald</b> {0}. <b>Combo:</b> Deal $3 damage. |
| AV_212 | 法力虹吸 | Siphon Mana | 2 | - | SPELL | 否 | 法力虹吸 | 造成$2点伤害。<b>荣誉消灭：</b>使你手牌中所有法术牌的法力值消耗减少（1）点。 | Deal $2 damage. <b>Honorable Kill</b>: Reduce the Cost of spells in your hand by (1). |
| BT_035 | 混乱打击 | Chaos Strike | 2 | - | SPELL | 否 | 混乱打击 | 在本回合中，使你的英雄获得+2攻击力。抽一张牌。 | Give your hero +2 Attack this turn. Draw a card. |
| CORE_BT_035 | 混乱打击 | Chaos Strike | 2 | - | SPELL | 否 | 混乱打击 | 在本回合中，使你的英雄获得+2攻击力。抽一张牌。 | Give your hero +2 Attack this turn. Draw a card. |
| ETC_069 | 渐强声浪 | Crescendo | 2 | - | SPELL | 否 | 渐强声浪：疲劳伤害（无疲劳数据时不计入）。 | 受到疲劳伤害。对所有敌人造成等量的伤害。0受到{0}点疲劳伤害。对所有敌人造成等量的伤害。 | [x]Take Fatigue damage. Deal that much damage to all enemies. |
| TIME_702 | 潮起潮落 | Ebb and Flow | 2 | - | SPELL | 否 | 潮起潮落 | 造成$3点伤害。如果你在本牌在你手中时使用过随从牌，获得5点护甲值。 | Deal $3 damage. If you played a minion while holding this, gain 5 Armor. |
| ONY_010 | 灭龙射击 | Dragonbane Shot | 2 | - | SPELL | 否 | 灭龙射击 | 造成$2点伤害。<b>荣誉消灭：</b>将一张灭龙射击置入你的手牌。 | [x]Deal $2 damage. <b>Honorable Kill:</b> Add a  Dragonbane Shot to your hand. |
| CATA_582 | 灼热裂隙 | Searing Fissure | 2 | - | SPELL | 否 | 灼热裂隙 | 对所有随从造成$1点伤害。在本回合中，使你的英雄获得+3攻击力。 | Deal $1 damage to all minions. Give your hero +3 Attack this turn. |
| TLC_901 | 烟雾熏蒸 | Fumigate | 2 | - | SPELL | 否 | 主目标 + 同 card_id 的其他随从 3 伤。 | 对一个随从及所有相同类型的其他随从造成$3点伤害。 | Deal $3 damage to a minion and all others of the same minion type. |
| CORE_EX1_610 | 爆炸陷阱 | Explosive Trap | 2 | - | SPELL | 否 | 爆炸陷阱 | <b>奥秘：</b>当你的英雄受到攻击，对所有敌人造成$2点伤害。 | <b>Secret:</b> When your hero is attacked, deal $2 damage to all enemies. |
| FIR_909 | 爆裂射击 | Bursting Shot | 2 | - | SPELL | 是 | 爆裂射击 | 随机对三个敌人造成$2点伤害。 | Deal $2 damage to three random enemies. |
| VAC_427 | 甜筒殡淇淋 | Corpsicle | 2 | - | SPELL | 否 | 甜筒殡淇淋：2 费 3 伤，可打脸/随从。残骸≥3 时回合结束回手（同回合斩杀只计一次 3 伤）。 | 造成$3点伤害。消耗3份<b>残骸</b>，在你的回合结束时将本牌移回你的手牌。 | Deal $3 damage. Spend 3 <b>Corpses</b> to return this to your hand at the end of your turn. |
| JAM_008 | 直播事故 | Dead Air | 2 | - | SPELL | 否 | 直播事故 | 消灭你的亡灵。再次召唤它们。 | Destroy your Undead. Resummon them. |
| GDB_460 | 神圣之星 | Divine Star | 2 | - | SPELL | 否 | 神圣之星 | 对一个随从造成$3点伤害。随机使你手牌中的一张随从牌获得+3生命值。 | Deal $3 damage to a minion. Give a random minion in your hand +3 Health. |
| CORE_BAR_541 | 符文宝珠 | Runed Orb | 2 | - | SPELL | 否 | 符文宝珠 | 造成$2点伤害。<b>发现</b>一张法术牌。 | Deal $2 damage. <b>Discover</b> a spell. |
| TIME_600 | 精确射击 | Precise Shot | 2 | - | SPELL | 否 | 精确射击：亮边 5 伤，否则 3 伤；仅打脸（无嘲）或点嘲讽随从。 | 造成$3点伤害。如果本牌位于你手牌的正中间，改为造成 $5点。 | Deal $3 damage. If this is EXACTLY in the center of your hand, deal $5 instead. |
| MAW_001 | 纵火指控 | Arson Accusation | 2 | - | SPELL | 否 | 消灭最优敌方随从（有嘲讽时仅嘲讽；清场指向性无嘲讽时可点随从）。 | 选择一个随从，在你的英雄受到伤害后将其消灭。 | Choose a minion. Destroy it after your hero takes damage. |
| BAR_314 | 罪罚（等级1） | Condemn (Rank 1) | 2 | - | SPELL | 否 | 罪罚 | 对所有敌方随从造成$1点伤害。<i>（当你有5点法力值时升级。）</i> | [x]Deal $1 damage to all enemy minions. <i>(Upgrades when you have 5 Mana.)</i> |
| REV_307 | 自然死亡 | Natural Causes | 2 | - | SPELL | 否 | 自然死亡 | 造成$2点伤害。召唤一个2/2的树人。 | Deal $2 damage. Summon a 2/2 Treant. |
| ULD_714 | 苦修 | Penance | 2 | - | SPELL | 否 | 苦修 | <b>吸血</b> 对一个随从造成$3点伤害。 | <b>Lifesteal</b> Deal $3 damage to a minion. |
| TLC_902 | 虫害侵扰 | Infestation | 2 | - | SPELL | 否 | 虫害侵扰：两张毒刺虫 token，各 2 伤 + 2/1 突袭。 | 获取两张法力值消耗为（1）的格里什毒刺虫。毒刺虫可以造成$2点伤害并召唤一只2/1具有<b>突袭</b>的异种虫幼体。 | [x]Get two 1-Cost Gorishi Stingers. Each one deals $2 damage and summons a 2/1 Grub with <b>Rush</b>. |
| BAR_916 | 血岩碎片刺背野猪人 | Blood Shard Bristleback | 2 | 3/3 | MINION | 否 | 罪罚 | <b>吸血</b>，<b>战吼：</b>如果你的牌库少于或等于10张，对一个随从造成6点伤害。 | [x]<b>Lifesteal</b>. <b>Battlecry:</b> If your deck contains 10 or fewer cards, deal 6 damage to a minion. |
| CFM_696 | 衰变 | Devolve | 2 | - | SPELL | 否 | 衰变（简化）：移除所有敌方随从关键词，身材不变。 | 随机将所有 敌方随从变形成为法力值消耗减少（1）点的随从。 | Transform all enemy minions into random ones that cost (1) less. |
| MAW_019 | 谋杀指控 | Murder Accusation | 2 | - | SPELL | 否 | 消灭最优敌方随从（有嘲讽时仅嘲讽；清场指向性无嘲讽时可点随从）。 | 选择一个随从，在另一个敌方随从死亡后将其消灭。 | Choose a minion. Destroy it after another enemy minion dies. |
| TIME_027 | 超光子弹幕 | Tachyon Barrage | 2 | - | SPELL | 是 | 超光子弹幕 | 造成$6点伤害，随机分配到所有敌人身上。将2张时空撕裂洗入你的牌库。 | Deal $6 damage split among all enemies. Shuffle 2 Shreds of Time into your deck. |
| CATA_203 | 迦罗娜的奋战 | Garona's Last Stand | 2 | - | SPELL | 否 | 迦罗娜的奋战：消灭一个传说随从。 | <b>可交易</b> 消灭一个<b>传说</b> 随从。 | [x]<b>Tradeable</b> Destroy a <b>Legendary</b> minion. |
| BAR_920 | 邪恶挥刺 | BAR_920 | 2 | - | - | 否 | 邪恶挥刺 |  |  |
| BAR_921 | 邪恶挥刺 | BAR_921 | 2 | - | - | 否 | 邪恶挥刺 |  |  |
| BAR_319 | 邪恶挥刺（等级1） | Wicked Stab (Rank 1) | 2 | - | SPELL | 否 | 邪恶挥刺 | 造成$2点伤害。<i>（当你有5点法力值时升级。）</i> | Deal $2 damage. <i>(Upgrades when you have 5 Mana.)</i> |
| BAR_319t | 邪恶挥刺（等级2） | Wicked Stab (Rank 2) | 2 | - | SPELL | 否 | 邪恶挥刺 | 造成$4点伤害。<i>（当你有10点法力值时升级。）</i> | Deal $4 damage. <i>(Upgrades when you have 10 Mana.)</i> |
| BAR_319t2 | 邪恶挥刺（等级3） | Wicked Stab (Rank 3) | 2 | - | SPELL | 否 | 邪恶挥刺 | 造成$6点伤害。 | Deal $6 damage. |
| SW_040 | 邪能弹幕 | Fel Barrage | 2 | - | SPELL | 否 | 邪能弹幕 | 对生命值最低的敌人造成$2点伤害两次。 | [x]Deal $2 damage to the lowest Health enemy, twice. |
| CORE_CS2_013 | 野性成长 | Wild Growth | 2 | - | SPELL | 否 | 野性成长：+1 空水晶。 | 获得一个空的法力水晶。 | Gain an empty Mana Crystal. |
| CS2_013 | 野性成长 | Wild Growth | 2 | - | SPELL | 否 | 野性成长：+1 空水晶。 | 获得一个空的法力水晶。 | Gain an empty Mana Crystal. |
| REV_939 | 锯齿骨刺 | Serrated Bone Spike | 2 | - | SPELL | 否 | 锯齿骨刺 | 对一个随从造成$3点伤害。如果该随从死亡，在本回合中，你的下一张牌法力值消耗减少（2）点。 | [x]Deal $3 damage to a  minion. If it dies, your  next card this turn  costs (2) less. |
| TIME_215 | 雷霆动地 | Thunderquake | 2 | - | SPELL | 否 | 雷霆动地 | 对所有随从造成$1点伤害。获取一张静电震击。 | [x]Deal $1 damage to all minions. Get a Static Shock. |
| WW_006 | 飞镖投掷 | Dart Throw | 2 | - | SPELL | 是 | 飞镖投掷：随机对敌方随从造成 2 点伤害，触发两次。 | 随机向敌方随从投掷两枚造成$2点伤害的飞镖。<i>（如果两枚击中同一个随从，获取一张幸运币！）</i> | [x]Throw two $2 damage darts at random enemy minions. <i>(If both hit the same minion, get a Coin!)</i> |
| JAIL_445 | 骨刃乱舞 | JAIL_445 | 2 | - | - | 是 | 骨刃乱舞：3 伤随机分配到所有敌人；本回合友方随从死亡则再 3（亮边共 6）。 |  |  |
| VAC_323t | 麦芽岩浆 | Malted Magma | 2 | - | SPELL | 否 | 麦芽岩浆：全体敌人 1 伤，连喝（VAC_323 衍生链）。 | 对所有敌人造成$1点伤害。<i>（还剩2杯！）</i> | Deal $1 damage to all enemies. <i>(2 Drinks left!)</i> |
| VAC_323t1 | 麦芽岩浆 | VAC_323t1 | 2 | - | - | 否 | 麦芽岩浆：全体敌人 1 伤，连喝（VAC_323 衍生链）。 |  |  |
| VAC_323t2 | 麦芽岩浆 | Malted Magma | 2 | - | SPELL | 否 | 麦芽岩浆：全体敌人 1 伤，连喝（VAC_323 衍生链）。 | 对所有敌人造成$1点伤害。<i>（最后一杯！）</i> | Deal $1 damage to all enemies. <i>(Last Drink!)</i> |
| CATA_464t | 龙息 | Dragon Breath | 2 | - | SPELL | 否 | 龙息 CATA_464t：黑翼实验品亡语衍生，伤害=TAG_SCRIPT_DATA_NUM_1（等于其攻击力）。 | 造成$1点伤害。 | Deal $1 damage. |
| VAC_951 | “健康”饮品 | "Health" Drink | 3 | - | SPELL | 否 | 吸血 3 伤；剩余杯数>0 时回手再喝（无自伤）。 | <b>吸血</b> 对一个随从造成$3点伤害。<i>（还剩3杯！）</i> | <b>Lifesteal</b>. Deal $3 damage to a minion. <i>(3 Drinks left!)</i> |
| VAC_951t | “健康”饮品 | "Health" Drink | 3 | - | SPELL | 否 | 吸血 3 伤；剩余杯数>0 时回手再喝（无自伤）。 | <b>吸血</b> 对一个随从造成$3点伤害。<i>（还剩2杯！）</i> | <b>Lifesteal</b>. Deal $3 damage to a minion. <i>(2 Drinks left!)</i> |
| VAC_951t2 | “健康”饮品 | "Health" Drink | 3 | - | SPELL | 否 | 吸血 3 伤；剩余杯数>0 时回手再喝（无自伤）。 | <b>吸血</b> 对一个随从造成$3点伤害。<i>（最后一杯！）</i> | <b>Lifesteal</b>. Deal $3 damage to a minion. <i>(Last Drink!)</i> |
| TLC_365 | 乱翻库存 | Storage Scuffle | 3 | - | SPELL | 否 | 乱翻库存 | 对一个随从造成$3点伤害。如果你在本回合中<b>发现</b>过，则本牌的法力值消耗为（0）点。 | Deal $3 damage to a minion. Costs (0) if you've <b>Discovered</b> this turn. |
| CORE_GVG_061 | 作战动员 | Muster for Battle | 3 | - | SPELL | 否 | 作战动员：三个 1/1 + 1/4 武器（新兵当回合失调）。 | 召唤三个1/1的白银之手新兵，装备一把1/4的武器。 | Summon three 1/1 Silver Hand Recruits. Equip a 1/4 Weapon. |
| RLK_512 | 冰川突进 | Glacial Advance | 3 | - | SPELL | 否 | 冰川突进 | 造成$4点伤害。在本回合中，你的下一个法术法力值消耗减少（2）点。 | Deal $4 damage. Your next spell this turn costs (2) less. |
| DINO_406 | 喷吐火焰 | Fire Breath | 3 | - | SPELL | 否 | 喷吐火焰：4 伤单目标 + 己方元素 +1/+1。 | 造成$4点伤害。使你的元素获得+1/+1。 | Deal $4 damage. Give your Elementals +1/+1. |
| CORE_BAR_311 | 噬灵疫病 | Devouring Plague | 3 | - | SPELL | 是 | 噬灵疫病 | <b>吸血</b> 造成$4点伤害，随机分配到所有敌方随从 身上。 | [x]<b>Lifesteal</b>. Deal $4 damage randomly split among all enemy minions. |
| CORE_CS2_062 | 地狱烈焰 | Hellfire | 3 | - | SPELL | 否 | 地狱烈焰 | 对所有角色造成$3点伤害。 | Deal $3 damage to ALL characters. |
| MIS_027 | 多米诺效应 | Domino Effect | 3 | - | SPELL | 否 | 多米诺效应 | 对一个随从造成$2点伤害。向左侧或右侧重复此效果，每次伤害增加1点。 | Deal $2 damage to a minion. Repeat to the left or right, dealing 1 more damage each time. |
| TIME_209t2 | 天神下凡形态 | Avatar Form | 3 | - | SPELL | 否 | 天神下凡形态：场攻向简化，不计入直伤。 | 在本回合中，使一个友方角色获得+2攻击力和“在本角色攻击后，对所有敌人造成2点伤害”。 | [x]Give a friendly character +2 Attack and "After this attacks, deal 2 damage to all enemies" this turn. |
| CORE_CS2_093 | 奉献 | Consecration | 3 | - | SPELL | 否 | 奉献 | 对所有敌人造成$2点伤害。 | Deal $2 damage to all enemies. |
| TIME_855 | 奥术弹幕 | Arcane Barrage | 3 | - | SPELL | 是 | 奥术弹幕 | 对一个敌人造成$3点伤害，并随机对两个其他敌人造成$2点伤害。 | Deal $3 damage to an enemy and $2 damage to two other random ones. |
| CORE_EX1_246 | 妖术 | Hex | 3 | - | SPELL | 否 | 妖术 | 使一个随从变形成为一只0/1并具有<b>嘲讽</b>的青蛙。 | Transform a minion into a 0/1 Frog with <b>Taunt</b>. |
| REV_924 | 始源之潮 | Primordial Wave | 3 | - | SPELL | 否 | 始源之潮 | 将敌方随从变形成为法力值消耗减少（1）点的随从，将友方随从变形成为法力值消耗增加（1）点的随从。 | [x]Transform enemy minions  into ones that cost (1) less  and friendly minions into  ones that cost (1) more. |
| RLK_570t2 | 恐怖药剂 | Dreadful Concoction | 3 | - | SPELL | 是 | Dreadful Concoction | 随机消灭一个敌方随从。<i>将另一份药剂置入你的手牌，即可混合在一起！</i> | Destroy a random enemy minion. <i>Add another Concoction to your hand to mix together!</i> |
| CORE_CS2_094 | 愤怒之锤 | Hammer of Wrath | 3 | - | SPELL | 否 | 愤怒之锤 | 造成$3点伤害。抽一张牌。 | Deal $3 damage. Draw a card. |
| CS2_094 | 愤怒之锤 | Hammer of Wrath | 3 | - | SPELL | 否 | 愤怒之锤 | 造成$3点伤害。抽一张牌。 | Deal $3 damage. Draw a card. |
| WORK_022 | 打卡 | Punch Card | 3 | - | SPELL | 否 | 打卡：+3 攻（顺劈 v1 不模拟）。 | 在本回合中，使你的英雄获得+3攻击力和“同时对相邻随从造成伤害”。 | Give your hero +3 Attack and "Also damages adjacent minions" this turn. |
| TIME_433 | 抹除存在 | Cease to Exist | 3 | - | SPELL | 是 | 抹除存在：随机沉默消灭 1 个敌方随从；回溯模拟 2 次取较好结果。 | <b>回溯</b>。<b>沉默</b>并消灭一个随机敌方随从。 | <b>Rewind</b> <b>Silence</b> and destroy a random enemy minion. |
| CATA_498 | 拉法姆的奋战 | Rafaams' Last Stand | 3 | - | SPELL | 是 | 随机对两个敌方随从造成伤害；手牌 TAG_SCRIPT_DATA_NUM_1 为当前单次伤害（默认 2）。 | 随机对两个敌方随从造成$2点伤害。<i>（每回合都会升级！）</i> | Deal $2 damage to two  random enemy minions. <i>(Upgrades each turn!)</i> |
| EDR_460 | 新月祈愿 | Wish of the New Moon | 3 | - | SPELL | 否 | 新月祈愿 | 对一个随从 造成$6点伤害。 <i>（施放3个法术 以获得<b>吸血</b>。）</i> | Deal $6 damage to a minion. <i>(Cast 3 spells to gain <b>Lifesteal</b>.)</i> |
| TIME_216 | 新生闪电 | Nascent Bolt | 3 | - | SPELL | 否 | 新生闪电 | 对一个随从造成$5点伤害。如果该随从依然存活，抽两张牌。 | Deal $5 damage to a minion. If it survives, draw 2 cards. |
| TIME_001 | 时空飞刃 | Chrono Daggers | 3 | - | SPELL | 是 | 时空飞刃 | <b>回溯</b>。随机向敌人射出3把飞刀，每把造成$2点伤害。 | <b>Rewind</b> Throw 3 knives at random enemies that deal $2 damage each. |
| ETC_305 | 暗弦术：改 | Shadow Chord: Distort | 3 | - | SPELL | 否 | 暗弦术：改 | 使一个随从获得-5/-5。如果该随从拥有0点攻击力，将其消灭。 | Give a minion -5/-5. If it has 0 Attack, destroy it. |
| CATA_138 | 森林赠礼 | Forest's Gift | 3 | - | SPELL | 否 | 森林赠礼：使一个可指定的友方随从获得你每控制一个随从的 +1/+1（跳过魔法免疫）。 | 你每控制一个随从，使一个友方随从获得+1/+1。 | Give a friendly minion +1/+1 for each minion you control. |
| CORE_CS2_012 | 横扫 | Swipe | 3 | - | SPELL | 否 | 横扫：主目标 4 伤，其余敌人各 1 伤（无嘲讽打脸 4）。 | 对一个敌人造成$4点伤害，并对所有其他敌人 造成$1点伤害。 | Deal $4 damage to an enemy and $1 damage to all other enemies. |
| CS2_012 | 横扫 | Swipe | 3 | - | SPELL | 否 | 横扫：主目标 4 伤，其余敌人各 1 伤（无嘲讽打脸 4）。 | 对一个敌人造成$4点伤害，并对所有其他敌人 造成$1点伤害。 | Deal $4 damage to an enemy and $1 damage to all other enemies. |
| END_025 | 永时火焰箭 | Eternal Firebolt | 3 | - | SPELL | 否 | 永时火焰箭 | <b>吸血</b>。对一个随从造成$3点伤害。如果该随从死亡，在你的回合结束时将本牌移回你的手牌。 | <b>Lifesteal</b> Deal $3 damage to a minion. If it dies, return this to your hand at the end of your turn. |
| BT_134 | 沼泽射线 | Bogbeam | 3 | - | SPELL | 否 | 沼泽射线 | 对一个随从造成$3点伤害。如果你拥有至少七个法力水晶，则法力值消耗为（0）点。 | Deal $3 damage to a minion. Costs (0) if you have at least 7 Mana Crystals. |
| RLK_570t3 | 泡泡药剂 | Bubbling Concoction | 3 | - | SPELL | 否 | Bubbling Concoction | 造成$3点伤害。<i>将另一份药剂置入你的手牌，即可混合在一起！</i> | Deal $3 damage. <i>Add another Concoction to your hand to mix together!</i> |
| VAC_953 | 浪潮涌起 | Rising Waves | 3 | - | SPELL | 否 | 浪潮涌起：全场 2 伤；若无死亡再 2 伤。 | 对所有随从造成 $2点伤害。如果没有随从死亡，再造成$2点。 | Deal $2 damage to all minions. If none die, deal $2 more. |
| GDB_902 | 潜入 | Infiltrate | 3 | - | SPELL | 否 | 选择一个随从，对其余所有随从造成 3 点伤害（含己方）。 | 选择一个随从。对所有其他随从造成$3点伤害。 | Choose a minion. Deal $3 damage to all other minions. |
| ETC_528 | 灯光表演 | Lightshow | 3 | - | SPELL | 是 | 灯光表演 | 向敌人发射2道可以造成$2点伤害的灯光。你此后的灯光表演多发射一道。 | [x]Shoot 2 beams at enemies that each deal $2 damage. Your future Lightshows shoot one more beam. |
| EDR_262 | 灵魂联结 | Spirit Bond | 3 | - | SPELL | 否 | 灵魂联结：3 伤；击杀召唤 3/2 突袭狼。 | 对一个随从造成$3点伤害。如果该随从死亡，召唤一只3/2并具有<b>突袭</b>的狼。 | Deal $3 damage to a minion. If it dies, summon a 3/2 Wolf with <b>Rush</b>. |
| FIR_910 | 灼烧之风 | Scorching Winds | 3 | - | SPELL | 否 | 灼烧之风：3 伤；亮边（手牌有火焰法术可弃）再 +3。 | 造成$3点伤害。随机弃掉一张火焰法术牌以再造成$3点。 | Deal $3 damage. Discard a random Fire spell to deal $3 more. |
| VAC_414 | 炽热火炭 | Hot Coals | 3 | - | SPELL | 否 | 炽热火炭：全体敌人 2 伤；亮边（本回合英雄受过伤）再 +1。 | 对所有敌人造成$2点伤害。如果你的英雄在本回合受到过伤害，再造成$1点。 | [x]Deal $2 damage to all enemies. If your hero took damage this turn, deal $1 more. |
| TLC_227 | 熔岩涌流 | Lava Flow | 3 | - | SPELL | 否 | 熔岩涌流 | 对生命值最低的敌人造成$2点伤害，触发三次。<b>过载：</b>（1）。 | Deal $2 damage to the lowest Health enemy, three times. <b>Overload:</b> (1) |
| CORE_LOOT_101 | 爆炸符文 | Explosive Runes | 3 | - | SPELL | 否 | 爆炸符文 | <b>奥秘：</b>在你的对手使用一张随从牌后，对该随从造成$6点伤害，超过其生命值的伤害将由对方英雄 承受。 | <b>Secret:</b> After your opponent plays a minion, deal $6 damage to it and any excess to their hero. |
| CORE_CS1_112 | 神圣新星 | Holy Nova | 3 | - | SPELL | 否 | 神圣新星 | 对所有敌方随从造成$2点伤害，为所有友方角色恢复#2点 生命值。 | Deal $2 damage to all enemy minions. Restore #2 Health to all friendly characters. |
| CORE_RLK_087 | 窒息 | Asphyxiate | 3 | - | SPELL | 否 | 窒息：消灭攻击力最高的敌方随从。 | 消灭攻击力最高的敌方随从。 | Destroy the highest Attack enemy minion. |
| REV_239 | 窒息暗影 | Suffocating Shadows | 3 | - | SPELL | 是 | 窒息暗影：正常打出时随机消灭一个敌方随从（弃牌触发不模拟）。 | 当你使用或弃掉这张牌时，随机消灭一个敌方随从。 | [x]When you play or  discard this, destroy a  random enemy minion. |
| GVG_010 | 维伦的恩泽 | Velen's Chosen | 3 | - | SPELL | 否 | 维伦的恩泽：友方随从 +2/+4。 | 使一个随从获得+2/+4和<b>法术伤害+1</b>。 | Give a minion +2/+4 and <b>Spell Damage +1</b>. |
| TTN_460 | 致命诛灭 | Mortal Eradication | 3 | - | SPELL | 是 | 致命诛灭：5 伤随机分配到敌方随从。 | 造成$5点伤害，随机分配到所有敌方随从身上。每消灭一个随从，为你的英雄恢复#2点生命值。 | [x]Deal $5 damage randomly split among all enemy minions. Restore #2 Health to your hero for each killed. |
| CATA_EVENT_402 | 致命贿赂 | Deadly Bribe | 3 | - | SPELL | 否 | 致命贿赂 | 消灭一个随从并使你的对手获得一张幸运币。<b>连击：</b>你也会获取一张。 | [x]Destroy a minion and give your opponent a Coin. <b>Combo:</b> You get one too. |
| RLK_570t1t2 | 调好的药剂 | Mixed Concoction | 3 | - | SPELL | 是 | Mixed Concoction | 随机召唤一个法力值消耗为（3）的随从。随机消灭一个敌方随从。 | Summon a random 3-Cost minion. Destroy a random enemy minion. |
| RLK_570t1t3 | 调好的药剂 | Mixed Concoction | 3 | - | SPELL | 否 | Mixed Concoction | 造成$3点伤害。随机召唤一个法力值消耗为（3）的随从。 | Deal $3 damage. Summon a random 3-Cost minion. |
| RLK_570t2t1 | 调好的药剂 | Mixed Concoction | 3 | - | SPELL | 否 | Mixed Concoction | 造成$3点伤害。随机消灭一个敌方随从。 | Deal $3 damage. Destroy a random enemy minion. |
| RLK_570t2t2 | 调好的药剂 | Mixed Concoction | 3 | - | SPELL | 是 | Mixed Concoction | 随机消灭两个敌方随从。 | Destroy two random enemy minions. |
| RLK_570t3t | 调好的药剂 | Mixed Concoction | 3 | - | SPELL | 否 | Mixed Concoction | 造成$3点伤害，触发两次。 | Deal $3 damage, twice. |
| RLK_570t4t1 | 调好的药剂 | Mixed Concoction | 3 | - | SPELL | 是 | Mixed Concoction | 将一张另一职业的牌置入你的手牌，其法力值消耗减少（3）点。随机消灭一个敌方随从。 | Add a card to your hand from another class. It costs (3) less. Destroy a random enemy minion. |
| RLK_570t4t2 | 调好的药剂 | Mixed Concoction | 3 | - | SPELL | 否 | Mixed Concoction | 造成$3点伤害。将一张另一职业的牌置入你的手牌，其法力值消耗减少（3）点。 | Deal $3 damage. Add a card to your hand from another class. It costs (3) less. |
| RLK_570tt2 | 调好的药剂 | Mixed Concoction | 3 | - | SPELL | 否 | Mixed Concoction | 造成$3点伤害。抽两张牌。 | Deal $3 damage. Draw 2 cards. |
| RLK_570tt4 | 调好的药剂 | Mixed Concoction | 3 | - | SPELL | 是 | Mixed Concoction | 抽两张牌。随机消灭一个敌方随从。 | Draw 2 cards. Destroy a random enemy minion. |
| TIME_619t2 | 赞达拉的惨象 | What Befell Zandalar | 3 | - | SPELL | 否 | 赞达拉惨象 | 对所有敌人造成$2点伤害。选择并使邦桑迪获得一项恩泽。 | [x]Deal $2 damage to all enemies. Choose a Boon to give to Bwonsamdi. |
| DALA_723 | 超级能量枪 | Hyperblaster | 3 | 1/0 | WEAPON | 否 | 超级能量枪 | <b>剧毒</b> 你的英雄在攻击时<b>免疫</b>。 | <b>Poisonous</b>. Your hero is <b>Immune</b> while attacking. |
| ONY_005tb1 | 超级能量枪 | Hyperblaster | 3 | 1/0 | WEAPON | 否 | 超级能量枪 | <b>剧毒</b> 你的英雄在攻击时<b>免疫</b>。 | <b>Poisonous</b>. Your hero is <b>Immune</b> while attacking. |
| PVPDR_SCH_Active51 | 超级能量枪 | Hyperblaster | 3 | 1/0 | WEAPON | 否 | 超级能量枪 | <b>剧毒</b> 你的英雄在攻击时<b>免疫</b>。 | <b>Poisonous</b>. Your hero is <b>Immune</b> while attacking. |
| VAC_464t14 | 超级能量枪 | Hyperblaster | 3 | 1/0 | WEAPON | 否 | 超级能量枪 | <b>剧毒</b> 你的英雄在攻击时<b>免疫</b>。 | <b>Poisonous</b>. Your hero is <b>Immune</b> while attacking. |
| GILA_854 | 野兽美女 | Beastly Beauty | 3 | 2/5 | MINION | 否 | 野兽美女：0/3 突袭；攻击随从并存活后变 8/8。 | <b>突袭</b> 在本随从攻击一个随从并存活下来后，变形成为8/8的随从。 | [x]<b>Rush</b> After this attacks a minion and survives, transform this into an 8/8. |
| ONY_005ta9 | 野兽美女 | Beastly Beauty | 3 | 2/6 | MINION | 否 | 野兽美女：0/3 突袭；攻击随从并存活后变 8/8。 | <b>突袭</b> 在本随从攻击一个随从并存活下来后，变形成为8/8的随从。 | [x]<b>Rush</b> After this attacks a minion and survives, transform this into an 8/8. |
| PVPDR_SCH_Active29 | 野兽美女 | Beastly Beauty | 3 | 2/6 | MINION | 否 | 野兽美女：0/3 突袭；攻击随从并存活后变 8/8。 | <b>突袭</b> 在本随从攻击一个随从并存活下来后，变形成为8/8的随从。 | [x]<b>Rush</b> After this attacks a minion and survives, transform this into an 8/8. |
| VAC_464t27 | 野兽美女 | Beastly Beauty | 3 | 2/6 | MINION | 否 | 野兽美女：0/3 突袭；攻击随从并存活后变 8/8。 | <b>突袭</b> 在本随从攻击一个随从并存活下来后，变形成为8/8的随从。 | [x]<b>Rush</b> After this attacks a minion and survives, transform this into an 8/8. |
| CORE_OG_047 | 野性之怒 | Feral Rage | 3 | - | SPELL | 否 | 野性之心：斩杀搜索取 +4 攻分支（忽略 8 甲）。 | <b>抉择：</b>使你的英雄在本回合中获得+4攻击力；或者获得8点护甲值。 | <b>Choose One -</b> Give your hero +4 Attack this turn; or Gain 8 Armor. |
| OG_047 | 野性之怒 | Feral Rage | 3 | - | SPELL | 否 | 野性之心：斩杀搜索取 +4 攻分支（忽略 8 甲）。 | <b>抉择：</b>使你的英雄在本回合中获得+4攻击力；或者获得8点护甲值。 | <b>Choose One -</b> Give your hero +4 Attack this turn; or Gain 8 Armor. |
| CORE_EX1_259 | 闪电风暴 | Lightning Storm | 3 | - | SPELL | 否 | 闪电风暴 | 对所有敌方随从造成$3点伤害，<b>过载：</b>（1） | Deal $3 damage to all enemy minions. <b>Overload:</b> (1) |
| CORE_MAW_021 | 问心无愧 | Clear Conscience | 3 | - | SPELL | 否 | 可靠陪伴：使一个友方随从获得 +2/+3（抽牌 v1 不模拟）。 | 使一个友方随从获得+2/+3和“在你对手的回合<b>扰魔</b>。” | Give a friendly minion +2/+3 and "<b>Elusive</b> on your opponent's turn." |
| MAW_021 | 问心无愧 | Clear Conscience | 3 | - | SPELL | 否 | 可靠陪伴：使一个友方随从获得 +2/+3（抽牌 v1 不模拟）。 | 使一个友方随从获得+2/+3和“在你对手的回合<b>扰魔</b>。” | Give a friendly minion +2/+3 and "<b>Elusive</b> on your opponent's turn." |
| REV_364 | 雄鹿冲锋 | Stag Charge | 3 | - | SPELL | 否 | 雄鹿冲锋 | 造成$3点伤害。随机召唤一个<b>休眠</b>的灵种。 | Deal $3 damage. Summon a random <b>Dormant</b> Wildseed. |
| TOY_714 | 飞速离架 | Fly Off the Shelves | 3 | - | SPELL | 否 | 飞速离架 | 对所有敌方随从造成$1点伤害。你手牌中每有一张龙牌，重复一次。 | Deal $1 damage to all enemy minions. Repeat for each Dragon you're holding. |
| TTN_753 | 鼓动火焰 | Bellowing Flames | 3 | - | SPELL | 否 | 鼓动火焰：5 伤单目标；锻造分支再 5 随机敌方随从。 | 对一个随从造成$5点伤害。<b>锻造：</b>然后造成$5点伤害，随机分配到所有敌方随从身上。 | Deal $5 damage to a minion. <b>Forge:</b> Then deal $5 damage split among all enemy minions. |
| ETC_413 | 低沉摇摆 | Going Down Swinging | 4 | - | SPELL | 否 | 低沉摇摆 | 在本回合中，使你的英雄获得+2攻击力和<b>免疫</b>，然后攻击每个敌方随从。 | [x]Give your hero +2 Attack and <b>Immune</b> this turn, then  attack each enemy minion. |
| TOY_716 | 光速抢购 | Flash Sale | 4 | - | SPELL | 否 | 光速抢购：召唤 1/2 圣盾嘲讽机械；使你的随从获得 +1/+2（含新机械，当回合失调）。 | 召唤一个1/2并具有<b>圣盾</b>和<b>嘲讽</b>的机械。使你的随从获得+1/+2。 | Summon a 1/2 Mech with <b>Divine Shield</b> and <b>Taunt</b>. Give your minions +1/+2. |
| RLK_709 | 冷酷严冬 | Remorseless Winter | 4 | - | SPELL | 否 | 冷酷严冬 | 对所有敌人造成$2点伤害。抽一张牌。 | Deal $2 damage to all enemies. Draw a card. |
| CORE_CS2_076 | 刺杀 | Assassinate | 4 | - | SPELL | 否 | 消灭最优敌方随从（有嘲讽时仅嘲讽；清场指向性无嘲讽时可点随从）。 | 消灭一个敌方随从。 | Destroy an enemy minion. |
| END_028 | 力敌万世 | For All Time | 4 | - | SPELL | 否 | 力敌万世 | 消灭所有攻击力小于或等于4的随从。<b>过载：</b>（2）。 | Destroy all minions with 4 or less Attack. <b>Overload:</b> (2) |
| END_014 | 协作火花 | Synchronized Spark | 4 | - | SPELL | 否 | 协作火花：对一名敌人 3 伤；若消灭随从，随机友方随从 +3/+3（取场攻最优）。 | 对一个敌人造成$3点伤害。如果该角色死亡，随机使一个友方随从获得+3/+3。 | [x]Deal $3 damage to an enemy. If it dies, give a random friendly minion +3/+3. |
| MIS_903 | 可疑交易 | Dubious Purchase | 4 | - | SPELL | 是 | 可疑交易：连击时随机消灭一个敌方随从；未连击仅抽牌，场攻不计消灭。 | 抽三张牌。<b>连击：</b>随机消灭一个敌方随从。 | Draw 3 cards. <b>Combo:</b> Destroy a random enemy minion. |
| CORE_CATA_007 | 吞噬 | Consumption | 4 | - | SPELL | 是 | 吞噬 | 随机对两个敌方随从造成$3点伤害。每有一个随从死亡，抽一张牌。 | Deal $3 damage to two random enemy minions. Draw a card for each that dies. |
| MIS_709 | 圣光荧光棒 | Holy Glowsticks | 4 | - | SPELL | 否 | 圣光荧光棒 | <b>吸血</b>。对一个随从造成$4点伤害。如果你在本回合中施放过神圣法术，则法力值消耗为（1）点。 | <b>Lifesteal</b> Deal $4 damage to a minion. Costs (1) if you've cast a Holy spell this turn. |
| CATA_489 | 奥术涌流 | Arcane Flow | 4 | - | SPELL | 否 | 奥术涌流（合体/完整裂变）：4 伤嘲讽或脸 + 全体敌人 2 伤。 | <b>裂变</b> 造成$4点伤害。对所有敌人造成$2点伤害。123743造成$4点伤害。对所有敌人造成$2点伤害。 | [x]<b>Shatter</b> Deal $4 damage.  Deal $2 damage to  all enemies. |
| CATA_489t | 奥术涌流 | Arcane Flow | 4 | - | SPELL | 否 | 奥术涌流单段：仅嘲讽随从或英雄脸（无嘲讽时不点非嘲讽随从）。 | <b>已裂变</b> 造成$4点伤害。 | <b>Shattered</b> Deal $4 damage. |
| CATA_489t2 | 奥术涌流 | Arcane Flow | 4 | - | SPELL | 否 | 奥术涌流（碎裂·AOE 段）：全体敌人 2 伤。 | <b>已裂变</b> 对所有敌人造成$2点伤害。 | <b>Shattered</b> Deal $2 damage to all enemies. |
| TTN_853 | 审判恶徒 | Judge Unworthy | 4 | - | SPELL | 否 | 审判恶徒：将一个敌方随从变为 1 血，再全体敌人 1 伤。须有敌方随从方可使用。 | 将一个敌方随从的生命值变为1，然后对所有敌人造成$1点 伤害。 | Set an enemy minion's Health to 1, then deal $1 damage to all enemies. |
| DAL_716 | 宿敌 | Vendetta | 4 | - | SPELL | 否 | 宿敌 | 对一个随从造成$4点伤害。如果你的手牌中有另一职业的卡牌，则法力值消耗为（0）点。 | Deal $4 damage to a minion. Costs (0) if you're holding a card from another class. |
| TOY_640 | 工坊事故 | Workshop Mishap | 4 | - | SPELL | 否 | 工坊事故 | 对一个随从造成$5点伤害，相邻的随从均会受到超过其生命值的伤害。<b>流放：</b>获得<b>吸血</b>。 | Deal $5 damage to a minion. Excess damages both neighbors. <b>Outcast:</b> Gain <b>Lifesteal</b>. |
| WW_393 | 影叶入侵 | Invasive Shadeleaf | 4 | - | SPELL | 否 | 10 伤（随从）；溢出置 1 费瓶子，伤害=溢出值，由 apply_spell_sequence 同回合续施。 | 对一个敌方随从造成$10点伤害。将超过目标生命值的伤害存入法力值消耗为（1）的瓶子。 | Deal $10 damage to an enemy minion. Save any excess in a 1-Cost Bottle. |
| SW_088 | 恶魔来袭 | Demonic Assault | 4 | - | SPELL | 否 | 恶魔来袭：3 伤 + 两只 1/3 嘲讽虚空行者（当回合失调）。 | 造成$3点伤害。召唤两个1/3并具有<b>嘲讽</b>的虚空行者。 | [x]Deal $3 damage. Summon two 1/3 Voidwalkers with <b>Taunt</b>. |
| CATA_306 | 教派分歧 | Schism | 4 | - | SPELL | 否 | 教派分歧：友方随从 +2/+3，召唤其复制（v1 复制当回合失调）。 | <b>裂变</b> 使一个友方随从获得+2/+3和<b>扰魔</b>。召唤一个它的复制。122876使一个友方随从获得+2/+3和<b>扰魔</b>。召唤一个它的复制。 | [x]<b>Shatter</b> Give a friendly minion +2/+3 and <b>Elusive</b>. Summon a copy of it. |
| CORE_EX1_197 | 暗言术：毁 | Shadow Word: Ruin | 4 | - | SPELL | 否 | 暗言术：毁 | 消灭所有攻击力大于或等于5的随从。 | Destroy all minions with 5 or more Attack. |
| TIME_441 | 永世裂痕 | Aeon Rend | 4 | - | SPELL | 是 | 永世裂痕 | <b>回溯</b>。随机对两个敌人造成$4点伤害。 | <b>Rewind</b> Deal $4 damage to two random enemies. |
| DMF_701 | 深水炸弹 | Dunk Tank | 4 | - | SPELL | 否 | 深水炸弹：4 伤可选目标；腐蚀后再对所有敌方随从 2 伤（不含英雄）。 | 造成$4点伤害。<b>腐蚀：</b>再对所有敌方随从造成$2点伤害。 | Deal $4 damage. <b>Corrupt:</b> Then deal $2 damage to all enemy minions. |
| DMF_701t | 深水炸弹 | Dunk Tank | 4 | - | SPELL | 否 | 深水炸弹：4 伤可选目标；腐蚀后再对所有敌方随从 2 伤（不含英雄）。 | <b>已腐蚀</b> 造成$4点伤害，再对所有敌方随从造成$2点 伤害。 | <b>Corrupted</b> Deal $4 damage, then deal $2 damage to all enemy minions. |
| YOG_502 | 清理污染 | Sanitize | 4 | - | SPELL | 否 | 清理污染：对所有随从造成等同于护甲的伤害。 | 对所有随从造成等同于你的护甲值的伤害。<b>锻造：</b>先获得3点护甲值。 | [x]Deal damage equal to your Armor to all minions. <b>Forge:</b> Gain 3 Armor first. |
| SW_107 | 火热促销 | Fire Sale | 4 | - | SPELL | 否 | 火热促销 | <b>可交易</b> 对所有随从造成 $3点伤害。 | <b>Tradeable</b> Deal $3 damage to all minions. |
| CORE_CS2_029 | 火球术 | Fireball | 4 | - | SPELL | 否 | 火球术 | 造成$6点伤害。 | Deal $6 damage. |
| CS2_029 | 火球术 | Fireball | 4 | - | SPELL | 否 | 火球术 | 造成$6点伤害。 | Deal $6 damage. |
| RLK_024 | 灵界打击 | Death Strike | 4 | - | SPELL | 否 | 灵界打击 | <b>吸血</b> 对一个随从造成$6点伤害。 | <b>Lifesteal</b> Deal $6 damage to a minion. |
| CORE_EX1_309 | 灵魂虹吸 | Siphon Soul | 4 | - | SPELL | 否 | 灵魂虹吸：消灭一个随从，英雄恢复 3 生命。 | 消灭一个随从，为你的英雄恢复#3点生命值。 | Destroy a minion. Restore #3 Health to your hero. |
| LOOTA_838 | 砰砰博士的砰砰箱 | Dr. Boom's Boombox | 4 | - | SPELL | 是 | 砰砰箱：7 次随机 1–4 伤。 | 召唤七个“砰砰机器人”。 | [x]Summon 7 'Boom Bots'. |
| ONY_005tb12 | 砰砰博士的砰砰箱 | Dr. Boom's Boombox | 4 | - | SPELL | 是 | 砰砰箱：7 次随机 1–4 伤。 | 召唤七个“砰砰机器人”。 | [x]Summon 7 'Boom Bots'. |
| VAC_464t21 | 砰砰博士的砰砰箱 | Dr. Boom's Boombox | 4 | - | SPELL | 是 | 砰砰箱：7 次随机 1–4 伤。 | 召唤七个“砰砰机器人”。 | [x]Summon 7 'Boom Bots'. |
| TOY_500 | 苏打火山 | Baking Soda Volcano | 4 | - | SPELL | 是 | 苏打火山：10 伤随机分配到所有随从（吸血不计己方）。 | <b>吸血</b>。造成$10点伤害，随机分配到所有随从身上。<b>过载：</b>（1） | <b>Lifesteal</b>. Deal $10 damage randomly split among all minions. <b>Overload:</b> (1) |
| CORE_SW_442 | 虚空碎片 | Void Shard | 4 | - | SPELL | 否 | 虚空碎片 | <b>吸血</b> 造成$4点伤害。 | <b>Lifesteal</b> Deal $4 damage. |
| WW_405 | 迅疾连射 | Fan the Hammer | 4 | - | SPELL | 否 | 迅疾连射 | 造成$6点伤害，分配到生命值最低的敌人身上。 | Deal $6 damage split among the lowest Health enemies. |
| DMF_117 | 连环灾难 | Cascading Disaster | 4 | - | SPELL | 是 | 连环灾难 | 随机消灭一个敌方随从。<b>腐蚀：</b>消灭两个。<b>再次腐蚀：</b>消灭三个。 | [x]Destroy a random enemy minion. <b>Corrupt:</b> Destroy 2. <b>Corrupt Again:</b> Destroy 3. |
| DMF_117t | 连环灾难 | Cascading Disaster | 4 | - | SPELL | 是 | 连环灾难 | <b>已腐蚀</b> 随机消灭两个敌方随从。<b>腐蚀：</b>消灭 三个。 | <b>Corrupted</b> Destroy 2 random enemy minions. <b>Corrupt:</b> Destroy 3. |
| DMF_117t2 | 连环灾难 | Cascading Disaster | 4 | - | SPELL | 是 | 连环灾难 | <b>已腐蚀</b> 随机消灭三个敌方随从。 | <b>Corrupted</b> Destroy 3 random enemy minions. |
| NX2_020 | 野蛮残食 | Cannibalize | 4 | - | SPELL | 否 | 野蛮残食：消灭一个随从，为友方角色恢复等同于其生命值的生命。 | 消灭一个随从。为所有友方角色恢复生命值，数值相当于该随从的生命值。 | Destroy a minion. Restore its Health to all friendly characters. |
| TOY_800 | 闪光试剂瓶 | Sparkling Phial | 4 | - | SPELL | 否 | 闪光试剂瓶 | 造成$2点伤害。在本回合中，你的下一张牌减少与伤害量相同的法力值消耗。 | [x]Deal $2 damage. Your next card this turn costs that much less. |
| TOY_377 | 霜巫十字绣 | Frost Lich Cross-Stitch | 4 | - | SPELL | 否 | 霜巫十字绣：3 伤；若消灭则召唤 3/6（当回合失调）。 | 对一个角色造成$3点伤害。如果该角色死亡，召唤一个3/6的可以<b><b>冻结</b></b>攻击目标的水元素。 | Deal $3 damage to a character. If it dies, summon a 3/6 Water Elemental that <b><b>Freeze</b>s</b>. |
| CATA_479 | 飞龙机动 | Flight Maneuvers | 4 | - | SPELL | 否 | 飞龙机动：召唤两条 4/2 幼龙；己方随从 +1 攻与圣盾（v1 幼龙当回合失调）。 | <b>裂变</b> 召唤两条4/2的幼龙。使你的随从获得+1攻击力和<b>圣盾</b>。123141召唤两条4/2的幼龙。使你的随从获得+1攻击力和<b>圣盾</b>。 | [x]<b>Shatter</b>. Summon two 4/2 Drakes. Give your minions +1 Attack and <b>Divine Shield</b>. |
| TIME_715 | 为了荣耀！ | For Glory! | 5 | - | SPELL | 否 | 为了荣耀！ | 抽两张牌。你的对手每控制一个随从，本牌的法力值消耗便减少（1）点。 | Draw 2 cards. Costs (1) less for each minion your opponent controls. |
| CORE_RLK_060 | 亡者大军 | Army of the Dead | 5 | - | SPELL | 否 | 亡者大军：消耗最多5份残骸，各复活为2/2突袭复活的食尸鬼。 | 将最多5份<b>残骸</b>复活为2/2并具有<b>突袭</b>的复活的食尸鬼。 | Raise up to 5 <b>Corpses</b> as 2/2 Risen Ghouls with <b>Rush</b>. |
| RLK_060 | 亡者大军 | Army of the Dead | 5 | - | SPELL | 否 | 亡者大军：消耗最多5份残骸，各复活为2/2突袭复活的食尸鬼。 | 将最多5份<b>残骸</b>复活为2/2并具有<b>突袭</b>的复活的食尸鬼。 | Raise up to 5 <b>Corpses</b> as 2/2 Risen Ghouls with <b>Rush</b>. |
| DALA_702 | 侏儒军刀 | Gnomish Army Knife | 5 | - | SPELL | 否 | 侏儒军刀 | 使一个随从获得<b>冲锋，风怒，圣盾，吸血，剧毒，嘲讽</b>以及<b>潜行</b>。 | [x]Give a minion <b>Charge</b>, <b>Windfury</b>, <b>Divine Shield</b>, <b>Lifesteal</b>, <b>Poisonous</b>, <b>Taunt</b>, and <b>Stealth</b>. |
| ONY_005tb2 | 侏儒军刀 | Gnomish Army Knife | 5 | - | SPELL | 否 | 侏儒军刀 | 使一个随从获得<b>突袭</b>，<b>风怒</b>，<b>圣盾</b>，<b>吸血</b>，<b>剧毒</b>，<b>嘲讽</b>以及<b>潜行</b>。 | [x]Give a minion <b>Rush</b>, <b>Windfury</b>, <b>Divine Shield</b>, <b>Lifesteal</b>, <b>Poisonous</b>, <b>Taunt</b>, and <b>Stealth</b>. |
| VAC_464t15 | 侏儒军刀 | Gnomish Army Knife | 5 | - | SPELL | 否 | 侏儒军刀 | 使一个随从获得<b>突袭</b>，<b>风怒</b>，<b>圣盾</b>，<b>吸血</b>，<b>剧毒</b>，<b>嘲讽</b>以及<b>潜行</b>。 | [x]Give a minion <b>Rush</b>, <b>Windfury</b>, <b>Divine Shield</b>, <b>Lifesteal</b>, <b>Poisonous</b>, <b>Taunt</b>, and <b>Stealth</b>. |
| REV_252 | 净场 | Clean the Scene | 5 | - | SPELL | 否 | 净场 | 消灭所有攻击力小于或等于3的随从。<b>注能（3）：</b>改为小于或等于6。 | Destroy all minions with 3 or less Attack. <b>Infuse (3):</b> 6 or less. |
| ONY_011 | 别站在火里！ | Don't Stand in the Fire! | 5 | - | SPELL | 是 | 别站在火里！ | 造成$10点伤害，随机分配到所有敌方随从身上。<b>过载：</b>（1） | Deal $10 damage randomly split among all enemy minions. <b>Overload:</b> (1) |
| CORE_UNG_952 | 剑龙骑术 | Spikeridged Steed | 5 | - | SPELL | 否 | 剑龙骑术：使一个随从获得 +2/+6 和嘲讽（亡语召唤剑龙 v1 不模拟）。 | 使一个随从获得+2/+6和<b>嘲讽</b>。当该随从死亡时，召唤一只剑龙。 | Give a minion +2/+6 and <b>Taunt</b>. When it dies, summon a Stegodon. |
| UNG_952 | 剑龙骑术 | Spikeridged Steed | 5 | - | SPELL | 否 | 剑龙骑术：使一个随从获得 +2/+6 和嘲讽（亡语召唤剑龙 v1 不模拟）。 | 使一个随从获得+2/+6和<b>嘲讽</b>。当该随从死亡时，召唤一只剑龙。 | Give a minion +2/+6 and <b>Taunt</b>. When it dies, summon a Stegodon. |
| JAM_018t3 | 动情狂想曲 | Emotional Rhapsody | 5 | - | SPELL | 否 | 混搭狂想曲及手牌衍生形态。 | 对所有随从造成$3点伤害。在本回合中，使你的英雄获得+5攻击力。<i>（每回合都会改变。）</i> | [x]Deal $3 damage to all minions. Give your hero +5 Attack this turn. <i>(Changes each turn.)</i> |
| ETC_356 | 变音和弦 | Altered Chord | 5 | - | SPELL | 否 | 变音和弦 | <b>吸血</b>。对一个随从造成$6点伤害。如果你有<b>过载</b>的法力水晶，本牌的法力值消耗减少（3）点。 | <b>Lifesteal</b> Deal $6 damage to a minion. Costs (3) less if you're <b>Overloaded</b>. |
| JAM_018t4 | 哀嚎狂想曲 | Wailing Rhapsody | 5 | - | SPELL | 否 | 混搭狂想曲及手牌衍生形态。 | 对所有随从造成$3点伤害。召唤一个5/5的恶魔。<i>（每回合都会改变。）</i> | Deal $3 damage to all minions. Summon a 5/5 Demon. <i>(Changes each turn.)</i> |
| LOOT_417 | 大灾变 | Cataclysm | 5 | - | SPELL | 否 | 大灾变：消灭所有随从（弃牌斩杀模拟中不计）。 | 消灭所有随从。弃两张牌。 | Destroy all minions. Discard 2 cards. |
| DED_517 | 奥术溢爆 | Arcane Overflow | 5 | - | SPELL | 否 | 奥术溢爆 | 对一个敌方随从造成$8点伤害。召唤一滩残渣，属性值等同于超过目标生命值的伤害。 | [x]Deal $8 damage to an enemy minion. Summon a  Remnant with stats equal to the excess damage. |
| SCH_138 | 威能祝福 | Blessing of Authority | 5 | - | SPELL | 否 | 威能祝福：+8/+8；本回合不能攻击英雄。 | 使一个随从获得+8/+8，在本回合中无法攻击英雄。 | Give a minion +8/+8. It can't attack heroes this turn. |
| GILA_410 | 布巴 | Bubba | 5 | 9/9 | MINION | 否 | 布巴：6 条 1/1 突袭猎犬攻击敌方随从。 | <b>战吼：</b>召唤六只1/1的血猎犬，攻击一个敌方随从。 | <b>Battlecry</b>: Summon six 1/1 Bloodhounds to attack an enemy minion. |
| ONY_005ta5 | 布巴 | Bubba | 5 | 8/8 | MINION | 否 | 布巴：6 条 1/1 突袭猎犬攻击敌方随从。 | <b>战吼：</b>召唤六只1/1并具有<b>突袭</b>的血猎犬并使其攻击一个敌方随从。 | [x]<b>Battlecry</b>: Summon six 1/1 Bloodhounds with <b>Rush</b> to attack an enemy minion. |
| PVPDR_SCH_Active47 | 布巴 | Bubba | 5 | 6/6 | MINION | 否 | 布巴：6 条 1/1 突袭猎犬攻击敌方随从。 | <b>战吼：</b>召唤六只1/1的血猎犬，攻击一个敌方随从。 | <b>Battlecry</b>: Summon six 1/1 Bloodhounds to attack an enemy minion. |
| VAC_464t6 | 布巴 | Bubba | 5 | 8/8 | MINION | 否 | 布巴：6 条 1/1 突袭猎犬攻击敌方随从。 | <b>战吼：</b>召唤六只 1/1并具有<b>突袭</b>的血猎犬并使其攻击一个 敌方随从。 | [x]<b>Battlecry</b>: Summon six 1/1 Bloodhounds with <b>Rush</b> to attack an enemy minion. |
| ONY_005tb5 | 异鳞之杖 | Staff of Scales | 5 | - | SPELL | 否 | 异鳞之杖：三条 1/1 突袭剧毒复生蛇。 | 召唤三条1/1并具有<b>突袭，剧毒</b>和<b>复生</b>的蛇。 | Summon three 1/1 Snakes with <b>Rush</b>, <b>Poisonous</b> and <b>Reborn</b>. |
| ULDA_008 | 异鳞之杖 | Staff of Scales | 5 | - | SPELL | 否 | 异鳞之杖：三条 1/1 突袭剧毒复生蛇。 | 召唤三条1/1并具有<b>突袭，剧毒</b>和<b>复生</b>的蛇。 | Summon three 1/1 Snakes with <b>Rush</b>, <b>Poisonous</b> and <b>Reborn</b>. |
| VAC_464t17 | 异鳞之杖 | Staff of Scales | 5 | - | SPELL | 否 | 异鳞之杖：三条 1/1 突袭剧毒复生蛇。 | 召唤三条1/1并具有<b>突袭，剧毒</b>和<b>复生</b>的蛇。 | Summon three 1/1 Snakes with <b>Rush</b>, <b>Poisonous</b> and <b>Reborn</b>. |
| MIS_701 | 恋旧风潮 | Wave of Nostalgia | 5 | - | SPELL | 否 | 恋旧风潮 | 将所有随从变形成为来自过去的随机<b>传说</b>随从。 | Transform ALL minions into random <b>Legendary</b> ones from the past. |
| JAIL_913 | 拦住他们！ | JAIL_913 | 5 | - | - | 否 | 拦住他们！：使一个友方随从获得 +5/+5 和吸血（吸血不计场攻）。 |  |  |
| EDR_461 | 新月仪式 | Ritual of the New Moon | 5 | - | SPELL | 否 | 新月/满月仪式：随机召唤两个指定费随从（召唤失调，本回合不可攻击）。 | 随机召唤两个法力值消耗为（3）的随从。<i>（施放3个法术以改为召唤法力值消耗为6的随从。）</i> | [x]Summon two random 3-Cost minions. <i>(Cast 3 spells to summon 6-Cost minions instead.)</i> |
| JAM_002 | 星辰能量 | Star Power | 5 | - | SPELL | 是 | 星辰能量 | 随机对一个敌方随从造成$5点伤害。重复此效果，每次伤害减少1点。 | [x]Deal $5 damage to a random enemy minion. Repeat this with 1 less damage. |
| NAX14_04 | 极寒之击 | Pure Cold | 5 | - | SPELL | 否 | 极寒之击：8 直伤（冻结 v1 不计入场攻）。 | 对敌方英雄造成$8点伤害，并使其<b>冻结</b>。 | Deal $8 damage to the enemy hero, and <b>Freeze</b> it. |
| ONY_005ta4 | 极寒之击 | Pure Cold | 5 | - | SPELL | 否 | 极寒之击：8 直伤（冻结 v1 不计入场攻）。 | 对敌方英雄造成$8点伤害，并使其<b>冻结</b>。 | Deal $8 damage to the enemy hero, and <b>Freeze</b> it. |
| PVPDR_SCH_Active61 | 极寒之击 | Pure Cold | 5 | - | SPELL | 否 | 极寒之击：8 直伤（冻结 v1 不计入场攻）。 | 对敌方英雄造成$8点伤害，并使其<b>冻结</b>。 | Deal $8 damage to the enemy hero, and <b>Freeze</b> it. |
| VAC_464t5 | 极寒之击 | Pure Cold | 5 | - | SPELL | 否 | 极寒之击：8 直伤（冻结 v1 不计入场攻）。 | 对敌方英雄造成$8点伤害，并使其<b>冻结</b>。 | Deal $8 damage to the enemy hero, and <b>Freeze</b> it. |
| YOP_026 | 树木生长 | Arbor Up | 5 | - | SPELL | 否 | 树木生长：召唤两个 2/2 树人；使你的随从获得 +2/+1（含新树人，当回合失调）。 | 召唤两个2/2的树人。使你的随从获得+2/+1。 | Summon two 2/2 Treants. Give your minions +2/+1. |
| BT_011 | 正义圣契 | Libram of Justice | 5 | - | SPELL | 否 | 正义圣契：敌方随从变 1 血 + 装备 1/4 武器。 | 装备一把1/4的武器。将所有敌方随从的生命值变为1。 | Equip a 1/4 weapon. Change the Health of all enemy minions to 1. |
| VAC_416 | 死亡翻滚 | Death Roll | 5 | - | SPELL | 是 | 死亡翻滚：消灭敌方随从，按其攻击力随机分配到所有敌人。 | 消灭一个敌方随从。造成等同于其攻击力的伤害，随机分配到所有敌人身上。 | [x]Destroy an enemy minion.  Deal damage equal to its Attack randomly split among all enemies. |
| CATA_533 | 涣漫洪流 | Flash Flood | 5 | - | SPELL | 否 | 最左 + 最右 5 伤；亮边（流放）时再执行一次。 | 对你的对手最左边和最右边的随从造成$5点伤害。<b>流放：</b>重复一次。 | [x]Deal $5 damage to your opponent's left  and right-most minions. <b>Outcast:</b> Do it again. |
| JAM_018 | 混搭狂想曲 | Remixed Rhapsody | 5 | - | SPELL | 否 | 混搭狂想曲及手牌衍生形态。 | 对所有随从造成$3点伤害。在你的手牌中时会获得一项额外效果，该效果每回合都会改变。 | Deal $3 damage to all minions. Gains an extra effect in your hand that changes each turn. |
| EDR_461t | 满月仪式 | Ritual of the Full Moon | 5 | - | SPELL | 否 | 新月/满月仪式：随机召唤两个指定费随从（召唤失调，本回合不可攻击）。 | 随机召唤两个法力值消耗为（6）的随从。 | Summon two random 6-Cost minions. |
| JAM_018t | 盛怒狂想曲 | Angsty Rhapsody | 5 | - | SPELL | 否 | 混搭狂想曲及手牌衍生形态。 | 对所有随从造成$3点伤害。抽三张牌。<i>（每回合都会改变。）</i> | Deal $3 damage to all minions. Draw 3 cards. <i>(Changes each turn.)</i> |
| CORE_EX1_407 | 绝命乱斗 | Brawl | 5 | - | SPELL | 否 | 绝命乱斗 | 随机选择一个随从，消灭除了该随从外的所有其他随从。 | Destroy all minions except one. <i>(chosen randomly)</i> |
| END_023 | 苦涩结局 | Bitter End | 5 | - | SPELL | 否 | 苦涩结局 | <b>冻结</b>一个随从及其相邻随从，并消灭其中受伤的随从。 | <b>Freeze</b> a minion and its neighbors. Destroy any that are damaged. |
| ETC_362 | 跳吧，虫子！ | JIVE, INSECT! | 5 | - | SPELL | 否 | 跳吧，虫子！ | 将一个随从变形成为炎魔之王拉格纳罗斯。<b>过载：</b>（2） | Transform a minion into Ragnaros the Firelord. <b>Overload:</b> (2) |
| CATA_978 | 辛达苟萨的胜利 | Sindragosa's Triumph | 5 | - | SPELL | 否 | 辛达苟萨的胜利 | 对一个随从造成$8点伤害。使你手牌中一张随机牌的法力值消耗减少，减少的量等于超过目标生命值的伤害。 | [x]Deal $8 damage to a minion. Reduce the Cost of a random card in your hand by the excess damage. |
| CORE_RLK_035 | 邪爆 | Corpse Explosion | 5 | - | SPELL | 否 | 邪爆 | 引爆一份<b>残骸</b>，对所有随从造成$1点伤害。如果有随从存活，重复此效果。 | Detonate a <b>Corpse</b> to deal $1 damage to all minions. If any are still alive, repeat this. |
| GDB_305 | 阳炎耀斑 | Solar Flare | 5 | - | SPELL | 否 | 阳炎耀斑 | 对所有敌人造成$2点伤害。你每控制一个元素，本牌的法力值消耗便减少（1）点。 | Deal $2 damage to all enemies. Costs (1) less for each Elemental you control. |
| JAM_018t2 | 高亢狂想曲 | Resounding Rhapsody | 5 | - | SPELL | 否 | 混搭狂想曲及手牌衍生形态。 | 对所有随从造成$3点伤害，造成两次。<i>（每回合都会改变。）</i> | Deal $3 damage to all minions, twice. <i>(Changes each turn.)</i> |
| CATA_308 | 麦迪文的胜利 | Medivh's Triumph | 5 | - | SPELL | 否 | 麦迪文的胜利 | 对所有随从造成$4点伤害。如果你控制着<b>传说</b>牌，本牌的法力值消耗为（1）点。 | Deal $4 damage to all minions. Costs (1) if you control a <b>Legendary</b> card. |
| CFM_662 | 龙息药水 | Dragonfire Potion | 5 | - | SPELL | 否 | 龙息药水：对除龙以外的所有随从 5 伤（含己方）。 | 对所有非龙随从造成$5点伤害。 | [x]Deal $5 damage to all minions except Dragons. |
| TOY_602 | 化工泄漏 | Chemical Spill | 6 | - | SPELL | 否 | 化工泄漏 | 从你的手牌中召唤法力值消耗最高的随从，然后对其造成$5点伤害。 | Summon the highest Cost minion from your hand, then deal $5 damage to it. |
| LOOTA_842 | 奎尔德拉 | Quel'Delar | 6 | 6/0 | WEAPON | 否 | 奎尔德拉 | 在你的英雄攻击后，对所有敌人造成6点伤害。 | After your hero attacks, deal 6 damage to all enemies. |
| ONY_005tc7 | 奎尔德拉 | Quel'Delar | 6 | 4/0 | WEAPON | 否 | 奎尔德拉 | 在你的英雄攻击后，对所有敌人造成4点伤害。 | After your hero attacks, deal 4 damage to all enemies. |
| PVPDR_SCH_Active25 | 奎尔德拉 | Quel'Delar | 6 | 4/0 | WEAPON | 否 | 奎尔德拉 | <b>对战开始时：</b>抽到这张牌。在你的英雄攻击后，对所有敌人造成4点伤害。 | <b>Start of Game:</b> Draw This. After your hero attacks, deal 4 damage to all enemies. |
| VAC_464t31 | 奎尔德拉 | Quel'Delar | 6 | 4/0 | WEAPON | 否 | 奎尔德拉 | 在你的英雄攻击后，对所有敌人造成4点伤害。 | After your hero attacks, deal 4 damage to all enemies. |
| CATA_581 | 屠灭 | Decimation | 6 | - | SPELL | 否 | 屠灭：对所有随从造成等同于场上随从数量的伤害（TAG_SCRIPT / 实时场面）。 | 对所有随从造成$1点伤害<i>（战场上每有一个随从都会提高）</i>。 | [x]Deal $1 damage to all minions. <i>(Improved for each minion on the battlefield.)</i> |
| ETC_314 | 悦耳流行歌 | Harmonic Pop | 6 | - | SPELL | 否 | 悦耳流行歌 | 对所有随从造成$3点伤害。召唤一个6/6的流行歌星。<i>（每回合切换。）</i> | Deal $3 damage to all minions. Summon a 6/6 Popstar. <i>(Swaps each turn.)</i> |
| EX1_173 | 星火术 | Starfire | 6 | - | SPELL | 否 | 星火术 | 造成$5点伤害。抽一张牌。 | Deal $5 damage. Draw a card. |
| VAN_EX1_173 | 星火术 | Starfire | 6 | - | SPELL | 否 | 星火术 | 造成$5点伤害。抽一张牌。 | Deal $5 damage. Draw a card. |
| CORE_CS2_028 | 暴风雪 | Blizzard | 6 | - | SPELL | 否 | 暴风雪 | 对所有敌方随从造成$2点伤害，并使其<b>冻结</b>。 | Deal $2 damage to all enemy minions and <b>Freeze</b> them. |
| CORE_EDR_476 | 月亮井 | Moonwell | 6 | - | SPELL | 否 | 月亮井：对全体敌人造成 4 点（含英雄），全体友方恢复 4 点。 | 对所有敌方 角色造成$4点伤害。为所有友方角色恢复#4点生命值。 | Deal $4 damage to all enemy characters. Restore #4 Health to all friendly characters. |
| EDR_476 | 月亮井 | Moonwell | 6 | - | SPELL | 否 | 月亮井：对全体敌人造成 4 点（含英雄），全体友方恢复 4 点。 | 对所有敌方 角色造成$4点伤害。为所有友方角色恢复#4点生命值。 | Deal $4 damage to all enemy characters. Restore #4 Health to all friendly characters. |
| REV_840 | 死神之躯 | Deathborne | 6 | - | SPELL | 否 | 死神之躯 | 对所有随从造成$2点伤害。每消灭一个随从，召唤一个2/2的不稳定的骷髅。 | Deal $2 damage to all minions. Summon a 2/2 Volatile Skeleton  for each killed. |
| TLC_221 | 炽火缠身 | Sizzling Swarm | 6 | - | SPELL | 否 | 炽火缠身：3 伤 + 召唤 3 个 2/1 炽烈烬火。 | 造成$3点伤害，召唤相同数量的2/1的炽烈烬火。 | Deal $3 damage. Summon that many 2/1 Sizzling Cinders. |
| ETC_082 | 绝望哀歌 | Dirge of Despair | 6 | - | SPELL | 否 | 绝望哀歌：对任意角色 3 伤；击杀则从牌库召唤恶魔（v1 召唤 3/3 突袭）。 | 对一个角色造成$3点伤害。如果该角色死亡，从你的牌库中召唤一个恶魔。 | [x]Deal $3 damage to a character. If it dies, summon a Demon from your deck. |
| TSC_932 | 血染大海 | Blood in the Water | 6 | - | SPELL | 否 | 3 伤（可选目标）+ 始终召唤 5/5 突袭（当回合仅解场、不打脸）。 | 对一个敌人造成$3点伤害。召唤一条5/5并具有<b>突袭</b>的鲨鱼。 | Deal $3 damage to an enemy. Summon a 5/5 Shark with <b>Rush</b>. |
| CATA_156 | 试验演示 | Experimental Animation | 6 | - | SPELL | 否 | 试验演示：全体敌方随从 4 伤（兆示/POWERED_UP 不改变伤害）。 | <b>兆示</b>{0}。对所有敌方随从造成$4点伤害。 | <b>Herald</b> {0}. Deal $4 damage to all enemy minions. |
| SCH_512 | 通窍 | Initiation | 6 | - | SPELL | 否 | 4 伤；击杀后召唤复制（冲锋可打脸，突袭仅解场，普通随从召唤失调）。 | 对一个随从造成$4点伤害。如果该随从死亡，召唤一个新的复制。 | Deal $4 damage to a minion. If it dies, summon a new copy. |
| UNG_955 | 陨石术 | Meteor | 6 | - | SPELL | 否 | 陨石术 | 对一个随从造成$15点伤害，并对其相邻的随从造成 $4点伤害。 | Deal $15 damage to a minion and $4 damage to adjacent ones. |
| GDB_445 | 陨石风暴 | Meteor Storm | 6 | - | SPELL | 否 | 陨石风暴 | 对所有随从造成$5点伤害。将5张小行星洗入你的牌库。 | Deal $5 damage to all minions. Shuffle 5 Asteroids into your deck. |
| RLK_063 | 冰霜巨龙之怒 | Frostwyrm's Fury | 7 | - | SPELL | 否 | 冰霜巨龙之怒：全体敌人 5 伤 + 召唤 5/5 突袭。 | 造成$5点伤害。<b>冻结</b>所有敌方随从。召唤一条5/5的冰霜巨龙。 | Deal $5 damage. <b>Freeze</b> all enemy minions. Summon a 5/5 Frostwyrm. |
| REV_950 | 圣洁鸣钟 | Divine Toll | 7 | - | SPELL | 否 | 圣洁鸣钟 | 随机向随从发射5道射线。射线可使友方随从获得+2/+2，或对敌方随从造成$2点伤害。 | [x]Shoot 5 rays at random minions. They give friendly minions +2/+2, and deal $2 damage to enemy minions. |
| EDR_255 | 复苏烈焰 | Renewing Flames | 7 | - | SPELL | 否 | 复苏烈焰 | <b>吸血</b>。对生命值最低的敌人造成$5点伤害，触发两次。 | <b>Lifesteal</b>. Deal $5 damage to the lowest Health enemy, twice. |
| CORE_BT_072 | 深度冻结 | Deep Freeze | 7 | - | SPELL | 否 | 深度冻结 | <b>冻结</b>一个敌人。召唤两个3/6的水元素。 | <b>Freeze</b> an enemy. Summon two 3/6 Water Elementals. |
| KAR_076 | 火焰之地传送门 | Firelands Portal | 7 | - | SPELL | 否 | 火焰之地传送门 | 造成$6点伤害。随机召唤一个法力值消耗为（6）的随从。 | Deal $6 damage. Summon a random 6-Cost minion. |
| CORE_CS2_032 | 烈焰风暴 | Flamestrike | 7 | - | SPELL | 否 | 烈焰风暴 | 对所有敌方随从造成$5点伤害。 | Deal $5 damage to all enemy minions. |
| TIME_712 | 诛灭暴君 | Dethrone | 7 | - | SPELL | 否 | 诛灭暴君：消灭一个随从（连击召唤 8 费随从 v1 不模拟）。 | 消灭一个随从。<b>连击：</b>随机召唤一个法力值消耗为（8）的随从。 | Destroy a minion. <b>Combo:</b> Summon a random 8-Cost minion. |
| CORE_OG_211 | 兽群呼唤 | Call of the Wild | 8 | - | SPELL | 否 | 兽群呼唤：召唤米莎、雷欧克、霍弗；霍弗冲锋，雷欧克给其他随从 +1 攻。 | 召唤全部三个动物伙伴。 | Summon all three Animal Companions. |
| OG_211 | 兽群呼唤 | Call of the Wild | 8 | - | SPELL | 否 | 兽群呼唤：召唤米莎、雷欧克、霍弗；霍弗冲锋，雷欧克给其他随从 +1 攻。 | 召唤全部三个动物伙伴。 | Summon all three Animal Companions. |
| EX1_312 | 扭曲虚空 | Twisting Nether | 8 | - | SPELL | 否 | 扭曲虚空 | 消灭所有随从和地标。 | Destroy all minions and locations. |
| TOY_529 | 死亡轮盘 | Wheel of DEATH!!! | 8 | - | SPELL | 否 | 死亡轮盘 | 摧毁你的牌库。5回合后，消灭敌方英雄。 | Destroy your deck. In 5 turns, destroy the enemy hero. |
| REV_369 | 间接伤害 | Collateral Damage | 8 | - | SPELL | 是 | 间接伤害 | 随机对三个敌方随从造成$6点伤害。超过目标生命值的伤害会命中敌方英雄。 | [x]Deal $6 damage to three  random enemy minions.  Excess damage hits  the enemy hero. |
| WW_427 | 夕阳漫射 | Sunset Volley | 9 | - | SPELL | 是 | 夕阳漫射：10 伤随机分配到所有敌人。 | 造成$10点伤害，随机分配到所有敌人身上。随机召唤一个法力值消耗为（10）的随从。 | Deal $10 damage randomly split among all enemies. Summon a random 10-Cost minion. |
| LOOTA_827 | 拉格纳罗斯的余烬 | Embers of Ragnaros | 10 | - | SPELL | 是 | 拉格纳罗斯的余烬：随机 3 个火球各 8 伤。 | 随机向敌人射出三个火球，每个造成$8点伤害。 | Shoot three fireballs at random enemies that deal $8 damage each. |
| ONY_005tc1 | 拉格纳罗斯的余烬 | Embers of Ragnaros | 10 | - | SPELL | 是 | 拉格纳罗斯的余烬：随机 3 个火球各 8 伤。 | 随机向敌人射出三个火球，每个造成$8点伤害。 | Shoot three fireballs at random enemies that deal $8 damage each. |
| PVPDR_SCH_Active55 | 拉格纳罗斯的余烬 | Embers of Ragnaros | 10 | - | SPELL | 是 | 拉格纳罗斯的余烬：随机 3 个火球各 8 伤。 | 随机向敌人射出三个火球，每个造成$8点伤害。 | Shoot three fireballs at random enemies that deal $8 damage each. |
| VAC_464t23 | 拉格纳罗斯的余烬 | Embers of Ragnaros | 10 | - | SPELL | 是 | 拉格纳罗斯的余烬：随机 3 个火球各 8 伤。 | 随机向敌人射出三个火球，每个造成$8点伤害。 | Shoot three fireballs at random enemies that deal $8 damage each. |
| TOY_883 | 掀桌子 | Table Flip | 10 | - | SPELL | 否 | 掀桌子：对所有敌方随从 3 伤（减费 v1 不模拟）。 | 对所有敌方随从造成$3点伤害。你每有一张其他手牌，本牌的法力值消耗便减少（1）点。 | Deal $3 damage to all enemy minions. Costs (1) less for each other card in your hand. |
| CATA_452 | 织法者的光辉 | Spellweaver's Brilliance | 10 | - | SPELL | 否 | 织法者的光辉：召唤 6/6 龙（当回合失调）。 | 召唤一条6/6的龙。在本回合中，你每用法术造成一点伤害，本牌的法力值消耗便减少（1）点。 | [x]Summon a 6/6 Dragon. Costs (1) less for each damage you dealt with spells this turn. |
| ETC_210 | 通灵最强音 | Climactic Necrotic Explosion | 10 | - | SPELL | 否 | 通灵最强音：脚本伤害（TAG_SCRIPT_DATA_NUM_1，随消耗残骸提升）+ 吸血。 | <b>吸血</b>。造成${0}点伤害。召唤{1}个{2}/{3}的灵魂。<i>（随你消耗过的<b>残骸</b>数量随机提升）</i> | [x]<b>Lifesteal</b>. Deal ${0} damage. Summon {1} {2}/{3} Souls. <i>(Randomly improved by <b>Corpses</b> you've spent)</i> |
| ONY_005tc2 | 亡者之书 | Book of the Dead | 14 | - | SPELL | 否 | 亡者之书：对所有敌人 7 伤。 | 对所有敌人造成$7点伤害。在本局对战中，每有一个随从死亡，本牌的法力值消耗便减少（1）点。 | Deal $7 damage to all enemies. Costs (1) less for each minion that's died this game. |
| PVPDR_SCH_Active54 | 亡者之书 | Book of the Dead | 14 | - | SPELL | 否 | 亡者之书：对所有敌人 7 伤。 | 对所有敌人造成$7点伤害。在本局对战中，每有一个随从死亡，本牌的法力值消耗便减少（1）点。 | Deal $7 damage to all enemies. Costs (1) less for each minion that's died this game. |
| VAC_464t24 | 亡者之书 | Book of the Dead | 14 | - | SPELL | 否 | 亡者之书：对所有敌人 7 伤。 | 对所有敌人造成$7点伤害。在本局对战中，每有一个随从死亡，本牌的法力值消耗便减少（1）点。 | Deal $7 damage to all enemies. Costs (1) less for each minion that's died this game. |
## 战吼随从

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| CORE_UNG_205 | 冰川裂片 | Glacial Shard | 1 | 2/1 | MINION | 否 | 冰川裂片 | <b>战吼：</b> <b>冻结</b>一个敌人。 | <b>Battlecry:</b> <b>Freeze</b> an enemy. |
| BT_722 | 防护改装师 | Guardian Augmerchant | 1 | 2/1 | MINION | 否 | 防护改装师 | <b>战吼：</b>对一个随从造成1点伤害，并使其获得<b>圣盾</b>。 | <b>Battlecry:</b> Deal 1 damage to a minion and give it <b>Divine Shield</b>. |
| MAW_000 | 冒牌小鬼 | Imp-oster | 2 | 1/1 | MINION | 否 | 冒牌小鬼 | <b>战吼：</b>选择一个友方小鬼，变形成为一个它的复制。 | <b>Battlecry:</b> Choose a friendly Imp. Transform into a copy of it. |
| YOG_501 | 历战无面者 | Battleworn Faceless | 2 | 2/2 | MINION | 否 | 历战无面者 | <b>战吼：</b>变形成为一个受伤的随从的复制。 | <b>Battlecry:</b> Transform into a copy of a damaged minion. |
| AV_294 | 怒爪精锐 | Clawfury Adept | 2 | 2/3 | MINION | 否 | 怒爪精锐：其他友方角色 +1 攻。 | <b>战吼：</b>在本回合中，使所有其他友方角色获得+1攻击力。 | <b>Battlecry:</b> Give all other friendly characters +1 Attack this turn. |
| CORE_CFM_753 | 污手街供货商 | Grimestreet Outfitter | 2 | 2/2 | MINION | 否 | 污手街供货商 | <b>战吼：</b>使你手牌中的所有随从牌获得+1/+1。 | <b>Battlecry:</b> Give all minions in your hand +1/+1. |
| CORE_EX1_082 | 疯狂投弹者 | Mad Bomber | 2 | 3/2 | MINION | 是 | 疯狂投弹者 | <b>战吼：</b>造成3点伤害，随机分配到所有其他角色身上。 | <b>Battlecry:</b> Deal 3 damage randomly split between all other characters. |
| RLK_867 | 维库通灵师 | Vrykul Necrolyte | 2 | 2/2 | MINION | 否 | 维库通灵师：仅标记生命值最低友方（亡语本回合不计入斩杀）。 | <b>战吼：</b>使一个友方随从获得“<b>亡语：</b>召唤一个2/2并具有<b>突袭</b>的僵尸。” | [x]<b>Battlecry:</b> Give a friendly minion "<b>Deathrattle:</b>  Summon a 2/2 Zombie with <b>Rush</b>." |
| TTN_456 | 蔽刺触手 | Thornveil Tentacle | 2 | 2/2 | MINION | 是 | 蔽刺触手 | <b>吸血</b>。<b>战吼：</b>随机对一个敌方随从造成2点伤害。 | [x]<b>Lifesteal</b> <b>Battlecry:</b> Deal 2 damage to a random enemy minion. |
| RLK_222 | 阿斯塔洛·血誓 | Astalor Bloodsworn | 2 | 2/2 | MINION | 否 | 阿斯塔洛·血誓 | <b>战吼：</b>将护卫阿斯塔洛置入你的手牌。<b>法力渴求（5）：</b>造成2点伤害。 | <b>Battlecry:</b> Add Astalor, the Protector to your hand. <b>Manathirst (5):</b> Deal 2 damage. |
| RLK_951 | 验尸官 | Coroner | 2 | 2/2 | MINION | 否 | 验尸官 | <b>战吼：</b><b>冻结</b>一个敌方随从。<b>法力渴求（6）：</b>先将其<b>沉默</b>。 | <b>Battlecry:</b> <b>Freeze</b> an enemy minion. <b>Manathirst (6):</b> <b>Silence</b> it first. |
| YOG_525 | 健身肌器人 | Muscle-o-Tron | 3 | 2/4 | MINION | 否 | 健身肌器人 | <b>战吼：</b>使你手牌中的所有随从牌获得+1/+1。<b>锻造：</b>改为+2/+2。 | [x]<b>Battlecry:</b> Give all minions in your hand +1/+1. <b>Forge:</b> +2/+2 instead. |
| VAC_701 | 刀剑保养师 | Swarthy Swordshiner | 3 | 3/3 | MINION | 否 | 刀剑保养师 | <b>战吼：</b>将你的武器的攻击力和耐久度变为3。 | <b>Battlecry:</b> Set the Attack and Durability of your weapon to 3. |
| LOE_017 | 奥达曼守护者 | Keeper of Uldaman | 3 | 3/4 | MINION | 否 | 奥达曼守护者 | <b>战吼：</b> 将一个随从的攻击力和生命值变为3。 | <b>Battlecry:</b> Set a minion's Attack and Health to 3. |
| CATA_EVENT_002 | 怨毒焰魔 | Baleful Blazer | 3 | 4/3 | MINION | 否 | 怨毒焰魔 | <b>战吼：</b>如果你在本回合中施放过火焰法术，消灭一个随从。 | <b>Battlecry:</b> If you've played a Fire spell this turn, destroy a minion. |
| TTN_457 | 悼词宣诵者 | Eulogizer | 3 | 3/3 | MINION | 否 | 悼词宣诵者 | <b>战吼：</b>消耗3份<b>残骸</b>，造成3点伤害。<b>锻造：</b>改为获得残骸。 | [x]<b>Battlecry:</b> Spend 3 <b>Corpses</b> to deal 3 damage. <b>Forge:</b> Gain them instead. |
| CORE_REV_023 | 拆迁修理工 | Demolition Renovator | 3 | 3/3 | MINION | 否 | 拆迁修理工 | <b>可交易</b> <b>战吼：</b>摧毁一个敌方地标。 | <b>Tradeable</b> <b>Battlecry:</b> Destroy  an enemy location. |
| TLC_606 | 拉特维亚护甲师 | Latorvian Armorer | 3 | 3/3 | MINION | 否 | 拉特维亚护甲师 | <b>战吼：</b>对一个敌方随从造成2点伤害。如果该随从死亡，获得5点护甲值。 | <b>Battlecry:</b> Deal 2 damage to an enemy minion. If it dies, gain 5 Armor. |
| CORE_OG_149 | 暴虐食尸鬼 | Ravaging Ghoul | 3 | 3/3 | MINION | 否 | 暴虐食尸鬼 | <b>战吼：</b>对所有其他随从造成1点伤害。 | <b>Battlecry:</b> Deal 1 damage to all other minions. |
| GDB_901 | 极紫外破坏者 | Ultraviolet Breaker | 3 | 3/2 | MINION | 否 | 极紫外破坏者 | <b>战吼：</b>对一个 敌方随从造成3点伤害。将3张小行星洗入你的牌库。 | [x]<b>Battlecry:</b> Deal 3 damage to an enemy minion. Shuffle 3 Asteroids into your deck. |
| DED_507 | 桅台观察员 | Crow's Nest Lookout | 3 | 2/2 | MINION | 否 | 桅台观察员 | <b>战吼：</b>对最左边和最右边的敌方随从造成2点伤害。 | [x]<b>Battlecry:</b> Deal 2 damage to the left and right-most enemy minions. |
| END_021 | 次元武器匠 | Dimensional Weaponsmith | 3 | 2/5 | MINION | 否 | 次元武器匠 | <b>战吼：</b>使你手牌中所有随从牌和武器牌获得+2攻击力。 | <b>Battlecry:</b> Give all minions and weapons in your hand +2 Attack. |
| CATA_161 | 残恶梦魇 | Gruesome Nightmare | 3 | 3/3 | MINION | 否 | 残恶梦魇 | <b>战吼：</b>使你手牌中或战场上的一个随从获得等同于本随从攻击力的攻击力。 | <b>Battlecry:</b> Give a minion in your hand or battlefield Attack equal to this minion's Attack. |
| TIME_609 | 游侠将军希尔瓦娜斯 | Ranger General Sylvanas | 3 | 2/4 | MINION | 否 | 游侠将军希尔瓦娜斯 | <b>奇闻</b> <b>战吼：</b>对所有敌人造成2点伤害。如果你使用过奥蕾莉亚或温蕾萨，每使用过一位，重复一次。 | [x]<b>Fabled</b>. <b>Battlecry:</b> Deal 2 damage to all enemies.     If you've played Alleria or       Vereesa, repeat for each. |
| LOOT_389 | 狗头人拾荒者 | Rummaging Kobold | 3 | 1/3 | MINION | 否 | 狗头人拾荒者 | <b>战吼：</b>将你的一把被摧毁的武器置入你的手牌。 | <b>Battlecry:</b> Return one of your destroyed weapons to your hand. |
| RLK_915 | 琥珀雏龙 | Amber Whelp | 3 | 3/3 | MINION | 否 | 琥珀雏龙 | <b>战吼：</b>如果你的手牌中有龙牌，则造成3点伤害。 | <b>Battlecry:</b> If you're holding a Dragon, deal 3 damage. |
| ETC_209 | 硬核信徒 | Hardcore Cultist | 3 | 2/1 | MINION | 否 | 硬核信徒 | <b>战吼：</b>造成2点伤害。<b>压轴：</b>改为对所有敌人。 | <b>Battlecry:</b> Deal 2 damage. <b>Finale:</b> To all enemies. |
| AV_126 | 碉堡中士 | Bunker Sergeant | 3 | 2/4 | MINION | 否 | 碉堡中士 | <b>战吼：</b>如果你的对手拥有2个或者更多随从，对所有敌方随从造成1点伤害。 | [x]<b>Battlecry:</b> If your opponent has 2 or more minions, deal 1 damage to all enemy minions. |
| TOY_520 | 秘迹观测者 | Observer of Mysteries | 3 | 2/2 | MINION | 否 | 秘迹观测者 | <b>战吼：</b> 随机施放2个<b>奥秘</b>。在你的回合开始时，摧毁这些奥秘。 | <b>Battlecry:</b> Cast 2 random <b>Secrets</b>. At the start of your turn, destroy them. |
| TID_002 | 自然使徒 | Herald of Nature | 3 | 3/3 | MINION | 否 | 自然使徒 | <b>战吼：</b>如果你在本牌在你手中时施放过自然法术，使你的其他随从获得+1/+1。 | <b>Battlecry:</b> If you've cast a Nature spell while holding this, give your other minions +1/+1. |
| GDB_132 | 躁动的愤怒卫士 | Relentless Wrathguard | 3 | 4/2 | MINION | 否 | 躁动的愤怒卫士 | <b>战吼：</b>对一个敌方随从造成2点伤害。如果该随从死亡，<b>发现</b>一张恶魔牌。 | <b>Battlecry:</b> Deal 2 damage to an enemy minion. If it dies, <b>Discover</b> a Demon. |
| JAIL_998 | 迪菲亚私运者 | JAIL_998 | 3 | - | - | 否 | 迪菲亚私运者：战吼使一个友方随从 +2 攻并获得突袭（预备费由 hand_minion_cost 处理）。 |  |  |
| CORE_SW_072 | 锈烂蝰蛇 | Rustrot Viper | 3 | 3/4 | MINION | 否 | 锈烂蝰蛇 | <b>可交易</b> <b>战吼：</b>摧毁对手的武器。 | [x]<b>Tradeable</b> <b>Battlecry:</b> Destroy your opponent's weapon. |
| TOY_370 | 三芯诡烛 | Triplewick Trickster | 4 | 2/3 | MINION | 是 | 三芯诡烛 | <b>战吼：</b>随机对一个敌人造成2点伤害，触发三次。 | <b>Battlecry:</b> Deal 2 damage to a random enemy, three times. |
| TIME_875 | 半兽人迦罗娜 | Garona Halforcen | 4 | 5/4 | MINION | 否 | 半兽人迦罗娜 | <b>奇闻</b> <b>战吼：</b>如果莱恩国王在对手手牌中，将其摧毁并将敌方英雄的生命值砍半。 | [x]<b>Fabled</b>. <b>Battlecry:</b> If your opponent is holding King Llane, destroy him and cut their Health in half. |
| JAM_014 | 后台保镖 | Backstage Bouncer | 4 | 4/5 | MINION | 否 | 后台保镖 | <b>嘲讽</b>。<b>战吼：</b>将一个友方随从变形成为本随从的复制。 | <b>Taunt</b> <b>Battlecry:</b> Transform a friendly minion into a copy of this. |
| WW_906 | 吵闹的伴侣 | Rowdy Partner | 4 | 4/3 | MINION | 否 | 吵闹的伴侣 | <b>战吼：</b>如果你手牌中有其他法力值消耗为4的牌，造成4点 伤害。 | <b>Battlecry:</b> If you're holding another 4-Cost card, deal 4 damage. |
| BAR_750 | 大地亡魂 | Earth Revenant | 4 | 2/6 | MINION | 否 | 大地亡魂 | <b>嘲讽</b>，<b>战吼：</b>对所有敌方随从造成1点 伤害。 | [x]<b>Taunt</b>  <b>Battlecry:</b> Deal 1 damage to all enemy minions. |
| ONY_024 | 奥妮克希亚幼龙 | Onyxian Drake | 4 | 4/5 | MINION | 否 | 奥妮克希亚幼龙 | <b>嘲讽</b>，<b>战吼：</b>对一个敌方随从造成等同于你的护甲值的伤害。 | [x]<b>Taunt</b>  <b>Battlecry:</b> Deal damage equal to your Armor to an enemy minion. |
| ETC_110 | 封面艺人 | Cover Artist | 4 | 3/3 | MINION | 否 | 封面艺人 | <b>战吼：</b>变形成为一个随从的3/3的复制。 | <b>Battlecry:</b> Transform into a 3/3 copy of a minion. |
| MEND_302 | 废土先锋 | Wasteland Vanguard | 4 | 3/3 | MINION | 是 | 废土先锋 | <b>战吼：</b>造成3点伤害，分配到所有敌人身上。如果有敌人死亡，再造成3点。 | [x]<b>Battlecry:</b> Deal 3 damage split among all enemies. If any die, deal 3 more. |
| VAC_341 | 断生鱿鱼 | Undercooked Calamari | 4 | 3/4 | MINION | 否 | 断生鱿鱼 | <b>战吼：</b>消灭一个攻击力小于或等于本随从的敌方随从。 | [x]<b>Battlecry:</b> Destroy an enemy minion with Attack less than or equal to this minion's. |
| BAR_840 | 旋风争斗者 | Whirling Combatant | 4 | 3/6 | MINION | 否 | 旋风争斗者 | <b>战吼，暴怒：</b> 对所有其他随从造成1点伤害。 | [x]<b>Battlecry and Frenzy:</b> Deal 1 damage to all other minions. |
| TIME_019 | 时间流具象 | Manifested Timeways | 4 | 3/3 | MINION | 否 | 时间流具象 | <b>战吼：</b>如果你控制着光环，对所有敌人造成3点伤害。 | <b>Battlecry:</b> If you control an Aura, deal 3 damage to all enemies. |
| WW_820 | 棘尾幼龙 | Spinetail Drake | 4 | 5/4 | MINION | 否 | 棘尾幼龙 | <b>战吼：</b> 如果你的手牌中有龙牌，则对一个敌方随从造成5点伤害。 | <b>Battlecry:</b> If you're holding a Dragon, deal 5 damage to an enemy minion. |
| TOY_513 | 沙画元素 | Sand Art Elemental | 4 | 4/4 | MINION | 否 | 沙画元素：+1 攻风怒 + 召唤 4/4。 | <b>微缩</b> <b>战吼：</b>在本回合中，使你的英雄获得+1攻击力和<b>风怒</b>。 | [x]<b>Miniaturize</b> <b>Battlecry:</b> Give your hero +1 Attack and <b>Windfury</b> this turn. |
| GDB_434 | 流彩巨岩 | Bolide Behemoth | 4 | 3/6 | MINION | 否 | 流彩巨岩 | <b>战吼：</b>在本局对战中，你的小行星造成的伤害增加1点。<b><b>法术迸发</b>：</b>将3张小行星洗入你的牌库。 | [x]<b>Battlecry:</b> Your Asteroids deal 1 more damage this game. <b><b>Spellburst</b>:</b> Shuffle 3 of them into your deck. |
| BT_717 | 潜地蝎 | Burrowing Scorpid | 4 | 5/2 | MINION | 否 | 潜地蝎 | <b>战吼：</b>造成2点伤害。如果消灭了目标，则获得<b>潜行</b>。 | [x]<b>Battlecry:</b> Deal 2 damage. If that kills the target, gain <b>Stealth</b>. |
| VAC_442 | 燃灯元素 | Lamplighter | 4 | 4/3 | MINION | 否 | 燃灯元素 | <b>战吼：</b>造成1点伤害<i>（每有一个你使用过元素牌的连续的回合，伤害都会提升）</i>。 | <b>Battlecry:</b> Deal 1 damage <i>(Improved by each turn in a row you've played an Elemental)</i>. |
| CORE_SW_066 | 王室图书管理员 | Royal Librarian | 4 | 4/4 | MINION | 否 | 王室图书管理员 | <b>可交易</b> <b>战吼：</b><b>沉默</b>一个 随从。 | [x]<b>Tradeable</b> <b>Battlecry:</b> <b>Silence</b> a minion. |
| CORE_EX1_005 | 王牌猎人 | Big Game Hunter | 4 | 4/2 | MINION | 否 | 王牌猎人 | <b>可交易</b> <b>战吼：</b>消灭一个攻击力大于或等于7的随从。 | [x]<b>Tradeable</b> <b>Battlecry:</b> Destroy a minion with 7 or more Attack. |
| TOY_642 | 球霸野猪人 | Ball Hog | 4 | 3/3 | MINION | 否 | 球霸野猪人 | <b>吸血</b>。<b>战吼，亡语：</b>对生命值最低的敌人造成3点伤害。 | [x]<b>Lifesteal</b> <b>Battlecry and Deathrattle:</b> Deal 3 damage to the lowest Health enemy. |
| LOOT_410 | 破晓之龙 | Duskbreaker | 4 | 3/3 | MINION | 否 | 破晓之龙 | <b>战吼：</b> 如果你的手牌中有龙牌，则对所有其他随从造成3点伤害。 | <b>Battlecry:</b> If you're holding a Dragon, deal 3 damage to all other minions. |
| TOY_504 | 神秘女巫哈加莎 | Hagatha the Fabled | 4 | 4/3 | MINION | 否 | 神秘女巫哈加莎 | <b>战吼：</b>抽两张法力值消耗大于或等于（5）点的法术牌，并将其变形成为会施放对应法术的泥浆怪。 | [x]<b>Battlecry:</b> Draw 2 spells that cost (5) or more. Transform them into Slimes that cast the spells. |
| TOY_388 | 粉笔美术家 | Chalk Artist | 4 | 4/3 | MINION | 否 | 粉笔美术家 | <b>战吼：</b>抽一张随从牌，将其变形成为随机<b>传说</b>随从牌<i>（保留其原始属性值和法力值消耗）</i>。 | [x]<b>Battlecry:</b> Draw a minion. Transform it into a random  <b>Legendary</b> one <i>(keeping its   original stats and Cost)</i>. |
| SCH_513 | 脆骨破坏者 | Brittlebone Destroyer | 4 | 3/3 | MINION | 否 | 脆骨破坏者 | <b>战吼：</b>在本回合中，如果你的英雄的生命值发生变化，消灭一个随从。 | [x]<b>Battlecry:</b> If your hero's Health changed this turn, destroy a minion. |
| TTN_458 | XB-488清理机器人 | XB-488 Disposalbot | 5 | 3/2 | MINION | 是 | XB-488清理机器人 | <b>战吼：</b>造成5点伤害，随机分配到所有敌方随从身上。<b>锻造：</b>获得<b>吸血</b>。 | <b>Battlecry:</b> Deal 5 damage randomly split among all enemy minions. <b>Forge:</b> Gain <b>Lifesteal</b>. |
| GDB_226 | 凶恶的入侵者 | Hostile Invader | 5 | 3/5 | MINION | 否 | 凶恶的入侵者 | <b>战吼，<b>法术迸发</b>， 亡语：</b>对所有其他随从造成2点伤害。 | <b>Battlecry, <b>Spellburst</b>, and Deathrattle:</b> Deal 2 damage to all other minions. |
| AV_313 | 可怕的憎恶 | Hollow Abomination | 5 | 2/8 | MINION | 否 | 可怕的憎恶 | <b>战吼：</b>对所有敌方随从造成1点伤害。<b>荣誉消灭：</b>获得目标随从的攻击力。 | [x]<b>Battlecry:</b> Deal 1 damage to all enemy minions. <b>Honorable Kill:</b> Gain the minion's Attack. |
| TOY_341 | 恋旧的小丑 | Nostalgic Clown | 5 | 6/5 | MINION | 否 | 恋旧的小丑 | <b>微缩</b> <b>战吼：</b>如果你在本牌在你手中时使用过法力值消耗更高的牌，造成4点伤害。 | [x]<b>Miniaturize</b> <b>Battlecry:</b> If you've played a higher Cost card while holding this, deal 4 damage. |
| DRG_076 | 无面腐蚀者 | Faceless Corruptor | 5 | 5/4 | MINION | 否 | 无面腐蚀者：打出本体 5/4 突袭，并将一个友方随从变形为 5/4 突袭复制（不触发亡语）。 | <b>突袭</b>。<b>战吼：</b>将你的一个随从变形成为本随从的复制。 | [x]<b>Rush</b>. <b>Battlecry:</b> Transform one of your minions into a copy of this. |
| TIME_EVENT_998 | 时光卫士露妮 | Runi, Temporal Guardian | 5 | 5/5 | MINION | 否 | 时光卫士露妮 | <b>战吼：</b>将你手牌中的所有随从牌送入2回合后的未来。这些牌返回时会具有+5/+5。 | [x]<b>Battlecry:</b> Send all minions in your hand 2 turns into the future. They return with +5/+5. |
| TOY_101 | 暗夜精灵女猎手 | Night Elf Huntress | 5 | 3/3 | MINION | 否 | 暗夜精灵女猎手：对三个不同敌人各 3 伤（随从/英雄均可，互不重复）。 | <b>战吼：</b>对三个不同的敌人各造成3点伤害。<i>（目标由你选定！）</i> | [x]<b>Battlecry:</b> Deal 3 damage to three different enemies. <i>(You pick the targets!)</i> |
| END_035 | 末世之兆 | Omen of the End | 5 | 5/5 | MINION | 否 | 末世之兆 | <b>战吼：</b>如果你的牌库中没有牌，摧毁敌方牌库顶的五张牌。 | [x]<b>Battlecry:</b> If your deck is empty, destroy the top 5  cards of the enemy deck. |
| ONY_035 | 死亡之翼的子嗣 | Spawn of Deathwing | 5 | 6/6 | MINION | 是 | 死亡之翼的子嗣 | <b>战吼：</b>随机消灭一个敌方随从。随机弃一张牌。 | <b>Battlecry:</b> Destroy a random enemy minion. Discard a random card. |
| TOY_375 | 滑冰元素 | Sleet Skater | 5 | 3/4 | MINION | 否 | 滑冰元素 | <b>微缩</b> <b>战吼：</b><b>冻结</b>一个敌方随从，获得等同于其攻击力的护甲值。 | <b>Miniaturize</b> <b>Battlecry:</b> <b>Freeze</b> an enemy minion. Gain Armor equal to its Attack. |
| DMF_101 | 焰火元素 | Firework Elemental | 5 | 3/5 | MINION | 否 | 焰火元素 | <b>战吼：</b>对一个随从造成3点伤害。<b>腐蚀：</b>改为12点。 | [x]<b>Battlecry:</b> Deal 3 damage to a minion. <b>Corrupt:</b> Deal 12 instead. |
| TOY_813 | 玩具队长塔林姆 | Toy Captain Tarim | 5 | 3/7 | MINION | 否 | 玩具队长塔林姆 | <b>微缩</b> <b>嘲讽</b>。<b>战吼：</b>将一个随从的攻击力和生命值变为与本随从相同。 | [x]<b>Miniaturize</b> <b>Taunt</b>. <b>Battlecry:</b> Set a minion's Attack and Health to this minion's. |
| REV_013 | 石裔指控者 | Stoneborn Accuser | 5 | 5/5 | MINION | 否 | 石裔指控者 | <b>注能（5）：</b>获得“<b>战吼：</b>造成5点伤害。” | [x]<b>Infuse (5):</b> Gain "<b>Battlecry:</b> Deal 5 damage." |
| YOG_519 | 腐化残渣 | Tainted Remnant | 5 | 7/4 | MINION | 是 | 腐化残渣 | <b>战吼：</b>如果你在上个回合使用过元素牌，则造成7点伤害，随机分配到所有敌人身上。 | [x]<b>Battlecry:</b> If you played an Elemental last turn, deal 7 damage randomly split between all enemies. |
| BAR_848 | 荷塘潜伏者 | Lilypad Lurker | 5 | 5/6 | MINION | 否 | 荷塘潜伏者 | <b>战吼：</b>如果你在上个回合使用过元素牌，则将一个敌方随从变形成为一只0/1并具有<b>嘲讽</b>的青蛙。 | [x]<b>Battlecry:</b> If you played an Elemental last turn, transform an enemy minion into a 0/1 Frog with <b>Taunt</b>. |
| AV_222 | 话痨奥术师 | Spammy Arcanist | 5 | 3/4 | MINION | 否 | 话痨奥术师 | <b>战吼：</b>对所有其他随从造成1点伤害。如果有随从死亡，则重复此效果。 | [x]<b>Battlecry:</b> Deal 1 damage to all other minions. If any die, repeat this. |
| LOOT_161 | 食肉魔块 | Carnivorous Cube | 5 | 4/6 | MINION | 否 | 食肉魔块 | <b>战吼：</b> 消灭一个友方随从。 <b>亡语：</b>召唤两个被消灭随从的复制。 | <b>Battlecry:</b> Destroy a friendly minion. <b>Deathrattle:</b> Summon 2 copies of it. |
| CATA_552 | 乌鳞斥候 | Ebonscale Scout | 6 | 4/4 | MINION | 否 | 乌鳞斥候 | <b>战吼：</b>造成等同于本随从攻击力的伤害。<i>（当本牌在你手中时，使用一张龙牌即可将本牌变为8/8的龙！）</i> | [x]<b>Battlecry:</b> Deal damage equal to this minion's Attack. <i>(While in hand, play a Dragon to  become an 8/8 Dragon!)</i> |
| REV_934 | 屠戮者奥格拉 | Decimator Olgra | 6 | 3/7 | MINION | 否 | 屠戮者奥格拉：受伤随从数 → +1/+1，对所有敌人攻击。 | <b>战吼：</b>每有一个受伤的随从，便获得+1/+1，然后攻击所有敌人。 | [x]<b>Battlecry:</b> Gain +1/+1 for each damaged minion,  then attack all enemies. |
| WW_434 | 日斑巨龙 | Sunspot Dragon | 6 | 6/6 | MINION | 否 | 日斑巨龙 WW_434：快枪（POWERED_UP=本回合抽到）造成 6 伤 + 6/6 吸血。 | <b>可交易</b> <b>吸血</b>。<b>快枪：</b>造成6点伤害。 | [x]<b>Tradeable</b>, <b>Lifesteal</b> <b>Quickdraw:</b> Deal 6 damage. |
| TIME_714 | 时光领主埃博克 | Chrono-Lord Epoch | 6 | 7/5 | MINION | 否 | 时光领主埃博克 | <b>战吼：</b>消灭你的对手上回合使用的 所有随从。 | <b>Battlecry:</b> Destroy all minions that your opponent played last turn. |
| CORE_CS2_042 | 火元素 | Fire Elemental | 6 | 6/5 | MINION | 否 | 火元素 CS2_042：战吼造成3/4点伤害（可打脸或解嘲讽）。 | <b>战吼：</b>造成4点伤害。 | <b>Battlecry:</b> Deal 4 damage. |
| CS2_042 | 火元素 | Fire Elemental | 6 | 6/5 | MINION | 否 | 火元素 CS2_042：战吼造成3/4点伤害（可打脸或解嘲讽）。 | <b>战吼：</b>造成4点伤害。 | <b>Battlecry:</b> Deal 4 damage. |
| VAN_CS2_042 | 火元素 | Fire Elemental | 6 | 6/5 | MINION | 否 | 火元素 CS2_042：战吼造成3/4点伤害（可打脸或解嘲讽）。 | <b>战吼：</b>造成3点伤害。 | <b>Battlecry:</b> Deal 3 damage. |
| WW_346 | 爆破龟 | Blast Tortoise | 6 | 2/7 | MINION | 否 | 爆破龟 | <b>嘲讽</b>。<b>战吼：</b>对所有敌方随从造成等同于本随从攻击力的伤害。 | [x]<b>Taunt</b> <b>Battlecry:</b> Deal damage to all enemy minions equal to this minion's Attack. |
| MAW_033 | 被告希尔瓦娜斯 | Sylvanas, the Accused | 6 | 5/5 | MINION | 否 | 被告希尔瓦娜斯 | <b>战吼：</b>消灭一个敌方随从。<b>注能（7）：</b>改为夺取其控制权。 | [x]<b>Battlecry:</b> Destroy an enemy minion. <b>Infuse (7):</b> Take control of it instead. |
| CORE_ULD_165 | 裂隙屠夫 | Riftcleaver | 6 | 7/5 | MINION | 否 | 裂隙屠夫 | <b>战吼：</b>消灭一个随从。你的英雄受到等同于该随从生命值的 伤害。 | <b>Battlecry:</b> Destroy a minion. Your hero takes damage equal to its Health. |
| CORE_RLK_505 | 髓骨使御者 | Marrow Manipulator | 6 | 5/5 | MINION | 是 | 髓骨使御者 | <b>战吼：</b>消耗最多5份<b>残骸</b>。每消耗一份残骸，随机对一个敌人造成2点伤害。 | [x]<b>Battlecry:</b> Spend up to 5 <b>Corpses</b>. Deal 2 damage to a random enemy for each. |
| TIME_004 | 时光流汇扫荡者 | Conflux Crasher | 7 | 7/7 | MINION | 是 | 时光流汇扫荡者 | <b>回溯</b>。<b>战吼：</b>随机对一个敌人造成7点 伤害。 | <b>Rewind</b> <b>Battlecry:</b> Deal 7 damage to a random enemy. |
| EDR_464 | 泰兰德 | Tyrande | 7 | 5/7 | MINION | 否 | 泰兰德：5/7；下三张法术双倍施放由 spell_board 处理。 | <b>战吼：</b> 你使用的下三张法术牌会施放两次。 | <b>Battlecry:</b> The next 3 spells you play cast twice. |
| RLK_593 | 洛瑟玛·塞隆 | Lor'themar Theron | 7 | 7/7 | MINION | 否 | 洛瑟玛·塞隆 | <b>战吼：</b> 使你牌库中所有随从牌的属性值翻倍。 | <b>Battlecry:</b> Double the stats of all minions in your deck. |
| WW_026 | 灾变飓风斯卡尔 | Skarr, the Catastrophe | 7 | 7/7 | MINION | 否 | 灾变飓风斯卡尔 | <b>战吼：</b>对所有敌人造成1点伤害<i>（每有一个你使用过元素牌的连续的回合，伤害都会提升）</i>。 | [x]<b>Battlecry:</b> Deal 1 damage to all enemies <i>(improved by each turn in a row you've  played an Elemental)</i>. |
| TSC_064 | 蛇行死鳞纳迦 | Slithering Deathscale | 7 | 5/9 | MINION | 否 | 蛇行死鳞纳迦 | <b>战吼：</b>如果你在本牌在你手中时施放过三个法术，则对所有敌人造成3点伤害。@<i>（还剩{0}个！）</i>@<i>（已经就绪！）</i> | <b>Battlecry:</b> If you've cast three spells while holding this, deal 3 damage to all enemies.@ <i>({0} left!)</i>@ <i>(Ready!)</i> |
| ICC_705 | 骨魇 | Bonemare | 7 | 5/5 | MINION | 否 | 骨魇 | <b>战吼：</b>使一个友方随从获得+4/+4和<b>嘲讽</b>。 | <b>Battlecry:</b> Give a friendly minion +4/+4 and <b>Taunt</b>. |
| GDB_855 | 吞星兽 | Star Grazer | 8 | 8/8 | MINION | 否 | 吞星兽：8/8 嘲讽；法术迸发 +8 攻由 spell_board 处理。 | <b>扰魔。嘲讽</b> <b>法术迸发：</b>使你的英雄获得本回合中的+8攻击力，并获得8点护甲值。 | <b>Elusive, Taunt</b> <b>Spellburst:</b> Give your hero +8 Attack this turn and gain 8 Armor. |
| CORE_UNG_848 | 始生幼龙 | Primordial Drake | 8 | 4/8 | MINION | 否 | 始生幼龙 | <b>嘲讽，战吼：</b> 对所有其他随从造成2点伤害。 | [x]<b>Taunt</b> <b>Battlecry:</b> Deal 2 damage to all other minions. |
| TID_716 | 潮汐亡魂 | Tidal Revenant | 8 | 5/8 | MINION | 否 | 潮汐亡魂 | <b>战吼：</b>造成5点伤害。获得8点护甲值。 | <b>Battlecry:</b> Deal 5 damage. Gain 8 Armor. |
| TIME_EVENT_301 | 灭世信徒 | Disciple of Demise | 8 | 8/8 | MINION | 是 | 灭世信徒 | <b>战吼：</b>随机消灭一个 其他随从。你手牌中每有一张龙牌，重复一次。 | [x]<b>Battlecry:</b> Randomly destroy another minion. Repeat for each Dragon you're holding. |
| END_034 | 碎裂扫荡者 | Crumblecrusher | 8 | 8/6 | MINION | 否 | 碎裂扫荡者 | <b>战吼：</b>随机消灭敌方随从，地标和武器各一个。 | [x]<b>Battlecry:</b> Destroy a random enemy minion, location, and weapon. |
| RLK_741 | 窃魂者 | Soulstealer | 8 | 5/5 | MINION | 否 | 窃魂者 | <b>战吼：</b> 消灭所有其他随从。每消灭一个敌方随从，获得1份<b>残骸</b>。 | [x]<b>Battlecry:</b> Destroy all other minions. Gain 1 <b>Corpse</b> for each enemy destroyed. |
| TOY_357 | 抱龙王噗鲁什 | King Plush | 9 | 6/6 | MINION | 否 | 抱龙王噗鲁什 | <b>冲锋</b>。<b>战吼：</b>将所有攻击力小于本随从的随从移回其拥有者的牌库。 | [x]<b>Charge</b> <b>Battlecry:</b> Return all minions with less Attack than this   to their owner's decks. |
| CATA_201 | 暮光主母 | Twilight Mistress | 9 | 4/12 | MINION | 否 | 暮光主母 | <b>战吼：</b>将所有敌方随从移回其拥有者的 手牌。 | <b>Battlecry:</b> Return all enemy minions to their owner's hand. |
| TIME_890 | 圣者麦迪文 | Medivh the Hallowed | 10 | 7/7 | MINION | 否 | 圣者麦迪文 | <b>奇闻</b> 如果你控制着卡拉赞，本牌的法力值消耗为（0）点。<b>战吼：</b><b>沉默</b>并消灭所有其他随从。 | [x]<b>Fabled</b>. Costs (0) if you control Karazhan. <b>Battlecry:</b> <b>Silence</b> and destroy all other minions. |
| CORE_REV_906 | 德纳修斯大帝 | Sire Denathrius | 10 | 10/10 | MINION | 是 | 战吼：对敌人分配 N 点伤害（N 随注能增加）；含吸血。 | <b>吸血</b>，<b>战吼：</b>对所有敌人造成总计5点伤害。<b>无限注能（2）：</b>伤害增加1点。 | <b><b>Lifesteal</b>.</b> <b>Battlecry:</b> Deal 5 damage amongst enemies. <b>Endlessly Infuse (2):</b> Deal 1 more. |
| REV_906 | 德纳修斯大帝 | Sire Denathrius | 10 | 10/10 | MINION | 是 | 战吼：对敌人分配 N 点伤害（N 随注能增加）；含吸血。 | <b>吸血</b>，<b>战吼：</b>对所有敌人造成总计5点伤害。<b>无限注能（2）：</b>伤害增加1点。 | <b><b>Lifesteal</b>.</b> <b>Battlecry:</b> Deal 5 damage amongst enemies. <b>Endlessly Infuse (2):</b> Deal 1 more. |
| NEW1_030 | 死亡之翼 | Deathwing | 10 | 12/12 | MINION | 否 | 死亡之翼 | <b>战吼：</b> 消灭所有其他随从，并弃掉你的手牌。 | <b>Battlecry:</b> Destroy all other minions and discard your hand. |
## 突袭随从

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| GDB_141 | 伊瑞尔，希望信标 | Yrel, Beacon of Hope | 0 | 3/3 | MINION | 否 | GDB_141 | <b>突袭</b>。<b>亡语：</b>获取来自更早时间线的三张不同圣契牌！ | [x]<b>Rush</b> <b>Deathrattle:</b> Get three different Librams from an older timeline! |
| DINO_401 | 伟岸的德拉克雷斯 | The Great Dracorex | 0 | 5/12 | MINION | 否 | DINO_401 | <b>突袭</b>。在本随从攻击一个敌方随从后，还会对所有其他敌方随从造成伤害。 | [x]<b>Rush</b> After this attacks an enemy minion, it damages ALL other enemy minions. |
| GDB_322 | 光注魔刃豹 | Lightfused Manasaber | 0 | 6/6 | MINION | 否 | GDB_322 | <b>突袭</b>。<b><b>法术迸发</b>：</b>获得<b>圣盾</b>。 | <b>Rush</b> <b><b>Spellburst</b>:</b> Gain <b>Divine Shield</b>. |
| CATA_493 | 地狱公爵 | Duke of Below | 0 | 2/2 | MINION | 否 | CATA_493 | <b>突袭</b>。在本局对战中，你每弃掉一张牌，便拥有+2/+2。 | [x]<b>Rush</b> Has +2/+2 for each card you've discarded this game. |
| TLC_240 | 填鳃暴龙 | Tyrannogill | 0 | 6/3 | MINION | 否 | TLC_240 | <b>突袭</b>。<b>亡语：</b> 召唤三个2/1的鱼人，使其各获得一项随机<b>额外效果</b>。 | [x]<b>Rush</b> <b>Deathrattle:</b> Summon three 2/1 Murlocs. Give them each a random <b>Bonus Effect</b>. |
| CATA_469 | 多彩龙巢母 | Chromatic Broodmother | 0 | 2/5 | MINION | 否 | CATA_469 | <b>突袭</b>。每当本随从 攻击时，复原等同于本随从攻击力的法力水晶。 | [x]<b>Rush</b>   Whenever this attacks, refresh Mana Crystals equal    to this minion's Attack. |
| CATA_153 | 奥拉基尔，风暴之主 | Al'Akir, Lord of Storms | 0 | 2/8 | MINION | 否 | CATA_153 | <b>巨型+2 <b>突袭。</b>风怒。</b><b>战吼：</b>获取2张法力值消耗等同于本随从攻击力的随从牌，这两张牌的法力值消耗为（1）点。 | [x]<b>Colossal +2, <b>Rush</b>, Windfury</b> <b>Battlecry:</b> Get 2 minions with Cost equal to this minion's Attack. They cost (1). |
| BT_487 | 巨型大恶魔 | Hulking Overfiend | 0 | 5/10 | MINION | 否 | BT_487 | <b>突袭</b> 在本随从攻击并消灭一个随从后，可再次攻击。 | <b>Rush</b>. After this attacks and kills a minion, it may attack again. |
| EDR_421 | 年兽 | Omen | 0 | 6/12 | MINION | 否 | EDR_421 | <b>突袭</b>。<b>风怒</b> <b>亡语：</b>对所有敌人造成1点伤害。<i>（在本随从攻击后提升！）</i> | [x]<b>Rush</b>, <b>Windfury</b> <b>Deathrattle:</b> Deal 1 damage to all enemies. <i>(Improves after this attacks!)</i> |
| TOY_312 | 恋旧的侏儒 | Nostalgic Gnome | 0 | 4/4 | MINION | 否 | TOY_312 | <b>微缩</b> <b>突袭</b>。在本随从在你的回合中造成了刚好消灭目标的伤害后，抽一张牌。 | [x]<b>Miniaturize</b> <b>Rush</b>. After this minion deals exact lethal damage on your turn, draw a card. |
| VAC_514 | 恐惧猎犬训练师 | Dreadhound Handler | 0 | 2/2 | MINION | 否 | VAC_514 | <b>突袭</b>。<b>亡语：</b>召唤一只1/1并具有<b>复生</b>的恐惧猎犬。 | [x]<b>Rush</b> <b>Deathrattle:</b> Summon a 1/1 Dreadhound with <b>Reborn</b>. |
| YOG_506 | 扭曲的霜翼龙 | Twisted Frostwing | 0 | 3/3 | MINION | 否 | YOG_506 | <b>突袭</b>。<b>亡语：</b>召唤一只属性值等同于本随从攻击力的奇美拉。 | [x]<b>Rush</b> <b>Deathrattle:</b> Summon a Chimaera with stats equal to this minion's Attack. |
| VAC_950 | 抱石伙伴 | Bouldering Buddy | 0 | 6/7 | MINION | 否 | VAC_950 | <b>突袭。嘲讽</b> 如果你拥有至少十个法力水晶，则法力值消耗为（1）点。 | [x]<b>Rush, Taunt</b> Costs (1) if you have at least 10 Mana Crystals. |
| TLC_366 | 掠食飞翼龙 | Pterrorwing Ravager | 0 | 7/5 | MINION | 否 | TLC_366 | <b>突袭</b>。<b>延系：</b>法力值消耗减少（2）点。 | <b>Rush</b> <b>Kindred:</b> Costs (2) less. |
| TLC_630 | 格里什异种虫 | Gorishi Wasp | 0 | 2/7 | MINION | 否 | TLC_630 | <b>突袭</b>。每当本随从受到伤害，获取一张法力值消耗为（1）的格里什毒刺虫。 | <b>Rush</b>. Whenever this takes damage, get a 1-Cost Gorishi Stinger. |
| TLC_243 | 涡流风暴幼龙 | Whirling Stormdrake | 0 | 8/8 | MINION | 否 | TLC_243 | <b>突袭</b>。<b>风怒</b> <b>延系：</b>在本回合中获得<b>免疫</b>。 | <b>Rush</b>, <b>Windfury</b> <b>Kindred:</b> Gain <b>Immune</b> this turn. |
| TSC_007 | 潜水跳板船员 | Gangplank Diver | 0 | 6/4 | MINION | 否 | TSC_007 | <b>休眠</b>1回合。<b>突袭</b>。攻击时具有<b>免疫</b>。 | <b>Dormant</b> for 1 turn. <b>Rush</b>. <b>Immune</b> while attacking. |
| TIME_029 | 灾毁迅疾幼龙 | Ruinous Velocidrake | 0 | 5/5 | MINION | 否 | TIME_029 | <b>突袭</b>。<b>战吼：</b>从你的牌库中施放一张时空撕裂以召唤一个本随从的复制。 | [x]<b>Rush</b> <b>Battlecry:</b> Cast a Shred  of Time from your deck to    summon a copy of this. |
| TTN_042 | 独眼突击者 | Cyclopian Crusher | 0 | 3/3 | MINION | 否 | TTN_042 | <b>突袭</b>。<b>锻造：</b>获得+3/+2。 | <b>Rush</b> <b>Forge:</b> Gain +3/+2. |
| TOY_356 | 玩具暴龙 | Toyrannosaurus | 0 | 7/7 | MINION | 否 | TOY_356 | <b>突袭</b> <b>亡语：</b>随机对一个敌人造成7点伤害。 | <b>Rush</b> <b>Deathrattle:</b> Deal 7 damage to a random enemy. |
| BAR_896 | 石槌掌锚手 | Stonemaul Anchorman | 0 | 4/6 | MINION | 否 | BAR_896 | <b>突袭</b>，<b>暴怒：</b>抽一张牌。 | [x]<b>Rush</b> <b>Frenzy:</b> Draw a card. |
| REV_352 | 石缚加尔贡 | Stonebound Gargon | 0 | 3/5 | MINION | 否 | REV_352 | <b>突袭</b>，<b>注能（3）：</b>同时对其攻击目标相邻的随从造成伤害。 | [x]<b>Rush</b> <b>Infuse (3):</b> Also damages the minions next to   whomever this attacks. |
| WW_326 | 矿车巡逻兵 | Minecart Cruiser | 0 | 4/5 | MINION | 否 | WW_326 | <b>突袭</b>。<b>过载：</b>（2）。<b>战吼：</b>如果你在上个回合使用过元素牌，则本牌不会<b>过载</b>。 | [x]<b>Rush</b>, <b>Overload:</b> (2) <b>Battlecry:</b> If you played an Elemental last turn, don't <b>Overload</b>. |
| MIS_314 | 积木魔像 | Building-Block Golem | 0 | 6/3 | MINION | 否 | MIS_314 | <b>突袭</b>。<b>亡语：</b>随机召唤三个法力值消耗为（1）的随从。 | [x]<b>Rush</b> <b>Deathrattle:</b> Summon three random 1-Cost minions. |
| TSC_645 | 积雷母舰 | Stormcoil Mothership | 0 | 5/4 | MINION | 否 | TSC_645 | <b>突袭</b>。<b>亡语：</b>随机召唤两个法力值消耗小于或等于（3）点的 机械。 | <b>Rush</b> <b>Deathrattle:</b> Summon two random Mechs that cost (3) or less. |
| TTN_466 | 米诺陶牛头人 | Minotauren | 0 | 5/5 | MINION | 否 | TTN_466 | <b>突袭</b> 每当本随从造成伤害时，获得等量的护甲值。 | [x]<b>Rush</b> Whenever this minion deals damage, gain that much Armor. |
| WORK_015 | 精魂商贩 | Spirit Peddler | 0 | 6/6 | MINION | 否 | WORK_015 | <b>突袭</b>。<b>亡语：</b>随机使你手牌中的一张随从牌的法力值消耗减少（6）点。 | [x]<b>Rush</b> <b>Deathrattle:</b> Reduce the Cost of a random minion in your hand by (6). |
| RLK_604 | 索利贝洛尔 | Thori'belore | 0 | 4/4 | MINION | 否 | RLK_604 | <b>突袭</b>。<b>亡语：</b>进入<b>休眠</b>状态。施放一个火焰法术以复活索利贝 洛尔！ | [x]<b>Rush</b>. <b>Deathrattle:</b> Go <b>Dormant</b>. Cast a Fire spell to revive Thori'belore! |
| EDR_486 | 纵火眼魔 | Scorching Observer | 0 | 7/9 | MINION | 否 | EDR_486 | <b>突袭</b>。<b>吸血</b> | <b>Rush</b> <b>Lifesteal</b> |
| TSC_945 | 艾萨拉的刃豹 | Azsharan Saber | 0 | 4/3 | MINION | 否 | TSC_945 | <b>突袭</b>，<b>亡语：</b>将一张沉没的刃豹置于你的牌库底。 | [x]<b><b>Rush</b>.</b> <b>Deathrattle:</b> Put a 'Sunken Saber' on the bottom of your deck. |
| SW_431 | 花园猎豹 | Park Panther | 0 | 4/4 | MINION | 否 | SW_431 | <b>突袭</b> 每当本随从攻击时，使你的英雄在本回合中获得+3攻击力。 | [x]<b>Rush</b>. Whenever this attacks, give your hero +3 Attack this turn. |
| WW_825 | 落日灵龙菲伊 | Fye, the Setting Sun | 0 | 4/12 | MINION | 否 | WW_825 | <b>突袭</b>。<b>吸血</b>。<b>嘲讽</b>。在本局对战中，你每召唤一条龙，本牌的法力值消耗便减少（1）点。 | [x]<b>Rush</b>, <b>Lifesteal</b>, <b>Taunt</b> Costs (1) less for each Dragon you've summoned this game. |
| TIME_850 | 血斗士洛戈什 | Lo'Gosh, Blood Fighter | 0 | 7/7 | MINION | 否 | TIME_850 | <b>奇闻</b> <b>突袭</b>。<b>亡语：</b>从你的手牌中召唤一位血斗士，使其获得+5/+5并随机攻击一个敌人。 | [x]<b>Fabled</b>, <b>Rush</b>. <b>Deathrattle:</b> Summon a Blood Fighter from your hand. It gains +5/+5 and attacks a random enemy. |
| CORE_BT_156 | 被禁锢的邪犬 | Imprisoned Vilefiend | 0 | 3/5 | MINION | 否 | CORE_BT_156 | <b>休眠</b>2回合。 <b>突袭</b> | <b>Dormant</b> for 2 turns. <b>Rush</b> |
| CATA_525 | 装甲放血纳迦 | Armored Bloodletter | 0 | 3/1 | MINION | 否 | CATA_525 | <b>突袭</b>。<b>战吼：</b><b>兆示</b>{0}。 | <b>Rush</b> <b>Battlecry:</b> <b>Herald</b> {0}. |
| WW_043 | 轮式淤泥怪 | Sludge on Wheels | 0 | 2/5 | MINION | 否 | WW_043 | <b>突袭</b>。每当本随从受到伤害时，获取一张淤泥桶并将一张淤泥桶置于你的牌库底。 | [x]<b>Rush</b>. Whenever this takes damage, get a Barrel of Sludge and add one to the bottom of your deck. |
| RLK_913 | 达库鲁大王 | Overlord Drakuru | 0 | 6/8 | MINION | 否 | RLK_913 | <b>突袭</b>，<b>风怒</b>。 在本随从攻击并消灭随从后，为你复活被消灭的随从。 | [x]<b>Rush</b>, <b>Windfury</b> After this attacks and kills a minion, resurrect it on your side. |
| WW_808 | 银蛇 | Silver Serpent | 0 | 2/3 | MINION | 否 | WW_808 | <b><b>突袭</b>。<b>剧毒</b> 快枪：</b>在本回合中获得<b>免疫</b>。 | <b><b>Rush</b>, <b>Poisonous</b> Quickdraw:</b> Gain <b>Immune</b> this turn. |
| SW_062 | 闪金镇豺狼人 | Goldshire Gnoll | 0 | 5/4 | MINION | 否 | SW_062 | <b>突袭</b> 你每有一张其他手牌，本牌的法力值消耗便减少（1）点。 | [x]<b>Rush</b> Costs (1) less for each   other card in your hand. |
| WW_418 | 食人魔帮歹徒 | Ogre-Gang Outlaw | 0 | 4/4 | MINION | 是 | WW_418 | <b>突袭。</b>50%几率攻击错误的敌人。 | <b>Rush</b> 50% chance to attack the wrong enemy. |
| TIME_209 | 高山之王穆拉丁 | Muradin, High King | 0 | 3/2 | MINION | 否 | TIME_209 | <b>奇闻</b> <b>突袭</b>。<b>战吼：</b>为本随从装备高山之王的战锤！<b>亡语：</b>将该战锤置入你的手牌。 | [x]<b>Fabled</b>, <b>Rush</b>. <b>Battlecry:</b> Bring the High King's Hammer to ME! <b>Deathrattle:</b> Add it to your hand. |
| SW_323 | 鼠王 | The Rat King | 0 | 5/5 | MINION | 否 | SW_323 | <b>突袭</b>，<b>亡语：</b>进入<b>休眠</b>状态。在5个友方随从死亡后复活。 | [x]<b>Rush</b>. <b>Deathrattle:</b> Go <b>Dormant</b>. Revive after 5 friendly minions die. |
| VAC_527 | 龙族美餐 | Draconic Delicacy | 0 | 6/6 | MINION | 否 | VAC_527 | <b>突袭</b>。<b>扰魔</b>。每次只能受到1点伤害。 | <b>Rush</b>, <b>Elusive</b> Can only take 1 damage at a time. |
| JAM_021 | 单曲流星 | One Hit Wonder | 2 | 2/1 | MINION | 否 | 单曲流星 | <b>突袭</b>。<b>连击：</b> 获得<b><b>剧毒</b>。</b> | <b>Rush</b> <b>Combo:</b> Gain <b><b>Poisonous</b>.</b> |
| ETC_742 | 摇滚巨石 | Rolling Stone | 2 | 2/2 | MINION | 否 | 摇滚巨石 | <b>突袭</b>。<b>战吼：</b>如果你使用的上一张牌法力值消耗为（1）点，便获得+1/+1。 | [x]<b>Rush</b> <b>Battlecry:</b> If the last card you played costs (1), gain +1/+1. |
| DMF_523 | 碰碰车 | Bumper Car | 2 | 1/3 | MINION | 否 | 碰碰车 | <b>突袭，亡语：</b>将两张1/1并具有<b>突袭</b>的乘客置入你的手牌。 | <b>Rush</b> <b>Deathrattle:</b> Add two 1/1 Riders with <b>Rush</b> to your hand. |
| CS3_038 | 红鳃锋颚战士 | Redgill Razorjaw | 2 | 3/1 | MINION | 否 | 红鳃锋颚战士 | <b>突袭</b> | <b>Rush</b> |
| ETC_410 | 蛇啮鼓手 | Snakebite | 2 | 1/1 | MINION | 否 | 蛇啮鼓手 | <b>突袭</b>。<b>战吼：</b>在本回合中每有一个随从死亡，便获得+1/+1。0<i>（已死亡0个）</i> | <b>Rush</b> <b>Battlecry:</b> Gain +1/+1 for each minion that died this turn.@ <i>(@)</i> |
| ETC_325 | 音乐治疗师 | Audio Medic | 2 | 2/3 | MINION | 否 | 音乐治疗师 | <b>突袭</b>。<b>压轴：</b>获得<b>吸血</b>。 | <b>Rush</b> <b>Finale:</b> Gain <b>Lifesteal</b>. |
| JAM_027 | 饭圈迷弟 | Fanboy | 2 | 2/2 | MINION | 否 | 饭圈迷弟 | <b>抉择：</b>使一个友方随从获得+2攻击力和<b>突袭</b>；或者+2生命值和<b>吸血</b>。 | [x]<b>Choose One -</b> Give a friendly minion +2 Attack and <b>Rush</b>; or +2 Health and <b>Lifesteal</b>. |
| TOY_823 | 彩虹裁缝 | Rainbow Seamstress | 3 | 3/3 | MINION | 否 | 彩虹裁缝 | <b>战吼：</b>如果你的套牌中有鲜血，冰霜或邪恶符文牌，则对应获得<b>吸血</b>，<b>复生</b>或<b>突袭</b>。 | [x]<b>Battlecry:</b> If your deck started with a Blood, Frost, or Unholy card, gain <b>Lifesteal</b>, <b>Reborn</b>, or <b>Rush</b> respectively. |
| TOY_516 | 折价区海盗 | Bargain Bin Buccaneer | 3 | 3/2 | MINION | 否 | 折价区海盗：亮边（连击）召唤复制。 | <b>突袭</b>。<b>连击：</b>召唤一个本随从的复制。 | <b>Rush</b> <b>Combo:</b> Summon a copy of this. |
| ETC_073 | 押韵狂人 | Rhyme Spinner | 3 | 1/3 | MINION | 否 | 押韵狂人 | <b>突袭</b>。<b>连击：</b>在本局对战中，你每使用过一张其他<b>连击</b>牌，便获得+1/+1。0<i>（已使用0张）</i> | [x]<b>Rush</b> <b>Combo:</b> Gain +1/+1 for each other <b>Combo</b> card you've  played this game.@ <i>(@)</i> |
| TIME_063 | 时光之主诺兹多姆 | Timelord Nozdormu | 3 | 8/8 | MINION | 否 | 时光之主诺兹多姆 | <b>休眠</b>5回合。<b>突袭</b>。在你使用一张最新扩展包的牌后，提前1回合唤醒。 | [x]<b>Dormant</b> for 5 turns. <b>Rush</b>. After you play a card from the newest expansion,  awaken 1 turn sooner. |
| TOY_821 | 毛绒暴暴狗 | Rambunctious Stuffy | 3 | 4/2 | MINION | 否 | 毛绒暴暴狗 | <b>突袭</b> 在你施放一个冰霜法术后，获得<b>复生</b>。 | <b>Rush</b> After you cast a Frost spell, gain <b>Reborn</b>. |
| TOY_517 | 泼漆彩鳍鱼人 | Plucky Paintfin | 3 | 2/3 | MINION | 否 | 泼漆彩鳍鱼人 | <b>剧毒</b>。<b>战吼：</b>抽一张<b>突袭</b>随从牌。 | [x]<b>Poisonous</b> <b>Battlecry:</b> Draw a <b>Rush</b> minion. |
| JAM_033 | 混搭乐师 | Remixed Musician | 3 | 3/3 | MINION | 否 | 混搭乐师 | <b>突袭</b>。在你的手牌中时会获得一项额外效果，该效果每回合都会改变。 | [x]<b>Rush</b> Gains an extra effect in your hand that changes each turn. |
| ETC_408 | 滑铲铁腿 | Power Slider | 3 | 2/3 | MINION | 否 | 滑铲铁腿 | <b>突袭</b>。<b>战吼：</b>在本局对战中，你每使用过一个不同类型的随从牌，便获得+1/+1。0<i>（已使用0个）</i> | [x]<b>Rush</b>. <b>Battlecry:</b> Gain +1/+1 for each minion of a different type you've played this game.@ <i>(@)</i> |
| TOY_811 | 绒绒虎 | Tigress Plushy | 3 | 3/2 | MINION | 否 | 绒绒虎 | <b>微缩</b> <b>突袭</b>，<b>吸血</b>，<b>圣盾</b> | <b>Miniaturize</b> <b>Rush</b>, <b>Lifesteal</b>, <b>Divine Shield</b> |
| CORE_WC_701 | 邪能响尾蛇 | Felrattler | 3 | 3/2 | MINION | 否 | 邪能响尾蛇 | <b>突袭</b>，<b>亡语：</b>对所有敌方随从造成 1点伤害。 | [x]<b>Rush</b> <b>Deathrattle:</b> Deal 1 damage to all enemy minions. |
| BT_123 | 卡加斯·刃拳 | Kargath Bladefist | 4 | 4/4 | MINION | 否 | 卡加斯·刃拳 | <b>突袭</b> <b>亡语：</b>将“终极卡加斯”洗入你的牌库。 | [x]<b>Rush</b> <b>Deathrattle:</b> Shuffle 'Kargath Prime' into your deck. |
| ETC_399 | 哈维利亚·墨鸦 | Halveria Darkraven | 4 | 4/3 | MINION | 否 | 哈维利亚·墨鸦 | <b>突袭</b>。在一个友方<b>突袭</b>随从攻击后，使你的随从获得+1攻击力。 | <b>Rush</b> After a friendly <b>Rush</b> minion attacks, give your minions +1 Attack. |
| TTN_713 | 生气的冥狱之犬 | Angry Helhound | 4 | 2/5 | MINION | 否 | 生气的冥狱之犬：2/5 突袭，你的回合 +4 攻。 | <b>突袭</b> 在你的回合拥有+4攻击力。 | <b>Rush</b> Has +4 Attack on your turn. |
| RLK_916 | 胆大的幼龙 | Daring Drake | 4 | 4/4 | MINION | 否 | 胆大的幼龙：手牌有龙则 5/5 否则 4/4 突袭。 | <b>突袭</b>。<b>战吼：</b>如果你的手牌中有龙牌，便获得+1/+1。 | [x]<b>Rush</b> <b>Battlecry:</b> If you're holding a Dragon, gain +1/+1. |
| CORE_TTN_843 | 艾瑞达欺诈者 | Eredar Deceptor | 4 | 3/5 | MINION | 否 | 艾瑞达欺诈者 | 每当你抽一张牌时，召唤一个1/1并具有<b>突袭</b>的恶魔。 | Whenever you draw a card, summon a 1/1 Demon with <b>Rush</b>. |
| ETC_357 | 铜管元素 | Brass Elemental | 4 | 3/3 | MINION | 否 | 铜管元素 | <b>突袭</b>，<b>圣盾</b>，<b>嘲讽</b>，<b>风怒</b> | <b>Rush</b>, <b>Divine Shield</b>, <b>Taunt</b>, <b>Windfury</b> |
| RLK_955 | 银月城军备官 | Silvermoon Armorer | 4 | 4/4 | MINION | 否 | 银月城军备官：法力渴求(7) +2/+2。 | <b>突袭</b>。<b>法力渴求（7）：</b>获得+2/+2。 | [x]<b>Rush</b> <b>Manathirst (7):</b> Gain +2/+2. |
| END_032 | 飞翼畸变体 | Winged Aberration | 4 | 4/4 | MINION | 否 | 飞翼畸变体 | <b>突袭</b>。<b><b>连击：</b>过载（2）</b>以获得<b>风怒</b>和在本回合中的<b>免疫</b>。 | [x]<b>Rush</b> <b><b>Combo:</b> Overload</b> for (2) to gain <b>Immune</b> this turn and <b>Windfury</b>. |
| REV_961 | 势利精英 | Elitist Snob | 5 | 3/4 | MINION | 否 | 势利精英 | <b>战吼：</b>你手牌中每有一张圣骑士牌，便从<b>圣盾</b>，<b>吸血</b>，<b>突袭</b>或<b>嘲讽</b>中获得一项。 | [x]<b>Battlecry:</b> For each Paladin card in your hand, randomly  gain <b>Divine Shield</b>, <b>Lifesteal</b>,  <b>Rush</b>, or <b>Taunt</b>. |
| BOT_548 | 奇利亚斯 | Zilliax | 5 | 3/2 | MINION | 否 | 奇利亚斯 | <b>磁力，圣盾，嘲讽，吸血，突袭</b> | <b>Magnetic</b> <b><b>Divine Shield</b>, <b>Taunt</b>, Lifesteal, Rush</b> |
| MAW_009 | 影犬 | Shadehound | 5 | 6/5 | MINION | 否 | 影犬 | 每当本随从攻击时，使你的其他野兽获得+2/+2。 <b>注能（3只野兽）：</b> 获得<b>突袭</b>。 | [x]Whenever this attacks, give your other Beasts +2/+2. <b>Infuse (3 Beasts):</b> Gain <b>Rush</b>. |
| TOY_894 | 折纸青蛙 | Origami Frog | 5 | 1/4 | MINION | 否 | 折纸青蛙 | <b>突袭</b>。<b>战吼：</b>与另一个随从交换攻击力。 | [x]<b>Rush</b> <b>Battlecry:</b> Swap Attack with another minion. |
| TIME_051 | 永恒龙士兵 | Soldier of the Infinite | 5 | 3/5 | MINION | 否 | 永恒龙士兵 | <b>突袭</b>。<b>战吼：</b>本随从的攻击力翻倍。 | <b>Rush</b> <b>Battlecry:</b> Double this minion's Attack. |
| MIS_306 | 火箭跳蛙 | Rocket Hopper | 5 | 10/10 | MINION | 否 | 火箭跳蛙 | <b>突袭</b>。<b>过载：</b>（4） | <b>Rush</b> <b>Overload:</b> (4) |
| TLC_436 | 重生的翼手龙 | Reanimated Pterrordax | 5 | 4/3 | MINION | 否 | 重生的翼手龙 | <b><b>突袭</b>。吸血</b> 消耗<b>残骸</b>而非 法力值。 | <b><b>Rush</b>, Lifesteal</b> Costs <b>Corpses</b> instead of Mana. |
| BT_720 | 锈骑劫匪 | Ruststeed Raider | 5 | 1/8 | MINION | 否 | 锈骑劫匪：1/8 嘲讽突袭，战吼 +4 攻。 | <b>嘲讽，突袭， 战吼：</b>在本回合获得+4攻击力。 | <b>Taunt</b>, <b>Rush</b> <b>Battlecry:</b> Gain +4 Attack this turn. |
| ETC_035 | 鼓乐独演者 | Drum Soloist | 5 | 5/5 | MINION | 否 | 鼓乐独演者 | <b>嘲讽</b>。<b>战吼：</b>如果你没有控制其他随从，获得+2/+2和<b>突袭</b>。 | [x]<b>Taunt</b> <b>Battlecry:</b> If you control no other minions, gain +2/+2 and <b>Rush</b>. |
| REV_015 | 假面狂欢者 | Masked Reveler | 6 | 4/4 | MINION | 否 | 假面狂欢者 | <b>突袭</b>，<b>亡语：</b>召唤你牌库中另一个随从的2/2的复制。 | [x]<b>Rush</b> <b>Deathrattle:</b> Summon a 2/2 copy of another minion in your deck. |
| DMF_226 | 刀锋舞娘 | Bladed Lady | 6 | 6/6 | MINION | 否 | 刀锋舞娘 | <b>突袭</b> 如果你的英雄的攻击力大于或等于6点，则法力值消耗为（1）点。 | [x]<b>Rush</b> Costs (1) if your hero has 6 or more Attack. |
| MAW_020 | 潦草的书记员 | Scribbling Stenographer | 6 | 4/4 | MINION | 否 | 潦草的书记员 | <b>突袭</b>。在本回合中你每使用过一张牌，本牌的法力值消耗便减少（1）点。 | <b>Rush</b>. Costs (1) less for each card you've played this turn. |
| TIME_050 | 灵知沙漏 | Sentient Hourglass | 6 | 4/9 | MINION | 否 | 灵知沙漏 | <b>突袭</b>。在本随从受到伤害并存活下来后，其攻击力和生命值互换。 | [x]<b>Rush</b> After this minion survives damage, swap its stats. |
| ETC_836 | 穆克拉先生 | Mister Mukla | 6 | 10/10 | MINION | 否 | 穆克拉先生 | <b>突袭</b>。<b>战吼：</b>用香蕉填满你对手的手牌。 | [x]<b>Rush</b>. <b>Battlecry:</b> Fill your opponent's hand with Bananas. |
| TIME_605 | 纪元追猎者 | Epoch Stalker | 6 | 3/4 | MINION | 否 | 纪元追猎者 | <b>突袭</b>。<b>扰魔</b> <b>战吼：</b>召唤一个本随从的复制。 | <b>Rush</b>, <b>Elusive</b> <b>Battlecry:</b> Summon a copy of this. |
| CORE_DRG_079 | 辟法巨龙 | Evasive Wyrm | 6 | 5/4 | MINION | 否 | 辟法巨龙 | <b>突袭</b>。<b>圣盾</b>。<b>扰魔</b> | <b>Rush</b> <b>Divine Shield</b> <b>Elusive</b> |
| JAM_004 | 镂骨恶犬 | Hollow Hound | 6 | 3/4 | MINION | 否 | 镂骨恶犬：吸血突袭顺劈。 | <b>吸血</b>，<b>突袭</b>。同时对其攻击目标相邻的随从造成伤害。 | [x]<b>Lifesteal</b>, <b>Rush</b> Also damages minions next to whomever this attacks. |
| CORE_RLK_657 | 地底虫王 | Underking | 7 | 6/6 | MINION | 否 | 地底虫王 | <b>突袭</b>。<b>战吼，亡语：</b>获得6点护甲值。 | [x]<b>Rush</b> <b>Battlecry and Deathrattle:</b> Gain 6 Armor. |
| REV_316 | 活体利刃蕾茉妮雅 | Remornia, Living Blade | 7 | 5/10 | MINION | 否 | 活体利刃蕾茉妮雅 | <b>突袭</b> 在本随从攻击后，装备它。 | <b>Rush</b> After this attacks, equip it. |
| REV_314 | 灌木巨龙托匹奥 | Topior the Shrubbagazzor | 7 | 5/5 | MINION | 否 | 灌木巨龙托匹奥 | <b>战吼：</b>在本局对战的剩余时间内，在你施放一个自然法术后，召唤一条3/3并具有<b>突袭</b>的雏龙。 | [x]<b>Battlecry:</b> For the rest of the game, after you cast a Nature spell, summon a 3/3 Whelp with <b>Rush</b>. |
| TOY_812 | 皮普希·彩蹄 | Pipsi Painthoof | 7 | 4/4 | MINION | 否 | 皮普希·彩蹄 | <b>亡语：</b>随机从你的牌库中召唤<b>圣盾</b>，<b>突袭</b>和<b>嘲讽</b>随从各一个。 | [x]<b>Deathrattle:</b> Summon a random <b>Divine Shield</b>, <b>Rush</b>, and <b>Taunt</b> minion from your deck. |
| TIME_872 | 不败冠军 | Undefeated Champion | 8 | 13/13 | MINION | 否 | 不败冠军 | <b>突袭</b>。<b>战吼：</b>用随机的法力值消耗为（1）的随从填满你对手的面板。 | [x]<b>Rush</b>. <b>Battlecry:</b> Fill your opponent's board with   random 1-Cost minions. |
| CS3_020 | 伊利达雷审判官 | Illidari Inquisitor | 8 | 8/8 | MINION | 否 | 伊利达雷审判官：8/8 突袭，英雄攻击后跟刀。 | <b>突袭</b> 在你的英雄攻击一个敌人后，本随从也会攻击该敌人。 | <b>Rush</b>. After your hero attacks an enemy, this attacks it too. |
| AV_339 | 圣殿骑士队长 | Templar Captain | 8 | 8/8 | MINION | 否 | 圣殿骑士队长 | <b>突袭</b>。 在本随从攻击一个随从后，召唤一个5/5并具有<b>嘲讽</b>的防御者。 | [x]<b>Rush</b>. After this attacks a minion, summon a 5/5 Defender with <b>Taunt</b>. |
| MAW_030 | 托加斯特管理员 | Torghast Custodian | 8 | 6/10 | MINION | 否 | 托加斯特管理员 | <b>战吼：</b> 每有一个敌方随从，随机从<b>突袭</b>，<b>圣盾</b>或<b>风怒</b>中获得一项。 | [x]<b>Battlecry:</b> For each enemy minion, randomly gain <b>Rush</b>, <b>Divine Shield</b>, or <b>Windfury</b>. |
| ETC_419 | 摇滚缝合怪 | Mish-Mash Mosher | 8 | 3/10 | MINION | 否 | 摇滚缝合怪 | <b>突袭</b>。在本随从攻击后，获得+1攻击力并随机攻击一个敌方随从。 | [x]<b>Rush</b> After this attacks, gain +1 Attack and attack a  random enemy minion. |
| DAL_047 | 活动喷泉 | Walking Fountain | 8 | 4/8 | MINION | 否 | 活动喷泉 | <b>吸血，突袭，风怒</b> | <b>Lifesteal</b>, <b>Rush</b>, <b>Windfury</b> |
| BT_761 | 盘牙督军 | Coilfang Warlord | 8 | 9/5 | MINION | 否 | 盘牙督军 | <b>突袭，亡语：</b>召唤一个5/9并具有<b>嘲讽</b> 的督军。 | [x]<b>Rush</b> <b>Deathrattle:</b> Summon a  5/9 Warlord with <b>Taunt</b>. |
| TIME_022 | 累世巨蛇 | Perennial Serpent | 8 | 7/9 | MINION | 否 | 累世巨蛇 | <b>突袭</b>。如果有<b>休眠</b>的随从，本牌的法力值消耗减少（4）点。 | [x]<b>Rush</b> Costs (4) less if a minion is <b>Dormant</b>. |
| RLK_212 | 安尼赫兰蛮魔 | Brutal Annihilan | 9 | 9/9 | MINION | 否 | 安尼赫兰蛮魔 | <b>嘲讽</b>。<b>突袭</b>。每当本随从受到伤害并存活下来时，对敌方英雄造成等量的伤害。 | [x]<b>Taunt</b>, <b>Rush</b> After this minion survives damage, deal that amount to the enemy hero. |
| ONY_004 | 团本首领奥妮克希亚 | Raid Boss Onyxia | 10 | 8/8 | MINION | 否 | 团本首领奥妮克希亚：8/8 突袭 + 六条 2/1 突袭雏龙。 | <b>突袭</b>。当你控制着雏龙时<b>免疫</b>。<b>战吼：</b>召唤六条2/1并具有<b>突袭</b>的雏龙。 | [x]<b>Rush</b>. <b>Immune</b> while you control a Whelp. <b>Battlecry:</b> Summon six  2/1 Whelps with <b>Rush</b>. |
| MIS_711 | 安全专家 | Safety Expert | 10 | 8/8 | MINION | 否 | 安全专家 | <b>突袭</b>。<b>亡语：</b>将三张“炸弹” 牌洗入你对手的牌库。 | <b>Rush</b>. <b>Deathrattle:</b> Shuffle three Bombs into your opponent's deck. |
| ETC_840 | 班卓龙 | Banjosaur | 10 | 5/6 | MINION | 否 | 班卓龙 | <b>突袭</b>。每当本随从攻击时，抽一张野兽牌并获得其属性值。 | [x]<b>Rush</b> Whenever this attacks, draw a Beast and gain its stats. |
| REV_375 | 石裔干将 | Stoneborn General | 10 | 8/8 | MINION | 否 | 石裔干将 | <b>突袭</b>，<b>亡语：</b>召唤一只8/8并具有<b>突袭</b>的墓翼蝠。 | [x]<b>Rush</b>    <b>Deathrattle:</b> Summon an     8/8 Gravewing with <b>Rush</b>. |
## 武器

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| EDR_842 | 亵渎之矛 | Defiled Spear | 0 | 2/0 | WEAPON | 否 | 亵渎之矛 | 在你的英雄攻击 一个敌人后，随机对另一个敌人造成等同于你的英雄攻击力的伤害。 | [x]After your hero attacks an  enemy, deal your hero's Attack damage to another random enemy. |
| BAR_844 | 前锋战斧 | Outrider's Axe | 0 | 3/0 | WEAPON | 否 | 前锋战斧 | 在你的英雄攻击并消灭一个随从后，抽一张牌。 | After your hero attacks and kills a minion, draw a card. |
| TTN_467 | 匠人之锤 | Craftsman's Hammer | 0 | 3/0 | WEAPON | 否 | 匠人之锤 | 每当你的英雄攻击时，便获得4点 护甲值。 | Whenever your hero attacks, gain 4 Armor. |
| CATA_467 | 命令之爪 | Command Claw | 0 | 2/0 | WEAPON | 否 | 命令之爪 | 在你的英雄攻击后，随机使一个友方随从获得+2攻击力。 | [x]After your hero attacks, give a random friendly minion +2 Attack. |
| TIME_890t | 圣杖埃提耶什 | Atiesh the Greatstaff | 0 | 1/0 | WEAPON | 否 | 圣杖埃提耶什 | 如果你控制着麦迪文，本牌的法力值消耗为（0）点。你的法术的伤害和治疗效果翻倍。 | [x]Costs (0) if you control Medivh. Double the damage and healing of your spells. |
| TIME_020t1 | 塞纳留斯之斧 | Axe of Cenarius | 0 | 3/0 | WEAPON | 否 | 塞纳留斯之斧 | <b>吸血</b>。在你的英雄攻击并消灭一个随从后，抽一张阿古斯传送门。 | [x]<b>Lifesteal</b> After your hero attacks and kills a minion, draw a Portal to Argus. |
| RLK_828 | 奎尔萨拉斯的希望 | Hope of Quel'Thalas | 0 | 4/0 | WEAPON | 否 | 奎尔萨拉斯的希望 | 在你的英雄攻击后，使你的所有随从获得+1/+1<i>（无论它们在哪）</i>。 | [x]After your hero attacks, give your minions +1/+1 <i>(wherever they are).</i> |
| ETC_423 | 奥金利斧 | Arcanite Ripper | 0 | 3/0 | WEAPON | 否 | 奥金利斧 | <b>亡语：</b>召唤一个1/1并具有<b>吸血</b>的亡灵。<i>（装备期间，在你的回合中使你的生命值发生变化以提升此效果！）</i> | [x]<b>Deathrattle:</b> Summon a 1/1 <b>Lifesteal</b> Undead. <i>(Change your Health on your turn while equipped to improve!)</i> |
| YOP_011 | 审判圣契 | Libram of Judgment | 0 | 5/0 | WEAPON | 否 | 审判圣契 | <b>腐蚀：</b>获得<b>吸血</b>。 | <b>Corrupt:</b> Gain <b>Lifesteal</b>. |
| EDR_253 | 巨熊之槌 | Ursine Maul | 0 | 4/0 | WEAPON | 否 | 巨熊之槌 | 在你的英雄攻击后，抽一张牌。 | After your hero attacks, draw a card. |
| TIME_875t1 | 弑君者 | The Kingslayers | 0 | 3/0 | WEAPON | 否 | 弑君者 | 在你的英雄 攻击后，双方玩家各抽一张<b>传说</b>卡牌。 | After your hero attacks, both players draw a <b>Legendary</b> card. |
| CORE_DAL_720 | 摇摆矿锄 | Waggle Pick | 0 | 4/0 | WEAPON | 否 | 摇摆矿锄 | <b>亡语：</b>随机将一个友方随从移回你的手牌。它的法力值消耗减少（2）点。 | [x]<b>Deathrattle:</b> Return a random friendly minion to your hand. It costs (2) less. |
| REV_509 | 放大战刃 | Magnifying Glaive | 0 | 3/0 | WEAPON | 否 | 放大战刃 | 在你的英雄攻击后，抽牌，直到你拥有三张牌。 | [x]After your hero attacks, draw until you have 3 cards. |
| DMF_705 | 敲狼锤 | Whack-A-Gnoll Hammer | 0 | 3/0 | WEAPON | 否 | 敲狼锤 | 在你的英雄攻击后，随机使一个友方随从获得+1/+1。 | After your hero attacks, give a random friendly minion +1/+1. |
| GDB_726 | 斩星巨刃 | Interstellar Starslicer | 0 | 3/0 | WEAPON | 否 | 斩星巨刃 | <b>战吼，亡语：</b>在本局对战中，你的圣契的法力值消耗减少（1）点。 | <b>Battlecry and Deathrattle:</b> Reduce the Cost of your Librams by (1) this game. |
| ETC_521 | 星界键盘 | Cosmic Keyboard | 0 | 0/0 | WEAPON | 否 | 星界键盘 | 在你施放一个法术后，召唤一个属性值等同于其法力值消耗的元素。失去1点耐久度。 | [x]After you cast a spell, summon an Elemental with stats equal to its Cost. Lose 1 Durability. |
| BT_922 | 棕红之翼 | Umberwing | 0 | 1/0 | WEAPON | 否 | 棕红之翼 | <b>战吼：</b>召唤两只1/1的邪翼蝠。 | <b>Battlecry:</b> Summon two 1/1 Felwings. |
| BOT_286 | 死金匕首 | Necrium Blade | 0 | 3/0 | WEAPON | 否 | 死金匕首 | <b>亡语：</b> 随机触发一个友方随从的<b>亡语</b>。 | <b>Deathrattle:</b> Trigger the <b>Deathrattle</b> of a random friendly minion. |
| BT_102 | 沼泽拳刺 | Boggspine Knuckles | 0 | 4/0 | WEAPON | 否 | 沼泽拳刺 | 在你的英雄攻击后，随机将你的所有随从变形成为法力值消耗增加（1）点的随从。 | After your hero attacks, transform your minions into random ones that cost (1) more. |
| REV_933 | 灌能战斧 | Imbued Axe | 0 | 2/0 | WEAPON | 否 | 灌能战斧 | 在你的英雄攻击后，使你受伤的随从获得+1/+2。<b>注能（2）：</b>改为+2/+2。 | [x]After your hero attacks, give your damaged minions +1/+2. <b>Infuse (2):</b> +2/+2 instead. |
| CATA_472 | 灵感之槌 | Inspiring Maul | 0 | 2/0 | WEAPON | 否 | 灵感之槌 | <b>亡语：</b>随机触发一个友方随从的回合结束效果。 | <b>Deathrattle:</b> Trigger a random friendly minion's end of turn effect. |
| CATA_580 | 灾变战斧 | Cataclysmic War Axe | 0 | 3/0 | WEAPON | 否 | 灾变战斧 | <b>战吼：</b><b>兆示</b>{0}。 | <b>Battlecry:</b> <b>Herald</b> {0}. |
| EDR_416 | 牧人之杖 | Shepherd's Crook | 0 | 3/0 | WEAPON | 否 | 牧人之杖 | 在你的英雄 攻击后，召唤一只3/3并<b>休眠</b>2回合的羊。 | After your hero attacks, summon a 3/3 Sheep that's <b>Dormant</b> for 2 turns. |
| TOY_810 | 画师的美德 | Painter's Virtue | 0 | 2/0 | WEAPON | 否 | 画师的美德 | <b>吸血</b> 在你的英雄攻击后，使你手牌中的随从牌获得+1/+1。 | <b>Lifesteal</b> After your hero attacks, give minions in your hand +1/+1. |
| MEND_803 | 砺胆重剑 | Emboldening Blade | 0 | 3/0 | WEAPON | 否 | 砺胆重剑 | <b>战吼：</b>在本局对战中，使你的白银之手新兵获得+1/+1。 | [x]<b>Battlecry:</b> Give your Silver Hand Recruits +1/+1 this game. |
| RLK_516 | 碎骨手斧 | Bone Breaker | 0 | 2/0 | WEAPON | 否 | 碎骨手斧 | 在你的英雄 攻击随从后，对敌方英雄造成2点伤害。 | [x]After your hero attacks a minion, deal 2 damage to the enemy hero. |
| TOY_641 | 裁判拳套 | Umpire's Grasp | 0 | 3/0 | WEAPON | 否 | 裁判拳套 | <b>亡语：</b>抽一张恶魔牌，并使其法力值消耗减少（2）点。 | <b>Deathrattle:</b> Draw a Demon and reduce its Cost by (2). |
| TLC_478 | 远祖之斧 | Axe of the Forefathers | 0 | 2/0 | WEAPON | 否 | 远祖之斧 | 在你的英雄攻击后，对所有随从造成1点伤害。 | After your hero attacks, deal 1 damage to all minions. |
| TOY_358 | 遥控器 | Remote Control | 0 | 1/0 | WEAPON | 否 | 遥控器 | 在你的英雄攻击后，召唤一只1/1的猎犬。 | After your hero attacks, summon a 1/1 Hound. |
| TIME_209t | 高山之王的战锤 | High King's Hammer | 0 | 3/0 | WEAPON | 否 | 高山之王的战锤 | <b>风怒</b>。<b>亡语：</b>将本武器洗入你的牌库并永久具有+2攻击力。 | [x]<b>Windfury</b> <b>Deathrattle:</b> Shuffle this into your deck with +2  Attack permanently. |
| TSC_070 | 鱼叉炮 | Harpoon Gun | 0 | 3/0 | WEAPON | 否 | 鱼叉炮 | 在你的英雄攻击后，<b>探底</b>。如果选中的是野兽牌，使其法力值消耗减少（2）点。 | After your hero attacks, <b>Dredge</b>. If it's a Beast, reduce its Cost by (2). |
| ETC_312 | 爱豆的爱 | Idol's Adoration | 1 | 0/0 | WEAPON | 否 | 爱豆的爱 | 你的英雄技能法力值消耗为（0）点。在你使用技能后，失去1点耐久度。 | Your Hero Power costs (0). After you use it, lose 1 Durability. |
| TIME_444 | 迷时战刃 | Time-Lost Glaive | 1 | 2/0 | WEAPON | 否 | 迷时战刃 | <b>亡语：</b>随机获取 一张来自过去的恶魔牌。 | <b>Deathrattle:</b> Get a random Demon from the past. |
| ETC_084 | 邪弦竖琴 | Felstring Harp | 1 | 0/0 | WEAPON | 否 | 邪弦竖琴 | 每当你的英雄即将在你的回合受到伤害，改为恢复#2点生命值。失去1点耐久度。 | [x]Whenever your hero would take damage on your turn, restore #2 Health instead. Lose 1 Durability. |
| JAM_015 | 混搭音叉 | Remixed Tuning Fork | 2 | 2/0 | WEAPON | 否 | 混搭音叉 | 在你的手牌中时会获得一项额外效果，该效果每回合都会改变。 | Gains an extra effect in your hand that changes each turn. |
| CORE_TRL_111 | 猎头者之斧 | Headhunter's Hatchet | 2 | 2/0 | WEAPON | 否 | 猎头者之斧 | <b>战吼：</b>如果你控制一个野兽，便获得+1耐久度。 | [x]<b>Battlecry:</b> If you control a Beast, gain +1 Durability. |
| REV_917 | 石雕凿刀 | Carving Chisel | 2 | 1/0 | WEAPON | 否 | 石雕凿刀 | 在你的英雄攻击后，随机召唤一个基础图腾。 | After your hero attacks, summon a random basic Totem. |
| CORE_LOOT_044 | 铁刃护手 | Bladed Gauntlet | 2 | 0/0 | WEAPON | 否 | 铁刃护手 | 攻击力等同于你的 护甲值。无法攻击英雄。 | Has Attack equal to your Armor. Can't attack heroes. |
| CORE_BT_781 | 埃辛诺斯壁垒 | Bulwark of Azzinoth | 3 | 1/0 | WEAPON | 否 | 埃辛诺斯壁垒 | 每当你的英雄即将受到伤害，改为埃辛诺斯壁垒失去1点耐久度。 | [x]Whenever your hero would take damage, this loses  1 Durability instead. |
| CORE_BT_921 | 奥达奇战刃 | Aldrachi Warblades | 3 | 2/0 | WEAPON | 否 | 奥达奇战刃 | <b>吸血</b> | <b>Lifesteal</b> |
| ETC_518 | 搓盘机 | Record Scratcher | 3 | 3/0 | WEAPON | 否 | 搓盘机 | <b>亡语：</b>复原1个法力水晶。<i>（装备期间，使用<b>连击</b>牌以提升此效果！）</i> | [x]<b>Deathrattle:</b> Refresh 1 Mana Crystal. <i>(Play <b>Combo</b> cards while     equipped to improve!)</i> |
| END_012 | 无穷之手 | Hand of Infinity | 3 | 4/0 | WEAPON | 否 | 无穷之手 | 无法攻击英雄。<b>战吼：</b>在本回合中，将本武器的攻击力变为无穷大！ | [x]Can't attack heroes. <b>Battlecry:</b> Set this weapon's Attack to INFINITY this turn! |
| TLC_EVENT_402 | 末日使者之杖 | Staff of the Endbringer | 3 | 1/0 | WEAPON | 否 | 末日使者之杖 | <b>亡语：</b>消灭所有随从。 | <b>Deathrattle:</b> Destroy all minions. |
| ETC_813 | 爵士贝斯 | Jazz Bass | 3 | 3/0 | WEAPON | 否 | 爵士贝斯 | <b>亡语：</b>你的下一张法术牌法力值消耗减少（1）点。<i>（装备期间，<b>过载</b>以提升此效果！）</i> | [x]<b>Deathrattle:</b> Your next spell costs (1) less. <i>(<b>Overload</b> while equipped to improve!)</i> |
| TOY_604 | 砰砰扳手 | Boom Wrench | 3 | 3/0 | WEAPON | 否 | 砰砰扳手 | <b>微缩</b> <b>亡语：</b>随机触发一个友方机械的<b>亡语</b>。 | [x]<b>Miniaturize</b> <b>Deathrattle:</b> Trigger the <b>Deathrattle</b> of a random friendly Mech. |
| ETC_317 | 迪斯科战槌 | Disco Maul | 3 | 3/0 | WEAPON | 否 | 迪斯科战槌 | <b>亡语：</b>随机使一个友方随从获得+1/+1。<i>（装备期间，使用随从牌以提升此效果！）</i> | [x]<b>Deathrattle:</b> Give a random friendly minion +1/+1. <i>(Play minions while equipped to improve!)</i> |
| CORE_GVG_059 | 齿轮光锤 | Coghammer | 3 | 2/0 | WEAPON | 否 | 齿轮光锤 | <b>战吼：</b>随机使一个友方随从获得<b>圣盾</b>和<b>嘲讽</b>。 | <b>Battlecry:</b> Give a random friendly minion <b>Divine Shield</b> and <b>Taunt</b>. |
| ETC_832 | 丛林弹唱琴 | Jungle Jammer | 4 | 4/0 | WEAPON | 否 | 丛林弹唱琴 | <b>亡语：</b>随机召唤一只法力值消耗为（1）的野兽。<i>（装备期间，施放法术以提升此效果！）</i> | [x]<b>Deathrattle:</b> Summon a random 1-Cost Beast. <i>(Cast spells while     equipped to improve!)</i> |
| ETC_388 | 实木手鼓 | Timber Tambourine | 4 | 2/0 | WEAPON | 否 | 实木手鼓 | <b>亡语：</b>召唤1棵5/5的古树。<i>（装备期间，使用法力值消耗5点或以上的卡牌以提升此效果！）</i> | [x]<b>Deathrattle:</b> Summon 1 5/5 Ancient. <i>(Play cards that cost (5) or more while   equipped to improve!)</i> |
| ETC_405 | 战刃吉他 | Glaivetar | 4 | 4/0 | WEAPON | 否 | 战刃吉他 | <b>亡语：</b>抽1张牌。<i>（装备期间，使用<b>流放</b>牌以提升此效果！）</i> | [x] <b>Deathrattle:</b> Draw 1 card.  <i>(Play <b>Outcast</b> cards while  equipped to improve!)</i> |
| END_016 | 时空之爪 | Chronoclaws | 4 | 4/0 | WEAPON | 否 | 时空之爪 | 在你的英雄 攻击后，弃掉你法力值消耗最高的牌。 | After your hero attacks, discard your highest Cost card. |
| TOY_522 | 水弹枪 | Watercannon | 4 | 3/0 | WEAPON | 否 | 水弹枪 | 在你的英雄攻击后，召唤一个1/1的海盗，并使其随机攻击一个敌人。 | After your hero attacks, summon a 1/1 Pirate that attacks a random enemy. |
| ETC_520 | 科多兽皮组鼓 | Kodohide Drumkit | 4 | 3/0 | WEAPON | 否 | 科多兽皮组鼓 | <b>亡语：</b>对所有随从造成1点伤害。<i>（装备期间，获得护甲值以提升此效果！）</i> | [x]<b>Deathrattle:</b> Deal 1 damage to all minions. <i>(Gain Armor while     equipped to improve!)</i> |
| CORE_OG_031 | 暮光神锤 | Hammer of Twilight | 5 | 4/0 | WEAPON | 否 | 暮光神锤 | <b>亡语：</b>召唤一个4/2的元素。 | <b>Deathrattle:</b> Summon a 4/2 Elemental. |
| MIS_101 | 海绵斧 | Foamrender | 5 | 5/0 | WEAPON | 否 | 海绵斧 | 每当你的英雄攻击时，消耗3份 <b>残骸</b>以获得+1耐久度。 | Whenever your hero attacks, spend 3 <b>Corpses</b> to gain +1 Durability. |
| CORE_RLK_086 | 霜之哀伤 | Frostmourne | 6 | 4/0 | WEAPON | 否 | 霜之哀伤 | <b>亡语：</b>召唤被该武器消灭的所有 随从。 | <b>Deathrattle:</b> Summon every minion killed by this weapon. |
| JAM_011 | 风领主的管号 | Horn of the Windlord | 6 | 3/0 | WEAPON | 否 | 风领主的管号 | <b>风怒</b>。每当你的英雄攻击随从时，将被攻击随从的属性值变为3/3。 | [x]<b>Windfury</b> Whenever your hero attacks a minion, set its stats to 3/3. |
## 连击

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| ETC_077 | 八爪碟机 | Disc Jockey | 2 | 4/1 | MINION | 否 | 八爪碟机 | <b>连击：</b>随机将一张<b>连击</b>牌置入你的手牌。 | <b>Combo:</b> Add a random <b>Combo</b> card to your hand. |
| JAM_021 | 单曲流星 | One Hit Wonder | 2 | 2/1 | MINION | 否 | 单曲流星 | <b>突袭</b>。<b>连击：</b> 获得<b><b>剧毒</b>。</b> | <b>Rush</b> <b>Combo:</b> Gain <b><b>Poisonous</b>.</b> |
| CORE_DMF_511 | 狐人老千 | Foxy Fraud | 2 | 3/2 | MINION | 否 | 狐人老千 | <b>战吼：</b> 在本回合中，你的下一张<b>连击</b>牌法力值消耗减少（2）点。 | <b>Battlecry:</b> Your next <b>Combo</b> card this turn costs (2) less. |
| GDB_870 | 艾瑞达潜藏者 | Eredar Skulker | 2 | 1/3 | MINION | 否 | 艾瑞达潜藏者：亮边连击 +2 攻（3/3，当回合不能攻击）。 | <b>连击，<b>法术迸发</b>：</b>获得+2攻击力和<b>潜行</b>。 | [x]<b>Combo and <b>Spellburst</b>:</b> Gain +2 Attack and <b>Stealth</b>. |
| CORE_EX1_131 | 迪菲亚头目 | Defias Ringleader | 2 | 3/2 | MINION | 否 | 迪菲亚头目 | <b>连击：</b>召唤一个2/1的迪菲亚强盗。 | <b>Combo:</b> Summon a 2/1 Defias Bandit. |
| ETC_072 | B-Box拳手 | Beatboxer | 3 | 4/3 | MINION | 是 | B-Box拳手 | <b>连击：</b>造成4点伤害，随机分配到所有敌人身上。 | [x]<b>Combo:</b> Deal 4 damage randomly split among  all enemies. |
| CORE_EX1_134 | 军情七处特工 | SI:7 Agent | 3 | 3/3 | MINION | 否 | 军情七处特工 | <b>连击：</b>造成3点伤害。 | <b>Combo:</b> Deal 3 damage. |
| DAL_415 | 怪盗恶霸 | EVIL Miscreant | 3 | 1/5 | MINION | 否 | 怪盗恶棍：亮边连击获取 2 张跟班（入手牌，当回合无场攻）。 | <b>连击：</b>随机将两张<b>跟班</b>牌置入你的手牌。 | <b>Combo:</b> Add two random <b>Lackeys</b> to your hand. |
| TOY_516 | 折价区海盗 | Bargain Bin Buccaneer | 3 | 3/2 | MINION | 否 | 折价区海盗 | <b>突袭</b>。<b>连击：</b>召唤一个本随从的复制。 | <b>Rush</b> <b>Combo:</b> Summon a copy of this. |
| ETC_073 | 押韵狂人 | Rhyme Spinner | 3 | 1/3 | MINION | 否 | 押韵狂人 | <b>突袭</b>。<b>连击：</b>在本局对战中，你每使用过一张其他<b>连击</b>牌，便获得+1/+1。0<i>（已使用0张）</i> | [x]<b>Rush</b> <b>Combo:</b> Gain +1/+1 for each other <b>Combo</b> card you've  played this game.@ <i>(@)</i> |
| TLC_516 | 尼斐塞特武器匠 | Neferset Weaponsmith | 4 | 5/4 | MINION | 否 | 奈法瑞特武器匠：战吼发现武器 v1 不模拟；亮边连击武器 +2 攻。 | <b>战吼：</b>随机获取一张另一职业的武器牌。<b>连击：</b>使其获得+2攻击力。 | [x]<b>Battlecry:</b> Get a random weapon from another class. <b>Combo:</b> Give it +2 Attack. |
| TIME_710 | 暴徒双人组 | Troubled Double | 4 | 3/3 | MINION | 否 | 暴徒双人组 | <b>潜行</b>。<b>连击：</b>召唤一个本随从的复制。 | <b>Stealth</b> <b>Combo:</b> Summon a copy of this. |
| REV_826 | 私家眼线 | Private Eye | 4 | 3/4 | MINION | 否 | 私家眼线 | <b>战吼：</b>从你的牌库中施放一个<b>奥秘</b>。<b>连击：</b>改为施放2个。 | [x]<b>Battlecry:</b> Cast a <b>Secret</b> from your deck.  <b>Combo:</b> Cast 2 instead. |
| END_032 | 飞翼畸变体 | Winged Aberration | 4 | 4/4 | MINION | 否 | 飞翼畸变体 | <b>突袭</b>。<b><b>连击：</b>过载（2）</b>以获得<b>风怒</b>和在本回合中的<b>免疫</b>。 | [x]<b>Rush</b> <b><b>Combo:</b> Overload</b> for (2) to gain <b>Immune</b> this turn and <b>Windfury</b>. |
| CORE_BOT_576 | 疯狂的药剂师 | Crazed Chemist | 5 | 4/4 | MINION | 否 | 疯狂的药剂师 | <b>连击：</b>使一个友方随从获得+4攻击力。 | <b>Combo:</b> Give a friendly minion +4 Attack. |
| UNG_064 | 邪脊吞噬者 | Vilespine Slayer | 5 | 3/4 | MINION | 否 | 邪脊吞噬者：亮边连击消灭一个随从。 | <b>连击：</b> 消灭一个随从。 | <b>Combo:</b> Destroy a minion. |
| TSC_933 | 镣铐水鬼 | Bootstrap Sunkeneer | 5 | 4/4 | MINION | 否 | 镣铐水鬼：亮边连击将敌方随从移出场面（置入牌库底，v1 等同移除）。 | <b>连击：</b>将一个敌方随从置于你对手的牌库底。 | [x]<b>Combo:</b> Put an enemy minion on the bottom of  your opponent's deck. |
## 英雄技能

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| __dh_claws_2 | 恶魔之咬 | __dh_claws_2 | 1 | - | - | 否 | 恶魔之咬 |  |  |
| __dh_claws_1 | 恶魔之爪 | __dh_claws_1 | 1 | - | - | 否 | 恶魔之爪 |  |  |
| __rogue_dagger_1_2 | 匕首精通 | __rogue_dagger_1_2 | 2 | - | - | 否 | 匕首精通 / 浸毒匕首：装备匕首（替换已有武器）。 |  |  |
| __druid_shapeshift_1 | 变形 | __druid_shapeshift_1 | 2 | - | - | 否 | 变形：+1 攻（护甲 v1 不计场攻）。 |  |  |
| CATA_190p | 无情 | Ruthless | 2 | - | HERO_POWER | 否 | 无情 | 在本回合中 +$a5攻击力。 | +$a5 Attack this turn. |
| __rogue_dagger_2_2 | 浸毒匕首 | __rogue_dagger_2_2 | 2 | - | - | 否 | 匕首精通 / 浸毒匕首：装备匕首（替换已有武器）。 |  |  |
| __mage_fireblast_1 | 火焰冲击 | __mage_fireblast_1 | 2 | - | - | 否 | 火焰冲击：1 点定向伤害（无嘲讽打脸；有嘲讽则打随从）。 |  |  |
| __hunter_steady_2 | 稳固射击 | __hunter_steady_2 | 2 | - | - | 否 | 稳固射击：对敌方英雄造成 2 点伤害（无视嘲讽）。 |  |  |
| AV_207p2 | 虚空之刺 | Void Spike | 2 | - | HERO_POWER | 否 | 虔诚者泽瑞拉「虚空之刺」：对敌方英雄造成 5 点伤害（无视嘲讽）。 | 造成$5点伤害。每回合翻转。 | Deal $5 damage. Flip each turn. |
| __dk_ghoul_1_1 | 食尸鬼冲锋 | __dk_ghoul_1_1 | 2 | - | - | 否 | 食尸鬼冲锋：召唤冲锋食尸鬼，当回合可解场/打脸。 |  |  |
| __dk_ghoul_2_1 | 食尸鬼冲锋 | __dk_ghoul_2_1 | 2 | - | - | 否 | 食尸鬼冲锋：召唤冲锋食尸鬼，当回合可解场/打脸。 |  |  |
## 地标

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| CATA_584 | 喷发火山 | Erupting Volcano | 0 | - | LOCATION | 是 | 喷发火山 | 造成3点伤害，随机分配到所有敌人身上。如果你在本回合中使用过火焰法术牌，再造成3点。 | [x]Deal 3 damage randomly split among enemies. If you've played a Fire spell this turn, deal 3 more. |
| CORE_REV_290 | 赎罪教堂 | Cathedral of Atonement | 0 | - | LOCATION | 否 | 赎罪教堂：+2/+1，优先风怒可攻随从，否则攻击最低的可攻随从。 | 使一个随从获得+2/+1。抽一张牌。 | Give a minion +2/+1 and draw a card. |
| REV_290 | 赎罪教堂 | Cathedral of Atonement | 0 | - | LOCATION | 否 | 赎罪教堂：+2/+1，优先风怒可攻随从，否则攻击最低的可攻随从。 | 使一个随从获得+2/+1。抽一张牌。 | Give a minion +2/+1 and draw a card. |
## 手牌回合结束

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| CORE_RLK_720 | 侏儒嚼嚼怪 | Gnome Muncher | 6 | 5/6 | MINION | 否 | 打出回合结束随从：召唤失调，标记 sim_summon 供 end_turn 与 hold-attack 识别。 | <b>嘲讽</b>，<b>吸血</b>。在你的回合结束时，攻击生命值最低的敌人。 | [x]<b>Taunt</b>, <b>Lifesteal</b> At the end of your turn, attack the lowest Health enemy. |
| RLK_720 | 侏儒嚼嚼怪 | Gnome Muncher | 6 | 5/6 | MINION | 否 | 打出回合结束随从：召唤失调，标记 sim_summon 供 end_turn 与 hold-attack 识别。 | <b>嘲讽</b>，<b>吸血</b>。在你的回合结束时，攻击生命值最低的敌人。 | [x]<b>Taunt</b>, <b>Lifesteal</b> At the end of your turn, attack the lowest Health enemy. |
| EDR_453 | 棘嗣幼龙 | Briarspawn Drake | 10 | 12/7 | MINION | 否 | 打出回合结束随从：召唤失调，标记 sim_summon 供 end_turn 与 hold-attack 识别。 | 在你的回合结束时，随机攻击一个敌方随从<i>（超过目标生命值的伤害会命中敌方英雄）</i>。 | [x]At the end of your turn, attack a random enemy minion <i>(excess damage hits the enemy hero)</i>. |
## 受伤法强

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| END_022 | 时光扭曲先知 | Time-Twisted Seer | 1 | 1/3 | MINION | 否 | 打出受伤法强随从：当回合召唤（失调），供序列内火焰冲击点伤激活法强。 | 受伤时拥有 <b>法术伤害+2</b>。 | Has <b>Spell Damage +2</b> while damaged. |
## 场面回合结束

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| TOY_601t | 工厂装配机 | Factory Assemblybot | 1 | 1/1 | MINION | 是 | 回合结束:工厂装配机(微缩)，召唤6/7 | <b>微型</b> 在你的回合结束时，召唤一个6/7的机器人并使其攻击一个随机敌人。 | <b>Mini</b> At the end of your turn, summon a 6/7 Bot that attacks a random enemy. |
| BAR_063 | 甜水鱼人斥候 | Lushwater Scout | 2 | 1/3 | MINION | 否 | 回合结束:沃坎诺斯，数值2 | 在你召唤一个鱼人后，使其获得+1攻击力和<b>突袭</b>。 | After you summon a Murloc, give it +1 Attack and <b>Rush</b>. |
| BAR_064 | 精明的奥术师 | Talented Arcanist | 2 | 1/3 | MINION | 否 | 回合结束:亮铜之翼，数值2 | <b>战吼：</b>在本回合中，你的下一个法术拥有<b>法术伤害+2</b>。 | <b>Battlecry:</b> Your next spell this turn has <b>Spell Damage +2</b>. |
| TOY_824 | 黑棘针线师 | Darkthorn Quilter | 4 | 2/4 | MINION | 是 | 回合结束:黑棘针线师，用自身攻击力 | 在你的回合结束时，造成等同于本随从攻击力的伤害，随机分配到所有敌人身上。 | [x]At the end of your turn, deal this minion's Attack damage randomly split    among enemies. |
| CATA_999 | 土石幼龙 | Earthen Drake | 5 | 4/4 | MINION | 否 | 回合结束:土石幼龙，数值4 | 在你的回合结束时，对敌方英雄造成4点 伤害。 | At the end of your turn, deal 4 damage to the enemy hero. |
| TOY_820 | 废弃电子玩偶 | Forgotten Animatronic | 5 | 4/6 | MINION | 否 | 回合结束:废弃电子玩偶，用自身攻击力 | 在你的回合结束时，消灭一个攻击力低于本随从的随从。 | At the end of your turn, destroy a minion with less Attack than this. |
| RLK_720 | 侏儒嚼嚼怪 | Gnome Muncher | 6 | 5/6 | MINION | 否 | 回合结束:侏儒嚼嚼怪，用自身攻击力 | <b>嘲讽</b>，<b>吸血</b>。在你的回合结束时，攻击生命值最低的敌人。 | [x]<b>Taunt</b>, <b>Lifesteal</b> At the end of your turn, attack the lowest Health enemy. |
| CATA_475 | 破鳞盾卫 | Scalebreaker Bulwark | 6 | 3/6 | MINION | 否 | 回合结束:破鳞盾卫，数值2 | 在你的回合结束时，对所有敌人造成 2点伤害。 | [x]At the end of your turn, deal 2 damage to all enemies. |
| CORE_RLK_706 | 亚历山德罗斯·莫格莱尼 | Alexandros Mograine | 7 | 7/7 | MINION | 否 | 回合结束:莫格莱尼，数值3 | <b>战吼：</b>在本局对战的剩余时间内，在你的回合结束时，对你的对手造成3点伤害。 | <b>Battlecry:</b> For the rest of the game, deal 3 damage to your opponent at the end of your turns. |
| RLK_706 | 亚历山德罗斯·莫格莱尼 | Alexandros Mograine | 7 | 7/7 | MINION | 否 | 回合结束:莫格莱尼，数值3 | <b>战吼：</b>在本局对战的剩余时间内，在你的回合结束时，对你的对手造成3点伤害。 | <b>Battlecry:</b> For the rest of the game, deal 3 damage to your opponent at the end of your turns. |
| BT_493 | 愤怒的女祭司 | Priestess of Fury | 7 | 6/7 | MINION | 否 | 回合结束:愤怒的女祭司，数值6 | 在你的回合结束时，造成6点伤害，随机分配到所有敌人身上。 | At the end of your turn, deal 6 damage randomly split among all enemies. |
| CORE_BT_493 | 愤怒的女祭司 | Priestess of Fury | 7 | 6/7 | MINION | 否 | 回合结束:愤怒的女祭司，数值6 | 在你的回合结束时，造成6点伤害，随机分配到所有敌人身上。 | At the end of your turn, deal 6 damage randomly split among all enemies. |
| CORE_TTN_866 | 神秘恐魔 | Mythical Terror | 7 | 4/10 | MINION | 否 | 回合结束:神秘恐魔 | <b>吸血</b>。在你的回合结束时，迫使所有敌方随从攻击本随从。 | [x]<b>Lifesteal</b> At the end of your turn, force all enemy minions to attack this. |
| AV_340 | 亮铜之翼 | Brasswing | 8 | 9/7 | MINION | 否 | 回合结束:亮铜之翼，数值2 | 在你的回合结束时，对所有敌人造成2点伤害。<b>荣誉消灭：</b>为你的英雄恢复#4点生命值。 | [x]At the end of your turn, deal 2 damage to all enemies. <b>Honorable Kill:</b> Restore #4 Health to your hero. |
| TOY_647 | 玛瑟里顿（未发售版） | Magtheridon, Unreleased | 8 | 12/12 | MINION | 否 | 回合结束:玛瑟里顿，数值3，休眠 | <b>休眠</b>2回合。<b>休眠</b>状态下，在你的回合结束时，对所有敌人造成3点伤害。 | [x]<b>Dormant</b> for 2 turns. While <b>Dormant</b>, deal 3 damage to all enemies at the end of your turn. |
| SCH_337 | 问题学生 | Troublemaker | 8 | 6/8 | MINION | 是 | 回合结束:问题学生，召唤3/3 | 在你的回合结束时，召唤两个3/3的无赖并使其攻击随机敌人。 | At the end of your turn, summon two 3/3 Ruffians that attack random enemies. |
| TOY_601 | 工厂装配机 | Factory Assemblybot | 10 | 6/7 | MINION | 是 | 回合结束:工厂装配机，召唤6/7 | <b>微缩</b> 在你的回合结束时，召唤一个6/7的机器人并使其攻击一个随机敌人。 | <b>Miniaturize</b> At the end of your turn, summon a 6/7 Bot that attacks a random enemy. |
| EDR_453 | 棘嗣幼龙 | Briarspawn Drake | 10 | 12/7 | MINION | 是 | 回合结束:棘嗣幼龙，用自身攻击力 | 在你的回合结束时，随机攻击一个敌方随从<i>（超过目标生命值的伤害会命中敌方英雄）</i>。 | [x]At the end of your turn, attack a random enemy minion <i>(excess damage hits the enemy hero)</i>. |
| CORE_YOP_034 | 窜逃的黑翼龙 | Runaway Blackwing | 10 | 10/10 | MINION | 是 | 回合结束:窜逃的黑翼龙，数值10 | 在你的回合结束时，随机对一个敌方随从造成10点伤害。 | [x]At the end of your turn, deal 10 damage to a random enemy minion. |
| YOP_034 | 窜逃的黑翼龙 | Runaway Blackwing | 10 | 10/10 | MINION | 是 | 回合结束:窜逃的黑翼龙，数值10 | 在你的回合结束时，随机对一个敌方随从造成10点伤害。 | [x]At the end of your turn, deal 10 damage to a random enemy minion. |
## 亡语

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| CATA_150t | 拉格纳罗斯之手 | Hand of Ragnaros | 1 | 2/1 | MINION | 否 | 亡语:random_attacker_script | <b>亡语：</b>随机对一个敌人造成{0}点伤害。<i><b>兆示</b>两次后升级。</i>@<b>亡语：</b>随机对一个敌人造成{0}点伤害。<i><b>兆示</b>一次后升级。</i>@<b>亡语：</b>随机对一个敌人造成{0}点伤害。 | [x]<b>Deathrattle:</b> Deal {0} damage to a random enemy. <i><b>Herald</b> twice to upgrade.</i>@[x]<b>Deathrattle:</b> Deal {0} damage to a random enemy. <i><b>Herald</b> once to upgrade.</i>@[x]<b>Deathrattle:</b> Deal {0} damage to a random enemy. |
| CATA_150t1 | 拉格纳罗斯之手 | Hand of Ragnaros | 1 | 2/1 | MINION | 否 | 亡语:random_attacker_script | <b>亡语：</b>随机对一个敌人造成{0}点伤害。<i><b>兆示</b>两次后升级。</i>@<b>亡语：</b>随机对一个敌人造成{0}点伤害。<i><b>兆示</b>一次后升级。</i>@<b>亡语：</b>随机对一个敌人造成{0}点伤害。 | [x]<b>Deathrattle:</b> Deal {0} damage to a random enemy. <i><b>Herald</b> twice to upgrade.</i>@[x]<b>Deathrattle:</b> Deal {0} damage to a random enemy. <i><b>Herald</b> once to upgrade.</i>@[x]<b>Deathrattle:</b> Deal {0} damage to a random enemy. |
| CATA_580t | 拉格纳罗斯的士兵 | Soldier of Ragnaros | 1 | 2/1 | MINION | 否 | 亡语:random_attacker_script | <b>亡语：</b>随机对一个敌人造成{0}点伤害。<i><b>兆示</b>两次后升级。</i>@<b>亡语：</b>随机对一个敌人造成{0}点伤害。<i><b>兆示</b>一次后升级。</i>@<b>亡语：</b>随机对一个敌人造成{0}点伤害。 | [x]<b>Deathrattle:</b> Deal {0} damage to a random enemy. <i><b>Herald</b> twice to upgrade.</i>@[x]<b>Deathrattle:</b> Deal {0} damage to a random enemy. <i><b>Herald</b> once to upgrade.</i>@[x]<b>Deathrattle:</b> Deal {0} damage to a random enemy. |
| CORE_SW_439 | 活泼的松鼠 | Vibrant Squirrel | 1 | 2/1 | MINION | 否 | 亡语:summon_enemy，召唤2/1 | <b>亡语：</b>将四张橡果洗入你的牌库。当抽到橡果时，召唤一只2/1的松鼠。 | [x]<b>Deathrattle:</b> Shuffle 4 Acorns into your deck. When drawn, summon a 2/1 Squirrel. |
| TLC_249 | 炽烈烬火 | Sizzling Cinder | 1 | 2/1 | MINION | 否 | 亡语:random_split_attackers，数值2 | <b>亡语：</b>造成2点伤害，随机分配到所有敌人身上。 | <b>Deathrattle:</b> Deal 2 damage randomly split among all enemies. |
| REV_356 | 狂蝠来宾 | Batty Guest | 1 | 1/1 | MINION | 否 | 亡语:summon_enemy，召唤2/1 | <b>亡语：</b>召唤一只2/1的蝙蝠。 | <b>Deathrattle:</b> Summon a 2/1 Bat. |
| BOT_700 | 大铡蟹 | SN1P-SN4P | 3 | 2/3 | MINION | 否 | 亡语:summon_enemy，召唤1/1 | <b>磁力，回响，亡语：</b>召唤两个1/1的微型机器人。 | <b>Magnetic</b>, <b>Echo</b> <b>Deathrattle:</b> Summon two 1/1 Microbots. |
| CORE_UNG_022 | 幻象制造者 | Mirage Caller | 3 | 2/3 | MINION | 否 | 亡语:aoe_all_minions，数值1 | <b>战吼：</b>选择一个随从，召唤一个它的1/1复制。 | <b>Battlecry:</b> Choose a minion. Summon a 1/1 copy of it. |
| UNG_022 | 幻象制造者 | Mirage Caller | 3 | 2/3 | MINION | 否 | 亡语:aoe_all_minions，数值1 | <b>战吼：</b>选择一个随从，召唤一个它的1/1复制。 | <b>Battlecry:</b> Choose a minion. Summon a 1/1 copy of it. |
| TOY_814 | 玩具兵盒 | Bucket of Soldiers | 3 | 0/2 | MINION | 否 | 亡语:summon_enemy，召唤1/1 | <b>亡语：</b>召唤五个1/1并具有随机<b>额外效果</b>的士兵。 | <b>Deathrattle:</b> Summon five 1/1 Soldiers with random <b>Bonus Effects</b>. |
| CORE_WC_701 | 邪能响尾蛇 | Felrattler | 3 | 3/2 | MINION | 否 | 亡语:aoe_attacker_minions，数值1 | <b>突袭</b>，<b>亡语：</b>对所有敌方随从造成 1点伤害。 | [x]<b>Rush</b> <b>Deathrattle:</b> Deal 1 damage to all enemy minions. |
| EDR_459 | 受难的毁灭者 | Afflicted Devastator | 4 | 6/6 | MINION | 否 | 亡语:aoe_attacker_minions，数值3 | <b>战吼：</b>对所有其他友方随从造成3点伤害。<b>亡语：</b>对所有敌方随从造成3点伤害。 | [x]<b>Battlecry:</b> Deal 3 damage to all other friendly minions. <b>Deathrattle:</b> Deal 3 damage to all enemy minions. |
| TIME_017 | 坦克机械师 | Tankgineer | 4 | 2/1 | MINION | 否 | 亡语:summon_enemy，召唤7/7，嘲讽 | <b>圣盾</b>。<b>亡语：</b>召唤一辆7/7并具有<b>圣盾</b> 的坦克。 | [x]<b>Divine Shield</b> <b>Deathrattle:</b> Summon a 7/7 Tank with <b>Divine Shield</b>. |
| TOY_670 | 欢乐的玩具匠 | Giggling Toymaker | 4 | 2/1 | MINION | 否 | 亡语:summon_enemy，召唤1/2，嘲讽 | <b>亡语：</b>召唤两个1/2并具有<b>嘲讽</b>和<b>圣盾</b>的 机械。 | <b>Deathrattle:</b> Summon two 1/2 Mechs with <b>Taunt</b> and <b>Divine Shield</b>. |
| TOY_642 | 球霸野猪人 | Ball Hog | 4 | 3/3 | MINION | 否 | 亡语:lowest_attacker，数值3 | <b>吸血</b>。<b>战吼，亡语：</b>对生命值最低的敌人造成3点伤害。 | [x]<b>Lifesteal</b> <b>Battlecry and Deathrattle:</b> Deal 3 damage to the lowest Health enemy. |
| GDB_226 | 凶恶的入侵者 | Hostile Invader | 5 | 3/5 | MINION | 否 | 亡语:aoe_other_minions，数值2 | <b>战吼，<b>法术迸发</b>， 亡语：</b>对所有其他随从造成2点伤害。 | <b>Battlecry, <b>Spellburst</b>, and Deathrattle:</b> Deal 2 damage to all other minions. |
| RLK_554 | 恐惧感知者 | Harkener of Dread | 5 | 2/2 | MINION | 否 | 亡语:summon_enemy，召唤4/4，嘲讽 | <b><b>嘲讽</b>，复生</b>  <b>亡语：</b>召唤一个4/4并具有<b>嘲讽</b>的亡灵。 | [x]<b><b>Taunt</b>, Reborn</b> <b>Deathrattle:</b> Summon a 4/4 Undead with <b>Taunt</b>. |
| CATA_586 | 毁灭之焰 | Destructive Blaze | 5 | 3/3 | MINION | 否 | 亡语:random_attacker，数值2 | 在本随从受到伤害并存活下来后，召唤一个毁灭之焰。<b>亡语：</b>随机对一个敌人造成2点伤害。 | [x]After this survives damage, summon a Destructive Blaze. <b>Deathrattle:</b> Deal 2 damage to a random enemy. |
| FP1_012 | 淤泥喷射者 | Sludge Belcher | 5 | 3/6 | MINION | 否 | 亡语:summon_enemy，召唤1/2，嘲讽 | <b>嘲讽，亡语：</b>召唤一个1/2并具有<b>嘲讽</b>的泥浆怪。 | [x]<b>Taunt</b> <b>Deathrattle:</b> Summon a 1/2 Slime with <b>Taunt</b>. |
| TOY_908 | 焰火机师 | Fireworker | 5 | 5/5 | MINION | 否 | 亡语:random_split_attackers，数值4 | <b>亡语：</b> 召唤两个1/1的砰砰机器人。<i>警告：该机器人随时可能爆炸。</i> | <b>Deathrattle:</b> Summon two 1/1 Boom Bots. <i>WARNING: Bots may explode.</i> |
| TLC_468 | 黏团焦油 | Blob of Tar | 5 | 4/4 | MINION | 否 | 亡语:summon_enemy，召唤2/2，嘲讽 | <b>剧毒</b>。<b>嘲讽</b>。<b>亡语：</b>召唤一个2/2并具有<b>剧毒</b>的黏团，以及一个2/2并具有<b>嘲讽</b>的黏团。 | [x]<b>Poisonous</b>, <b>Taunt</b> <b>Deathrattle:</b> Summon a 2/2 Blob with <b>Poisonous</b> and a 2/2 Blob with <b>Taunt</b>. |
| AV_325 | 不死信徒 | Undying Disciple | 6 | 3/7 | MINION | 否 | 亡语:aoe_attacker_minions_atk | <b>嘲讽</b>。<b>亡语：</b>对所有敌方随从造成等同于本随从攻击力的伤害。 | [x]<b>Taunt</b> <b>Deathrattle:</b> Deal damage equal to this minion's Attack to all enemy minions. |
| REV_012 | 沼泽兽 | Bog Beast | 6 | 3/6 | MINION | 否 | 亡语:summon_enemy，召唤2/4，嘲讽 | <b>嘲讽</b>，<b>亡语：</b>召唤一滩2/4并具有<b>嘲讽</b>的泥浆。 | [x]<b><b>Taunt</b></b>  <b>Deathrattle:</b> Summon a 2/4  Muckmare with <b>Taunt</b>. |
| DINO_422 | 甲龙 | Ankylodon | 6 | 7/5 | MINION | 否 | 亡语:summon_attack_attackers，召唤3/3 | <b><b>嘲讽</b>。亡语：</b>随机召唤两只法力值消耗为（3）的野兽，并使其攻击随机敌人。 | [x]<b><b>Taunt</b>. Deathrattle:</b> Summon two random 3-Cost Beasts.  They attack random enemies. |
| AV_337 | 山岭野熊 | Mountain Bear | 7 | 5/6 | MINION | 否 | 亡语:summon_enemy，召唤2/4，嘲讽 | <b>嘲讽</b>，<b>亡语：</b>召唤两只2/4并具有<b>嘲讽</b>的山熊宝宝。 | [x]<b>Taunt</b> <b>Deathrattle:</b> Summon two 2/4 Cubs with <b>Taunt</b>. |
| CORE_AV_337 | 山岭野熊 | Mountain Bear | 7 | 5/6 | MINION | 否 | 亡语:summon_enemy，召唤2/4，嘲讽 | <b>嘲讽</b>，<b>亡语：</b>召唤两只2/4并具有<b>嘲讽</b>的山熊宝宝。 | [x]<b>Taunt</b> <b>Deathrattle:</b> Summon two 2/4 Cubs with <b>Taunt</b>. |
| ETC_526 | 凯吉·海德 | Cage Head | 8 | 5/1 | MINION | 否 | 亡语:summon_enemy，召唤9/9，嘲讽，冲锋 | <b>亡语：</b>召唤一只9/9并具有<b>冲锋</b>和<b>嘲讽</b>的凋零野猪。 | <b>Deathrattle:</b> Summon a 9/9 Blight Boar with <b>Charge</b> and <b>Taunt</b>. |
| GDB_331 | 分裂星岩 | Splitting Spacerock | 8 | 8/8 | MINION | 否 | 亡语:summon_enemy，召唤4/4 | <b>亡语：</b>召唤两个4/4的分裂块岩。 | <b>Deathrattle:</b> Summon two 4/4 Splitting Boulders. |
| BT_761 | 盘牙督军 | Coilfang Warlord | 8 | 9/5 | MINION | 否 | 亡语:summon_enemy，召唤5/9，嘲讽 | <b>突袭，亡语：</b>召唤一个5/9并具有<b>嘲讽</b> 的督军。 | [x]<b>Rush</b> <b>Deathrattle:</b> Summon a  5/9 Warlord with <b>Taunt</b>. |
| CORE_SW_068 | 莫尔葛熔魔 | Mo'arg Forgefiend | 8 | 8/8 | MINION | 否 | 亡语:enemy_armor，数值8 | <b>嘲讽</b>，<b>亡语：</b>获得8点护甲值。 | <b>Taunt</b> <b>Deathrattle:</b> Gain 8 Armor. |
| SW_068 | 莫尔葛熔魔 | Mo'arg Forgefiend | 8 | 8/8 | MINION | 否 | 亡语:enemy_armor，数值8 | <b>嘲讽</b>，<b>亡语：</b>获得8点护甲值。 | <b>Taunt</b> <b>Deathrattle:</b> Gain 8 Armor. |
| TOY_914 | 邪鬼皇后 | Wretched Queen | 8 | 4/4 | MINION | 否 | 亡语:summon_enemy，召唤4/6，嘲讽 | <b>嘲讽</b> <b>亡语：</b>召唤两个4/6并具有<b>嘲讽</b>的骑士。 | [x]<b>Taunt</b> <b>Deathrattle:</b> Summon two 4/6 Knights with <b>Taunt</b>. |
| EDR_421 | 年兽 | Omen | 10 | 6/12 | MINION | 否 | 亡语:all_attackers，数值1 | <b>突袭</b>。<b>风怒</b> <b>亡语：</b>对所有敌人造成1点伤害。<i>（在本随从攻击后提升！）</i> | [x]<b>Rush</b>, <b>Windfury</b> <b>Deathrattle:</b> Deal 1 damage to all enemies. <i>(Improves after this attacks!)</i> |
## 法术快速估算

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| CORE_CS2_072 | 背刺 | Backstab | 0 | - | SPELL | 否 | 快速估算直伤2，可打脸=否 | 对一个未受伤的随从造成$2点 伤害。 | Deal $2 damage to an undamaged minion. |
| CS2_072 | 背刺 | Backstab | 0 | - | SPELL | 否 | 快速估算直伤2，可打脸=否 | 对一个未受伤的随从造成$2点 伤害。 | Deal $2 damage to an undamaged minion. |
| CS2_037 | 冰霜震击 | Frost Shock | 1 | - | SPELL | 否 | 快速估算直伤1，可打脸=是 | 对一个敌方角色造成$1点伤害，并使其<b>冻结</b>。 | Deal $1 damage to an enemy character and <b>Freeze</b> it. |
| BT_175 | 双刃斩击 | Twin Slice | 1 | - | SPELL | 否 | 快速估算直伤2，可打脸=否 | 在本回合中，使你的英雄获得+2攻击力。将“二次斩击”置入你的手牌。 | Give your hero +2 Attack this turn. Add 'Second Slice' to your hand. |
| DS1_185 | 奥术射击 | Arcane Shot | 1 | - | SPELL | 否 | 快速估算直伤2，可打脸=是 | 造成$2点伤害。 | Deal $2 damage. |
| CORE_EX1_308 | 灵魂之火 | Soulfire | 1 | - | SPELL | 否 | 快速估算直伤4，可打脸=是 | 造成$4点伤害，随机弃一 张牌。 | [x]Deal $4 damage. Discard a random card. |
| EX1_308 | 灵魂之火 | Soulfire | 1 | - | SPELL | 否 | 快速估算直伤4，可打脸=是 | 造成$4点伤害，随机弃一 张牌。 | [x]Deal $4 damage. Discard a random card. |
| CORE_CS2_236 | 神圣之灵 | Divine Spirit | 1 | - | SPELL | 否 | 快速估算直伤2，可打脸=否 | 使一个随从的生命值翻倍。 | Double a minion's Health. |
| CS2_236 | 神圣之灵 | Divine Spirit | 1 | - | SPELL | 否 | 快速估算直伤2，可打脸=否 | 使一个随从的生命值翻倍。 | Double a minion's Health. |
| CORE_EX1_238 | 闪电箭 | Lightning Bolt | 1 | - | SPELL | 否 | 快速估算直伤3，可打脸=是 | 造成$3点伤害，<b>过载：</b>（1） | Deal $3 damage. <b>Overload:</b> (1) |
| EX1_238 | 闪电箭 | Lightning Bolt | 1 | - | SPELL | 否 | 快速估算直伤3，可打脸=是 | 造成$3点伤害，<b>过载：</b>（1） | Deal $3 damage. <b>Overload:</b> (1) |
| CS2_025 | 魔爆术 | Arcane Explosion | 1 | - | SPELL | 否 | 快速估算直伤3，可打脸=是 | 对所有敌方随从造成$1点伤害。 | Deal $1 damage to all enemy minions. |
| CS2_024 | 寒冰箭 | Frostbolt | 2 | - | SPELL | 否 | 快速估算直伤3，可打脸=是 | 对一个角色造成$3点伤害，并使其<b>冻结</b>。 | Deal $3 damage to a character and <b>Freeze</b> it. |
| EX1_154 | 愤怒 | Wrath | 2 | - | SPELL | 否 | 快速估算直伤3，可打脸=是 | <b>抉择：</b> 对一个随从造成$3点伤害；或者造成$1点伤害并抽一张牌。 | <b>Choose One -</b> Deal $3 damage to a minion; or $1 damage and draw a card. |
| CORE_EX1_400 | 旋风斩 | Whirlwind | 2 | - | SPELL | 否 | 快速估算直伤2，可打脸=是 | 对所有随从造成$1点伤害。 | Deal $1 damage to ALL minions. |
| EX1_400 | 旋风斩 | Whirlwind | 2 | - | SPELL | 否 | 快速估算直伤2，可打脸=是 | 对所有随从造成$1点伤害。 | Deal $1 damage to ALL minions. |
| EX1_278 | 毒刃 | Shiv | 2 | - | SPELL | 否 | 快速估算直伤1，可打脸=是 | 造成$1点伤害。抽一张牌。 | Deal $1 damage. Draw a card. |
| EX1_275 | 冰锥术 | Cone of Cold | 3 | - | SPELL | 否 | 快速估算直伤3，可打脸=是 | <b>冻结</b>一个随从和其相邻的随从，并对它们造成$1点伤害。 | <b>Freeze</b> a minion and the minions next to it, and deal $1 damage to them. |
| CS2_057 | 暗影箭 | Shadow Bolt | 3 | - | SPELL | 否 | 快速估算直伤4，可打脸=否 | 对一个随从造成$4点伤害。 | Deal $4 damage to a minion. |
| CORE_EX1_539 | 杀戮命令 | Kill Command | 3 | - | SPELL | 否 | 快速估算直伤5，可打脸=是 | 造成$3点伤害。如果你控制一个野兽，则改为造成 $5点伤害。 | Deal $3 damage. If you control a Beast, deal $5 damage instead. |
| EX1_539 | 杀戮命令 | Kill Command | 3 | - | SPELL | 否 | 快速估算直伤5，可打脸=是 | 造成$3点伤害。如果你控制一个野兽，则改为造成 $5点伤害。 | Deal $3 damage. If you control a Beast, deal $5 damage instead. |
| CORE_EX1_241 | 熔岩爆裂 | Lava Burst | 3 | - | SPELL | 否 | 快速估算直伤5，可打脸=是 | 造成$5点伤害，<b>过载：</b>（2） | Deal $5 damage. <b>Overload:</b> (2) |
| EX1_241 | 熔岩爆裂 | Lava Burst | 3 | - | SPELL | 否 | 快速估算直伤5，可打脸=是 | 造成$5点伤害，<b>过载：</b>（2） | Deal $5 damage. <b>Overload:</b> (2) |
| BT_801 | 眼棱 | Eye Beam | 4 | - | SPELL | 否 | 快速估算直伤3，可打脸=否 | <b>吸血</b>。 对一个随从造成$3点伤害。<b>流放：</b>法力值消耗为（1）点。 | <b>Lifesteal</b>. Deal $3 damage to a minion. <b>Outcast:</b> This costs (1). |
| EX1_279 | 炎爆术 | Pyroblast | 10 | - | SPELL | 否 | 快速估算直伤10，可打脸=是 | 造成$10点伤害。 | Deal $10 damage. |
## 冲锋快速估算

| card_id | 中文名 | 英文名 | 费用 | 攻/血 | 类型 | 随机 | 模拟说明 | 中文描述 | 英文描述 |
|---------|--------|--------|------|------|------|------|----------|----------|----------|
| CS2_150 | 雷矛特种兵 | Stormpike Commando | 1 | 4/2 | MINION | 否 | 快速估算冲锋打脸1 | <b>战吼：</b>造成2点伤害。 | <b>Battlecry:</b> Deal 2 damage. |
| WW_364t | 狡诈巨龙威拉罗克 | Velarok, the Deceiver | 3 | 3/3 | MINION | 否 | 快速估算冲锋打脸3 | <b>冲锋</b>。在本随从攻击后，<b>发现</b>一张另一职业的卡牌，其法力值消耗减少（3）点。 | [x]<b>Charge</b> After this attacks, <b>Discover</b> a card from another class. It costs (3) less. |
| CS2_124 | 狼骑兵 | Wolfrider | 3 | 3/1 | MINION | 否 | 快速估算冲锋打脸3 | <b>冲锋</b> | <b>Charge</b> |
| NEW1_011 | 库卡隆精英卫士 | Kor'kron Elite | 5 | 4/3 | MINION | 否 | 快速估算冲锋打脸5 | <b>冲锋</b> | <b>Charge</b> |
| EX1_116 | 火车王里诺艾 | Leeroy Jenkins | 6 | 6/2 | MINION | 否 | 快速估算冲锋打脸6 | <b>冲锋，战吼：</b> 为你的对手召唤两条1/1的雏龙。 | <b>Charge</b>. <b>Battlecry:</b> Summon two 1/1 Whelps for your opponent. |
