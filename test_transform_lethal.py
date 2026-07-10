#!/usr/bin/env python3
"""CHANGE_ENTITY 变形后立即重算场攻/斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker


def _setup_local_game(gs: GameState, local: int = 2, opp: int = 1):
    gs.local_player_id = local
    gs.opponent_player_id = opp
    gs.in_game = True
    gs.game_entity_id = 1
    ge = gs.get_entity(1)
    ge.cardtype = "GAME"
    ge.tags["TURN"] = 10
    ge.tags["CURRENT_PLAYER"] = local
    for pid, eid in ((local, 10), (opp, 20)):
        h = gs.get_entity(eid)
        h.cardtype = "HERO"
        h.controller = pid
        h.zone = "PLAY"
        h.health = 30
        h.tags["ZONE"] = "PLAY"
        h.tags["RESOURCES"] = 10
        gs.hero_entity_ids[pid] = eid


def _board_minion(gs, eid, pid, card_id, atk, hp, *, pos: int = 1):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags.update({
        "ZONE": "PLAY",
        "ATK": atk,
        "HEALTH": hp,
        "ZONE_POSITION": pos,
        "NUM_TURNS_IN_PLAY": 1,
    })
    gs.board_slots.setdefault(pid, {})[pos] = eid


def _feed_transform_lines(parser: PowerLogParser, card_id: str, *, dormant: bool = False):
    hp = "12" if dormant else "7"
    lines = [
        "D 00:00:00.000 GameState.DebugPrintPower() - "
        f"CHANGE_ENTITY - Updating Entity=[entityName=随从 id=234 zone=PLAY zonePos=2 cardId=ONY_004 player=2] CardID={card_id}",
        "D 00:00:00.001 GameState.DebugPrintPower() -         tag=ATK value=12 ",
        f"D 00:00:00.002 GameState.DebugPrintPower() -         tag=HEALTH value={hp} ",
    ]
    if dormant:
        lines.append("D 00:00:00.004 GameState.DebugPrintPower() -         tag=DORMANT value=1 ")
    lines.extend([
        "D 00:00:00.005 GameState.DebugPrintPower() -         tag=NUM_TURNS_IN_PLAY value=0 ",
        "D 00:00:00.006 GameState.DebugPrintPower() -         tag=EXHAUSTED value=1 ",
        "D 00:00:00.010 GameState.DebugPrintPower() - BLOCK_END",
    ])
    for line in lines:
        parser.process_line(line)


def test_change_entity_transform_ready_after_stats():
    """CHANGE_ENTITY 后属性 tag 就绪时触发 entity_transform_ready。"""
    gs = GameState()
    _setup_local_game(gs)
    _board_minion(gs, 234, 2, "ONY_004", 8, 8, pos=2)
    _board_minion(gs, 17, 1, "CATA_158", 5, 2, pos=1)

    parser = PowerLogParser("nul", gs)
    ready = []
    parser.on("entity_transform_ready", lambda e: ready.append(e))
    _feed_transform_lines(parser, "EDR_453")

    assert len(ready) == 1, ready
    assert ready[0].entity_id == 234
    assert ready[0].card_id == "EDR_453"
    assert ready[0].atk == 12
    assert ready[0].health == 7

    lc = LethalChecker(gs)
    pure = lc._compute_pure_board_face(
        gs.get_overlay_board(2), 2, [], False,
    )
    assert pure == 10, f"expected overflow 10 after transform, got {pure}"
    print("OK change_entity transform_ready", pure)


def test_magtheridon_transform_dormant_end_turn():
    """变形为休眠玛瑟里顿：pure 场攻立刻 +3。"""
    gs = GameState()
    _setup_local_game(gs)
    _board_minion(gs, 234, 2, "ONY_004", 8, 8, pos=2)

    parser = PowerLogParser("nul", gs)
    ready = []
    parser.on("entity_transform_ready", lambda e: ready.append(e))
    _feed_transform_lines(parser, "TOY_647", dormant=True)

    assert len(ready) == 1
    lc = LethalChecker(gs)
    pure = lc._compute_pure_board_face(
        gs.get_overlay_board(2), 2, [], False,
    )
    assert pure == 3, f"expected dormant magtheridon +3, got {pure}"
    print("OK magtheridon transform end turn", pure)


if __name__ == "__main__":
    test_change_entity_transform_ready_after_stats()
    test_magtheridon_transform_dormant_end_turn()
    print("all passed")
