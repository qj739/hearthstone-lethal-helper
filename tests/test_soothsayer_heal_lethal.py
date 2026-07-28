#!/usr/bin/env python3
"""回归：预言师 / 光沐元素亡语回血应抬高有效血，避免误报斩杀。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.deathrattle import on_minion_died, sim_hero_heal
from hdt_python.board_damage import living_taunt_minions


def _hero(gs, eid, pid, *, mana=10, used=0, health=30, armor=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = health
    h.damage = 0
    h.tags["ARMOR"] = armor
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="", taunt=False):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["TAUNT"] = 1 if taunt else 0
    m.tags["DEATHRATTLE"] = 1
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def test_soothsayer_deathrattle_heal_unit():
    dead = {
        "kind": "minion", "entity_id": 1, "atk": 6, "health": 0,
        "card_id": "JAIL_912", "taunt": True,
    }
    board = [dead]
    res = on_minion_died(dead, board, [])
    assert res.opponent_lifesteal_heal == 6, res.opponent_lifesteal_heal
    assert sim_hero_heal(board) == 6, sim_hero_heal(board)
    print("OK JAIL_912 unit heal", res.opponent_lifesteal_heal)


def test_lightshower_deathrattle_heal_unit():
    dead = {
        "kind": "minion", "entity_id": 1, "atk": 6, "health": 0,
        "card_id": "CORE_BAR_310", "taunt": True,
    }
    board = [dead]
    res = on_minion_died(dead, board, [])
    assert res.opponent_lifesteal_heal == 8, res.opponent_lifesteal_heal
    assert sim_hero_heal(board) == 8
    print("OK CORE_BAR_310 unit heal", res.opponent_lifesteal_heal)


def test_soothsayer_blocks_false_lethal():
    """7 攻解 6/6 预言师嘲讽后 5 打脸：对手 5 血 + 亡语回 6 = 11 有效，不够斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2, health=5, armor=0)
    _minion(gs, 10, 1, 7, 7, card_id="CS2_150")
    _minion(gs, 11, 1, 5, 1, card_id="CS2_121")
    _minion(gs, 20, 2, 6, 6, card_id="JAIL_912", taunt=True)

    assert len(living_taunt_minions(gs.get_board(2), gs)) == 1

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    eff = lc.get_opponent_effective_hp()
    assert eff == 11, eff
    assert face == 5, (face, lc.overlay_board_breakdown(), lc.overlay_spell_note())
    assert not has, (face, has, eff)
    print("OK JAIL_912 blocks false lethal", face, eff)


def test_soothsayer_still_lethal_when_enough_face():
    """清预言师后 12 打脸仍够 5 血 + 6 亡语回血。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2, health=5, armor=0)
    _minion(gs, 10, 1, 7, 7, card_id="CS2_150")
    _minion(gs, 11, 1, 12, 1, card_id="CS2_121")
    _minion(gs, 20, 2, 6, 6, card_id="JAIL_912", taunt=True)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, has = lc.calculate_lethal_potential()
    eff = lc.get_opponent_effective_hp()
    assert eff == 11, eff
    assert face >= 12, face
    assert has, (face, has, eff)
    print("OK JAIL_912 still lethal", face, eff)


def test_red_card_soothsayer_not_blocked_by_sticky_deathrattle():
    """
    复现末手漏斩：对手 7 血 + 嘲讽预言师，红牌休眠（不击杀）+ 团队之灵 + 技能 = 7。
    若上次清嘲 sticky 把预言师亡语 +6 叠进有效血，会假漏斩（场攻已显示 7）。
    """
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=6, used=0)
    _hero(gs, 2, 2, health=7, armor=0)

    hp = gs.get_entity(65)
    hp.cardtype = "HERO_POWER"
    hp.controller = 1
    hp.zone = "PLAY"
    hp.card_id = "HERO_10bp"
    hp.cost = 1
    hp.tags["ZONE"] = "PLAY"
    hp.tags["COST"] = 1
    hp.tags["EXHAUSTED"] = 0

    _minion(gs, 78, 1, 3, 2, card_id="CORE_EX1_319")
    _minion(gs, 20, 1, 1, 2, card_id="JAIL_460")
    _minion(gs, 60, 2, 6, 6, card_id="JAIL_912", taunt=True)

    for eid, cid, cost, ctype in (
        (25, "TOY_644", 1, "SPELL"),
        (16, "TOY_028", 2, "MINION"),
    ):
        c = gs.get_entity(eid)
        c.cardtype = ctype
        c.controller = 1
        c.zone = "HAND"
        c.card_id = cid
        c.cost = cost
        c.tags["ZONE"] = "HAND"
        c.tags["COST"] = cost

    lc = LethalChecker(gs)
    lc._last_deathrattle_armor = 6  # sticky：假想上次击杀过预言师
    face = lc.overlay_board_face_damage()
    total, _, has = lc.calculate_lethal_potential()
    line_hp = lc._overlay_line_threshold_hp()
    assert face >= 7, (face, lc.overlay_spell_note())
    assert line_hp == 7, line_hp  # 休眠线不应叠亡语 +6
    assert has, (face, total, has, line_hp, lc.overlay_spell_note())
    assert lc.overlay_red_prompt_ok(), (face, line_hp)
    print("OK red card vs soothsayer ignores sticky DR", face, line_hp)


if __name__ == "__main__":
    test_soothsayer_deathrattle_heal_unit()
    test_lightshower_deathrattle_heal_unit()
    test_soothsayer_blocks_false_lethal()
    test_soothsayer_still_lethal_when_enough_face()
    test_red_card_soothsayer_not_blocked_by_sticky_deathrattle()
    print("all ok")
