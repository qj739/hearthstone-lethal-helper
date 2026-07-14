# 竞技场新赛季新增接入卡牌

> 来源: `ARENA_GAP_REPORT.md` 缺口清单批量接入
> 合计: **200** 条注册

## 总览

| 模块 | 新增数 |
|------|--------|
| 法术 | 71 |
| 战吼 | 30 |
| 突袭 | 44 |
| 武器 | 26 |
| 连击 | 12 |
| 亡语 | 10 |
| 回合结束 | 7 |

## 明细

### 法术（71）

| card_id | 中文名 | 实现 |
|---------|--------|------|
| `END_025` | 永时火焰箭 | minion_direct(3) |
| `JAM_022` | 致聋术 | minion_direct(2) |
| `CORE_CS2_032` | 烈焰风暴 | enemy_aoe(5) |
| `END_023` | 苦涩结局 | 冻结邻接v1消灭受伤 |
| `END_028` | 力敌万世 | destroy_atk_le(4) |
| `REV_840` | 死神之躯 | all_minions_aoe(2) |
| `END_007` | 发挥优势 | direct_plus_hero(1) |
| `END_014` | 协作火花 | face_direct(3) |
| `REV_252` | 净场 | destroy_atk_le(3) |
| `REV_364` | 雄鹿冲锋 | face_direct(3) |
| `CORE_BT_072` | 深度冻结 | 冻结+水元素v1不计 |
| `RLK_024` | 灵界打击 | minion_direct(6) |
| `REV_369` | 间接伤害 | random_enemy_minions(6) |
| `CORE_CS1_130` | 神圣惩击 | minion_direct(3) |
| `CORE_BRM_013` | 快速射击 | face_direct(3) |
| `JAM_013` | 即兴演奏 | all_other_minions(1) |
| `MAW_019` | 谋杀指控 | 延迟消灭v1立即 |
| `ETC_305` | 暗弦术：改 | destroy_weak(5) |
| `CORE_LOOT_101` | 爆炸符文 | 奥秘 |
| `CATA_EVENT_402` | 致命贿赂 | destroy_any |
| `TOY_714` | 飞速离架 | enemy_aoe(1) |
| `CORE_CS2_076` | 刺杀 | destroy_enemy |
| `END_020` | 永时困苦 | minion_direct(1) |
| `RLK_025` | 冰霜打击 | minion_direct(3) |
| `CORE_EX1_610` | 爆炸陷阱 | 奥秘 |
| `REV_834` | 灭绝圣物 | random_enemy_minion_hits(1) |
| `TOY_640` | 工坊事故 | minion_direct(5) |
| `TIME_001` | 时空飞刃 | random_split_enemies(6) |
| `CORE_BAR_801` | 击伤猎物 | face_direct(1) |
| `TLC_365` | 乱翻库存 | minion_direct(3) |
| `TIME_441` | 永世裂痕 | random_split_enemies(8) |
| `MAW_023` | 盗窃指控 | 延迟消灭v1立即 |
| `MIS_701` | 恋旧风潮 | noop |
| `CORE_EX1_197` | 暗言术：毁 | destroy_atk_ge(5) |
| `VAC_460` | 把经理叫来！ | face_direct(2) |
| `MIS_709` | 圣光荧光棒 | minion_direct(4) |
| `CORE_CS2_108` | 斩杀 | destroy_damaged_enemy |
| `CORE_BAR_311` | 噬灵疫病 | random_split_enemies(4) |
| `REV_920` | 可信的伪装 | noop |
| `JAM_008` | 直播事故 | noop |
| `TIME_218` | 静电震击 | direct_plus_hero(1) |
| `TIME_715` | 为了荣耀！ | noop |
| `ETC_528` | 灯光表演 | random_split_enemies(4) |
| `CORE_ICC_055` | 吸取灵魂 | minion_direct(3) |
| `MAW_010` | 否决动议 | 奥秘 |
| `CORE_EX1_302` | 死亡缠绕 | minion_direct(1) |
| `TIME_027` | 超光子弹幕 | random_split_enemies(6) |
| `MIS_027` | 多米诺效应 | minion_direct(2) |
| `ETC_356` | 变音和弦 | minion_direct(6) |
| `MAW_001` | 纵火指控 | 延迟消灭v1立即 |
| `TIME_212` | 引雷针 | minion_direct(4) |
| `CORE_SW_442` | 虚空碎片 | face_direct(4) |
| `REV_924` | 始源之潮 | noop |
| `REV_950` | 圣洁鸣钟 | noop |
| `TOY_384` | 净化之力 | noop |
| `ONY_011` | 别站在火里！ | random_split_enemies(10) |
| `CORE_RLK_035` | 邪爆 | all_minions_aoe(1) |
| `MIS_707` | 批量生产 | face_direct(3) |
| `CORE_BOT_222` | 灵魂炸弹 | minion_direct(4) |
| `EX1_312` | 扭曲虚空 | destroy_all_minions |
| `CORE_ULD_152` | 压感陷阱 | 奥秘 |
| `SCH_514` | 亡者复生 | noop |
| `LOOT_504` | 不稳定的异变 | noop |
| `ETC_413` | 低沉摇摆 | hero_attack(2) |
| `DEEP_011` | 灼燃之心 | minion_direct(2) |
| `TOY_800` | 闪光试剂瓶 | face_direct(2) |
| `ETC_362` | 跳吧，虫子！ | noop |
| `TOY_602` | 化工泄漏 | noop |
| `BT_134` | 沼泽射线 | face_direct(3) |
| `TOY_529` | 死亡轮盘 | noop |
| `CORE_EX1_407` | 绝命乱斗 | 留一随机v1全灭 |

