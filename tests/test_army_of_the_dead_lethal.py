#!/usr/bin/env python3
"""亡者大军 RLK_060：残骸复活 2/2 突袭食尸鬼应参与斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState
from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def


def _hero(gs, eid, pid, *, mana=10, used=0, corpses=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    if corpses:
        h.tags["CORPSES"] = corpses
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    return s


def test_army_of_the_dead_registered():
    assert get_board_spell_def("RLK_060") is not None
    assert get_board_spell_def("CORE_RLK_060") is not None


def test_army_of_the_dead_summons_rush_ghouls():
    defn = get_board_spell_def("RLK_060")
    spell = type("C", (), {"card_id": "RLK_060", "entity_id": 11, "tags": {}})()
    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 1, 1, corpses=3)
    fighters = []
    apply_spell_sequence(
        [], fighters, [(defn, 5, spell)],
        gs=gs, player_id=1,
    )
    assert len(fighters) == 3
    assert all(f.get("rush") and f.get("atk") == 2 for f in fighters)


def test_army_of_the_dead_lethal_empty_board():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.first_player_id = 1
    gs.game_entity_id = 100
    game = gs.get_entity(100)
    game.tags["TURN"] = 10
    _hero(gs, 1, 1, mana=10, used=0, corpses=5)
    opp = _hero(gs, 2, 2)
    opp.health = 10
    _hand_spell(gs, 11, 1, "RLK_060", 5)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    assert face >= 10, (face, lc.overlay_spell_note(), lc.overlay_board_breakdown())
    assert has, (face, has, lc.overlay_spell_note())


def test_army_of_the_dead_clears_taunt_then_face():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0, corpses=3)
    _hero(gs, 2, 2)
    taunt = gs.get_entity(20)
    taunt.cardtype = "MINION"
    taunt.controller = 2
    taunt.zone = "PLAY"
    taunt.card_id = "T1"
    taunt.atk = 1
    taunt.health = 1
    taunt.tags.update({"ZONE": "PLAY", "ATK": 1, "HEALTH": 1, "TAUNT": 1})
    _hand_spell(gs, 11, 1, "CORE_RLK_060", 5)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 4, (face, lc.overlay_spell_note(), lc.overlay_board_breakdown())


if __name__ == "__main__":
    test_army_of_the_dead_registered()
    test_army_of_the_dead_summons_rush_ghouls()
    test_army_of_the_dead_lethal_empty_board()
    test_army_of_the_dead_clears_taunt_then_face()
    print("OK army of the dead")
