#!/usr/bin/env python3
"""CHANGE_ENTITY 变形后保留 NUM_TURNS_IN_PLAY，避免水蛭等已在场随从场攻被漏算。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import PowerLogParser, GameState, Entity
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import build_board_card, board_active_turn_for_display, is_exhausted


def test_transform_preserves_turns_in_play_for_attack():
    gs = GameState()
    p = PowerLogParser("", gs)
    e = Entity(entity_id=128, card_id="EDR_810t", controller=2)
    e.cardtype = "MINION"
    e.zone = "PLAY"
    e.health = 2
    e.tags.update({
        "ZONE": 1,
        "ZONE_POSITION": 3,
        "CARDTYPE": "MINION",
        "HEALTH": 2,
        "NUM_TURNS_IN_PLAY": 2,
        "NUM_ATTACKS_THIS_TURN": 0,
        "EXHAUSTED": 0,
    })
    gs.entities[128] = e
    gs.board_slots[2] = {3: 128}
    gs.active_player_id = 2

    p._handle_change_entity(
        type("M", (), {
            "group": lambda self, k: {
                "entity": "[entityName=饱胀水蛭 id=128 zone=PLAY zonePos=3 cardId=EDR_810t player=2]",
                "card_id": "WW_423",
            }[k],
        })()
    )
    p._apply_tag(128, "NUM_TURNS_IN_PLAY", "0")
    p._apply_tag(128, "ATK", "2")
    p._apply_tag(128, "479", "2")
    p._apply_tag(128, "EXHAUSTED", "0")

    assert e.tags.get("NUM_TURNS_IN_PLAY") == 2
    assert not is_exhausted(e)
    active = board_active_turn_for_display(gs, 2)
    view = build_board_card(e, active, gs)
    assert view.can_attack_hero
    assert view.attack == 2


def test_bloated_leech_transform_overlay_from_log():
    log = Path(r"C:\Program Files (x86)\Hearthstone\Logs\Hearthstone_2026_06_20_19_38_35\Power.log")
    if not log.is_file():
        return
    with open(log, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    target = 56010
    start = max(s for s in starts if s < target)
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    for i in range(start, target):
        p.process_line(lines[i])
    gs.local_player_id = 2
    gs.opponent_player_id = 1

    leech = gs.entities.get(128)
    assert leech is not None
    assert leech.card_id == "WW_423"
    assert leech.tags.get("NUM_TURNS_IN_PLAY", 0) >= 1

    active = board_active_turn_for_display(gs, 2)
    view = build_board_card(leech, active, gs)
    assert view.attack >= 2, view.attack

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 2, face


if __name__ == "__main__":
    test_transform_preserves_turns_in_play_for_attack()
    test_bloated_leech_transform_overlay_from_log()
    print("ok")
