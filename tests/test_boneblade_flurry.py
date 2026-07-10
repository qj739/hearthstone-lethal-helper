#!/usr/bin/env python3
"""骨刃乱舞 JAIL_445：3 随机敌人；亮边（友方随从本回合死亡）再 +3。"""

import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.spell_board import (
    get_board_spell_def,
    hand_board_spells,
    hand_effect_active,
    spell_effective_cost,
)
from hdt_python.spell_p0_aoe import _apply_boneblade_flurry as apply_from_aoe


def _hero(gs, eid, pid, *, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _player(gs, eid, pid):
    p = gs.get_entity(eid)
    p.controller = pid
    gs.player_ids[eid] = pid
    return p


def _hand_spell(gs, eid, pid, card_id, *, cost=2, powered=False):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    if powered:
        s.tags["POWERED_UP"] = 1
    return s


def test_registered():
    defn = get_board_spell_def("JAIL_445")
    assert defn is not None
    assert defn.name == "骨刃乱舞"
    assert defn.base_cost == 2
    assert defn.uses_random is True


def test_powered_deals_six_face_empty_board():
    taunts, fighters = [], []
    card = type("C", (), {"card_id": "JAIL_445", "tags": {"POWERED_UP": 1}})()
    res = apply_from_aoe(
        taunts, fighters, mult=1, enemy_shield=False, card=card,
        rng=__import__("random").Random(0),
    )
    assert res.direct_face_damage == 6


def test_unpowered_deals_three_face_empty_board():
    taunts, fighters = [], []
    card = type("C", (), {"card_id": "JAIL_445", "tags": {}})()
    res = apply_from_aoe(
        taunts, fighters, mult=1, enemy_shield=False, card=card,
        rng=__import__("random").Random(0),
    )
    assert res.direct_face_damage == 3


def test_hand_effect_from_friendly_death_flag():
    gs = GameState()
    card = _hand_spell(gs, 40, 1, "JAIL_913", cost=5)
    card.card_id = "JAIL_445"
    assert hand_effect_active(card, friendly_minion_died_this_turn=True)


def test_powered_in_hand_playable():
    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 10, 1, mana=2)
    _hand_spell(gs, 40, 1, "JAIL_445", powered=True)
    plays = hand_board_spells(gs, 1, 2)
    assert any(c.card_id == "JAIL_445" for c, _, _ in plays)


def test_powered_from_power_log():
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_07_08_10_53_05\Power.log"
    )
    if not log.is_file():
        print("SKIP (log missing)")
        return
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    target = 653979
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
    hold = next(c for c in gs.get_hand(2) if c.card_id == "JAIL_445")
    assert hold.tags.get("POWERED_UP") == 1
    assert spell_effective_cost(hold, gs, 2) == 2
    assert hand_effect_active(hold)


if __name__ == "__main__":
    test_registered()
    test_powered_deals_six_face_empty_board()
    test_unpowered_deals_three_face_empty_board()
    test_hand_effect_from_friendly_death_flag()
    test_powered_in_hand_playable()
    test_powered_from_power_log()
    print("OK boneblade flurry")