### 战吼（30）

| card_id | 中文名 | 实现 |
|---------|--------|------|
| `TOY_520` | 秘迹观测者 | destroy_enemy |
| `TOY_375` | 滑冰元素 | 无直伤战吼 |
| `CORE_SW_072` | 锈烂蝰蛇 | destroy_enemy |
| `CORE_UNG_205` | 冰川裂片 | 无直伤战吼 |
| `CORE_REV_023` | 拆迁修理工 | destroy_enemy |
| `END_034` | 碎裂扫荡者 | 随机随从/地标/武器v1消灭随从 |
| `CORE_CFM_753` | 污手街供货商 | 无直伤战吼 |
| `CORE_EX1_082` | 疯狂投弹者 | random_split_characters |
| `TIME_EVENT_301` | 灭世信徒 | 龙数重复v1一次 |
| `TOY_388` | 粉笔美术家 | 无直伤战吼 |
| `TIME_875` | 半兽人迦罗娜 | destroy_enemy |
| `END_021` | 次元武器匠 | 无直伤战吼 |
| `TIME_019` | 时间流具象 | all_enemies |
| `CORE_EX1_005` | 王牌猎人 | destroy_high_atk |
| `ETC_110` | 封面艺人 | 无直伤战吼 |
| `TOY_357` | 抱龙王噗鲁什 | 冲锋+弹回 |
| `CORE_UNG_848` | 始生幼龙 | all_other_minions |
| `TOY_504` | 神秘女巫哈加莎 | 无直伤战吼 |
| `TIME_EVENT_998` | 时光卫士露妮 | 无直伤战吼 |
| `YOG_525` | 健身肌器人 | 无直伤战吼 |
| `RLK_593` | 洛瑟玛·塞隆 | 无直伤战吼 |
| `LOOT_389` | 狗头人拾荒者 | destroy_enemy |
| `CORE_OG_149` | 暴虐食尸鬼 | all_other_minions |
| `LOOT_161` | 食肉魔块 | destroy_enemy |
| `MAW_000` | 冒牌小鬼 | 无直伤战吼 |
| `YOG_501` | 历战无面者 | 无直伤战吼 |
| `CATA_EVENT_002` | 怨毒焰魔 | destroy_enemy |
| `CORE_ULD_165` | 裂隙屠夫 | destroy_enemy |
| `NEW1_030` | 死亡之翼 | all_other_minions_destroy |
| `END_035` | 末世之兆 | destroy_enemy |

