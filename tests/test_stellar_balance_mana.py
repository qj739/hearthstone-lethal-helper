#!/usr/bin/env python3
"""星体平衡衍生星火：法力不够时不得按完整 2+6 记斩杀。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import apply_spell_sequence_with_meta, get_board_spell_def


def _hero(gs, eid, pid, *, damage=0, mana_max=6, mana_used=6):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = damage
    h.tags.update({
        "DAMAGE": damage, "HEALTH": 30, "ARMOR": 0,
        "RESOURCES": mana_max, "RESOURCES_USED": mana_used,
    })
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, card_id=""):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk, "HEALTH": hp,
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0, "NUM_TURNS_IN_PLAY": 1,
    })
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand(gs, eid, pid, card_id, cost):
    e = gs.get_entity(eid)
    e.cardtype = "SPELL"
    e.controller = pid
    e.zone = "HAND"
    e.card_id = card_id
    e.cost = cost
    e.tags.update({"ZONE": "HAND", "COST": cost, "CARDTYPE": "SPELL"})
    return e


def test_stellar_chain_respects_mana_budget():
    defn = get_board_spell_def("EDR_874")
    assert defn is not None
    seq = [(defn, 2, None)]
    res7, _, left7 = apply_spell_sequence_with_meta(
        [], [], seq, mana_budget=7,
    )
    assert res7.direct_face_damage == 2, res7.direct_face_damage
    assert left7 == 5, left7
    res8, _, left8 = apply_spell_sequence_with_meta(
        [], [], seq, mana_budget=8,
    )
    assert res8.direct_face_damage == 8, res8.direct_face_damage
    assert left8 == 0, left8


def test_next_turn_preview_no_fake_starfire_spell_face():
    """下回合 7 费：不得把星体平衡记成法术 8（星火还差 1 费）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 2  # 对方回合 → 下回合预览
    gs.in_game = True
    _hero(gs, 10, 1, mana_max=6, mana_used=6)
    _hero(gs, 20, 2, damage=25)  # 5 血
    _minion(gs, 30, 1, 5, 4, "JAIL_101")
    _minion(gs, 31, 1, 3, 1, "TIME_610t2")
    _minion(gs, 32, 1, 3, 1, "TIME_610t2")
    _minion(gs, 33, 1, 6, 2, "TIME_610t2")
    _minion(gs, 40, 2, 1, 1, "OPPX")
    _hand(gs, 50, 1, "EDR_874", 2)

    lc = LethalChecker(gs)
    assert lc._next_turn_mana(1) == 7
    face = lc.overlay_board_face_damage()
    spell = getattr(lc, "_overlay_spell_face", 0)
    assert spell <= 2, f"spell face must not include unaffordable starfire, got {spell}"
    # 场面已够斩 5 血；法术分项不应虚高到 8
    assert face >= 17
    note = getattr(lc, "_overlay_spell_note", "") or ""
    if "星体平衡" in note:
        assert spell <= 2, note


def test_stellar_alone_not_lethal_on_7_mana_empty_board():
    """空手场面、对手 8 血、仅 7 费：星体平衡不能虚斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana_max=7, mana_used=0)
    _hero(gs, 20, 2, damage=22)  # 8 血
    _hand(gs, 50, 1, "EDR_874", 2)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    spell = getattr(lc, "_overlay_spell_face", 0)
    assert spell <= 2, spell
    assert face < 8, f"should not count full chain, face={face}"
    total, _, has_lethal = lc.calculate_lethal_potential()
    assert not has_lethal, f"false lethal total={total} face={face}"


if __name__ == "__main__":
    test_stellar_chain_respects_mana_budget()
    test_next_turn_preview_no_fake_starfire_spell_face()
    test_stellar_alone_not_lethal_on_7_mana_empty_board()
    print("ok")
