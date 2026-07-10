#!/usr/bin/env python3
"""回归：工厂装配机回合结束随机攻击不应与 pure_face 重复计入场攻。"""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import GameState, PowerLogParser
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


def _set_local_turn(gs, local_pid=1):
    if gs.game_entity_id is None:
        gs.game_entity_id = 100
        ge = gs.get_entity(100)
        ge.cardtype = "GAME"
    gs.first_player_id = local_pid
    game = gs.entities[gs.game_entity_id]
    game.tags["TURN"] = 1
    game.tags["CURRENT_PLAYER"] = local_pid


def _minion(gs, eid, pid, atk, hp, *, card_id="", can_attack=True):
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
    m.tags["HEALTH"] = hp
    if can_attack:
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    else:
        m.tags["NUM_TURNS_IN_PLAY"] = 0
        m.tags["EXHAUSTED"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid


def _hand_spell(gs, eid, pid, card_id, cost):
    c = gs.get_entity(eid)
    c.cardtype = "SPELL"
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = cost


def test_toy601_end_turn_not_double_counted_in_overlay():
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_23_08_17_32\Power.log"
    )
    if not log.is_file():
        print("SKIP toy601 log replay (log missing)")
        return

    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[:21098]:
            if line.strip():
                parser.process_line(line.rstrip())

    lc = LethalChecker(gs)
    board_view = lc._board_view_for_fighters(gs.local_player_id or 1)
    pure_immediate = lc._compute_immediate_board_face(
        board_view, gs.local_player_id or 1, [], False,
    )
    et = lc._board_end_turn_face(gs.local_player_id or 1, False)
    pure_face = pure_immediate + et

    face = lc.overlay_board_face_damage()
    pure, minion_bd, _, _, _ = lc.overlay_board_breakdown()

    assert pure_immediate == 0, pure_immediate
    assert et == 6, et
    assert pure_face == 6, pure_face
    assert face <= 6, (face, minion_bd, pure, lc.overlay_face_stats())
    assert minion_bd <= 6, (face, minion_bd, pure)
    print("OK toy601 end turn no double count", face, minion_bd, pure)


def test_t2_only_plus_spell_no_et_double():
    """场上仅有可攻 token + 阳炎：不应把回合结束再算一遍。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 1, card_id="TOY_601t2", can_attack=True)
    _hand_spell(gs, 30, 1, "GDB_305", 0)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    pure, minion_bd, _, spell_bd, _ = lc.overlay_board_breakdown()
    uses_random = lc.overlay_face_stats()[2]
    assert not uses_random, uses_random
    assert pure == 6, pure
    assert face == pure + spell_bd, (face, pure, spell_bd)
    assert face <= 10, face
    print("OK t2+spell no double ET", face, pure, spell_bd)


def test_factory_enemies_spell_peak_not_double_et():
    """刚下装配机 + 敌方随从 + 阳炎：峰值应为 法2+ET6，不是 12。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 7, card_id="TOY_601", can_attack=False)
    _minion(gs, 20, 2, 2, 2, card_id="E1")
    _minion(gs, 21, 2, 3, 3, card_id="E2")
    _hand_spell(gs, 30, 1, "GDB_305", 0)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    pure, minion_bd, _, spell_bd, _ = lc.overlay_board_breakdown()
    mc_max, _, uses_random, top = lc.overlay_face_stats()
    assert uses_random
    assert pure == 0, pure
    assert face <= 8, (face, minion_bd, spell_bd, mc_max, top)
    assert mc_max <= 8, mc_max
    print("OK factory+spell peak", face, spell_bd, mc_max, top)


if __name__ == "__main__":
    test_toy601_end_turn_not_double_counted_in_overlay()
    test_t2_only_plus_spell_no_et_double()
    test_factory_enemies_spell_peak_not_double_et()
