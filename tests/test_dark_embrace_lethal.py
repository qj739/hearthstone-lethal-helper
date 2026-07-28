#!/usr/bin/env python3
"""回归：黑暗之拥 JAIL_941t + 埃提耶什翻倍漏斩。

末手：对手 9 血、空场、3 费；手牌黑暗之拥(2) + 武器 1。
埃提耶什使 4 伤翻倍为 8，再挥击 1 = 9 斩。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, spell_effect_multiplier


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10, used=0, card_id="HERO_09"):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.card_id = card_id
    h.health = hp
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    h.tags["ATK"] = 0
    h.tags["479"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _weapon(gs, eid, pid, card_id="TIME_890t", atk=1, dur=1):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.card_id = card_id
    w.controller = pid
    w.zone = "PLAY"
    w.atk = atk
    w.health = dur
    w.tags["ZONE"] = "PLAY"
    w.tags["ATK"] = atk
    w.tags["479"] = atk
    w.tags["DURABILITY"] = dur
    gs.weapon_entity_ids[pid] = eid
    hero = gs.get_hero(pid)
    if hero:
        hero.tags["MAIN_HAND_WEAPON_ENTITY"] = eid
        hero.tags["ATK"] = atk
        hero.tags["479"] = atk
    return w


def _hand_spell(gs, eid, pid, card_id, cost):
    c = gs.get_entity(eid)
    c.cardtype = "SPELL"
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = cost
    return c


def test_dark_embrace_registered():
    assert get_board_spell_def("JAIL_941t") is not None
    assert get_board_spell_def("JAIL_941") is not None
    print("OK JAIL_941 / JAIL_941t registered")


def test_holy_embrace_queues_dark():
    defn = get_board_spell_def("JAIL_941")
    res = defn.apply([], [], mult=1, enemy_shield=False)
    assert res.add_hand_pending == [("JAIL_941t", 2, 0)], res.add_hand_pending
    assert res.self_hero_heal == 4, res.self_hero_heal
    res2 = defn.apply([], [], mult=2, enemy_shield=False)
    assert res2.self_hero_heal == 8, res2.self_hero_heal
    print("OK holy queues dark + heal")


def test_dark_embrace_atiesh_lethal_vs_9():
    """对手 9 血：黑暗之拥 4×2 + 武器 1 = 9。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=3, used=0)
    _hero(gs, 2, 2, hp=30, dmg=21, card_id="HERO_09aq")  # 9 血
    _weapon(gs, 40, 1, card_id="TIME_890t", atk=1, dur=1)
    _hand_spell(gs, 50, 1, "JAIL_941t", 2)

    assert spell_effect_multiplier(gs, 1) == 2

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    total, _, has = lc.calculate_lethal_potential()
    assert face >= 9, (face, lc.overlay_board_breakdown(), lc.overlay_spell_note())
    assert has, (face, total, has, lc.overlay_spell_note())
    assert lc.overlay_red_prompt_ok()
    print("OK dark embrace + Atiesh lethal vs 9", face, lc.overlay_spell_note())


if __name__ == "__main__":
    test_dark_embrace_registered()
    test_holy_embrace_queues_dark()
    test_dark_embrace_atiesh_lethal_vs_9()
    print("ALL PASS")
