#!/usr/bin/env python3
"""回归：球霸斩杀按「场攻+3 能否斩 → 场攻能否压英雄至最低血」。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.spell_board import board_enables_lowest_hit_face_lethal


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10, atk=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = dmg
    h.atk = atk
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    if atk:
        h.tags["ATK"] = atk
        h.tags["479"] = atk
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="M", turns=1):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk, "HEALTH": hp,
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0 if turns else 1,
        "NUM_TURNS_IN_PLAY": turns,
    })
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_bc(gs, eid, pid, card_id, cost):
    c = gs.get_entity(eid)
    c.cardtype = "MINION"
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = cost
    return c


def test_board_enables_lowest_hit_face_lethal_helper():
    """算法单元：1) 场攻+3 够斩；2) 场攻能把英雄压到最低血。"""
    # 4 血、随从 2 血、场攻 3：3+3>=4 且 4-3=1 <= 2 → 可斩
    assert board_enables_lowest_hit_face_lethal(
        board_face=3, opponent_hp=4, enemy_minion_healths=[5, 2, 3], hit_damage=3,
    )
    # 场攻只有 2：打脸后英雄仍 2，与套娃并列最低，但 2+3>=4；
    # 全打脸后 hero=2 <= min=2 → 仍可（并列优先英雄）
    assert board_enables_lowest_hit_face_lethal(
        board_face=2, opponent_hp=4, enemy_minion_healths=[5, 2, 3], hit_damage=3,
    )
    # 场攻+3 不够斩
    assert not board_enables_lowest_hit_face_lethal(
        board_face=1, opponent_hp=5, enemy_minion_healths=[2], hit_damage=3,
    )
    # 场攻够斩总和，但压不低英雄（场攻 0，英雄 4 > 随从 2）
    assert not board_enables_lowest_hit_face_lethal(
        board_face=0, opponent_hp=4, enemy_minion_healths=[2], hit_damage=3,
    )
    print("OK lowest-hit lethal helper")


def test_ball_hog_attack_first_then_face_lethal():
    """
    对手 4 血；场上有 2 血非嘲讽；我方 3 攻可打脸 + 手牌球霸。
    1) 场攻 3 + 球霸 3 >= 4 → 可能斩
    2) 不出球霸先打脸 → 英雄 1 血，低于套娃 2 → 球霸打脸斩杀
    """
    assert get_battlecry_def("TOY_642") is not None
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, hp=30, dmg=26)  # 4 血
    _minion(gs, 10, 1, 3, 3, card_id="REV_244", turns=1)
    _minion(gs, 20, 2, 5, 5, card_id="END_015")
    _minion(gs, 21, 2, 3, 2, card_id="TOY_893")
    _minion(gs, 22, 2, 1, 3, card_id="ETC_831")
    _hand_bc(gs, 30, 1, "TOY_642", 4)

    lc = LethalChecker(gs)
    enemy = lc._build_enemy_minion_states(1)
    fighters = lc._build_fighters(gs.get_overlay_board(1), 1)
    card = next(c for c in gs.get_hand(1) if c.card_id == "TOY_642")
    defn = get_battlecry_def("TOY_642")
    seq = [(defn, 4, card)]

    sf = lc._unpack_face_outcome(
        lc._simulate_line_outcome(
            enemy, fighters, seq, "spell_first",
            spell_mult=1, defender_shield=False, available_mana=10,
        )
    )
    af = lc._unpack_face_outcome(
        lc._simulate_line_outcome(
            enemy, fighters, seq, "attack_first",
            spell_mult=1, defender_shield=False, available_mana=10,
        )
    )
    # spell_first: 板 3，球霸打套娃 → 总伤 3
    assert sf[0] == 3, f"spell_first expected 3, got {sf}"
    # attack_first: 板 3 + 球霸打脸 3 → 6
    assert af[0] >= 6, f"attack_first expected >=6 (3+3), got {af}"
    assert af[8] >= 3 or (af[0] - af[1]) >= 3, (
        f"battlecry face should be counted, got {af}"
    )

    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    _, _, lethal = lc.calculate_lethal_potential()
    assert face >= 6, f"overlay face expected >=6, got {face} note={note!r}"
    assert lethal, f"should lethal vs 4hp, face={face} note={note!r}"
    assert "球霸" in note or "野猪" in note, note
    assert "先攻后法" in note, f"expected 先攻后法, note={note!r}"
    print("OK ball hog attack-first lethal", face, note, lethal)


if __name__ == "__main__":
    test_board_enables_lowest_hit_face_lethal_helper()
    test_ball_hog_attack_first_then_face_lethal()
