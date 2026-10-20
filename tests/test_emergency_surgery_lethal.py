#!/usr/bin/env python3
"""紧急手术 JAIL_454：四只 3/1 吸血亡灵攻击所选敌方随从，用于解嘲后打脸。"""

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, SpellSimTier, spell_sim_tier_for_card
from hdt_python.spell_p0_other import _apply_emergency_surgery


def test_emergency_surgery_registered():
    assert get_board_spell_def("JAIL_454") is not None
    assert get_board_spell_def("JAIL_454").name == "紧急手术"
    spell_sim_tier_for_card.cache_clear()
    assert spell_sim_tier_for_card("JAIL_454") == SpellSimTier.CLEAR_BOARD


def test_emergency_surgery_kills_taunt_tokens_dont_face():
    taunts = [{
        "entity_id": 18, "health": 2, "atk": 6, "taunt": True, "shield": False,
        "kind": "minion",
    }]
    fighters = [
        {"kind": "minion", "atk": 6, "health": 1, "attacks_left": 1, "can_face": True, "card_id": "END_004"},
        {"kind": "minion", "atk": 5, "health": 1, "attacks_left": 1, "can_face": True, "card_id": "END_002"},
        {"kind": "minion", "atk": 2, "health": 1, "attacks_left": 1, "can_face": True, "card_id": "EDR_813at"},
        {"kind": "minion", "atk": 1, "health": 2, "attacks_left": 1, "can_face": True, "card_id": "EDR_816"},
    ]
    _apply_emergency_surgery(taunts, fighters, mult=1, enemy_shield=False)
    assert all(t.get("health", 0) <= 0 or not t.get("taunt") for t in taunts) or not taunts
    tokens = [f for f in fighters if f.get("card_id") == "JAIL_454t" and f.get("health", 0) > 0]
    assert tokens, "should leave leftover nurses after 2-hp taunt dies"
    assert all(f.get("attacks_left", 0) == 0 and not f.get("can_face") for f in tokens)
    # 原场面随从仍可打脸 6+5+2+1=14
    ready = sum(
        f["atk"] for f in fighters
        if f.get("kind") == "minion" and f.get("health", 0) > 0 and f.get("can_face") and f.get("attacks_left", 0) > 0
    )
    assert ready == 14, ready


def _hero(gs, eid, pid, *, dmg=0, mana=10, health=30):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = health
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["HEALTH"] = health
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m", taunt=False):
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
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0, "NUM_TURNS_IN_PLAY": 1,
    })
    if taunt:
        m.tags["TAUNT"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags.update({"ZONE": "HAND", "COST": cost})
    return s


def _hero_power(gs, eid, pid, card_id="HERO_11bp", cost=2):
    p = gs.get_entity(eid)
    p.cardtype = "HERO_POWER"
    p.controller = pid
    p.zone = "PLAY"
    p.card_id = card_id
    p.cost = cost
    p.tags.update({"ZONE": "PLAY", "COST": cost, "EXHAUSTED": 0})
    return p


def test_emergency_surgery_clears_taunt_then_lethal():
    """对手 14 血、2 血嘲讽；场面 14 攻被挡。手术解嘲后应斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=16, health=30)  # 14 血
    _minion(gs, 30, 1, 6, 1, card_id="END_004")
    _minion(gs, 31, 1, 5, 1, card_id="END_002")
    _minion(gs, 32, 1, 2, 1, card_id="EDR_813at")
    _minion(gs, 33, 1, 1, 2, card_id="EDR_816")
    _minion(gs, 40, 2, 6, 2, card_id="CATA_551t", taunt=True)
    _minion(gs, 41, 2, 12, 6, card_id="CATA_553t")
    _hand_spell(gs, 50, 1, "JAIL_454", 5)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    total, _, lethal = lc.calculate_lethal_potential()
    note = lc.overlay_spell_note()
    assert lethal or face >= 14, f"face={face} total={total} note={note!r}"
    assert "紧急手术" in (note or ""), note


def test_last_game_surgery_lethal_from_log():
    log = Path(r"C:\Program Files (x86)\Hearthstone\Logs\Hearthstone_2026_10_06_15_15_29\Power.log")
    if not log.is_file():
        print("SKIP log missing")
        return
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[364388:390881]:
            if line:
                parser.process_line(line)
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    total, _, lethal = lc.calculate_lethal_potential()
    note = lc.overlay_spell_note()
    assert lethal, f"expected lethal face={face} total={total} note={note!r}"
    assert "紧急手术" in (note or ""), note
    print("OK log surgery lethal", face, total, note)


if __name__ == "__main__":
    test_emergency_surgery_registered()
    test_emergency_surgery_kills_taunt_tokens_dont_face()
    test_emergency_surgery_clears_taunt_then_lethal()
    test_last_game_surgery_lethal_from_log()
    print("all ok")
