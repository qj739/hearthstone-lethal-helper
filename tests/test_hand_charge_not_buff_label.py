#!/usr/bin/env python3
"""手牌冲锋不得记入「含BUFF」；应单独步骤列出。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.overlay_combo_format import (
    overlay_minion_face_bonus_paren,
    build_lethal_combo_lines,
)


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


def _minion(gs, eid, pid, atk, hp, *, turns=1):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = "board"
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk,
        "EXHAUSTED": 0, "NUM_TURNS_IN_PLAY": turns, "NUM_ATTACKS_THIS_TURN": 0,
    })
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_charge(gs, eid, pid, card_id, *, cost, atk, hp):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.cost = cost
    m.atk = atk
    m.health = hp
    m.tags.update({
        "ZONE": "HAND", "COST": cost, "ATK": atk, "HEALTH": hp, "479": atk, "CHARGE": 1,
    })
    return m


def test_hand_charge_not_labeled_as_buff():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=15)
    _minion(gs, 30, 1, 5, 5, turns=2)
    _hand_charge(gs, 40, 1, "EX1_116", cost=6, atk=6, hp=3)  # 雷矛 6
    _hand_charge(gs, 41, 1, "CS2_124", cost=3, atk=3, hp=1)  # 狼骑 3

    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    hand_chg = lc.overlay_hand_charge_face()
    paren = overlay_minion_face_bonus_paren(lc)
    combo = build_lethal_combo_lines(lc)
    joined = "|".join(combo)

    assert hand_chg == 9, hand_chg
    assert "含BUFF" not in paren, paren
    assert "含BUFF" not in joined, combo
    assert any("冲锋" in ln for ln in combo), combo
    assert lc.overlay_display_face() == 5, lc.overlay_display_face()


if __name__ == "__main__":
    test_hand_charge_not_labeled_as_buff()
    print("ok")
