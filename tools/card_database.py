# card_database.py - 炉石传说卡牌数据库
# 用于斩杀计算

"""
如何添加新卡牌:
1. 找到卡牌的 CardID（在 Power.log 中查看，或访问 https://hearthstonejson.com/）
2. 添加到相应的字典中
3. 格式: "CardID": (费用, 伤害, 是否需要目标)
"""

# ========================================
# 法术伤害卡牌
# ========================================

SPELL_DAMAGE = {
    # === 法师 ===
    "CS2_029": (4, 6, True),       # 火球术 Fireball
    "EX1_279": (10, 10, True),     # 炎爆术 Pyroblast
    "CS2_024": (2, 3, True),       # 寒冰箭 Frostbolt
    "CS2_025": (2, 1, False),      # 魔爆术 Arcane Explosion (仅敌方随从)
    "CS2_032": (7, 4, False),      # 烈焰风暴 Flamestrike (AOE)
    "EX1_275": (3, 3, True),       # 寒冰枪 Ice Lance (冻结目标0费)
    "NEW1_012": (4, 4, False),     # （遗留条目，勿与魔爆混淆）
    "CS2_023": (0, 1, True),       # 奥术智慧 Arcane Intellect (抽牌)
    "EX1_277": (1, 3, True),       # 奥术飞弹 Arcane Missiles
    "CORE_EX1_277": (1, 3, True),  # 奥术飞弹 Arcane Missiles
    "VAN_EX1_277": (1, 3, True),

    # === 术士 ===
    "CS2_057": (3, 4, True),       # 暗影箭 Shadow Bolt (只能打随从)
    "EX1_308": (1, 4, True),       # 灵魂虹吸 Soulfire
    "CS2_061": (1, 3, True),       # 腐蚀术 Corruption
    "EX1_309": (3, 3, True),       # 暗影烈焰 Shadowflame
    "CS2_062": (5, 2, True),       # 地狱烈焰 Hellfire (AOE包括自己)
    "EX1_320": (4, 3, True),       # 灵魂之火 Soulfire
    "CORE_EX1_308": (1, 4, True),  # 灵魂虹吸 Soulfire

    # === 猎人 ===
    "DS1_185": (1, 2, True),       # 奥术射击 Arcane Shot
    "EX1_539": (3, 5, True),       # 杀戮命令 Kill Command (有野兽5伤害)
    "DS1_183": (2, 3, False),      # 多重射击 Multi-Shot
    "EX1_549": (5, 5, True),       # 爆炸射击 Explosive Shot
    "CORE_EX1_539": (3, 5, True),  # 杀戮命令 Kill Command

    # === 德鲁伊 ===
    "CS2_012": (4, 4, True),       # 横扫 Swipe
    "EX1_154": (2, 3, True),       # 愤怒 Wrath
    "CS2_005": (1, 2, True),       # 爪击 Claw (给英雄+2攻)
    "EX1_161": (6, 5, True),       # 自然之力 Naturalize
    "CORE_CS2_012": (4, 4, True),  # 横扫 Swipe

    # === 盗贼 ===
    "CS2_072": (0, 2, True),       # 背刺 Backstab (未受伤随从)
    "CS2_076": (5, 0, True),       # 刺杀 Assassinate (消灭随从)
    "EX1_278": (2, 1, True),       # 刺骨 Shiv
    "EX1_133": (2, 2, True),       # 暗影打击 Shadow Strike (只能打随从)
    "CS2_074": (1, 0, False),      # 致命药膏 Deadly Poison (武器+2攻)
    "CORE_CS2_072": (0, 2, True),  # 背刺 Backstab

    # === 萨满 ===
    "CS2_037": (1, 1, True),       # 冰霜震击 Frost Shock
    "EX1_238": (1, 3, True),       # 闪电箭 Lightning Bolt
    "EX1_241": (3, 5, True),       # 熔岩爆裂 Lava Burst
    "CS2_042": (3, 0, True),       # 妖术 Hex (变羊)
    "EX1_245": (5, 3, False),      # 地震术 Earthquake (AOE)
    "CORE_EX1_238": (1, 3, True),  # 闪电箭 Lightning Bolt
    "CORE_EX1_241": (3, 5, True),  # 熔岩爆裂 Lava Burst

    # === 牧师 ===
    "CS2_236": (1, 2, True),       # 神圣惩击 Holy Smite
    "CS1_130": (5, 2, False),      # 神圣新星 Holy Nova (AOE)
    "CS2_234": (2, 0, True),       # 暗言术：痛 Shadow Word: Pain (消灭)
    "EX1_332": (6, 5, True),       # 暗言术：灭 Shadow Word: Death
    "CORE_CS2_236": (1, 2, True),  # 神圣惩击 Holy Smite

    # === 战士 ===
    "CS2_108": (1, 0, True),       # 斩杀 Execute (消灭受伤随从)
    "EX1_400": (2, 2, True),       # 猛击 Slam
    "CS2_114": (3, 2, False),      # 顺劈斩 Cleave (2个敌方随从)
    "EX1_391": (1, 1, True),       # 冲锋 Charge (给随从+2攻和冲锋)
    "CORE_EX1_400": (2, 2, True),  # 猛击 Slam

    # === 圣骑士 ===
    "CS2_094": (4, 3, True),       # 锤击 Hammer of Wrath
    "EX1_360": (5, 0, True),       # 神圣愤怒 Holy Wrath (随机伤害)
    "CS2_093": (1, 1, True),       # 奉献 Consecration (AOE)
    "EX1_355": (2, 2, True),       # 正义之剑 Blessing of Might
    "CORE_CS2_094": (4, 3, True),  # 锤击 Hammer of Wrath

    # === 恶魔猎手 ===
    "BT_175": (1, 1, True),        # 混乱打击 Chaos Strike
    "BT_801": (4, 3, True),        # 眼棱 Eye Beam
    "BT_480": (0, 1, True),        # 旁观者 Spectral Sight

    # === 中立 ===
}

