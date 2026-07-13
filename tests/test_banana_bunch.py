#!/usr/bin/env python3
"""一串香蕉 ETC_201：友方 +1/+1，同回合可连打 3 次。"""

import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import (
    apply_spell_sequence,
    get_board_spell_def,
    spell_sequence_mana_left,
    _pick_best_spell_target_fighter,
)
from hdt_python.combat_sim import project_board_face_after_spell


def _hero(gs, eid, pid, *, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="", spell_immune=False, exhausted=True):
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
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    if spell_immune:
        m.tags["ELUSIVE"] = 1
    if exhausted:
        m.tags["EXHAUSTED"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _fighter(fighters, eid, atk, hp, *, attacks_left=1, spell_immune=False):
    fighters.append({
        "kind": "minion", "entity_id": eid, "atk": atk, "health": hp,
        "attacks_left": attacks_left, "can_face": True, "rush": False,
        "spell_immune": spell_immune,
    })


def _hand_spell(gs, eid, pid, card_id):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = 1
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = 1
    return s


def test_registered():
    defn = get_board_spell_def("ETC_201")
    assert defn is not None
    assert defn.name == "一串香蕉"
    assert get_board_spell_def("ETC_201t") is defn


def test_triple_banana_buff_same_turn():
    gs = GameState()
    card = _hand_spell(gs, 40, 1, "ETC_201")
    defn = get_board_spell_def("ETC_201")
    fighters = []
    _fighter(fighters, 20, 3, 5, attacks_left=1)
    seq = [(defn, 1, card)]
    apply_spell_sequence([], fighters, seq, gs=gs, player_id=1, mana_budget=3)
    assert fighters[0]["atk"] == 6
    assert fighters[0]["health"] == 8
    assert project_board_face_after_spell([], fighters, False) == 6


def test_mana_budget_counts_three_bananas():
    gs = GameState()
    card = _hand_spell(gs, 40, 1, "ETC_201")
    defn = get_board_spell_def("ETC_201")
    seq = [(defn, 1, card)]
    left = spell_sequence_mana_left(seq, 3)
    assert left == 0


def test_single_banana_with_1_mana():
    gs = GameState()
    card = _hand_spell(gs, 40, 1, "ETC_201")
    defn = get_board_spell_def("ETC_201")
    fighters = []
    _fighter(fighters, 20, 2, 4, attacks_left=1)
    apply_spell_sequence([], fighters, seq := [(defn, 1, card)], gs=gs, player_id=1, mana_budget=1)
    assert fighters[0]["atk"] == 3


def test_banana_skips_spell_immune_board_minion():
    """扰魔友方不可被香蕉指定，应改 buff 其他可指定随从。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=7)
    _hero(gs, 2, 2)
    _minion(gs, 195, 1, 4, 3, card_id="TIME_058", spell_immune=True)
    _minion(gs, 221, 1, 9, 7, card_id="EDR_259")
    card = _hand_spell(gs, 40, 1, "ETC_201")
    defn = get_board_spell_def("ETC_201")
    fighters = []
    picked = _pick_best_spell_target_fighter(fighters, gs=gs, player_id=1)
    assert picked is not None and picked[2].get("card_id") == "EDR_259"
    apply_spell_sequence([], fighters, [(defn, 1, card)], gs=gs, player_id=1, mana_budget=3)
    ursol = next(f for f in fighters if f.get("card_id") == "EDR_259")
    assert ursol["atk"] == 12 and ursol["health"] == 10
    assert not any(f.get("card_id") == "TIME_058" and f.get("atk", 0) > 4 for f in fighters)


def test_banana_skips_elusive_enchantment_only():
    """黑暗之赐扰魔附魔在随从实体上无 ELUSIVE 标签时仍须跳过。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    butterfly = _minion(gs, 195, 1, 4, 3, card_id="TIME_058", spell_immune=False)
    butterfly.tags.pop("ELUSIVE", None)
    _minion(gs, 221, 1, 9, 7, card_id="EDR_259")
    enc = gs.get_entity(200)
    enc.cardtype = "ENCHANTMENT"
    enc.card_id = "EDR_100t1e"
    enc.controller = 1
    enc.tags["ATTACHED"] = 195
    card = _hand_spell(gs, 40, 1, "ETC_201")
    defn = get_board_spell_def("ETC_201")
    fighters = []
    picked = _pick_best_spell_target_fighter(fighters, gs=gs, player_id=1)
    assert picked is not None and picked[2].get("card_id") == "EDR_259"
    apply_spell_sequence([], fighters, [(defn, 1, card)], gs=gs, player_id=1, mana_budget=3)
    ursol = next(f for f in fighters if f.get("card_id") == "EDR_259")
    assert ursol["atk"] == 12


def test_from_power_log_elusive_butterfly():
    """Power.log：渺小的振翅蝶扰魔，香蕉只能 buff 乌索尔。"""
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_07_13_11_22_29\Power.log"
    )
    if not log.is_file():
        print("SKIP (log missing)")
        return
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    target = 303913
    starts = [
        i for i, l in enumerate(lines[:target])
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = starts[-1]
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            p.process_line(lines[i].rstrip())
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    pure, board, weapon, spell, hp = lc.overlay_board_breakdown()
    assert board == 12, (board, pure, weapon, spell, hp, lc.overlay_spell_note())
    assert weapon == 1


def test_from_power_log():
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_07_10_10_22_36\Power.log"
    )
    if not log.is_file():
        print("SKIP (log missing)")
        return
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    target = 335358
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
    touch = next(c for c in gs.get_hand(1) if c.card_id == "ETC_201")
    assert get_board_spell_def(touch.card_id) is not None


if __name__ == "__main__":
    test_registered()
    test_triple_banana_buff_same_turn()
    test_mana_budget_counts_three_bananas()
    test_single_banana_with_1_mana()
    test_banana_skips_spell_immune_board_minion()
    test_banana_skips_elusive_enchantment_only()
    test_from_power_log_elusive_butterfly()
    test_from_power_log()
    print("OK banana bunch")
