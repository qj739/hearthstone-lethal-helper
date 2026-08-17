#!/usr/bin/env python3
"""玩具队长塔林姆 TOY_813：战吼按手牌 BUFF 后的实际攻/血复制。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.combat_sim import fighters_face_damage
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import apply_spell_sequence_with_meta


def _hero(gs, eid, pid, *, hp=30, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = 0
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="", turns=1):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["ATK"] = atk
    m.tags["HEALTH"] = hp
    m.tags["NUM_TURNS_IN_PLAY"] = turns
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_minion(gs, eid, pid, card_id, atk, hp, cost):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.cost = cost
    m.tags["ZONE"] = "HAND"
    m.tags["ATK"] = atk
    m.tags["HEALTH"] = hp
    m.tags["COST"] = cost
    m.tags["TAUNT"] = 1
    return m


def test_toy_tarim_uses_hand_buff_stats():
    """美德等把手牌塔林姆抬到 4/8 后，战吼应复制 4/8 而非写死 3/7。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2, hp=17)

    _minion(gs, 10, 1, 4, 4, card_id="A", turns=2)
    _minion(gs, 11, 1, 4, 5, card_id="B", turns=2)
    _minion(gs, 12, 1, 1, 1, card_id="CS2_101t7", turns=2)
    _minion(gs, 13, 1, 5, 5, card_id="C", turns=2)
    card = _hand_minion(gs, 40, 1, "TOY_813", 4, 8, 5)

    defn = get_battlecry_def("TOY_813")
    assert defn is not None
    checker = LethalChecker(gs)
    fs = checker._build_fighters(checker._board_view_for_fighters(1), 1)
    enemy = checker._build_enemy_minion_states(1)
    apply_spell_sequence_with_meta(
        enemy, fs, [(defn, 5, card)],
        gs=gs, player_id=1, enemy_shield=False, mana_budget=5,
    )
    recruit = next(f for f in fs if f.get("card_id") == "CS2_101t7")
    assert recruit["atk"] == 4 and recruit["health"] == 8, recruit
    face = fighters_face_damage(fs, False)
    assert face >= 17, face


def test_toy_tarim_buffed_enables_lethal():
    """复盘：对手 17 血，4/8 塔林姆抬新兵后场攻应斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2, hp=17)

    _minion(gs, 10, 1, 4, 4, card_id="TIME_043", turns=2)
    _minion(gs, 11, 1, 4, 5, card_id="JAM_014", turns=2)
    _minion(gs, 12, 1, 1, 1, card_id="CS2_101t7", turns=2)
    _minion(gs, 13, 1, 5, 5, card_id="CORE_RLK_505", turns=2)
    _hand_minion(gs, 40, 1, "TOY_813", 4, 8, 5)

    checker = LethalChecker(gs)
    face = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note()
    assert face >= 17, (face, note)
    assert "塔林姆" in note, note
    total, _, lethal = LethalChecker(gs).calculate_lethal_potential()
    assert lethal, (total, face, note)


def test_toy_tarim_mini_registered():
    assert get_battlecry_def("TOY_813t") is not None


if __name__ == "__main__":
    test_toy_tarim_uses_hand_buff_stats()
    test_toy_tarim_buffed_enables_lethal()
    test_toy_tarim_mini_registered()
    print("ok")