# ========================================
# 冲锋/战吼伤害随从
# ========================================

CHARGE_MINIONS = {
    # === 中立 ===
    "CS2_124": (3, "charge", 3),       # 狼骑兵 Wolfrider 3/1冲锋
    "CS2_150": (1, "charge", 1),       # 银色侍从 Stonetusk Boar 1/1冲锋
    "EX1_116": (6, "charge", 6),       # 雷矛特种兵 Reckless Rocketeer 6/3冲锋
    "EX1_162": (4, "charge", 4),       # 狂野雄鹿 Dragonhawk Rider 4/2冲锋
    "NEW1_023": (4, "charge", 4),      # 破法者 Spellbreaker 4/3

    # === 战士 ===
    "NEW1_011": (5, "charge", 5),      # 恐怖的奴隶主 Kor'kron Elite 5/5冲锋
    "CS2_103": (3, "charge", 3),       # 冲锋 Charge +2攻击和冲锋
    "EX1_414": (1, "spell", 2),        # 冲锋 Charge (法术)

    # === 猎人 ===
    "DS1_070": (3, "charge", 4),       # 狂野雄鹿 Wolfrider 4/2冲锋
    "NEW1_033": (5, "charge", 4),      # 森林狼 Tundra Rhino 4/4

    # === 圣骑士 ===
    "CS2_093": (3, "charge", 3),       # 圣骑士的冲锋 Stonetusk Boar
    "EX1_379": (3, "charge", 3),       # 飞刀杂耍者 Knife Juggler (战吼)

    # === 萨满 ===
    "EX1_248": (5, "charge", 5),       # 白银之手骑士 Silvermoon Guardian

    # 战吼伤害随从
    "CS2_188": (4, "battlecry", 3),    # 火元素 Fire Elemental 战吼3伤害
    "EX1_011": (1, "battlecry", 1),    # 麻疯侏儒 Leper Gnome 战吼1伤害
    "NEW1_017": (3, "battlecry", 2),   # 蓝鳃战士 Bluegill Warrior 2/1冲锋
}

# ========================================
# 武器
# ========================================

WEAPONS = {
    # === 战士 ===
    "CS2_106": (1, 1, 3),          # 炽炎战斧 Fiery War Axe 3/2
    "EX1_411": (5, 5, 2),          # 血吼 Gorehowl 7/1
    "CS2_112": (7, 7, 1),          # 奥金斧 Arcanite Reaper 5/2

    # === 圣骑士 ===
    "CS2_097": (4, 4, 2),          # 真银圣剑 Truesilver Champion 4/2
    "EX1_383": (1, 1, 4),          # 圣光之剑 Lights Justice 1/4

    # === 猎人 ===
    "CS2_084": (3, 3, 2),          # 鹰弓 Eaglehorn Bow 3/2

    # === 盗贼 ===
    "CS2_080": (1, 1, 2),          # 刺客之刃 Assassins Blade 1/2
    "NEW1_019": (3, 3, 2),         # 刀扇 Blade Flurry

    # === 萨满 ===
    "CS2_039": (5, 5, 2),          # 风怒 Doomhammer 2/8 风怒

    # === 恶魔猎手 ===
    "BT_921": (5, 5, 2),           # 双刃 Twin Slice
}

