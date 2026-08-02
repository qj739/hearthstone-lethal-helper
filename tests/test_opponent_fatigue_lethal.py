#!/usr/bin/env python3
"""对手牌库空时，下回合斩杀预览应把疲劳单独加进场攻总和并显示。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState


def _hero(gs, eid, pid, *, dmg=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ARMOR"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _player(gs, eid, pid, *, fatigue=0):
    p = gs.get_entity(eid)
    p.cardtype = "PLAYER"
    p.controller = pid
    p.tags["FATIGUE"] = fatigue
    gs.player_ids[eid] = pid
    gs.player_names[pid] = f"Player{pid}"
    return p


def test_opponent_turn_fatigue_added_to_face():
    """对方回合：牌库空、已疲3 → 下次疲4；场攻12+疲4=16，对手15血应判下回合斩。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 1
    _hero(gs, 10, 2)
    _hero(gs, 20, 1, dmg=15)
    _player(gs, 5, 1, fatigue=3)

    lc = LethalChecker(gs)
    assert lc._opponent_deck_count() == 0
    assert lc._opponent_fatigue_counter() == 3
    assert lc._opponent_upcoming_fatigue_damage() == 4
    assert lc._lethal_threshold_hp() == 15
    assert lc._lethal_search_threshold_hp() == 11

    lc._reset_overlay_board_breakdown(12, 12, 0, 12)
    assert lc.overlay_fatigue_face() == 4
    assert lc.cached_overlay_face() == 16
    assert lc.overlay_display_face() == 16
    assert lc.overlay_red_prompt_ok(opp_lethal_now=False) is True


def test_opponent_turn_fatigue_zero_means_next_is_one():
    """牌库空但尚未疲劳：下一次为 1。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 1
    _hero(gs, 10, 2)
    _hero(gs, 20, 1, dmg=20)
    _player(gs, 5, 1, fatigue=0)

    lc = LethalChecker(gs)
    assert lc._opponent_upcoming_fatigue_damage() == 1
    lc._reset_overlay_board_breakdown(9, 9, 0, 9)
    assert lc.overlay_fatigue_face() == 1
    assert lc.cached_overlay_face() == 10


def test_local_turn_fatigue_counted_for_end_turn_lethal():
    """我方回合：结束回合后对方抽牌疲劳应计入（最强音+疲劳等）。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 2
    _hero(gs, 10, 2)
    _hero(gs, 20, 1, dmg=21)  # 9 血
    _player(gs, 5, 1, fatigue=3)

    lc = LethalChecker(gs)
    assert lc._opponent_upcoming_fatigue_damage() == 4
    assert lc._lethal_threshold_hp() == 9
    assert lc._lethal_search_threshold_hp() == 5

    lc._reset_overlay_board_breakdown(6, 0, 6, 6)
    assert lc.overlay_fatigue_face() == 4
    assert lc.cached_overlay_face() == 10
    assert lc.overlay_red_prompt_ok(opp_lethal_now=False) is True


def test_climactic_plus_fatigue_lethal_from_log():
    """复盘：通灵最强音 6 + 下次疲劳 4 ≥ 对手 9 血。"""
    import contextlib
    import io
    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_07_31_22_51_53\Power.log"
    )
    if not log.is_file():
        print("SKIP climactic+fatigue log")
        return
    target = 415200
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        with log.open(encoding="utf-8", errors="ignore") as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    p.process_line(line.rstrip())
                if i >= target:
                    break
    gs.in_game = True
    lc = LethalChecker(gs)
    assert lc._opponent_deck_count() == 0
    assert lc._opponent_fatigue_counter() == 3
    assert lc._opponent_upcoming_fatigue_damage() == 4
    face = lc.overlay_board_face_damage()
    assert lc.overlay_fatigue_face() == 4
    assert face >= 9, (face, lc.overlay_spell_note(), lc.overlay_board_breakdown())
    assert lc.overlay_red_prompt_ok(), (face, lc.overlay_spell_note())
    print("OK climactic+fatigue", face, lc.overlay_spell_note())


def test_opponent_turn_with_cards_in_deck_no_fatigue():
    """牌库未空时不计入疲劳。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 1
    _hero(gs, 10, 2)
    _hero(gs, 20, 1, dmg=15)
    _player(gs, 5, 1, fatigue=3)
    card = gs.get_entity(30)
    card.controller = 1
    card.zone = "DECK"
    card.tags["ZONE"] = "DECK"
    card.tags["CONTROLLER"] = 1

    lc = LethalChecker(gs)
    assert lc._opponent_deck_count() == 1
    assert lc._opponent_upcoming_fatigue_damage() == 0
    assert lc._lethal_threshold_hp() == 15
    lc._reset_overlay_board_breakdown(12, 12, 0, 12)
    assert lc.overlay_fatigue_face() == 0
    assert lc.cached_overlay_face() == 12


def test_opponent_deck_count_stable_while_entities_grow():
    """牌库计数遍历前快照实体列表，模拟期间新增实体不影响本次计数。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 1
    _hero(gs, 10, 2)
    _hero(gs, 20, 1, dmg=15)
    _player(gs, 5, 1, fatigue=3)
    card = gs.get_entity(30)
    card.controller = 1
    card.zone = "DECK"
    card.tags["ZONE"] = "DECK"
    card.tags["CONTROLLER"] = 1

    lc = LethalChecker(gs)
    assert lc._opponent_deck_count() == 1
    gs.get_entity(9000)
    gs.get_entity(9001)
    assert lc._opponent_deck_count() == 1


def test_fatigue_tag_from_battle_tag_power_log():
    """战网名 TAG_CHANGE FATIGUE 须写入 Player 实体（否则永远疲1）。"""
    import contextlib
    import io
    from pathlib import Path
    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_07_23_18_25_26\Power.log"
    )
    if not log.is_file():
        print("SKIP fatigue battle-tag log")
        return
    # FATIGUE value=4 之后
    target = 180000
    with open(log, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max(s for s in starts if s < target)
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            p.process_line(lines[i].rstrip())
    gs.in_game = True
    lc = LethalChecker(gs)
    assert lc._opponent_deck_count() == 0
    assert lc._opponent_fatigue_counter() >= 4, lc._opponent_fatigue_counter()
    assert lc.is_opponent_turn()
    assert lc._opponent_upcoming_fatigue_damage() == lc._opponent_fatigue_counter() + 1
    print("OK fatigue from battle-tag log", lc._opponent_fatigue_counter())


if __name__ == "__main__":
    test_opponent_turn_fatigue_added_to_face()
    test_opponent_turn_fatigue_zero_means_next_is_one()
    test_local_turn_fatigue_counted_for_end_turn_lethal()
    test_opponent_turn_with_cards_in_deck_no_fatigue()
    test_opponent_deck_count_stable_while_entities_grow()
    test_fatigue_tag_from_battle_tag_power_log()
    test_climactic_plus_fatigue_lethal_from_log()
    print("OK opponent fatigue lethal")
