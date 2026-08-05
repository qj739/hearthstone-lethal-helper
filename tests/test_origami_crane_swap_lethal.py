#!/usr/bin/env python3
"""折纸仙鹤 TOY_895：战吼与另一随从交换生命值，用于换嘲讽斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.spell_board import get_board_spell_def


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="M", taunt=False, turns=1, reborn=False):
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
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0 if turns else 1,
        "NUM_TURNS_IN_PLAY": turns,
    })
    if taunt:
        m.tags["TAUNT"] = 1
    if reborn:
        m.tags["REBORN"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand(gs, eid, pid, card_id, cost, *, cardtype="MINION"):
    c = gs.get_entity(eid)
    c.cardtype = cardtype
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = cost
    return c


def test_origami_crane_registered():
    assert get_battlecry_def("TOY_895") is not None
    assert get_board_spell_def("CORE_CS1_130") is not None
    print("OK crane+smite registered")


def test_origami_crane_swap_reborn_taunt_lethal():
    """
    复盘 2026-08-05：对手 16 血，复生嘲讽 2/6；我方场攻 17。
    仙鹤换血→嘲讽变 1 血 + 神圣惩击/南瓜解嘲 → 应斩。
    """
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, hp=30, dmg=14)  # 16 血
    # 避免疲劳把 15 伤抬成斩杀
    for i, eid in enumerate(range(100, 108)):
        e = gs.get_entity(eid)
        e.controller = 2
        e.zone = "DECK"
        e.card_id = f"DECK_{i}"
        e.tags["ZONE"] = "DECK"
    _minion(gs, 10, 1, 5, 3, card_id="TOY_383", turns=1)
    _minion(gs, 11, 1, 3, 1, card_id="RLK_223", turns=1)
    _minion(gs, 12, 1, 2, 2, card_id="CORE_RLK_745", turns=1)
    _minion(gs, 13, 1, 7, 4, card_id="JAIL_101", turns=1)
    _minion(gs, 20, 2, 2, 3, card_id="CORE_RLK_116")
    _minion(gs, 21, 2, 2, 6, card_id="TOY_828", taunt=True, reborn=True)
    _minion(gs, 22, 2, 2, 1, card_id="ETC_209")
    _hand(gs, 30, 1, "TOY_895", 4)
    _hand(gs, 31, 1, "CORE_CS1_130", 1, cardtype="SPELL")
    hp = gs.get_entity(40)
    hp.cardtype = "HERO_POWER"
    hp.controller = 1
    hp.zone = "PLAY"
    hp.card_id = "TOY_829hp"
    hp.cost = 2
    hp.tags.update({"ZONE": "PLAY", "COST": 2, "EXHAUSTED": 0})

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note() or ""
    _, _, lethal = lc.calculate_lethal_potential()
    assert face >= 16, f"expected >=16, got {face} note={note}"
    assert lethal, (face, note)
    assert "仙鹤" in note or "TOY_895" in note, note
    print("OK crane+smite+pumpkin lethal", face, note)


if __name__ == "__main__":
    test_origami_crane_registered()
    test_origami_crane_swap_reborn_taunt_lethal()
