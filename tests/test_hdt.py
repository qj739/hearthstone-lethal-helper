#!/usr/bin/env python3
# test_hdt.py - ?? HDT Python ??

"""????????????????????"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def test_imports():
    print("=" * 60)
    print("?? 1: ????")
    print("=" * 60)

    try:
        from hdt_python import log_watcher  # noqa: F401
        print("? log_watcher ????")

        from hdt_python import power_parser  # noqa: F401
        print("? power_parser ????")

        from hdt_python import lethal_checker  # noqa: F401
        print("? lethal_checker ????")

        print("\n?????????")
        return True

    except Exception as e:
        print(f"\n? ????: {e}")
        return False


def test_find_logs():
    print("\n" + "=" * 60)
    print("?? 2: ??????")
    print("=" * 60)

    try:
        from hdt_python.log_watcher import find_hearthstone_logs

        log_dir = find_hearthstone_logs()
        if log_dir:
            print(f"? ??????: {log_dir}")
            return True
        print("? ???????")
        print("??: ??????????????????")
        return False

    except Exception as e:
        print(f"? ????: {e}")
        return False


def test_game_state():
    print("\n" + "=" * 60)
    print("?? 3: ??????")
    print("=" * 60)

    try:
        from hdt_python.power_parser import GameState

        gs = GameState()
        print("? GameState ????")

        entity = gs.get_entity(1)
        entity.card_id = "CS2_029"
        entity.controller = 1
        entity.zone = "HAND"
        entity.cost = 4
        print("? Entity ????")

        hand = gs.get_hand(1)
        print(f"? ??????: {len(hand)} ?")
        return True

    except Exception as e:
        print(f"? ????: {e}")
        return False


def test_lethal_checker():
    print("\n" + "=" * 60)
    print("?? 4: ?????")
    print("=" * 60)

    try:
        from hdt_python.power_parser import GameState
        from hdt_python.lethal_checker import LethalChecker

        gs = GameState()
        gs.local_player_id = 1
        gs.opponent_player_id = 2
        gs.active_player_id = 1  # ??????? calculate_lethal ???? 0

        my_hero = gs.get_entity(1)
        my_hero.cardtype = "HERO"
        my_hero.controller = 1
        my_hero.tags["RESOURCES"] = 10
        my_hero.tags["RESOURCES_USED"] = 0

        opp_hp = 9
        opp_hero = gs.get_entity(2)
        opp_hero.cardtype = "HERO"
        opp_hero.controller = 2
        opp_hero.health = opp_hp
        opp_hero.damage = 0
        opp_hero.tags["ARMOR"] = 0

        minion = gs.get_entity(10)
        minion.card_id = "CS2_124"
        minion.cardtype = "MINION"
        minion.controller = 1
        minion.zone = "PLAY"
        minion.atk = 3
        minion.health = 1
        minion.tags["NUM_ATTACKS_THIS_TURN"] = 0
        minion.tags["EXHAUSTED"] = 0
        minion.tags["NUM_TURNS_IN_PLAY"] = 2
        minion.tags["ZONE_POSITION"] = 1

        spell = gs.get_entity(20)
        spell.card_id = "CS2_029"
        spell.cardtype = "SPELL"
        spell.controller = 1
        spell.zone = "HAND"
        spell.cost = 4

        checker = LethalChecker(gs)
        total_damage, sources, has_lethal = checker.calculate_lethal()

        print("? ??????")
        print(f"   ???: {total_damage}")
        print(f"   ????: {opp_hp}")
        print(f"   ???: {has_lethal}")

        if has_lethal and total_damage >= opp_hp:
            print("\n? ????????")
            print("\n????:")
            for source in sources:
                print(f"   ? {source}")
            return True

        print("\n? ??????????")
        return False

    except Exception as e:
        print(f"? ????: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("\n" + "??" * 30)
    print("HDT Python ?? - ????")
    print("??" * 30 + "\n")

    results = [
        ("????", test_imports()),
        ("????", test_find_logs()),
        ("????", test_game_state()),
        ("????", test_lethal_checker()),
    ]

    print("\n" + "=" * 60)
    print("????")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "? ??" if result else "? ??"
        print(f"{status} - {name}")

    print("\n" + "=" * 60)
    print(f"??: {passed}/{total} ????")
    print("=" * 60)

    if passed == total:
        print("\n?? ??????????? hdt_tracker.py ?")
        return 0
    print("\n?? ??????????????")
    return 1


if __name__ == "__main__":
    sys.exit(main())
