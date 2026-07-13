#!/usr/bin/env python3
"""影犬 MAW_009：攻击后其他友方野兽 +2/+2，应计入斩杀/场攻。"""

import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import build_player_board
from hdt_python.spell_board import entity_is_beast
from hdt_python.rush_combat import stamp_fighter_attack_effects

POWER_LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_07_13_14_59_39\Power.log"
)
# 影犬刚落地、尚未攻击（对手 17 血，场上有嘲讽）
LINE_BEFORE_SHADEHOUND_ATTACK = 64534
# 影犬攻击燃琴小鬼后（鼠吻贮藏者已在日志中变为 4 攻）
LINE_AFTER_SHADEHOUND_ATTACK = 64939


def _hero(gs, eid, pid):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="", can_attack=True, beast=False):
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
    if beast:
        m.tags["CARDRACE"] = "BEAST"
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if not can_attack:
        m.tags["EXHAUSTED"] = 1
    return m


def test_power_parser_stores_cardrace_beast():
    gs = GameState()
    p = PowerLogParser("Power.log", gs)
    p._apply_tag(99, "CARDRACE", "BEAST")
    m = gs.get_entity(99)
    assert m.tags.get("CARDRACE") == "BEAST"
    assert entity_is_beast(m)


def _replay_power_log(line_no: int) -> GameState:
    if not POWER_LOG.is_file():
        return None
    lines = POWER_LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    starts = [
        i for i, l in enumerate(lines[:line_no])
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = starts[-1]
    gs = GameState()
    p = PowerLogParser(str(POWER_LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, line_no):
            p.process_line(lines[i].rstrip())
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    return gs


def test_power_log_before_shadehound_attack_simulates_buff():
    """实战回放：攻击前就应把影犬触发后的野兽攻算进场攻（8→10）。"""
    gs = _replay_power_log(LINE_BEFORE_SHADEHOUND_ATTACK)
    if gs is None:
        print("SKIP (log missing)")
        return

    shadehound = next(m for m in gs.get_board(2) if m.card_id == "MAW_009t")
    mouse = next(m for m in gs.get_board(2) if m.card_id == "JAIL_877t")
    assert entity_is_beast(mouse), "鼠吻贮藏者应有 CARDRACE=BEAST"
    stamp = {}
    stamp_fighter_attack_effects(stamp, shadehound.card_id or "")
    assert stamp.get("buff_other_beasts_on_attack") == (2, 2)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 10, (
        f"before attack expected face>=10 (shadehound buff), got {face}"
    )


def test_power_log_after_shadehound_attack_matches_simulation():
    """攻击后日志已写入 +2 攻，场攻应与攻击前模拟一致。"""
    gs_before = _replay_power_log(LINE_BEFORE_SHADEHOUND_ATTACK)
    gs_after = _replay_power_log(LINE_AFTER_SHADEHOUND_ATTACK)
    if gs_before is None:
        print("SKIP (log missing)")
        return

    lc_before = LethalChecker(gs_before)
    lc_after = LethalChecker(gs_after)
    face_before = lc_before.overlay_board_face_damage()
    face_after = lc_after.overlay_board_face_damage()
    mouse_after = next(m for m in gs_after.get_board(2) if m.card_id == "JAIL_877t")
    assert mouse_after.atk == 4
    assert face_before >= 10
    assert face_after >= 10
    assert face_before == face_after, (face_before, face_after)


def test_shadehound_buffs_other_beast_face_damage():
    """影犬 6 + 野兽 3 → 先 6 再 5 = 11 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    opp = _hero(gs, 20, 2)
    opp.tags["DAMAGE"] = 19
    opp.damage = 19
    _minion(gs, 30, 1, 6, 5, card_id="MAW_009", beast=True)
    _minion(gs, 31, 1, 3, 3, card_id="VAC_509t", beast=True)

    board = build_player_board(gs, 1, active_turn=True)
    face = board.face_attack_damage_no_taunt()
    assert face == 11, f"expected face=11 got {face}"

    lc = LethalChecker(gs)
    overlay_face = lc.overlay_board_face_damage()
    assert overlay_face >= 11, f"expected overlay face>=11 got {overlay_face}"
    total, _, has_lethal = lc.calculate_lethal_potential()
    assert has_lethal, f"should detect lethal total={total} face={overlay_face}"


def test_shadehound_does_not_buff_self():
    """仅影犬在场：6 打脸，不应给自己 +2。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    _hero(gs, 20, 2)
    _minion(gs, 30, 1, 6, 5, card_id="MAW_009", beast=True)

    board = build_player_board(gs, 1, active_turn=True)
    assert board.face_attack_damage_no_taunt() == 6


def test_shadehound_after_taunt_clear():
    """影犬先解 1 血嘲讽，buff 后野兽打脸 5。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1)
    opp = _hero(gs, 20, 2)
    opp.tags["DAMAGE"] = 24
    opp.damage = 24
    _minion(gs, 30, 1, 6, 5, card_id="MAW_009", beast=True)
    _minion(gs, 31, 1, 3, 3, card_id="VAC_509t", beast=True)
    taunt = _minion(gs, 40, 2, 1, 1, card_id="CS2_200")
    taunt.tags["TAUNT"] = 1

    lc = LethalChecker(gs)
    total, _, has_lethal = lc.calculate_lethal_potential()
    assert has_lethal, f"shadehound clear taunt then buffed beast should lethal total={total}"


if __name__ == "__main__":
    test_power_parser_stores_cardrace_beast()
    test_power_log_before_shadehound_attack_simulates_buff()
    test_power_log_after_shadehound_attack_matches_simulation()
    test_shadehound_buffs_other_beast_face_damage()
    test_shadehound_does_not_buff_self()
    test_shadehound_after_taunt_clear()
    print("ok")
