# -*- coding: utf-8 -*-
"""硬核信徒 + 饮血术解嘲：复现末局漏斩杀。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import get_board_spell_def


def _hero(gs, eid, pid, *, mana=10, used=0, health=30, damage=0, atk=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = health
    h.damage = damage
    h.tags.update({
        "HEALTH": health, "DAMAGE": damage, "ARMOR": 0,
        "RESOURCES": mana, "RESOURCES_USED": used, "MAXRESOURCES": mana,
    })
    if atk:
        h.tags["ATK"] = atk
        h.atk = atk
    gs.hero_entity_ids[pid] = eid
    return h


def _weapon(gs, eid, pid, card_id, atk, dur):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "PLAY"
    w.card_id = card_id
    w.atk = atk
    w.health = dur
    w.tags.update({
        "ZONE": "PLAY", "ATK": atk, "HEALTH": dur, "DURABILITY": dur,
        "CARDTYPE": "WEAPON",
    })
    return w


def _hero_power(gs, eid, pid, card_id, cost=2):
    hp = gs.get_entity(eid)
    hp.cardtype = "HERO_POWER"
    hp.controller = pid
    hp.zone = "PLAY"
    hp.card_id = card_id
    hp.cost = cost
    hp.tags.update({"ZONE": "PLAY", "CARDTYPE": "HERO_POWER", "COST": cost, "EXHAUSTED": 0})
    return hp


def _hand_minion(gs, eid, pid, card_id, cost, atk, hp):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.cost = cost
    m.atk = atk
    m.health = hp
    m.tags.update({"ZONE": "HAND", "ATK": atk, "HEALTH": hp, "COST": cost, "CARDTYPE": "MINION"})
    return m


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags.update({"ZONE": "HAND", "COST": cost, "CARDTYPE": "SPELL"})
    return s


def _taunt(gs, eid, pid, atk, hp, *, card_id="JAIL_453", damage=0):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = damage
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "HEALTH": hp, "DAMAGE": damage,
        "TAUNT": 1, "CARDTYPE": "MINION",
    })
    return m


def test_drink_blood_and_death_strike_registered():
    assert get_board_spell_def("JAIL_441") is not None
    assert get_board_spell_def("RLK_024") is not None
    assert get_battlecry_def("ETC_209") is not None


def test_hardcore_cultist_lethal_after_drink_blood_clears_taunt():
    """
    复现：对面 2 血嘲讽 + 英雄 8 血；泡沫刃5 + 食尸鬼1 + 信徒战吼2。
    未接入饮血术时信徒会去解嘲 → 场攻6 漏斩；接入后应 ≥8。
    """
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    gs.in_game = True
    gs.active_player_id = 1
    gs.get_entity(100).tags["TURN"] = 16
    _hero(gs, 1, 1, mana=10, used=1, atk=5)
    _hero(gs, 2, 2, health=30, damage=22)  # 8 hp
    _weapon(gs, 14, 1, "MIS_101", 5, 1)
    _hero_power(gs, 15, 1, "HERO_11bp", cost=2)
    _hand_minion(gs, 11, 1, "ETC_209", 3, 2, 1)
    _hand_spell(gs, 12, 1, "JAIL_441", 2)
    _taunt(gs, 26, 2, 3, 4, card_id="JAIL_453", damage=2)  # 2 hp taunt

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    seq = [(d.name, getattr(c, "card_id", None)) for d, _, c in lc._overlay_best_seq]
    assert face >= 8, (face, lc.overlay_battlecry_face(), note, seq, lc.overlay_board_breakdown())
    _, _, has = lc.calculate_lethal_potential()
    assert has, (face, has, note, seq)


def test_hardcore_cultist_battlecry_face_when_no_taunt():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    gs.in_game = True
    gs.active_player_id = 1
    gs.get_entity(100).tags["TURN"] = 10
    _hero(gs, 1, 1, mana=3, used=0)
    _hero(gs, 2, 2, health=30, damage=28)
    _hand_minion(gs, 11, 1, "ETC_209", 3, 2, 1)
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert lc.overlay_battlecry_face() >= 2
    assert face >= 2


if __name__ == "__main__":
    test_drink_blood_and_death_strike_registered()
    test_hardcore_cultist_battlecry_face_when_no_taunt()
    test_hardcore_cultist_lethal_after_drink_blood_clears_taunt()
    print("OK")
