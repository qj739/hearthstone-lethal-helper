#!/usr/bin/env python3
"""月亮井 + 龙息 + 6/6/3/1 场面：场攻/斩杀/步骤文案回归。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.overlay_combo_format import build_lethal_combo_lines


def _hero(gs, eid, pid, *, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, taunt=False, exhausted=False):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = "X"
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["EXHAUSTED"] = 1 if exhausted else 0
    m.tags["NUM_TURNS_IN_PLAY"] = 0 if exhausted else 1
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if taunt:
        m.tags["TAUNT"] = 1
    return m


def _hand_spell(gs, eid, pid, cid, cost, *, script_dmg=None):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = cid
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    if script_dmg is not None:
        s.tags["TAG_SCRIPT_DATA_NUM_1"] = script_dmg
    return s


def _moonwell_dragon_board(*, opp_damage=0, exhausted=False):
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 64, 1)
    opp = _hero(gs, 66, 2)
    opp.damage = opp_damage
    _minion(gs, 10, 1, 6, 6, exhausted=exhausted)
    _minion(gs, 11, 1, 3, 1, exhausted=exhausted)
    _minion(gs, 20, 2, 6, 4, taunt=True)
    _hand_spell(gs, 121, 1, "EDR_476", 5)
    _hand_spell(gs, 242, 1, "CATA_464t", 2, script_dmg=3)
    return gs


def test_moonwell_dragon_breath_max_face_with_taunt_clear():
    """龙息点残血嘲讽破嘲后双随从打脸：7 法术 + 9 随从 = 16。"""
    gs = _moonwell_dragon_board()
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, _, spell, _ = lc.overlay_board_breakdown()
    assert face == 16, (face, lc.overlay_board_breakdown(), lc.overlay_spell_note())
    assert spell == 7, (spell, lc.overlay_board_breakdown())
    assert lc.overlay_battlecry_face() == 0


def test_moonwell_dragon_breath_not_lethal_at_20_hp():
    gs = _moonwell_dragon_board(opp_damage=10)
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    assert face == 16
    assert not has, (face, has)


def test_moonwell_dragon_breath_only_spell_if_minions_cant_attack():
    """随从不能动时只有月亮井 4 + 龙息 3 打脸 = 7。"""
    gs = _moonwell_dragon_board(exhausted=True)
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face == 7, (face, lc.overlay_board_breakdown())


def test_moonwell_dragon_breath_combo_shows_dragon_on_taunt():
    """步骤文案应显示龙息打在嘲讽上，而非误导为仅打脸。"""
    gs = _moonwell_dragon_board()
    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    combo = " ".join(build_lethal_combo_lines(lc))
    assert "龙息" in combo
    assert "敌方英雄" not in combo or "6/2" in combo or "6/4" in combo or "嘲讽" in combo, combo


def test_battlecry_face_not_in_spell_breakdown():
    """战吼打脸单独分项，不计入法术。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 64, 1)
    _hero(gs, 66, 2)
    s = gs.get_entity(121)
    s.cardtype = "MINION"
    s.controller = 1
    s.zone = "HAND"
    s.card_id = "TOY_101"
    s.cost = 5
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = 5

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, _, spell, _ = lc.overlay_board_breakdown()
    bc = lc.overlay_battlecry_face()
    assert face == 3, (face, lc.overlay_board_breakdown())
    assert spell == 0, (spell, bc)
    assert bc == 3, (spell, bc)


if __name__ == "__main__":
    test_moonwell_dragon_breath_max_face_with_taunt_clear()
    test_moonwell_dragon_breath_not_lethal_at_20_hp()
    test_moonwell_dragon_breath_only_spell_if_minions_cant_attack()
    test_moonwell_dragon_breath_combo_shows_dragon_on_taunt()
    test_battlecry_face_not_in_spell_breakdown()
    print("OK moonwell dragon breath")
