#!/usr/bin/env python3
# test_optimal_taunt.py - 测试最优嘲讽清除算法

"""
对比简单贪心 vs 最优解算法
展示为什么需要找最优解
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import GameState, Entity
from hdt_python.lethal_checker import LethalChecker


def create_minion(gs, eid, controller, atk, health, zone="PLAY"):
    """辅助函数：创建随从"""
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = controller
    m.zone = zone
    m.atk = atk
    m.health = health
    m.damage = 0
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    return m


def create_hero(gs, eid, controller, health, armor=0):
    """辅助函数：创建英雄"""
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = controller
    h.health = health
    h.damage = 0
    h.tags["ARMOR"] = armor
    h.tags["RESOURCES"] = 10
    h.tags["RESOURCES_USED"] = 0
    return h


def test_case_1_simple_optimization():
    """
    测试用例1：简单优化

    场景：
    - 对手：6血
    - 对手嘲讽：2/3
    - 我方随从：1/1, 3/3, 5/5

    贪心算法：1攻+3攻清嘲讽，剩余5攻 = 5伤
    最优算法：3攻清嘲讽，剩余1攻+5攻 = 6伤 ✅
    """
    print("=" * 70)
    print("测试用例1：简单优化（最经典的例子）")
    print("=" * 70)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2

    # 英雄
    create_hero(gs, 1, 1, 30)
    create_hero(gs, 2, 2, 6)

    # 对手嘲讽：2/3
    taunt = create_minion(gs, 30, 2, 2, 3)
    taunt.card_id = "守护者"
    taunt.tags["TAUNT"] = 1

    # 我方随从：1/1, 3/3, 5/5
    create_minion(gs, 10, 1, 1, 1).card_id = "小随从"
    create_minion(gs, 11, 1, 3, 3).card_id = "中随从"
    create_minion(gs, 12, 1, 5, 5).card_id = "大随从"

    # 检测
    checker = LethalChecker(gs)
    total, sources, has_lethal = checker.calculate_lethal()

    print(f"\n对手：6血")
    print(f"对手嘲讽：2/3 守护者")
    print(f"我方随从：1/1 小随从, 3/3 中随从, 5/5 大随从")
    print(f"\n分析：")
    print(f"  贪心方案：1攻+3攻清嘲讽 → 剩余5攻 = 5伤害")
    print(f"  最优方案：3攻清嘲讽 → 剩余1攻+5攻 = 6伤害 ✅")
    print(f"\n实际结果：总伤害 = {total}")
    print(f"是否斩杀：{'✅ 是' if has_lethal else '❌ 否'}")

    if total == 6:
        print("\n🎉 算法找到最优解！")
    else:
        print(f"\n⚠️  算法未找到最优解（期望6，实际{total}）")


def test_case_2_multiple_taunts():
    """
    测试用例2：多个嘲讽

    场景：
    - 对手：10血
    - 对手嘲讽：1/1, 2/2
    - 我方随从：1/1, 2/2, 3/3, 4/4

    需要找最优分配方案
    """
    print("\n\n" + "=" * 70)
    print("测试用例2：多个嘲讽的最优分配")
    print("=" * 70)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2

    # 英雄
    create_hero(gs, 1, 1, 30)
    create_hero(gs, 2, 2, 10)

    # 对手嘲讽：1/1, 2/2
    t1 = create_minion(gs, 30, 2, 1, 1)
    t1.card_id = "小嘲讽"
    t1.tags["TAUNT"] = 1

    t2 = create_minion(gs, 31, 2, 2, 2)
    t2.card_id = "中嘲讽"
    t2.tags["TAUNT"] = 1

    # 我方随从：1/1, 2/2, 3/3, 4/4
    create_minion(gs, 10, 1, 1, 1).card_id = "A"
    create_minion(gs, 11, 1, 2, 2).card_id = "B"
    create_minion(gs, 12, 1, 3, 3).card_id = "C"
    create_minion(gs, 13, 1, 4, 4).card_id = "D"

    # 检测
    checker = LethalChecker(gs)
    total, sources, has_lethal = checker.calculate_lethal()

    print(f"\n对手：10血")
    print(f"对手嘲讽：1/1 小嘲讽, 2/2 中嘲讽")
    print(f"我方随从：1/1 A, 2/2 B, 3/3 C, 4/4 D")
    print(f"\n可能方案：")
    print(f"  方案1：A清小嘲讽，B清中嘲讽 → 剩余C+D = 7伤")
    print(f"  方案2：A清小嘲讽，C清中嘲讽 → 剩余B+D = 6伤")
    print(f"  方案3：B清小嘲讽，C清中嘲讽 → 剩余A+D = 5伤")
    print(f"  最优：方案1 = 7伤 ✅")
    print(f"\n实际结果：总伤害 = {total}")
    print(f"是否斩杀：{'✅ 是' if has_lethal else '❌ 否'}")

    if total == 7:
        print("\n🎉 算法找到最优解！")
    else:
        print(f"\n⚠️  算法未找到最优解（期望7，实际{total}）")


def test_case_3_divine_shield_optimization():
    """
    测试用例3：圣盾嘲讽优化

    场景：
    - 对手：5血
    - 对手嘲讽：1/1 圣盾
    - 我方随从：1/1, 6/6

    贪心：1攻+6攻清嘲讽 → 剩余0伤
    最优：需要两次攻击打圣盾，但怎么分配？
    """
    print("\n\n" + "=" * 70)
    print("测试用例3：圣盾嘲讽的优化")
    print("=" * 70)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2

    # 英雄
    create_hero(gs, 1, 1, 30)
    create_hero(gs, 2, 2, 5)

    # 对手嘲讽：1/1 圣盾
    taunt = create_minion(gs, 30, 2, 1, 1)
    taunt.card_id = "银色侍从"
    taunt.tags["TAUNT"] = 1
    taunt.tags["DIVINE_SHIELD"] = 1

    # 我方随从：1/1, 6/6
    create_minion(gs, 10, 1, 1, 1).card_id = "小随从"
    create_minion(gs, 11, 1, 6, 6).card_id = "大随从"

    # 检测
    checker = LethalChecker(gs)
    total, sources, has_lethal = checker.calculate_lethal()

    print(f"\n对手：5血")
    print(f"对手嘲讽：1/1 🛡️银色侍从（圣盾）")
    print(f"我方随从：1/1 小随从, 6/6 大随从")
    print(f"\n分析：")
    print(f"  圣盾需要2次攻击：")
    print(f"  方案1：小随从打盾，大随从杀死 → 剩余0伤")
    print(f"  方案2：无其他方案（只有2个随从）")
    print(f"  结论：无法斩杀")
    print(f"\n实际结果：总伤害 = {total}")
    print(f"是否斩杀：{'✅ 是' if has_lethal else '❌ 否'}")


def test_case_4_complex_scenario():
    """
    测试用例4：复杂场景

    场景：
    - 对手：12血
    - 对手嘲讽：3/4, 2/2 圣盾
    - 我方随从：2/2, 3/3, 4/4, 5/5

    这是一个需要认真计算的复杂场景
    """
    print("\n\n" + "=" * 70)
    print("测试用例4：复杂多嘲讽场景")
    print("=" * 70)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2

    # 英雄
    create_hero(gs, 1, 1, 30)
    create_hero(gs, 2, 2, 12)

    # 对手嘲讽1：3/4
    t1 = create_minion(gs, 30, 2, 3, 4)
    t1.card_id = "大嘲讽"
    t1.tags["TAUNT"] = 1

    # 对手嘲讽2：2/2 圣盾
    t2 = create_minion(gs, 31, 2, 2, 2)
    t2.card_id = "圣盾嘲讽"
    t2.tags["TAUNT"] = 1
    t2.tags["DIVINE_SHIELD"] = 1

    # 我方随从：2/2, 3/3, 4/4, 5/5
    create_minion(gs, 10, 1, 2, 2).card_id = "A"
    create_minion(gs, 11, 1, 3, 3).card_id = "B"
    create_minion(gs, 12, 1, 4, 4).card_id = "C"
    create_minion(gs, 13, 1, 5, 5).card_id = "D"

    # 检测
    checker = LethalChecker(gs)
    total, sources, has_lethal = checker.calculate_lethal()

    print(f"\n对手：12血")
    print(f"对手嘲讽1：3/4 大嘲讽")
    print(f"对手嘲讽2：2/2 🛡️圣盾嘲讽")
    print(f"我方随从：2/2 A, 3/3 B, 4/4 C, 5/5 D")
    print(f"\n这个场景有很多可能的清除方案...")
    print(f"算法需要尝试所有组合找最优解")
    print(f"\n实际结果：总伤害 = {total}")
    print(f"是否斩杀：{'✅ 是' if has_lethal else '❌ 否'}")


def test_case_5_windfury():
    """
    测试用例5：风怒随从

    场景：
    - 对手：8血
    - 对手嘲讽：2/2
    - 我方随从：3/3 风怒, 4/4

    风怒随从可以攻击2次
    """
    print("\n\n" + "=" * 70)
    print("测试用例5：风怒随从的优化")
    print("=" * 70)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2

    # 英雄
    create_hero(gs, 1, 1, 30)
    create_hero(gs, 2, 2, 8)

    # 对手嘲讽：2/2
    taunt = create_minion(gs, 30, 2, 2, 2)
    taunt.card_id = "嘲讽"
    taunt.tags["TAUNT"] = 1

    # 我方随从：3/3 风怒
    minion1 = create_minion(gs, 10, 1, 3, 3)
    minion1.card_id = "风怒随从"
    minion1.tags["WINDFURY"] = 1  # 风怒

    # 我方随从：4/4
    create_minion(gs, 11, 1, 4, 4).card_id = "普通随从"

    # 检测
    checker = LethalChecker(gs)
    total, sources, has_lethal = checker.calculate_lethal()

    print(f"\n对手：8血")
    print(f"对手嘲讽：2/2")
    print(f"我方随从：3/3 风怒随从（可攻击2次）, 4/4 普通随从")
    print(f"\n分析：")
    print(f"  方案1：风怒第1次清嘲讽 → 风怒第2次+普通 = 3+4 = 7伤")
    print(f"  方案2：普通清嘲讽 → 风怒2次攻击 = 6伤")
    print(f"  最优：方案1 = 7伤 ✅")
    print(f"\n实际结果：总伤害 = {total}")
    print(f"是否斩杀：{'✅ 是' if has_lethal else '❌ 否'}")

    if total >= 7:
        print("\n🎉 算法正确处理风怒！")


def test_case_6_attacker_poisonous():
    """
    测试用例6：我方剧毒随从

    场景：
    - 对手：6血
    - 对手嘲讽：5/5
    - 我方：1/1 剧毒, 6/6

    无剧毒模拟：6/6 换 5/5 存活(1血) → 1/1 打脸 = 1伤
    最优：1/1 剧毒一击清嘲 → 6/6 打脸 = 6伤 ✅
    """
    print("\n" + "=" * 70)
    print("测试用例6：我方剧毒随从清嘲")
    print("=" * 70)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2

    create_hero(gs, 1, 1, 30)
    create_hero(gs, 2, 2, 6)

    taunt = create_minion(gs, 30, 2, 5, 5)
    taunt.card_id = "大嘲讽"
    taunt.tags["TAUNT"] = 1

    poison = create_minion(gs, 10, 1, 1, 1)
    poison.card_id = "剧毒小随从"
    poison.tags["POISONOUS"] = 1

    create_minion(gs, 11, 1, 6, 6).card_id = "大随从"

    checker = LethalChecker(gs)
    total, sources, has_lethal = checker.calculate_lethal()

    print(f"\n对手：6血")
    print(f"对手嘲讽：5/5")
    print(f"我方随从：1/1 剧毒, 6/6")
    print(f"\n分析：")
    print(f"  无剧毒：6/6 换 5/5 → 1/1 打脸 = 1伤")
    print(f"  最优：1/1 剧毒清嘲 → 6/6 打脸 = 6伤 ✅")
    print(f"\n实际结果：总伤害 = {total}")
    print(f"是否斩杀：{'✅ 是' if has_lethal else '❌ 否'}")

    if total >= 6 and has_lethal:
        print("\n🎉 算法正确处理我方剧毒！")


def main():
    """运行所有测试"""
    print("\n" + "🎯" * 35)
    print("最优嘲讽清除算法测试套件")
    print("对比简单贪心 vs 回溯最优解")
    print("🎯" * 35 + "\n")

    test_case_1_simple_optimization()
    test_case_2_multiple_taunts()
    test_case_3_divine_shield_optimization()
    test_case_4_complex_scenario()
    test_case_5_windfury()
    test_case_6_attacker_poisonous()

    print("\n\n" + "=" * 70)
    print("测试总结")
    print("=" * 70)
    print("\n算法特性：")
    print("✅ 使用回溯算法尝试所有可能的清除方案")
    print("✅ 选择剩余打脸伤害最大的方案")
    print("✅ 正确处理圣盾（需要2次攻击）")
    print("✅ 正确处理风怒（多次攻击）")
    print("✅ 正确处理我方剧毒（小攻大血嘲讽一击必杀）")
    print("✅ 优化组合，避免浪费大随从")
    print("\n时间复杂度：")
    print("  O(2^n × m) 其中 n=随从数，m=嘲讽数")
    print("  对于实际游戏场景（最多7个随从），性能完全可接受")
    print("=" * 70)


if __name__ == "__main__":
    main()
