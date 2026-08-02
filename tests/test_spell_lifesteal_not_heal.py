#!/usr/bin/env python3
"""法术打到敌方吸血随从不应抬高对手有效血（吸血仅在其造成伤害时触发）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import _apply_damage


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


def _minion(gs, eid, pid, atk, hp, *, card_id="m", taunt=False, lifesteal=False):
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
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    if taunt:
        m.tags["TAUNT"] = 1
    if lifesteal:
        m.tags["LIFESTEAL"] = 1
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


def test_apply_damage_ignores_target_lifesteal():
    unit = {"health": 3, "shield": False, "lifesteal": True, "kind": "minion"}
    assert _apply_damage(unit, 2) == 0
    assert unit["health"] == 1


def test_aoe_into_leech_does_not_inflate_effective_hp():
    """对手 5 血 + 沼泽水蛭；场面 6 打脸足够，AOE 误算吸血时曾漏斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=25)  # 5 血
    _minion(gs, 30, 1, 3, 3, card_id="A")
    _minion(gs, 31, 1, 3, 3, card_id="B")
    _minion(gs, 40, 2, 2, 1, card_id="CORE_GIL_558", lifesteal=True)
    _hand_spell(gs, 50, 1, "CS2_012", 3)  # 横扫，会打到水蛭

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, lethal = lc.calculate_lethal_potential()
    ls = int(getattr(lc, "_overlay_lifesteal_heal", 0) or 0)
    eff = lc.get_opponent_effective_hp()
    red = lc.overlay_red_prompt_ok()
    assert ls == 0, (ls, face, lc.overlay_spell_note())
    assert eff == 5, (eff, ls)
    assert face >= 5, face
    assert lethal and red, (face, lethal, red, lc.overlay_spell_note())


if __name__ == "__main__":
    test_apply_damage_ignores_target_lifesteal()
    test_aoe_into_leech_does_not_inflate_effective_hp()
    print("ok")
