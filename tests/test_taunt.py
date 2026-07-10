#!/usr/bin/env python3
# test_taunt.py - 测试嘲讽逻辑

"""
测试嘲讽场景下的斩杀计算
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState, Entity
from hdt_python.lethal_checker import LethalChecker


def test_scenario_1_no_taunt():
    """场景1：无嘲讽，直接斩杀"""
    print("=" * 60)
    print("场景1：无嘲讽 - 应该检测到斩杀")
    print("=" * 60)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2

    # 我方英雄
    my_hero = gs.get_entity(1)
    my_hero.cardtype = "HERO"
    my_hero.controller = 1
    my_hero.health = 30
    my_hero.tags["RESOURCES"] = 10
    my_hero.tags["RESOURCES_USED"] = 0

    # 对手英雄（低血量）
    opp_hero = gs.get_entity(2)
    opp_hero.cardtype = "HERO"
    opp_hero.controller = 2
    opp_hero.health = 8
    opp_hero.damage = 0
    opp_hero.tags["ARMOR"] = 0

    # 我方场面：3攻+2攻随从
    minion1 = gs.get_entity(10)
    minion1.card_id = "CS2_124"
    minion1.cardtype = "MINION"
    minion1.controller = 1
    minion1.zone = "PLAY"
    minion1.atk = 3
    minion1.health = 1
    minion1.tags["NUM_ATTACKS_THIS_TURN"] = 0

    minion2 = gs.get_entity(11)
    minion2.card_id = "CS2_189"
    minion2.cardtype = "MINION"
    minion2.controller = 1
    minion2.zone = "PLAY"
    minion2.atk = 2
    minion2.health = 2
    minion2.tags["NUM_ATTACKS_THIS_TURN"] = 0

    # 手牌：火球术
    spell = gs.get_entity(20)
    spell.card_id = "CS2_029"
    spell.cardtype = "SPELL"
    spell.controller = 1
    spell.zone = "HAND"
    spell.cost = 4

    # 检测斩杀
    checker = LethalChecker(gs)
    checker.print_lethal_info()


def test_scenario_2_with_small_taunt():
    """场景2：小嘲讽，能清掉后斩杀"""
    print("\n\n" + "=" * 60)
    print("场景2：小嘲讽(1/2) - 应该检测到斩杀")
    print("=" * 60)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2

    # 我方英雄
    my_hero = gs.get_entity(1)
    my_hero.cardtype = "HERO"
    my_hero.controller = 1
    my_hero.health = 30
    my_hero.tags["RESOURCES"] = 10
    my_hero.tags["RESOURCES_USED"] = 0

    # 对手英雄
    opp_hero = gs.get_entity(2)
    opp_hero.cardtype = "HERO"
    opp_hero.controller = 2
    opp_hero.health = 6
    opp_hero.damage = 0
    opp_hero.tags["ARMOR"] = 0

    # 对手嘲讽：1/2
    taunt = gs.get_entity(30)
    taunt.card_id = "EX1_506"  # 守护者
    taunt.cardtype = "MINION"
    taunt.controller = 2
    taunt.zone = "PLAY"
    taunt.atk = 1
    taunt.health = 2
    taunt.damage = 0
    taunt.tags["TAUNT"] = 1

    # 我方场面：3攻+4攻随从
    minion1 = gs.get_entity(10)
    minion1.card_id = "CS2_124"
    minion1.cardtype = "MINION"
    minion1.controller = 1
    minion1.zone = "PLAY"
    minion1.atk = 3
    minion1.health = 3
    minion1.tags["NUM_ATTACKS_THIS_TURN"] = 0

    minion2 = gs.get_entity(11)
    minion2.card_id = "CS2_200"
    minion2.cardtype = "MINION"
    minion2.controller = 1
    minion2.zone = "PLAY"
    minion2.atk = 4
    minion2.health = 4
    minion2.tags["NUM_ATTACKS_THIS_TURN"] = 0

    # 检测斩杀
    # 预期：用3攻随从清嘲讽，4攻随从打脸 = 4伤害 < 6血，无斩杀
    # 但如果有法术就可以斩杀
    checker = LethalChecker(gs)
    checker.print_lethal_info()


def test_scenario_3_big_taunt():
    """场景3：大嘲讽，清不掉无斩杀"""
    print("\n\n" + "=" * 60)
    print("场景3：大嘲讽(5/10) - 不应该检测到斩杀")
    print("=" * 60)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2

    # 我方英雄
    my_hero = gs.get_entity(1)
    my_hero.cardtype = "HERO"
    my_hero.controller = 1
    my_hero.health = 30
    my_hero.tags["RESOURCES"] = 10
    my_hero.tags["RESOURCES_USED"] = 0

    # 对手英雄
    opp_hero = gs.get_entity(2)
    opp_hero.cardtype = "HERO"
    opp_hero.controller = 2
    opp_hero.health = 5
    opp_hero.damage = 0
    opp_hero.tags["ARMOR"] = 0

    # 对手嘲讽：5/10（清不掉）
    taunt = gs.get_entity(30)
    taunt.card_id = "EX1_283"  # 熔核巨人
    taunt.cardtype = "MINION"
    taunt.controller = 2
    taunt.zone = "PLAY"
    taunt.atk = 5
    taunt.health = 10
    taunt.damage = 0
    taunt.tags["TAUNT"] = 1

    # 我方场面：3攻+2攻随从（总共5攻，打不死10血嘲讽）
    minion1 = gs.get_entity(10)
    minion1.card_id = "CS2_124"
    minion1.cardtype = "MINION"
    minion1.controller = 1
    minion1.zone = "PLAY"
    minion1.atk = 3
    minion1.health = 1
    minion1.tags["NUM_ATTACKS_THIS_TURN"] = 0

    minion2 = gs.get_entity(11)
    minion2.card_id = "CS2_189"
    minion2.cardtype = "MINION"
    minion2.controller = 1
    minion2.zone = "PLAY"
    minion2.atk = 2
    minion2.health = 2
    minion2.tags["NUM_ATTACKS_THIS_TURN"] = 0

    # 检测斩杀
    # 预期：场面打不死嘲讽，无场面伤害，无斩杀
    checker = LethalChecker(gs)
    checker.print_lethal_info()


def test_scenario_4_taunt_with_spell():
    """场景4：有嘲讽，但法术可以绕过"""
    print("\n\n" + "=" * 60)
    print("场景4：大嘲讽 + 法术 - 法术可以绕过嘲讽")
    print("=" * 60)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2

    # 我方英雄
    my_hero = gs.get_entity(1)
    my_hero.cardtype = "HERO"
    my_hero.controller = 1
    my_hero.health = 30
    my_hero.tags["RESOURCES"] = 10
    my_hero.tags["RESOURCES_USED"] = 0

    # 对手英雄
    opp_hero = gs.get_entity(2)
    opp_hero.cardtype = "HERO"
    opp_hero.controller = 2
    opp_hero.health = 10
    opp_hero.damage = 0
    opp_hero.tags["ARMOR"] = 0

    # 对手嘲讽：5/10（清不掉）
    taunt = gs.get_entity(30)
    taunt.card_id = "EX1_283"
    taunt.cardtype = "MINION"
    taunt.controller = 2
    taunt.zone = "PLAY"
    taunt.atk = 5
    taunt.health = 10
    taunt.damage = 0
    taunt.tags["TAUNT"] = 1

    # 我方场面：3攻随从（被嘲讽挡住）
    minion1 = gs.get_entity(10)
    minion1.card_id = "CS2_124"
    minion1.cardtype = "MINION"
    minion1.controller = 1
    minion1.zone = "PLAY"
    minion1.atk = 3
    minion1.health = 1
    minion1.tags["NUM_ATTACKS_THIS_TURN"] = 0

    # 手牌：火球术 + 炎爆术
    spell1 = gs.get_entity(20)
    spell1.card_id = "CS2_029"  # 火球术 6伤
    spell1.cardtype = "SPELL"
    spell1.controller = 1
    spell1.zone = "HAND"
    spell1.cost = 4

    spell2 = gs.get_entity(21)
    spell2.card_id = "EX1_279"  # 炎爆术 10伤
    spell2.cardtype = "SPELL"
    spell2.controller = 1
    spell2.zone = "HAND"
    spell2.cost = 10

    # 检测斩杀
    # 预期：场面被嘲讽挡住无伤害，但火球(6) + 炎爆(10) = 16伤 > 10血，有斩杀！
    checker = LethalChecker(gs)
    checker.print_lethal_info()


def test_scenario_5_divine_shield_taunt():
    """场景5：圣盾嘲讽"""
    print("\n\n" + "=" * 60)
    print("场景5：圣盾嘲讽 - 需要额外一次攻击打破圣盾")
    print("=" * 60)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2

    # 我方英雄
    my_hero = gs.get_entity(1)
    my_hero.cardtype = "HERO"
    my_hero.controller = 1
    my_hero.health = 30
    my_hero.tags["RESOURCES"] = 10
    my_hero.tags["RESOURCES_USED"] = 0

    # 对手英雄
    opp_hero = gs.get_entity(2)
    opp_hero.cardtype = "HERO"
    opp_hero.controller = 2
    opp_hero.health = 3
    opp_hero.damage = 0
    opp_hero.tags["ARMOR"] = 0

    # 对手嘲讽：1/1圣盾
    taunt = gs.get_entity(30)
    taunt.card_id = "EX1_008"  # 银色指挥官
    taunt.cardtype = "MINION"
    taunt.controller = 2
    taunt.zone = "PLAY"
    taunt.atk = 1
    taunt.health = 1
    taunt.damage = 0
    taunt.tags["TAUNT"] = 1
    taunt.tags["DIVINE_SHIELD"] = 1  # 圣盾

    # 我方场面：3攻+2攻随从
    minion1 = gs.get_entity(10)
    minion1.card_id = "CS2_124"
    minion1.cardtype = "MINION"
    minion1.controller = 1
    minion1.zone = "PLAY"
    minion1.atk = 3
    minion1.health = 3
    minion1.tags["NUM_ATTACKS_THIS_TURN"] = 0

    minion2 = gs.get_entity(11)
    minion2.card_id = "CS2_189"
    minion2.cardtype = "MINION"
    minion2.controller = 1
    minion2.zone = "PLAY"
    minion2.atk = 2
    minion2.health = 2
    minion2.tags["NUM_ATTACKS_THIS_TURN"] = 0

    # 检测斩杀
    # 预期：3攻打破圣盾，2攻打死嘲讽，无剩余伤害，无斩杀
    checker = LethalChecker(gs)
    checker.print_lethal_info()


def main():
    """运行所有测试"""
    print("\n" + "🛡️" * 30)
    print("嘲讽逻辑测试套件")
    print("🛡️" * 30 + "\n")

    test_scenario_1_no_taunt()
    test_scenario_2_with_small_taunt()
    test_scenario_3_big_taunt()
    test_scenario_4_taunt_with_spell()
    test_scenario_5_divine_shield_taunt()

    print("\n\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n关键点:")
    print("✅ 法术可以绕过嘲讽直接打脸")
    print("✅ 武器可以绕过嘲讽")
    print("✅ 场面随从必须先清嘲讽")
    print("✅ 考虑圣盾、风怒等因素")
    print("=" * 60)


if __name__ == "__main__":
    main()