# ========================================
# 解场法术（参与场攻/清嘲讽模拟，定义在 hdt_python/spell_board.py）
# ========================================
# 已内置:
#   EDR_476       月亮井       — 6费，全体敌人4伤(含英雄)+友方回4；埃提耶识下翻倍
#   CATA_308      麦迪文的胜利 — 5费(控传说1费)，全体随从4伤；埃提耶识下翻倍
# 埃提耶识武器: TIME_890t（法术伤害/治疗 x2）
# 追加新法术: 编辑 hdt_python/spell_board.py 的 _register(...)


SPECIAL_CARDS = {
    # 需要特殊处理的卡牌

    # 杀戮命令：有野兽5伤害，否则3伤害
    "EX1_539": {
        "type": "conditional_damage",
        "base_damage": 3,
        "condition_damage": 5,
        "condition": "has_beast"
    },

    # 火元素：战吼造成3点伤害
    "CS2_188": {
        "type": "battlecry_damage",
        "damage": 3
    },

    # 灵魂虹吸：弃一张牌
    "EX1_308": {
        "type": "discard_card",
        "damage": 4
    },
}

# ========================================
# 英雄技能伤害
# ========================================

HERO_POWER_DAMAGE = {
    "CS2_034": 1,  # 火焰冲击 (法师)
    "CS2_054": 2,  # 吸血 (术士，伤害自己2点)
    "CS2_083": 2,  # 稳固射击 (猎人)
    "BT_292": 1,  # 恶魔之咬 (恶魔猎手)
}

# ========================================
# 工具函数
# ========================================

def get_spell_damage(card_id: str, spell_power: int = 0) -> int:
    """
    获取法术伤害

    Args:
        card_id: 卡牌ID
        spell_power: 法术伤害加成

    Returns:
        伤害值
    """
    if card_id in SPELL_DAMAGE:
        cost, base_damage, needs_target = SPELL_DAMAGE[card_id]
        return base_damage + spell_power
    return 0


def get_charge_damage(card_id: str) -> int:
    """获取冲锋随从伤害"""
    if card_id in CHARGE_MINIONS:
        cost, dmg_type, damage = CHARGE_MINIONS[card_id]
        if dmg_type in ["charge", "battlecry"]:
            return damage
    return 0


def get_weapon_damage(card_id: str) -> int:
    """获取武器伤害"""
    if card_id in WEAPONS:
        cost, attack, durability = WEAPONS[card_id]
        return attack
    return 0


def is_direct_damage_spell(card_id: str) -> bool:
    """判断是否为直接伤害法术"""
    return card_id in SPELL_DAMAGE


def calculate_mana_cost(card_id: str, current_cost: int = None) -> int:
    """
    计算卡牌费用（考虑减费效果）

    Args:
        card_id: 卡牌ID
        current_cost: 当前费用（如果有减费）

    Returns:
        实际费用
    """
    if current_cost is not None:
        return current_cost

    # 从数据库获取基础费用
    if card_id in SPELL_DAMAGE:
        return SPELL_DAMAGE[card_id][0]
    elif card_id in CHARGE_MINIONS:
        return CHARGE_MINIONS[card_id][0]
    elif card_id in WEAPONS:
        return WEAPONS[card_id][0]

    return 999  # 未知卡牌，默认很高费用


# ========================================
# 数据库统计
# ========================================

def print_database_stats():
    """打印数据库统计信息"""
    print("=" * 60)
    print("炉石传说卡牌数据库统计")
    print("=" * 60)
    print(f"法术伤害卡牌: {len(SPELL_DAMAGE)} 张")
    print(f"冲锋/战吼随从: {len(CHARGE_MINIONS)} 张")
    print(f"武器: {len(WEAPONS)} 张")
    print(f"特殊卡牌: {len(SPECIAL_CARDS)} 张")
    print("=" * 60)

    print("\n法术伤害卡牌列表:")
    for card_id, (cost, damage, needs_target) in sorted(SPELL_DAMAGE.items(), key=lambda x: x[1][0]):
        target = "需要目标" if needs_target else "AOE/随机"
        print(f"  {card_id}: {cost}费 {damage}伤害 ({target})")


if __name__ == "__main__":
    print_database_stats()

    # 测试示例
    print("\n" + "=" * 60)
    print("测试示例")
    print("=" * 60)

    test_cards = ["CS2_029", "EX1_539", "CS2_124"]
    spell_power = 1

    for card_id in test_cards:
        spell_dmg = get_spell_damage(card_id, spell_power)
        charge_dmg = get_charge_damage(card_id)
        weapon_dmg = get_weapon_damage(card_id)

        print(f"\n卡牌: {card_id}")
        if spell_dmg > 0:
            print(f"  法术伤害: {spell_dmg} (包含+{spell_power}法伤)")
        if charge_dmg > 0:
            print(f"  冲锋伤害: {charge_dmg}")
        if weapon_dmg > 0:
            print(f"  武器伤害: {weapon_dmg}")
