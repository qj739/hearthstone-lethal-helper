#!/usr/bin/env python3
"""拦住他们！预备（Prepare）减费：COST/PREPARED 标签应正确参与斩杀法力计算。"""

import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import spell_effective_cost, hand_board_spells


def _hero(gs, eid, pid, *, dmg=0, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
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


def _hand_spell(gs, eid, pid, card_id, *, cost=None, prepared=None):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost if cost is not None else 5
    s.tags["ZONE"] = "HAND"
    if cost is not None:
        s.tags["COST"] = cost
    if prepared is not None:
        s.tags["PREPARED"] = prepared
    return s


def test_spell_effective_cost_prepared_states():
    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 10, 1)

    full = _hand_spell(gs, 40, 1, "JAIL_913", cost=0, prepared=5)
    assert spell_effective_cost(full, gs, 1) == 0

    partial = _hand_spell(gs, 41, 1, "JAIL_913", cost=1, prepared=4)
    assert spell_effective_cost(partial, gs, 1) == 1

    stale = _hand_spell(gs, 42, 1, "JAIL_913", cost=5, prepared=4)
    assert spell_effective_cost(stale, gs, 1) == 1


def test_prepared_hold_playable_with_limited_mana():
    """预备至 0 费后，1 法力即可打出拦住他们！。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 10, 1, mana=1)
    _hero(gs, 20, 2, dmg=24)
    _minion(gs, 30, 1, 2, 3)
    _hand_spell(gs, 40, 1, "JAIL_913", cost=0, prepared=5)

    plays = hand_board_spells(gs, 1, 1)
    assert any(c.card_id == "JAIL_913" and cost == 0 for c, _, cost in plays)

    lc = LethalChecker(gs)
    _, _, lethal = lc.calculate_lethal_potential()
    assert lc.overlay_board_face_damage() >= 7
    assert lethal


def test_prepared_hold_from_power_log():
    """回放 log：PREPARED=4 COST=1 时 effective cost=1。"""
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_07_09_16_03_26\Power.log"
    )
    if not log.is_file():
        print("SKIP (log missing)")
        return
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    target = 258130
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = max((s for s in starts if s < target), default=starts[-1])
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            p.process_line(lines[i].rstrip())
    hold = next(c for c in gs.get_hand(1) if c.card_id == "JAIL_913")
    assert hold.tags.get("COST") == 1
    assert hold.tags.get("PREPARED") == 4
    assert spell_effective_cost(hold, gs, 1) == 1


if __name__ == "__main__":
    test_spell_effective_cost_prepared_states()
    test_prepared_hold_playable_with_limited_mana()
    test_prepared_hold_from_power_log()
    print("OK hold them off prepare cost")
