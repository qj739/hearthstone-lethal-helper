#!/usr/bin/env python3
"""亡语机制单元测试（ARENA_DEATHRATTLE_WORKLIST 14 张 + 食尸鬼）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.deathrattle import on_minion_died, remove_dead_taunts


def _fighter(eid, atk, hp, **kw):
    return {
        "kind": "minion",
        "entity_id": eid,
        "atk": atk,
        "health": hp,
        "attacks_left": 1,
        "can_face": True,
        **kw,
    }


def _enemy(eid, hp, *, card_id="", atk=1, taunt=False, script=0):
    d = {
        "entity_id": eid,
        "kind": "minion",
        "card_id": card_id,
        "atk": atk,
        "health": hp,
        "shield": False,
        "taunt": taunt,
    }
    if script:
        d["script_data_num_1"] = script
    return d


def test_ung_022_aoe_all_minions():
    dead = _enemy(1, 0, card_id="UNG_022")
    board = [_enemy(2, 3), dead]
    fighters = [_fighter(10, 2, 2)]
    on_minion_died(dead, board, fighters)
    assert board[0]["health"] == 2
    assert fighters[0]["health"] == 1
    print("OK UNG_022")


def test_gdb_226_other_minions_only():
    dead = _enemy(1, 0, card_id="GDB_226")
    ally = _enemy(2, 5)
    board = [ally, dead]
    fighters = [_fighter(10, 3, 3)]
    on_minion_died(dead, board, fighters)
    assert ally["health"] == 3
    assert fighters[0]["health"] == 1
    print("OK GDB_226")


def test_toy_642_lowest_attacker():
    dead = _enemy(1, 0, card_id="TOY_642")
    board = [dead]
    fighters = [_fighter(10, 3, 5), _fighter(11, 4, 2)]
    on_minion_died(dead, board, fighters)
    assert fighters[0]["health"] == 5
    assert fighters[1]["health"] <= 0
    print("OK TOY_642")


def test_tlc_249_random_split():
    dead = _enemy(1, 0, card_id="TLC_249")
    board = [dead]
    fighters = [_fighter(10, 2, 2)]
    on_minion_died(dead, board, fighters)
    assert fighters[0]["health"] == 0
    print("OK TLC_249")


def test_edr_421_script_damage():
    dead = _enemy(1, 0, card_id="EDR_421", script=3)
    board = [dead]
    fighters = [_fighter(10, 6, 6), _fighter(11, 2, 4)]
    on_minion_died(dead, board, fighters)
    assert fighters[0]["health"] == 3
    assert fighters[1]["health"] == 1
    print("OK EDR_421")


def test_harbinger_script_random():
    dead = _enemy(1, 0, card_id="CATA_580t", script=4)
    board = [dead]
    fighters = [_fighter(10, 2, 5)]
    on_minion_died(dead, board, fighters)
    assert fighters[0]["health"] == 1
    print("OK CATA_580t")


def test_fp1_012_summon_taunt():
    dead = _enemy(1, 0, card_id="FP1_012", taunt=True)
    board = [dead]
    fighters = [_fighter(10, 3, 3)]
    on_minion_died(dead, board, fighters)
    remove_dead_taunts(board)
    assert len(board) == 1
    slime = board[0]
    assert slime["taunt"] is True
    assert slime["health"] == 2
    assert slime["atk"] == 1
    print("OK FP1_012")


def test_edr_459_aoe_attacker():
    dead = _enemy(1, 0, card_id="EDR_459")
    board = [dead]
    fighters = [_fighter(10, 6, 6)]
    on_minion_died(dead, board, fighters)
    assert fighters[0]["health"] == 3
    print("OK EDR_459")


def test_av_325_atk_scaled():
    dead = _enemy(1, 0, card_id="AV_325", atk=3)
    board = [dead]
    fighters = [_fighter(10, 2, 5)]
    on_minion_died(dead, board, fighters)
    assert fighters[0]["health"] == 2
    print("OK AV_325")


def test_mountain_bear_two_cubs():
    dead = _enemy(1, 0, card_id="AV_337", taunt=True)
    board = [dead]
    fighters = [_fighter(10, 3, 3)]
    on_minion_died(dead, board, fighters)
    remove_dead_taunts(board)
    assert len(board) == 2
    assert all(m["taunt"] and m["health"] == 4 and m["atk"] == 2 for m in board)
    print("OK AV_337")


def test_forgefiend_armor():
    from hdt_python.deathrattle import sim_armor_gain

    dead = _enemy(1, 0, card_id="SW_068", taunt=True)
    board = [dead]
    res = on_minion_died(dead, board, [])
    assert res.armor_gain == 8
    assert sim_armor_gain(board) == 8
    print("OK SW_068")


def test_ankylodon_two_threes():
    dead = _enemy(1, 0, card_id="DINO_422", taunt=True)
    board = [dead]
    fighters = [_fighter(10, 3, 6)]
    on_minion_died(dead, board, fighters)
    assert fighters[0]["health"] == 0
    print("OK DINO_422")


def test_wretched_queen_two_knights():
    dead = _enemy(1, 0, card_id="TOY_914", taunt=True)
    board = [dead]
    on_minion_died(dead, board, [])
    remove_dead_taunts(board)
    assert len(board) == 2
    assert all(m["taunt"] and m["atk"] == 4 and m["health"] == 6 for m in board)
    print("OK TOY_914")


def test_coilfang_warlord():
    dead = _enemy(1, 0, card_id="BT_761", taunt=True)
    board = [dead]
    on_minion_died(dead, board, [])
    remove_dead_taunts(board)
    assert len(board) == 1
    assert board[0]["atk"] == 5 and board[0]["health"] == 9 and board[0]["taunt"]
    print("OK BT_761")


if __name__ == "__main__":
    test_ung_022_aoe_all_minions()
    test_gdb_226_other_minions_only()
    test_toy_642_lowest_attacker()
    test_tlc_249_random_split()
    test_edr_421_script_damage()
    test_harbinger_script_random()
    test_fp1_012_summon_taunt()
    test_edr_459_aoe_attacker()
    test_av_325_atk_scaled()
    test_mountain_bear_two_cubs()
    test_forgefiend_armor()
    test_ankylodon_two_threes()
    test_wretched_queen_two_knights()
    test_coilfang_warlord()
    print("all deathrattle tests passed")
