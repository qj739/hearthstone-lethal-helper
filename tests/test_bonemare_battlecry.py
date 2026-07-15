#!/usr/bin/env python3
"""骨魇 ICC_705 / CORE_ICC_705：战吼 +4/+4，CORE 变体须进入斩杀搜索。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.spell_board import _is_battlecry_step, spell_sim_tier, SpellSimTier


def _hero(gs, eid, pid, *, dmg=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m", turns=1):
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
    m.tags["NUM_TURNS_IN_PLAY"] = turns
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_minion(gs, eid, pid, card_id, *, cost=7, atk=5, hp=5):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.cost = cost
    m.atk = atk
    m.health = hp
    m.tags["ZONE"] = "HAND"
    m.tags["COST"] = cost
    m.tags["ATK"] = atk
    m.tags["HEALTH"] = hp
    m.tags["479"] = atk
    return m


def test_core_bonemare_recognized_as_battlecry():
    for cid in ("ICC_705", "CORE_ICC_705"):
        defn = get_battlecry_def(cid)
        assert defn is not None, cid
        assert defn.name == "骨魇"
        card = type("C", (), {"card_id": cid})()
        assert _is_battlecry_step(defn, card), cid
        assert spell_sim_tier(defn) == SpellSimTier.UTILITY, cid


def test_core_bonemare_enables_lethal():
    """2 攻场面 + 骨魇 +4 → 6，敌 5 血应斩杀；CORE_ 变体不得被直伤前缀丢掉。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=25)
    _minion(gs, 30, 1, 2, 2, turns=2)
    _hand_minion(gs, 40, 1, "CORE_ICC_705")

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 6, f"expected buffed face>=6, got {face}; combo={lc.overlay_combo_display_lines()}"
    _, _, lethal = lc.calculate_lethal_potential()
    assert lethal, f"should lethal; face={face} combo={lc.overlay_combo_display_lines()}"


if __name__ == "__main__":
    test_core_bonemare_recognized_as_battlecry()
    test_core_bonemare_enables_lethal()
    print("ok")
