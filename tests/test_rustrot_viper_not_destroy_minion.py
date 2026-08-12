#!/usr/bin/env python3
"""锈烂蝰蛇 CORE_SW_072：战吼只摧毁对方武器，不能当消灭随从解嘲讽。"""

import sys
from copy import deepcopy
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.arena_season_bulk import (
    _classify_battlecry,
    register_arena_season_gap,
)
from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState


def test_classify_weapon_destroy_not_destroy_enemy():
    text = "[x]<b>Tradeable</b> <b>Battlecry:</b> Destroy your opponent's weapon."
    spec = _classify_battlecry(text)
    assert spec.kind == "noop", spec
    assert spec.note == "摧毁武器", spec
    print("OK classify Rustrot Viper as weapon-destroy noop")


def test_ooze_same():
    text = "<b>Battlecry:</b> Destroy your opponent's weapon."
    spec = _classify_battlecry(text)
    assert spec.kind == "noop" and spec.note == "摧毁武器", spec
    print("OK Acidic Swamp Ooze classify")


def _hero(gs, eid, pid, *, hp=30, dmg=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = 10
    h.tags["RESOURCES_USED"] = 0
    h.tags["EXHAUSTED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, taunt=False, card_id="CS2_182"):
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
    m.tags["479"] = atk
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    if taunt:
        m.tags["TAUNT"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_viper(gs, eid, pid):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.card_id = "CORE_SW_072"
    m.controller = pid
    m.zone = "HAND"
    m.atk = 3
    m.health = 4
    m.tags["ZONE"] = "HAND"
    m.tags["ATK"] = 3
    m.tags["479"] = 3
    m.tags["HEALTH"] = 4
    m.tags["COST"] = 3
    m.tags["ZONE_POSITION"] = 1
    return m


def test_battlecry_does_not_kill_taunt():
    register_arena_season_gap()
    defn = get_battlecry_def("CORE_SW_072")
    assert defn is not None, "CORE_SW_072 should be registered"
    taunts = [{"kind": "minion", "atk": 2, "health": 5, "taunt": True, "card_id": "CS2_122"}]
    fighters: list = []
    card = type("C", (), {"card_id": "CORE_SW_072", "tags": {}})()
    # Entity-like for hand_minion_attack
    gs = GameState()
    ent = gs.get_entity(99)
    ent.cardtype = "MINION"
    ent.card_id = "CORE_SW_072"
    ent.atk = 3
    ent.health = 4
    ent.tags["ATK"] = 3
    ent.tags["479"] = 3
    ent.tags["HEALTH"] = 4

    t2 = deepcopy(taunts)
    defn.apply(t2, fighters, mult=1, card=ent, enemy_shield=False)
    assert t2[0]["health"] == 5, t2  # 嘲讽仍在
    assert any(f.get("card_id") == "CORE_SW_072" for f in fighters), fighters
    print("OK Rustrot Viper does not destroy taunt", t2, fighters)


def test_lethal_note_does_not_need_viper_when_board_clears():
    """场攻已够斩且对面无嘲讽时，不应提示打锈烂蝰蛇。"""
    register_arena_season_gap()
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2, hp=30, dmg=25)  # 5 血
    _minion(gs, 10, 1, 6, 6)  # 场攻 6 已斩
    _hand_viper(gs, 40, 1)

    checker = LethalChecker(gs)
    total, sources, is_lethal = checker.calculate_lethal_potential()
    assert is_lethal, (total, sources)
    face = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note() or ""
    assert "锈烂" not in note and "蝰蛇" not in note, note
    assert face >= 5, face
    print("OK lethal without Rustrot tip", total, note, face)


def test_viper_does_not_unlock_taunt_lethal():
    """仅靠锈烂蝰蛇「假消灭」嘲讽不应构成斩杀提示。"""
    register_arena_season_gap()
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2, hp=30, dmg=25)  # 5 血
    _minion(gs, 10, 1, 5, 5)
    _minion(gs, 20, 2, 1, 8, taunt=True)  # 嘲讽挡脸；蝰蛇不该拆掉它
    _hand_viper(gs, 40, 1)

    checker = LethalChecker(gs)
    total, sources, is_lethal = checker.calculate_lethal_potential()
    note = ""
    try:
        checker.overlay_board_face_damage()
        note = checker.overlay_spell_note() or ""
    except Exception:
        pass
    assert not is_lethal, (total, sources, note)
    assert "锈烂" not in note and "蝰蛇" not in note, note
    print("OK no false lethal via Rustrot", total, note)


if __name__ == "__main__":
    test_classify_weapon_destroy_not_destroy_enemy()
    test_ooze_same()
    test_battlecry_does_not_kill_taunt()
    test_lethal_note_does_not_need_viper_when_board_clears()
    test_viper_does_not_unlock_taunt_lethal()
    print("ALL PASS")
