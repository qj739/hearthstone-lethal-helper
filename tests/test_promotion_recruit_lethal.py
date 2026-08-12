#!/usr/bin/env python3
"""晋升 REV_842：白银之手新兵 +3/+3，应计入斩杀搜索。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import (
    get_board_spell_def,
    hand_board_spells,
    is_silver_hand_recruit_card_id,
)
from hdt_python.spell_p0_buff import _apply_promotion


def _hero(gs, eid, pid, *, dmg=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m"):
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
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
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


def test_silver_hand_recruit_ids():
    assert is_silver_hand_recruit_card_id("CS2_101t")
    assert is_silver_hand_recruit_card_id("CS2_101t8")
    assert is_silver_hand_recruit_card_id("CORE_CS2_101t")
    assert not is_silver_hand_recruit_card_id("CS2_101")
    assert not is_silver_hand_recruit_card_id("CS2_088")


def test_promotion_buffs_recruit_only():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2, dmg=19)
    _minion(gs, 30, 1, 3, 1, card_id="CS2_101t")
    _minion(gs, 31, 1, 8, 8, card_id="CS2_088")  # 非新兵，不应被选
    _hand_spell(gs, 40, 1, "REV_842", 1)

    lc = LethalChecker(gs)
    fighters = lc._build_fighters(gs.get_overlay_board(1), 1)
    recruit = next(f for f in fighters if f.get("card_id") == "CS2_101t")
    other = next(f for f in fighters if f.get("card_id") == "CS2_088")
    assert recruit["atk"] == 3
    _apply_promotion([], fighters, mult=1, enemy_shield=False, gs=gs, player_id=1)
    recruit = next(f for f in fighters if f.get("card_id") == "CS2_101t")
    other = next(f for f in fighters if f.get("card_id") == "CS2_088")
    assert recruit["atk"] == 6
    assert recruit["health"] == 4
    assert recruit.get("taunt") is True
    assert other["atk"] == 8

    assert get_board_spell_def("REV_842") is not None
    assert get_board_spell_def("CORE_REV_842") is not None
    assert any(s.card_id == "REV_842" for s, _, _ in hand_board_spells(gs, 1, 10))


def test_promotion_enables_lethal_with_consecration():
    """
    复盘：场攻约 17，对手 21 血；晋升抬一只新兵 +3 → 20，再疲劳/奉献等凑满斩。
    """
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 10, 1, dmg=0)
    hero.tags["RESOURCES"] = 8
    hero.tags["RESOURCES_USED"] = 3  # 剩 5 费
    _hero(gs, 20, 2, dmg=9)  # 21 血
    # 可攻新兵合计 17 攻
    _minion(gs, 30, 1, 5, 1, card_id="CS2_101t")
    _minion(gs, 31, 1, 5, 1, card_id="CS2_101t4")
    _minion(gs, 32, 1, 4, 1, card_id="CS2_101t5")
    _minion(gs, 33, 1, 3, 1, card_id="CS2_101t8")
    _hand_spell(gs, 40, 1, "REV_842", 1)
    _hand_spell(gs, 41, 1, "CORE_CS2_093", 4)  # 奉献 2 脸（可选）

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    total, _src, lethal = lc.calculate_lethal_potential()
    note = " ".join(lc.overlay_combo_display_lines()) + " " + (lc.overlay_spell_note() or "")
    assert face >= 21, f"expected face>=21 got {face} note={note}"
    assert lethal, f"should detect lethal total={total} face={face} note={note}"
    assert "晋升" in note, note


def test_promotion_skipped_without_recruit():
    """场上无新兵时，晋升不应进手法术枚举。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2, dmg=19)
    _minion(gs, 30, 1, 8, 8, card_id="CS2_088")
    _hand_spell(gs, 40, 1, "REV_842", 1)
    assert not any(s.card_id == "REV_842" for s, _, _ in hand_board_spells(gs, 1, 10))


if __name__ == "__main__":
    test_silver_hand_recruit_ids()
    test_promotion_buffs_recruit_only()
    test_promotion_enables_lethal_with_consecration()
    test_promotion_skipped_without_recruit()
    print("ok")
