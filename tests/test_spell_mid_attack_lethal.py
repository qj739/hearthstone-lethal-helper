#!/usr/bin/env python3
"""法间穿插：炽燃圣光 + 换嘲 + 抹除存在 → 必定斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def _hero(gs, eid, pid, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(
    gs, eid, pid, atk, hp, *, taunt=False, card_id="", dormant=False, board_ready=True,
):
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
    if board_ready:
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if taunt:
        m.tags["TAUNT"] = 1
    if dormant:
        m.tags["DORMANT"] = 1
        m.tags["UNTOUCHABLE"] = 1
    return m


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    return s


def test_light_burns_cease_mid_attack_guaranteed_lethal():
    """
    对手 6 血；休眠玛瑟里顿不挡脸；两嘲讽海獭 + 嘲讽 5/9 德鲁伊；
    两只 6 攻复制机器人；手牌炽燃圣光 + 抹除存在。

    必定线：圣光杀海獭 → 一只机器人换另一海獭 → 抹除存在必中德鲁伊 → 另一只打脸。
    """
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=7, used=0)
    h2 = _hero(gs, 2, 2)
    h2.damage = 24  # 6 HP

    _minion(gs, 10, 1, 6, 1, card_id="TOY_601t2")
    _minion(gs, 11, 1, 6, 3, card_id="TOY_601t2")
    _minion(gs, 20, 2, 12, 12, card_id="TOY_647", dormant=True)
    _minion(gs, 21, 2, 5, 9, taunt=True, card_id="TIME_033")
    _minion(gs, 22, 2, 3, 3, taunt=True, card_id="TSC_650t4")
    _minion(gs, 23, 2, 3, 3, taunt=True, card_id="TSC_650t4")
    _hand_spell(gs, 30, 1, "REV_249", 0)
    _hand_spell(gs, 31, 1, "TIME_433", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, prob, uses_random, _ = checker.overlay_face_stats()
    note = checker.overlay_spell_note() or ""
    order = getattr(checker, "_overlay_best_order", "")

    assert total >= 6, (total, note, order)
    assert prob == 1.0, (prob, note, order, uses_random)
    assert not uses_random, (uses_random, note, order)
    assert order == "spell_mid_attack" or "法间穿插" in note, (order, note)
    lethal_total, _, has_lethal = checker.calculate_lethal_potential()
    assert has_lethal, (lethal_total, note)
    print("OK mid-attack light+cease guaranteed lethal", total, prob, note, order)


def test_cease_alone_still_random_with_two_targets():
    """仅抹除存在、场上仍有多个有效目标时，仍走随机线。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 2, 6, taunt=True, card_id="T26")
    _minion(gs, 21, 2, 5, 5, card_id="N55")
    _hand_spell(gs, 30, 1, "TIME_433", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, uses_random, _ = checker.overlay_face_stats()
    assert total == 6, total
    assert uses_random
    print("OK cease alone still random", total)


if __name__ == "__main__":
    test_light_burns_cease_mid_attack_guaranteed_lethal()
    test_cease_alone_still_random_with_two_targets()
    print("all ok")
