#!/usr/bin/env python3
# test_hdt.py - 测试 HDT Python 实现

"""
快速测试脚本
检查所有模块是否正常工作
"""

import sys
from pathlib import Path

# 添加模块路径
sys.path.insert(0, str(Path(__file__).parent))

def test_imports():
    """测试导入"""
    print("=" * 60)
    print("测试 1: 导入模块")
    print("=" * 60)

    try:
        from hdt_python import log_watcher
        print("✅ log_watcher 导入成功")

        from hdt_python import power_parser
        print("✅ power_parser 导入成功")

        from hdt_python import lethal_checker
        print("✅ lethal_checker 导入成功")

        print("\n所有模块导入成功！")
        return True

    except Exception as e:
        print(f"\n❌ 导入失败: {e}")
        return False


def test_find_logs():
    """测试查找日志"""
    print("\n" + "=" * 60)
    print("测试 2: 查找炉石日志")
    print("=" * 60)

    try:
        from hdt_python.log_watcher import find_hearthstone_logs

        log_dir = find_hearthstone_logs()
        if log_dir:
            print(f"✅ 找到日志目录: {log_dir}")
            return True
        else:
            print("❌ 未找到日志目录")
            print("提示: 请确保炉石传说已安装并至少启动过一次")
            return False

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_game_state():
    """测试游戏状态"""
    print("\n" + "=" * 60)
    print("测试 3: 游戏状态管理")
    print("=" * 60)

    try:
        from hdt_python.power_parser import GameState, Entity

        # 创建游戏状态
        gs = GameState()
        print("✅ GameState 创建成功")

        # 创建实体
        entity = gs.get_entity(1)
        entity.card_id = "CS2_029"  # 火球术
        entity.controller = 1
        entity.zone = "HAND"
        entity.cost = 4
        print("✅ Entity 创建成功")

        # 测试查询
        hand = gs.get_hand(1)
        print(f"✅ 手牌查询成功: {len(hand)} 张")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_lethal_checker():
    """测试斩杀检测"""
    print("\n" + "=" * 60)
    print("测试 4: 斩杀检测器")
    print("=" * 60)

    try:
        from hdt_python.power_parser import GameState, Entity
        from hdt_python.lethal_checker import LethalChecker

        # 创建测试场景
        gs = GameState()
        gs.local_player_id = 1
        gs.opponent_player_id = 2

        # 我方英雄
        my_hero = gs.get_entity(1)
        my_hero.cardtype = "HERO"
        my_hero.controller = 1
        my_hero.tags["RESOURCES"] = 10
        my_hero.tags["RESOURCES_USED"] = 0

        # 对手英雄（低血量）
        opp_hero = gs.get_entity(2)
        opp_hero.cardtype = "HERO"
        opp_hero.controller = 2
        opp_hero.health = 10
        opp_hero.damage = 0
        opp_hero.tags["ARMOR"] = 0

        # 我方场面（一个3攻随从）
        minion = gs.get_entity(10)
        minion.card_id = "CS2_124"
        minion.cardtype = "MINION"
        minion.controller = 1
        minion.zone = "PLAY"
        minion.atk = 3
        minion.health = 1
        minion.tags["NUM_ATTACKS_THIS_TURN"] = 0

        # 我方手牌（火球术）
        spell = gs.get_entity(20)
        spell.card_id = "CS2_029"
        spell.cardtype = "SPELL"
        spell.controller = 1
        spell.zone = "HAND"
        spell.cost = 4

        # 检测斩杀
        checker = LethalChecker(gs)
        total_damage, sources, has_lethal = checker.calculate_lethal()

        print(f"✅ 斩杀检测成功")
        print(f"   总伤害: {total_damage}")
        print(f"   对手血量: 10")
        print(f"   有斩杀: {has_lethal}")

        if has_lethal:
            print("\n✅ 正确检测到斩杀！")
            print("\n伤害来源:")
            for source in sources:
                print(f"   • {source}")
        else:
            print("\n❌ 应该检测到斩杀但没有")

        return has_lethal

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "🎯" * 30)
    print("HDT Python 实现 - 测试套件")
    print("🎯" * 30 + "\n")

    results = []

    # 运行测试
    results.append(("导入模块", test_imports()))
    results.append(("查找日志", test_find_logs()))
    results.append(("游戏状态", test_game_state()))
    results.append(("斩杀检测", test_lethal_checker()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status} - {name}")

    print("\n" + "=" * 60)
    print(f"总计: {passed}/{total} 测试通过")
    print("=" * 60)

    if passed == total:
        print("\n🎉 所有测试通过！可以运行 hdt_tracker.py 了")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
