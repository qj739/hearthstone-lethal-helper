#!/usr/bin/env python3
"""紫罗兰惩戒者 JAIL_101：偷取敌方额外效果（嘲讽/突袭/复生等），每偷一个 +1/+1。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.battlecry_p0 import _apply_violet_spellsword


def _hero(gs, eid, pid, *, dmg=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags.update({
        "DAMAGE": dmg, "HEALTH": 30,
        "RESOURCES": mana, "RESOURCES_USED": 0,
    })
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m", **tags):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk, "HEALTH": hp,
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0, "NUM_TURNS_IN_PLAY": 1,
        **tags,
    })
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand_minion(gs, eid, pid, card_id, atk, hp, cost=3):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.cost = cost
    m.tags.update({
        "ZONE": "HAND", "CARDTYPE": "MINION",
        "ATK": atk, "HEALTH": hp, "COST": cost,
    })
    return m


def _deck(gs, eid, pid):
    c = gs.get_entity(eid)
    c.cardtype = "MINION"
    c.controller = pid
    c.zone = "DECK"
    c.tags["ZONE"] = "DECK"
    return c


def test_registered():
    assert get_battlecry_def("JAIL_101") is not None
    assert get_battlecry_def("JAIL_101").name == "紫罗兰惩戒者"


def test_steal_taunt_rush_reborn_face_lethal():
    """复盘：对面 10 血，10/6 嘲讽+突袭+复生挡脸；偷走后场面 16 打脸斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 10, 1, mana=10)
    _hero(gs, 20, 2, dmg=20)  # 10 血
    for eid, atk, hp in ((11, 3, 2), (12, 4, 9), (13, 4, 4), (14, 5, 3)):
        _minion(gs, eid, 1, atk, hp)
    taunt = _minion(
        gs, 30, 2, 10, 6, card_id="TIME_063",
        TAUNT=1, RUSH=1, REBORN=1, HAS_BEEN_REBORN=1,
    )
    _hand_minion(gs, 40, 1, "JAIL_101", 4, 3)
    for eid in (301, 302):
        _deck(gs, eid, 2)

    # 直接战吼：应偷 3 个效果 → 7/6 突袭，嘲讽消失
    enemy = [{
        "kind": "minion", "entity_id": 30, "card_id": "TIME_063",
        "atk": 10, "health": 6, "taunt": True, "rush": True, "reborn": True,
        "shield": False, "poisonous": False, "lifesteal": False,
    }]
    fighters = []
    card = gs.get_entity(40)
    _apply_violet_spellsword(enemy, fighters, mult=1, enemy_shield=False, card=card)
    assert enemy[0]["taunt"] is False
    assert enemy[0]["rush"] is False
    assert enemy[0]["reborn"] is False
    body = fighters[-1]
    assert body["atk"] == 7 and body["health"] == 6
    assert body["rush"] is True
    assert body["attacks_left"] == 1
    assert body["can_face"] is False

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    assert face >= 10, f"face={face} note={note}"
    assert "紫罗兰惩戒者" in note, note
    assert lc.overlay_red_prompt_ok()


if __name__ == "__main__":
    test_registered()
    test_steal_taunt_rush_reborn_face_lethal()
    print("ok")
