#!/usr/bin/env python3
"""反魔法护罩：全体友方 +N/+N 应计入斩杀打脸。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, hand_board_spells


def _hero(gs, eid, pid, *, dmg=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m", turns=1):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk,
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0,
        "NUM_TURNS_IN_PLAY": turns,
    })
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    return s


def test_anti_magic_shell_registered():
    assert get_board_spell_def("RLK_048") is not None
    assert get_board_spell_def("ICC_314t7") is not None
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 2, 2)
    _hand_spell(gs, 40, 1, "RLK_048", 3)
    assert any(s.card_id == "RLK_048" for s, _, _ in hand_board_spells(gs, 1, 10))
    print("OK anti-magic shell registered")


def test_rlk_shell_plus1_lethal():
    """两只 3 攻 + 反魔法护罩 +1 = 8，对手 8 血应斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, dmg=22)  # 8 hp
    _minion(gs, 10, 1, 3, 3, turns=1)
    _minion(gs, 11, 1, 3, 3, turns=1)
    _hand_spell(gs, 40, 1, "RLK_048", 3)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    _, _, has_lethal = lc.calculate_lethal_potential()
    assert total >= 8, f"expected >=8 after +1/+1 shell, got {total}"
    assert has_lethal, f"3+3+1+1 should lethal vs 8, total={total}"
    print("OK RLK shell +1 lethal", total)


def test_icc_shell_plus2_lethal():
    """一只 4 攻 + ICC 反魔法护罩 +2 = 6，对手 6 血应斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, dmg=24)  # 6 hp
    _minion(gs, 10, 1, 4, 4, turns=1)
    _hand_spell(gs, 40, 1, "ICC_314t7", 4)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    _, _, has_lethal = lc.calculate_lethal_potential()
    assert total >= 6, f"expected >=6 after +2/+2 shell, got {total}"
    assert has_lethal, f"4+2 should lethal vs 6, total={total}"
    print("OK ICC shell +2 lethal", total)


if __name__ == "__main__":
    test_anti_magic_shell_registered()
    test_rlk_shell_plus1_lethal()
    test_icc_shell_plus2_lethal()
    print("all passed")
