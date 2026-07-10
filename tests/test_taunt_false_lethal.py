#!/usr/bin/env python3
"""回归：对手有嘲讽时，场攻不能绕过嘲讽直接判斩杀。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import entity_has_taunt, living_taunt_minions, is_dormant


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


def _minion(gs, eid, pid, atk, hp, *, card_id="", taunt_tag=None):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if taunt_tag is not None:
        m.tags["TAUNT"] = taunt_tag
    return m


def test_card_db_taunt_without_tag():
    gs = GameState()
    m = gs.get_entity(1)
    m.card_id = "TOY_000"
    assert entity_has_taunt(m)


def test_taunt_blocks_board_lethal_when_not_enough_face():
    """焦油泥浆怪 5/5 嘲讽 + 8 场攻，清嘲后只剩 3 打脸，不够 6 血。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    gs.get_entity(100).tags["TURN"] = 10
    _hero(gs, 1, 1, mana=10, used=0)
    opp = _hero(gs, 2, 2)
    opp.health = 6
    opp.damage = 0
    _minion(gs, 10, 1, 8, 8, card_id="CS2_150")
    _minion(gs, 20, 2, 2, 5, card_id="TOY_000")  # 无 TAUNT tag，靠 card db

    assert len(living_taunt_minions(gs.get_board(2), gs)) == 1

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    assert face < 6, (face, lc.overlay_board_breakdown(), lc.overlay_spell_note())
    assert not has, (face, has, lc.overlay_spell_note())


def test_taunt_cleared_still_lethal():
    """大场攻清嘲后仍可斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    gs.get_entity(100).tags["TURN"] = 10
    _hero(gs, 1, 1, mana=10, used=0)
    opp = _hero(gs, 2, 2)
    opp.health = 6
    _minion(gs, 10, 1, 8, 8, card_id="CS2_150")
    _minion(gs, 11, 1, 8, 8, card_id="CS2_150")
    _minion(gs, 20, 2, 2, 5, card_id="TOY_000", taunt_tag=1)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    assert face >= 6, (face, lc.overlay_board_breakdown())
    assert has, (face, has)


def test_taunt_tag_zero_overrides_card_db():
    """红牌休眠后 TAUNT=0：不再用牌面库兜底成嘲讽。"""
    gs = GameState()
    m = gs.get_entity(1)
    m.card_id = "EDR_260"
    m.cardtype = "MINION"
    m.tags["TAUNT"] = 0
    m.tags["DORMANT"] = 1
    assert not entity_has_taunt(m, gs)


def test_dormant_wake_cached_tag_does_not_remark_dormant():
    """唤醒后 CACHED_TAG_FOR_DORMANT_CHANGE 不应把随从标回休眠。"""
    from hdt_python.power_parser import PowerLogParser

    gs = GameState()
    p = PowerLogParser("", gs)
    m = gs.get_entity(37)
    m.card_id = "EDR_260"
    m.cardtype = "MINION"
    m.controller = 2
    m.tags["ZONE"] = "PLAY"
    m.tags["ZONE_POSITION"] = 1
    m.tags["TAUNT"] = 0
    m.tags["DORMANT"] = 0
    line = (
        "CACHED_TAG_FOR_DORMANT_CHANGE Entity=[entityName=x id=37 zone=PLAY "
        "zonePos=1 cardId=EDR_260 player=2] tag=TAUNT value=0"
    )
    p._handle_cached_dormant_change(line)
    assert m.tags.get("DORMANT") == 0
    assert not is_dormant(m, gs)


def test_red_card_dormant_enemy_not_counted_as_taunt():
    """休眠敌方嘲讽不计入 living_taunts，场攻可打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    gs.get_entity(100).tags["TURN"] = 10
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="CS2_150")
    # 敌方大嘲讽被红牌休眠：TAUNT 已剥除
    dormant = _minion(gs, 20, 2, 4, 5, card_id="EDR_260", taunt_tag=0)
    dormant.tags["DORMANT"] = 1

    assert len(living_taunt_minions(gs.get_board(2), gs)) == 0
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 6, face


if __name__ == "__main__":
    test_card_db_taunt_without_tag()
    test_taunt_blocks_board_lethal_when_not_enough_face()
    test_taunt_cleared_still_lethal()
    test_taunt_tag_zero_overrides_card_db()
    test_dormant_wake_cached_tag_does_not_remark_dormant()
    test_red_card_dormant_enemy_not_counted_as_taunt()
    print("OK taunt false lethal")
