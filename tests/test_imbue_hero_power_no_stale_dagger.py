#!/usr/bin/env python3
"""灌注切换英雄技能后，SETASIDE 的旧匕首精通不可再当作可用技能。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.hero_power_board import list_usable_hero_powers, _player_hero_power_entities
from hdt_python.lethal_checker import LethalChecker


def _hero(gs, eid, pid, *, mana=10, health=30, dmg=0):
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


def _hero_power(gs, eid, pid, card_id, *, zone="PLAY", cost=2):
    e = gs.get_entity(eid)
    e.cardtype = "HERO_POWER"
    e.controller = pid
    e.zone = zone
    e.card_id = card_id
    e.cost = cost
    e.tags.update({
        "ZONE": zone, "COST": cost, "EXHAUSTED": 0,
        "CARDTYPE": "HERO_POWER",
    })
    return e


def test_setaside_dagger_not_usable_after_imbue():
    """PLAY 区为青铜龙的祝福时，SETASIDE 匕首精通不得进入 usable。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 64, 1, mana=10)
    _hero(gs, 66, 2, dmg=28)  # 2 血
    _hero_power(gs, 65, 1, "HERO_03bp", zone="SETASIDE", cost=2)
    _hero_power(gs, 191, 1, "END_000p", zone="PLAY", cost=2)

    in_play, pending = _player_hero_power_entities(gs, 1)
    assert any(e.card_id == "END_000p" for e in in_play)
    assert not any(e.zone == "SETASIDE" for e in pending)

    usable = list_usable_hero_powers(gs, 1, 10)
    assert usable == [], f"expected no usable HP (imbued unknown), got {usable}"

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note() or ""
    assert "匕首精通" not in note, note
    # 无挂刀：场攻不应凭空多出武器 1
    assert face == 0, f"face={face} note={note}"


def test_play_dagger_still_usable():
    """未灌注时 PLAY 区匕首精通仍可挂刀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "HERO_03bp", zone="PLAY", cost=2)

    usable = list_usable_hero_powers(gs, 1, 10)
    assert len(usable) == 1 and usable[0][1].name == "匕首精通"

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note() or ""
    assert face >= 1, face
    assert "匕首精通" in note


if __name__ == "__main__":
    test_setaside_dagger_not_usable_after_imbue()
    test_play_dagger_still_usable()
    print("ok")