### 突袭（44）

| card_id | 中文名 | 实现 |
|---------|--------|------|
| `TOY_894` | 折纸青蛙 | default_rush |
| `JAM_033` | 混搭乐师 | default_rush |
| `ETC_325` | 音乐治疗师 | default_rush |
| `JAM_027` | 饭圈迷弟 | default_rush |
| `TOY_517` | 泼漆彩鳍鱼人 | default_rush |
| `END_032` | 飞翼畸变体 | default_rush |
| `TOY_823` | 彩虹裁缝 | default_rush |
| `ETC_742` | 摇滚巨石 | default_rush |
| `JAM_021` | 单曲流星 | default_rush |
| `CS3_038` | 红鳃锋颚战士 | default_rush |
| `MAW_009` | 影犬 | default_rush |
| `REV_015` | 假面狂欢者 | default_rush |
| `TLC_436` | 重生的翼手龙 | default_rush |
| `TIME_605` | 纪元追猎者 | default_rush |
| `TOY_821` | 毛绒暴暴狗 | default_rush |
| `ETC_419` | 摇滚缝合怪 | default_rush |
| `TIME_051` | 永恒龙士兵 | default_rush |
| `BOT_548` | 奇利亚斯 | default_rush |
| `TIME_050` | 灵知沙漏 | default_rush |
| `ETC_035` | 鼓乐独演者 | default_rush |
| `REV_314` | 灌木巨龙托匹奥 | default_rush |
| `CORE_RLK_657` | 地底虫王 | default_rush |
| `ETC_073` | 押韵狂人 | default_rush |
| `MIS_306` | 火箭跳蛙 | default_rush |
| `TIME_022` | 累世巨蛇 | default_rush |
| `ETC_408` | 滑铲铁腿 | default_rush |
| `ETC_410` | 蛇啮鼓手 | default_rush |
| `MAW_030` | 托加斯特管理员 | default_rush |
| `MAW_020` | 潦草的书记员 | default_rush |
| `MIS_711` | 安全专家 | default_rush |
| `ETC_836` | 穆克拉先生 | default_rush |
| `AV_339` | 圣殿骑士队长 | default_rush |
| `ETC_840` | 班卓龙 | default_rush |
| `ETC_399` | 哈维利亚·墨鸦 | default_rush |
| `BT_123` | 卡加斯·刃拳 | default_rush |
| `REV_961` | 势利精英 | default_rush |
| `CORE_TTN_843` | 艾瑞达欺诈者 | default_rush |
| `RLK_212` | 安尼赫兰蛮魔 | default_rush |
| `TOY_812` | 皮普希·彩蹄 | default_rush |
| `DMF_226` | 刀锋舞娘 | default_rush |
| `REV_316` | 活体利刃蕾茉妮雅 | default_rush |
| `TIME_872` | 不败冠军 | default_rush |
| `DMF_523` | 碰碰车 | default_rush |
| `TIME_063` | 时光之主诺兹多姆 | default_rush |

### 武器（26）

