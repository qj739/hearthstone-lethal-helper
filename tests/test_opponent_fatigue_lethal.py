#!/usr/bin/env python3
"""对手牌库空时，下回合斩杀预览应计入即将承受的疲劳伤害。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState


def _hero(gs, eid, pid, *, dmg=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ARMOR"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _player(gs, eid, pid, *, fatigue=0):
    p = gs.get_entity(eid)
    p.cardtype = "PLAYER"
    p.controller = pid
    p.tags["FATIGUE"] = fatigue
    gs.player_ids[eid] = pid
    gs.player_names[pid] = f"Player{pid}"
    return p


def test_opponent_turn_fatigue_lowers_lethal_threshold():
    """对方回合：牌库空、疲劳3、英雄15血，场攻12应判下回合斩。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 1
    _hero(gs, 10, 2)
    _hero(gs, 20, 1, dmg=15)
    _player(gs, 5, 1, fatigue=3)

    lc = LethalChecker(gs)
    assert lc._opponent_deck_count() == 0
    assert lc._opponent_upcoming_fatigue_damage() == 3
    assert lc._lethal_threshold_hp() == 12

    lc._overlay_face_computed = True
    lc._overlay_incomplete = False
    lc._overlay_total_face = 12
    lc._overlay_mc_max = 12
    lc._overlay_uses_random = False
    assert lc.overlay_red_prompt_ok(opp_lethal_now=False) is True


def test_local_turn_fatigue_not_counted():
    """我方回合：疲劳发生在回合结束后，不应降低本回合斩杀血线。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 2
    _hero(gs, 10, 2)
    _hero(gs, 20, 1, dmg=15)
    _player(gs, 5, 1, fatigue=3)

    lc = LethalChecker(gs)
    assert lc._opponent_upcoming_fatigue_damage() == 0
    assert lc._lethal_threshold_hp() == 15

    lc._overlay_face_computed = True
    lc._overlay_incomplete = False
    lc._overlay_total_face = 12
    assert lc.overlay_red_prompt_ok(opp_lethal_now=False) is False


def test_opponent_turn_with_cards_in_deck_no_fatigue():
    """牌库未空时不计入疲劳。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 1
    _hero(gs, 10, 2)
    _hero(gs, 20, 1, dmg=15)
    _player(gs, 5, 1, fatigue=3)
    card = gs.get_entity(30)
    card.controller = 1
    card.zone = "DECK"
    card.tags["ZONE"] = "DECK"
    card.tags["CONTROLLER"] = 1

    lc = LethalChecker(gs)
    assert lc._opponent_deck_count() == 1
    assert lc._opponent_upcoming_fatigue_damage() == 0
    assert lc._lethal_threshold_hp() == 15


def test_opponent_deck_count_stable_while_entities_grow():
    """牌库计数遍历前快照实体列表，模拟期间新增实体不影响本次计数。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 1
    _hero(gs, 10, 2)
    _hero(gs, 20, 1, dmg=15)
    _player(gs, 5, 1, fatigue=3)
    card = gs.get_entity(30)
    card.controller = 1
    card.zone = "DECK"
    card.tags["ZONE"] = "DECK"
    card.tags["CONTROLLER"] = 1

    lc = LethalChecker(gs)
    assert lc._opponent_deck_count() == 1
    gs.get_entity(9000)
    gs.get_entity(9001)
    assert lc._opponent_deck_count() == 1


if __name__ == "__main__":
    test_opponent_turn_fatigue_lowers_lethal_threshold()
    test_local_turn_fatigue_not_counted()
    test_opponent_turn_with_cards_in_deck_no_fatigue()
    test_opponent_deck_count_stable_while_entities_grow()
    print("OK opponent fatigue lethal")
