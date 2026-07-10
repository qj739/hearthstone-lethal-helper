#!/usr/bin/env python3
"""悦耳嘻哈 ETC_717 / 刺耳嘻哈 ETC_717t：双形态直伤 + 武器加攻。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import (
    get_board_spell_def,
    hand_board_spells,
    apply_spell_sequence_with_meta,
)


def _hero(gs, eid, pid, *, dmg=0, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_spell(gs, eid, pid, card_id):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = 2
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = 2
    return s


def _weapon(gs, eid, pid, *, atk=3, durability=2):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.card_id = "TEST_WEAPON"
    w.controller = pid
    w.zone = "PLAY"
    w.atk = atk
    w.health = durability
    w.tags["ZONE"] = "PLAY"
    w.tags["ATK"] = atk
    w.tags["DURABILITY"] = durability
    gs.weapon_entity_ids[pid] = eid
    hero = gs.get_hero(pid)
    if hero:
        hero.tags["MAIN_HAND_WEAPON_ENTITY"] = eid
    return w


def test_dissonant_hip_hop_face_lethal():
    """刺耳嘻哈 ETC_717t：3 伤可打脸斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=27)
    _hand_spell(gs, 30, 1, "ETC_717t")

    assert get_board_spell_def("ETC_717t") is not None
    assert hand_board_spells(gs, 1, 10)

    lc = LethalChecker(gs)
    enemy = lc._build_enemy_minion_states(1)
    card = gs.get_entity(30)
    res, _, _ = apply_spell_sequence_with_meta(
        enemy, [], [(get_board_spell_def("ETC_717t"), 2, card)],
        spell_mult=1, enemy_shield=False, gs=gs, player_id=1,
    )
    assert res.direct_face_damage == 3

    total, _, lethal = lc.calculate_lethal_potential()
    assert lethal, f"3 hp should lethal with ETC_717t, total={total}"


def test_harmonic_hip_hop_weapon_buff_combo():
    """悦耳嘻哈 ETC_717：1 伤 + 武器 +3，配合 3 攻武器可打出更高斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=23)
    _weapon(gs, 40, 1, atk=3, durability=2)
    _hand_spell(gs, 30, 1, "ETC_717")

    from copy import deepcopy

    lc = LethalChecker(gs)
    board_view = gs.get_player_board(1)
    fighters = lc._build_fighters(board_view, 1)
    weapon_fs = [f for f in fighters if f.get("kind") == "weapon"]
    assert weapon_fs, "expected equipped weapon fighter"
    assert weapon_fs[0]["atk"] == 3

    enemy = lc._build_enemy_minion_states(1)
    card = gs.get_entity(30)
    defn = get_board_spell_def("ETC_717")
    fs = deepcopy(fighters)
    res = defn.apply(
        deepcopy(enemy), fs,
        mult=1, enemy_shield=False, card=card, gs=gs, player_id=1,
    )
    assert res.direct_face_damage == 1
    weapon_after = [f for f in fs if f.get("kind") == "weapon"]
    assert weapon_after and weapon_after[0]["atk"] == 6

    total, _, lethal = lc.calculate_lethal_potential()
    assert lethal, f"23 dmg enemy should lethal with 1 spell + 6 weapon, total={total}"


def test_both_forms_registered():
    assert get_board_spell_def("ETC_717") is not None
    assert get_board_spell_def("ETC_717t") is not None


if __name__ == "__main__":
    test_dissonant_hip_hop_face_lethal()
    test_harmonic_hip_hop_weapon_buff_combo()
    test_both_forms_registered()
    print("ok")