| card_id | 中文名 | 实现 |
|---------|--------|------|
| `MIS_101` | 海绵斧 | equip |
| `CORE_TRL_111` | 猎头者之斧 | equip |
| `TIME_444` | 迷时战刃 | equip |
| `ETC_317` | 迪斯科战槌 | equip |
| `TOY_522` | 水弹枪 | 水弹枪1/1海盗v1默认 |
| `ETC_832` | 丛林弹唱琴 | equip |
| `ETC_388` | 实木手鼓 | equip |
| `CORE_BT_921` | 奥达奇战刃 | equip |
| `REV_917` | 石雕凿刀 | equip |
| `JAM_011` | 风领主的管号 | equip |
| `ETC_405` | 战刃吉他 | equip |
| `TOY_604` | 砰砰扳手 | equip |
| `END_012` | 无穷之手 | 无穷之手v1默认 |
| `JAM_015` | 混搭音叉 | equip |
| `ETC_813` | 爵士贝斯 | equip |
| `ETC_312` | 爱豆的爱 | equip |
| `CORE_GVG_059` | 齿轮光锤 | equip |
| `ETC_518` | 搓盘机 | equip |
| `ETC_520` | 科多兽皮组鼓 | 亡语1伤全场v1默认 |
| `END_016` | 时空之爪 | equip |
| `ETC_084` | 邪弦竖琴 | equip |
| `TLC_EVENT_402` | 末日使者之杖 | 亡语全灭v1默认 |
| `CORE_OG_031` | 暮光神锤 | equip |
| `CORE_RLK_086` | 霜之哀伤 | equip |
| `CORE_LOOT_044` | 铁刃护手 | equip |
| `CORE_BT_781` | 埃辛诺斯壁垒 | equip |

### 连击（12）

| card_id | 中文名 | 实现 |
|---------|--------|------|
| `END_032` | 飞翼畸变体 | 连击免疫v1默认突袭 |
| `TOY_516` | 折价区海盗 | rush_p0已注册 |
| `JAM_021` | 单曲流星 | 连击剧毒v1默认突袭 |
| `ETC_077` | 八爪碟机 | combo_body_only |
| `ETC_072` | B-Box拳手 | random_split_enemies |
| `CORE_EX1_134` | 军情七处特工 | face_direct |
| `TIME_710` | 暴徒双人组 | summon_copy |
| `REV_826` | 私家眼线 | combo_body_only |
| `CORE_DMF_511` | 狐人老千 | combo_body_only |
| `ETC_073` | 押韵狂人 | rush_default |
| `CORE_EX1_131` | 迪菲亚头目 | 2/1强盗 |
| `CORE_BOT_576` | 疯狂的药剂师 | buff_friendly |

### 亡语（10）

| card_id | 中文名 | 实现 |
|---------|--------|------|
| `REV_356` | 狂蝠来宾 | summon_enemy |
| `TOY_670` | 欢乐的玩具匠 | summon_enemy |
| `TIME_017` | 坦克机械师 | summon_enemy |
| `TLC_468` | 黏团焦油 | summon_enemy |
| `REV_012` | 沼泽兽 | summon_enemy |
| `TOY_814` | 玩具兵盒 | summon_enemy |
| `GDB_331` | 分裂星岩 | summon_enemy |
| `BOT_700` | 大铡蟹 | summon_enemy |
| `TOY_908` | 焰火机师 | random_split_attackers |
| `CORE_SW_439` | 活泼的松鼠 | summon_enemy |

### 回合结束（7）

| card_id | 中文名 | 实现 |
|---------|--------|------|
| `TOY_824` | 黑棘针线师 | random_split_enemies |
| `TOY_820` | 废弃电子玩偶 | attack_lowest_enemy |
| `CORE_TTN_866` | 神秘恐魔 | hero_damage |
| `YOP_034` | 窜逃的黑翼龙 | random_enemy_minion |
| `CORE_YOP_034` | 窜逃的黑翼龙 | random_enemy_minion |
| `BAR_063` | 甜水鱼人斥候 | all_enemies_damage |
| `BAR_064` | 精明的奥术师 | all_enemies_damage |

## 说明

- **完整**：效果与卡牌文本一致或接近
- **简化/v1**：仅模拟主要伤害/场攻贡献，忽略发现、奥秘触发、延迟消灭等
- 修改缺口清单后重新运行 `python scripts/export_arena_new_cards.py` 可刷新本文档
