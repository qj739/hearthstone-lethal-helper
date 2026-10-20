#!/usr/bin/env python3
"""命令之爪 + 食尸鬼冲锋：上界剪枝不得漏掉武器攻击后加攻线。"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def _hero(gs, eid, pid, *, hp=30, damage=0, mana=10, atk=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = damage
    h.atk = atk
    h.tags.update({
        "DAMAGE": damage,
        "HEALTH": hp,
        "ARMOR": 0,
        "RESOURCES": mana,
        "RESOURCES_USED": 0,
        "ATK": atk,
        "479": atk,
    })
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id=""):
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
        "479": atk,
        "HEALTH": hp,
        "NUM_ATTACKS_THIS_TURN": 0,
        "EXHAUSTED": 0,
        "NUM_TURNS_IN_PLAY": 1,
    })
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _weapon(gs, eid, pid, atk, dur, card_id):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "PLAY"
    w.card_id = card_id
    w.atk = atk
    w.health = dur
    w.damage = 0
    w.durability = dur
    w.tags.update({
        "ZONE": "PLAY",
        "ATK": atk,
        "HEALTH": dur,
        "DURABILITY": dur,
    })
    gs.weapon_entity_ids[pid] = eid
    return w


def _hero_power(gs, eid, pid, card_id="HERO_11bp", cost=2):
    hp = gs.get_entity(eid)
    hp.cardtype = "HERO_POWER"
    hp.controller = pid
    hp.zone = "PLAY"
    hp.card_id = card_id
    hp.cost = cost
    hp.tags.update({
        "ZONE": "PLAY",
        "COST": cost,
        "CARDTYPE": "HERO_POWER",
        "EXHAUSTED": 0,
    })
    return hp


def test_estimate_upper_includes_claw_buff():
    fighters = [
        {"kind": "minion", "card_id": "A", "atk": 7, "health": 4, "attacks_left": 1},
        {"kind": "minion", "card_id": "B", "atk": 3, "health": 6, "attacks_left": 1},
        {"kind": "minion", "card_id": "C", "atk": 2, "health": 4, "attacks_left": 1},
        {
            "kind": "weapon", "card_id": "CATA_467", "atk": 2, "health": 1,
            "attacks_left": 1, "durability": 1, "buff_friendly_atk_after": 2,
        },
    ]
    upper = LethalChecker._estimate_fighters_face_upper(fighters)
    # 7+3+2+2(weapon)+2(claw) = 16，不得只有 14
    assert upper >= 16, upper


def test_command_claw_plus_ghoul_lethal_17():
    """场面 12 + 武器 2 + 爪 +2 + 食尸鬼 1 = 17，对手 17 血应斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10, atk=2)
    _hero(gs, 20, 2, damage=13)
    _minion(gs, 30, 1, 7, 4, card_id="TIME_EVENT_300")
    _minion(gs, 31, 1, 3, 6, card_id="EDR_873")
    _minion(gs, 32, 1, 2, 4, card_id="EDR_571")
    _weapon(gs, 40, 1, 2, 1, "CATA_467")
    _hero_power(gs, 50, 1, "HERO_11bp", cost=2)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 17, (
        f"expected face>=17 got {face} "
        f"hp_face={getattr(lc, '_overlay_hero_power_face', None)} "
        f"best_hp={getattr(lc, '_overlay_best_hp_name', None)}"
    )
    total, _, has_lethal = lc.calculate_lethal_potential()
    assert has_lethal, f"should lethal total={total} face={face}"


if __name__ == "__main__":
    test_estimate_upper_includes_claw_buff()
    test_command_claw_plus_ghoul_lethal_17()
    print("ok")
