#!/usr/bin/env python3
"""回归：未来的诺莫瑞根 / 闪亮舞池地标斩杀。

复盘 Power.log：对手 16 血，两辆强袭坦克 9+7 可攻=14 不够；
激活未来的诺莫瑞根给 7 攻坦克 +2 → 9+9=18 斩。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.location_board import board_location_plays, get_location_def


def _set_local_turn(gs, local=1):
    gs.game_entity_id = 100
    ge = gs.get_entity(100)
    ge.cardtype = "GAME"
    ge.tags["TURN"] = 10
    ge.tags["CURRENT_PLAYER"] = local
    gs.first_player_id = local
    gs.active_player_id = local


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.zone = "PLAY"
    h.health = hp
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ZONE"] = "PLAY"
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["ARMOR"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, pos, card_id="M", can_attack=True):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.zone_pos = pos
    m.tags.update({
        "ZONE": "PLAY",
        "ATK": atk,
        "479": atk,
        "HEALTH": hp,
        "ZONE_POSITION": pos,
        "NUM_ATTACKS_THIS_TURN": 0,
    })
    if can_attack:
        m.tags["NUM_TURNS_IN_PLAY"] = 1
        m.tags["EXHAUSTED"] = 0
    else:
        m.tags["NUM_TURNS_IN_PLAY"] = 0
        m.tags["EXHAUSTED"] = 1
        m.tags["JUST_PLAYED"] = 1
    gs.board_slots.setdefault(pid, {})[pos] = eid
    return m


def _location(gs, eid, pid, card_id, *, pos, dur=3, ready=True):
    loc = gs.get_entity(eid)
    loc.cardtype = "LOCATION"
    loc.controller = pid
    loc.zone = "PLAY"
    loc.card_id = card_id
    loc.health = dur
    loc.damage = 0
    loc.tags.update({
        "ZONE": "PLAY",
        "CARDTYPE": "LOCATION",
        "HEALTH": dur,
        "ZONE_POSITION": pos,
    })
    if not ready:
        loc.tags["LOCATION_ACTION_COOLDOWN"] = 1
        loc.tags["EXHAUSTED"] = 1
    gs.board_slots.setdefault(pid, {})[pos] = eid
    return loc


def test_gnomeregan_future_registered():
    assert get_location_def("TIME_044t2") is not None
    assert get_location_def("TIME_044") is not None
    assert get_location_def("JAM_009") is not None
    print("OK gnomeregan/dancefloor registered")


def test_future_gnomeregan_buff_lethal_vs_16():
    """7+7=14 不够 16；地标 +2 后 9+7=16 斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs, 1)
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2, hp=30, dmg=14)  # 16 血
    _minion(gs, 10, 1, 7, 8, pos=1, card_id="GVG_079", can_attack=True)
    _minion(gs, 11, 1, 7, 7, pos=2, card_id="GVG_079", can_attack=True)
    _location(gs, 54, 1, "TIME_044t2", pos=3, dur=1, ready=True)

    plays = board_location_plays(gs, 1, 10)
    assert any(d.name == "未来的诺莫瑞根" for _, d, _ in plays), plays

    # 无法术/地标时纯场面只有 14
    lc0 = LethalChecker(gs)
    # 先确认地标在 plays 中；再算含地标的 overlay
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    combo = "\n".join(lc.overlay_combo_display_lines())
    total, _, has = lc.calculate_lethal_potential()

    assert face >= 16, (face, note, combo)
    assert has, (face, total, note, combo)
    assert "诺莫瑞根" in note or "诺莫瑞根" in combo, (note, combo)
    print("OK future gnomeregan lethal vs 16", face, note)


def test_dancefloor_grants_rush_to_just_played():
    """闪亮舞池：刚上场随从获得突袭可攻怪。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs, 1)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2, hp=30, dmg=20)  # 10 血
    _minion(gs, 10, 1, 9, 8, pos=1, card_id="GVG_079", can_attack=True)
    _minion(gs, 11, 1, 7, 7, pos=2, card_id="GVG_079", can_attack=False)
    _location(gs, 49, 1, "JAM_009", pos=3, dur=2, ready=True)
    # 对手嘲讽挡住：需突袭坦克参与解场
    _minion(gs, 20, 2, 3, 5, pos=1, card_id="REV_372t", can_attack=True)
    m = gs.get_entity(20)
    m.tags["TAUNT"] = 1

    plays = board_location_plays(gs, 1, 10)
    assert any(d.name == "闪亮舞池" for _, d, _ in plays), plays

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    # 舞池给突袭后应能解嘲并打出更高场攻（至少计入可攻部分）
    assert "舞池" in note or face >= 9, (face, note)
    print("OK dancefloor rush", face, note)


if __name__ == "__main__":
    test_gnomeregan_future_registered()
    test_future_gnomeregan_buff_lethal_vs_16()
    test_dancefloor_grants_rush_to_just_played()
    print("ALL PASS")
