#!/usr/bin/env python3
"""回归：私藏魔杖生成奥术飞弹后应能计入斩杀（非亡语）。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


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


def test_contraband_wands_queues_missiles():
    defn = get_board_spell_def("JAIL_312")
    assert defn is not None
    res = defn.apply([], [], mult=1, enemy_shield=False)
    assert len(res.add_hand_pending) == 3
    assert all(sid == "EX1_277" for sid, _, _ in res.add_hand_pending)
    print("OK wand queues 3 missiles")


def test_wand_plus_missiles_lethal_vs_4():
    """
    对手 4 血、空场、4 费：私藏魔杖(2) → 两发奥术飞弹(1+1) = 6 打脸。
    复现对局末手：冰冻之触后 4 血，魔杖未接入时只显示技能 1。
    """
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=4)
    _hero(gs, 2, 2, hp=30, dmg=26)  # 4 血
    _hand_spell(gs, 30, 1, "JAIL_312", 2)

    # 英雄技能火焰冲击（可选）
    hp = gs.get_entity(40)
    hp.cardtype = "HERO_POWER"
    hp.controller = 1
    hp.zone = "PLAY"
    hp.card_id = "HERO_08bp"
    hp.cost = 2
    hp.tags["ZONE"] = "PLAY"
    hp.tags["COST"] = 2

    defn = get_board_spell_def("JAIL_312")
    card = next(c for c in gs.get_hand(1) if c.card_id == "JAIL_312")
    res = apply_spell_sequence(
        [], [], [(defn, 2, card)],
        enemy_shield=False, gs=gs, player_id=1, mana_budget=4,
    )
    assert res.direct_face_damage >= 6, (
        f"expected >=6 face from wand+2 missiles, got {res.direct_face_damage}"
    )

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    _, _, lethal = lc.calculate_lethal_potential()
    assert face >= 6, f"overlay face expected >=6, got {face} note={note!r}"
    assert lethal, f"should lethal vs 4, face={face} note={note!r}"
    assert "魔杖" in note or "飞弹" in note, note
    print("OK wand lethal", face, note, lethal)


def test_wand_missile_mana_spent_includes_generated():
    """私藏魔杖+3飞弹费用应为 2+1+1+1=5，不能只记魔杖 2 费。"""
    from hdt_python.spell_board import spell_sequence_mana_left

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=5)
    _hero(gs, 2, 2, hp=30, dmg=20)  # 10 血
    _hand_spell(gs, 30, 1, "JAIL_312", 2)

    defn = get_board_spell_def("JAIL_312")
    card = next(c for c in gs.get_hand(1) if c.card_id == "JAIL_312")
    seq = [(defn, 2, card)]
    left = spell_sequence_mana_left(seq, 5)
    assert left == 0, f"expected 0 mana left after wand+3 missiles, got {left}"

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    spent = getattr(lc, "_overlay_mana_spent", 0)
    _, _, _, spell_face, _ = lc.overlay_board_breakdown()
    assert spent == 5, f"overlay mana_spent expected 5, got {spent} face={face}"
    assert spell_face == 9, f"three missiles expected 9 spell face, got {spell_face}"
    print("OK wand mana spent", spent, "spell", spell_face, "face", face)


def test_wand_not_enough_mana_for_fourth_missile():
    """魔杖后手牌另有飞弹时，3 费只能再打 3 发，不能把第 4 发算进去。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=3)
    _hero(gs, 2, 2, hp=30, dmg=21)  # 9 血
    # 已生成在手的 4 张飞弹（魔杖已打出）
    for i, eid in enumerate((30, 31, 32, 33)):
        _hand_spell(gs, eid, 1, "EX1_277", 1)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    spent = getattr(lc, "_overlay_mana_spent", 0)
    note = lc.overlay_spell_note()
    _, _, _, spell_face, _ = lc.overlay_board_breakdown()
    assert spent == 3, (spent, face, note)
    assert spell_face == 9, (spell_face, note)
    # 关键：不得把第 4 发算进费用或分项
    assert "奥术飞弹+奥术飞弹+奥术飞弹+奥术飞弹" not in note, note
    print("OK three missiles only", spell_face, spent, note)


if __name__ == "__main__":
    test_contraband_wands_queues_missiles()
    test_wand_plus_missiles_lethal_vs_4()
    test_wand_missile_mana_spent_includes_generated()
    test_wand_not_enough_mana_for_fourth_missile()
