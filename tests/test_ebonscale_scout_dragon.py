#!/usr/bin/env python3
"""乌鳞斥候：战吼等于攻击力；打出龙后变为 8/8（CATA_552t）应打 8。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.battlecry_p0 import _apply_ebonscale_scout
from hdt_python.spell_board import apply_spell_sequence, entity_is_dragon


def _hero(gs, eid, pid, *, dmg=0, mana=10, health=30):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = health
    h.damage = dmg
    h.tags.update({
        "DAMAGE": dmg, "HEALTH": health,
        "RESOURCES": mana, "RESOURCES_USED": 0,
    })
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_minion(gs, eid, pid, card_id, atk, hp, cost=6):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.cost = cost
    m.tags.update({
        "ZONE": "HAND", "CARDTYPE": "MINION",
        "ATK": atk, "HEALTH": hp, "COST": cost,
    })
    return m


def _deck(gs, eid, pid):
    c = gs.get_entity(eid)
    c.cardtype = "MINION"
    c.controller = pid
    c.zone = "DECK"
    c.tags["ZONE"] = "DECK"
    return c


def _gs():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    return gs


def test_token_registered_and_deals_eight():
    assert get_battlecry_def("CATA_552t") is not None
    assert get_battlecry_def("CATA_552") is get_battlecry_def("CATA_552t")
    gs = _gs()
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=22, health=30)  # 8 血
    card = _hand_minion(gs, 40, 1, "CATA_552t", 8, 8)
    for eid in (301, 302):
        _deck(gs, eid, 2)
    res = _apply_ebonscale_scout([], [], mult=1, enemy_shield=False, card=card)
    assert res.direct_face_damage == 8
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 8, f"face={face} note={lc.overlay_spell_note()}"
    assert lc.calculate_lethal_potential()[2]


def test_base_scout_deals_four():
    gs = _gs()
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=26, health=30)  # 4 血
    card = _hand_minion(gs, 40, 1, "CATA_552", 4, 4)
    for eid in (301, 302):
        _deck(gs, eid, 2)
    res = _apply_ebonscale_scout([], [], mult=1, enemy_shield=False, card=card)
    assert res.direct_face_damage == 4
    lc = LethalChecker(gs)
    assert lc.overlay_board_face_damage() >= 4
    assert lc.calculate_lethal_potential()[2]


def test_dragon_played_earlier_upgrades_battlecry():
    gs = _gs()
    scout = _hand_minion(gs, 40, 1, "CATA_552", 4, 4)
    dragon = _hand_minion(gs, 41, 1, "EX1_562", 4, 12, cost=9)
    dragon.tags["CARDRACE"] = "DRAGON"
    assert entity_is_dragon(dragon)
    scout_def = get_battlecry_def("CATA_552")
    # 用斥候定义占位，卡面换成龙，只为让序列先打出龙
    res = apply_spell_sequence(
        [], [],
        [(scout_def, 0, dragon), (scout_def, 0, scout)],
        gs=gs, player_id=1, mana_budget=10,
    )
    assert res.battlecry_face_damage == 8, res.battlecry_face_damage


if __name__ == "__main__":
    test_token_registered_and_deals_eight()
    test_base_scout_deals_four()
    test_dragon_played_earlier_upgrades_battlecry()
    print("ok")
