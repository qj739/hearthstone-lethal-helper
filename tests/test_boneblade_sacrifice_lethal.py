#!/usr/bin/env python3
"""骨刃乱舞：1 攻食尸鬼撞死亮边，再点杀清场，6 点打脸应在回合开始就算斩。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def _hero(gs, eid, pid, *, dmg=0, mana=10, atk=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.atk = atk
    h.tags.update({
        "DAMAGE": dmg, "ATK": atk, "HEALTH": 30,
        "RESOURCES": mana, "RESOURCES_USED": 0,
        "EXHAUSTED": 0, "NUM_ATTACKS_THIS_TURN": 0,
    })
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m", exhausted=False):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk, "HEALTH": hp,
        "NUM_ATTACKS_THIS_TURN": 1 if exhausted else 0,
        "EXHAUSTED": 1 if exhausted else 0,
        "NUM_TURNS_IN_PLAY": 1,
    })
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _weapon(gs, eid, pid):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "PLAY"
    w.card_id = "JAIL_450"
    w.atk = 1
    w.health = 3
    w.tags.update({
        "ZONE": "PLAY", "ATK": 1, "HEALTH": 3, "DURABILITY": 3, "DAMAGE": 0,
    })
    gs.weapon_entity_ids = getattr(gs, "weapon_entity_ids", {})
    gs.weapon_entity_ids[pid] = eid
    return w


def _spell(gs, eid, pid, card_id, cost, *, powered=False):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags.update({"ZONE": "HAND", "COST": cost, "CARDTYPE": "SPELL"})
    if powered:
        s.tags["POWERED_UP"] = 1
    return s


def _hero_power(gs, eid, pid):
    p = gs.get_entity(eid)
    p.cardtype = "HERO_POWER"
    p.controller = pid
    p.zone = "PLAY"
    p.card_id = "HERO_11bp"
    p.cost = 2
    p.tags.update({
        "ZONE": "PLAY", "COST": 2, "EXHAUSTED": 0,
        "HEROPOWER_ACTIVATIONS_THIS_TURN": 0,
    })
    gs.hero_power_entity_ids = getattr(gs, "hero_power_entity_ids", {})
    gs.hero_power_entity_ids[pid] = eid
    return p


def _deck(gs, eid, pid):
    c = gs.get_entity(eid)
    c.cardtype = "MINION"
    c.controller = pid
    c.zone = "DECK"
    c.tags["ZONE"] = "DECK"
    return c


def _gs():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    return gs


def test_turn_start_sacrifice_ghoul_powers_boneblade():
    """对手 23 血、有 3/5。食尸鬼撞死亮骨刃，新生闪电清掉，再打 6。"""
    gs = _gs()
    _hero(gs, 10, 1, mana=9, atk=1)
    _hero(gs, 20, 2, dmg=7)  # 23 血
    _weapon(gs, 31, 1)
    for eid, atk in ((24, 2), (184, 4), (125, 3), (178, 3), (128, 3)):
        _minion(gs, eid, 1, atk, 4)
    _minion(gs, 36, 2, 3, 5, card_id="CATA_786")
    _spell(gs, 40, 1, "JAIL_445", 2)
    _spell(gs, 84, 1, "TIME_216", 3)
    _hero_power(gs, 65, 1)
    for eid in (301, 302):
        _deck(gs, eid, 2)
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 23, f"face={face} note={lc.overlay_spell_note()}"
    assert lc.overlay_red_prompt_ok()


def test_powered_boneblade_plus_hero_power_is_sure_lethal():
    """场面已攻完、骨刃已亮、对面无随从：6+食尸鬼 1 对 7 血是确定斩。"""
    gs = _gs()
    _hero(gs, 10, 1, mana=5)
    _hero(gs, 20, 2, dmg=23)  # 7 血
    _minion(gs, 24, 1, 2, 4, exhausted=True)
    _spell(gs, 40, 1, "JAIL_445", 2, powered=True)
    _hero_power(gs, 65, 1)
    for eid in (301, 302):
        _deck(gs, eid, 2)
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 7, f"face={face} note={lc.overlay_spell_note()}"
    assert lc.overlay_red_prompt_ok()


if __name__ == "__main__":
    test_turn_start_sacrifice_ghoul_powers_boneblade()
    test_powered_boneblade_plus_hero_power_is_sure_lethal()
    print("ok")
