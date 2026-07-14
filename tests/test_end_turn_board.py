#!/usr/bin/env python3
"""回合结束随从场攻：P0 + P1 共 9 张。"""

import json
import os
import sys
from functools import lru_cache
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker
from hdt_python.end_turn_board import END_TURN_BY_CARD, end_turn_face_damage

_CARD_DB = Path(__file__).resolve().parent.parent / "json" / "cards.json"


@lru_cache(maxsize=1)
def _load_card_db() -> dict:
    return {c["id"]: c for c in json.loads(_CARD_DB.read_text(encoding="utf-8"))}


def _db_minion_stats(card_id: str) -> tuple[int, int]:
    """从 cards.json 读取随从 atk/hp。"""
    card = _load_card_db()[card_id]
    return int(card["attack"]), int(card["health"])


def _hero(gs, eid, pid, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid


def test_current_player_handoff_at_turn_start():
    """回合开始：对手 CURRENT_PLAYER=0 后应立刻切到我方，不能仍判为对方回合。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.player_names[1] = "Me#1111"
    gs.player_names[2] = "Opp#2222"
    gs.active_player_id = 2

    parser = PowerLogParser(os.devnull, gs)
    parser._handle_player_current_player("Opp#2222", "0")
    assert gs.active_player_id == 1, f"expected local turn after opp CP=0, got {gs.active_player_id}"

    checker = LethalChecker(gs)
    assert checker.is_local_turn()
    assert not checker.is_opponent_turn()
    print("OK current player handoff")


def _set_local_turn(gs, local_pid: int = 1):
    """标记当前为本地玩家回合，避免 overlay 误用下回合场攻。"""
    if gs.game_entity_id is None:
        gs.game_entity_id = 100
        ge = gs.get_entity(100)
        ge.cardtype = "GAME"
    gs.first_player_id = local_pid
    game = gs.entities[gs.game_entity_id]
    game.tags["TURN"] = 1
    game.tags["CURRENT_PLAYER"] = local_pid


def _minion(gs, eid, pid, atk, hp, *, card_id="", dormant=False, taunt=False, can_attack=True):
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
    if can_attack:
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    else:
        m.tags["NUM_TURNS_IN_PLAY"] = 0
        m.tags["EXHAUSTED"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if dormant:
        m.tags["DORMANT"] = 1
    if taunt:
        m.tags["TAUNT"] = 1


def _minion_db(gs, eid, pid, card_id: str, **kwargs):
    """按 cards.json 身材创建场上随从。"""
    atk, hp = _db_minion_stats(card_id)
    return _minion(gs, eid, pid, atk, hp, card_id=card_id, **kwargs)


def test_magtheridon_dormant_end_turn():
    """休眠玛瑟里顿：回合结束 +3 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "TOY_647", dormant=True)

    total = LethalChecker(gs).overlay_board_face_damage()
    assert total == 3, f"expected 3 from Magtheridon, got {total}"
    print("OK magtheridon dormant +3", total)


def test_magtheridon_awake_no_end_turn():
    """已唤醒玛瑟里顿不再触发休眠回合结束伤害。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "TOY_647", dormant=False)

    face, _ = end_turn_face_damage(gs.get_board(1), [], False)
    assert face == 0, f"awake Magtheridon end-turn API should be 0, got {face}"
    print("OK magtheridon awake no end-turn", face)


def test_factory_bot_mini_no_taunt():
    """微缩工厂装配机 TOY_601t（1/1）：空场时回合结束同样 +6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs, 1)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "TOY_601t", can_attack=False)

    face, _ = end_turn_face_damage(gs.get_board(1), [], False)
    assert face == 6, f"expected 6 from mini factory bot, got {face}"

    lc = LethalChecker(gs)
    total, _, has_lethal = lc.calculate_lethal_potential()
    mc_max, prob, uses_random, top = lc.overlay_face_stats()
    assert total == 6
    assert mc_max == 6
    assert uses_random
    assert top == [(6, 1.0)]
    print("OK factory mini +6", total, prob, top)


def test_factory_bot_mini_can_attack_one_plus_et():
    """微缩 1/1 当回合可攻只计 1 点；回合结束 token 仍随机 +6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs, 1)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "TOY_601t", can_attack=True)

    lc = LethalChecker(gs)
    board_view = gs.get_overlay_board(1)
    immediate = lc._compute_immediate_board_face(board_view, 1, [], False)
    assert immediate == 1, f"mini body should be 1 atk, got {immediate}"

    face = lc.overlay_board_face_damage()
    pure, minion_bd, _, _, _ = lc.overlay_board_breakdown()
    mc_max, _, uses_random, top = lc.overlay_face_stats()
    assert uses_random
    assert pure == 1, pure
    assert face == 7, (face, pure, minion_bd, mc_max, top)
    assert mc_max == 7, mc_max
    print("OK factory mini 1/1 + ET", face, pure, top)


def test_factory_bot_no_taunt():
    """工厂装配机：空场时回合结束机器人 +6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "TOY_601", can_attack=False)

    face, _ = end_turn_face_damage(gs.get_board(1), [], False)
    assert face == 6, f"expected 6 from factory bot, got {face}"
    print("OK factory bot +6", face)


def test_factory_bot_with_taunt_random_upper_bound():
    """有嘲讽时随机攻击仍可能打脸；无 rng 取乐观上界 +6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "TOY_601", can_attack=False)
    enemy = [{"entity_id": 20, "atk": 3, "health": 5, "taunt": True}]

    face, _ = end_turn_face_damage(_board_entities(gs, 1), enemy, False)
    assert face == 6, f"factory random attack upper bound should be 6, got {face}"
    print("OK factory bot vs taunt upper 6", face)


def test_factory_bot_with_taunt_random_mc():
    """有 rng 时随机攻击可能打随从或打脸。"""
    import random

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "TOY_601", can_attack=False)
    enemy = [{"entity_id": 20, "atk": 3, "health": 5, "taunt": True}]

    faces = set()
    for i in range(50):
        eb = [{"entity_id": 20, "atk": 3, "health": 5, "taunt": True}]
        face, _ = end_turn_face_damage(
            _board_entities(gs, 1), eb, False, rng=random.Random(i),
        )
        faces.add(face)
    assert 0 in faces and 6 in faces, f"expected both 0 and 6 in samples, got {faces}"
    print("OK factory bot random mc", faces)


def test_factory_bot_prob_lethal_at_six_hp():
    """对手 6 血 + 场上随从：回合结束随机 6 攻应识别为概率斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs, 1)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    gs.get_entity(2).health = 6
    _minion_db(gs, 10, 1, "TOY_601", can_attack=False)
    for i, (atk, hp) in enumerate([(2, 1), (2, 2), (2, 2)], start=20):
        _minion(gs, i, 2, atk, hp, card_id=f"E{i}")

    lc = LethalChecker(gs)
    total, _, has_lethal = lc.calculate_lethal_potential()
    mc_max, prob, uses_random, top = lc.overlay_face_stats()
    assert uses_random, "factory end-turn should be random with enemy minions"
    assert mc_max == 6, f"peak face should be 6 end-turn random, got {mc_max}"
    assert prob > 0, f"should have non-zero lethal prob, got {prob}"
    assert has_lethal, "probabilistic lethal should trigger when peak >= eff hp"
    assert total == 6, f"lethal total should align with overlay peak, got {total}"
    print("OK factory prob lethal", total, mc_max, prob, top)


def test_factory_bot_one_third_lethal_prob():
    """对手 6 血 + 2 随从：随机 6 攻打脸概率约 33%（3 个目标各 1/3）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs, 1)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    gs.get_entity(2).health = 6
    _minion_db(gs, 10, 1, "TOY_601", can_attack=False)
    for i, (atk, hp) in enumerate([(2, 2), (2, 2)], start=20):
        _minion(gs, i, 2, atk, hp, card_id=f"E{i}")

    lc = LethalChecker(gs)
    total, _, has_lethal = lc.calculate_lethal_potential()
    mc_max, prob, uses_random, top = lc.overlay_face_stats()
    assert uses_random
    assert mc_max == 6
    assert 0.28 <= prob <= 0.38, f"expected ~33% lethal prob, got {prob}"
    assert has_lethal
    assert total == 6
    print("OK factory one-third prob", total, mc_max, prob, top)


def test_factory_bot_end_turn_only_overlay_lethal():
    """仅回合结束 6 打脸（随从均已疲劳）应与斩杀总伤对齐。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs, 1)
    _hero(gs, 1, 1, mana=10, used=9)
    _hero(gs, 2, 2)
    gs.get_entity(2).health = 10
    _minion_db(gs, 10, 1, "TOY_601", can_attack=False)
    _minion_db(gs, 11, 1, "CATA_476", can_attack=False)

    lc = LethalChecker(gs)
    total, _, has_lethal = lc.calculate_lethal_potential()
    overlay = lc.overlay_board_face_damage()
    mc_max, prob, uses_random, top = lc.overlay_face_stats()
    assert overlay == 6, f"expected 6 end-turn face, got {overlay}"
    assert total == 6, f"lethal total should match overlay, got {total}"
    assert uses_random
    assert top == [(6, 1.0)]
    assert not has_lethal
    print("OK factory end-turn only align", overlay, total, prob, top)


def test_factory_bot_user_scenario_overlay():
    """用户场景：3×4/4嘲+1×3/5嘲，我方6/6+3/3+工厂，清嘲后 token 可随机打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M1", can_attack=True)
    _minion(gs, 11, 1, 3, 3, card_id="M2", can_attack=True)
    _minion(gs, 12, 1, *_db_minion_stats("TOY_601"), card_id="TOY_601", can_attack=False)
    for i, (atk, hp) in enumerate([(4, 4), (4, 4), (4, 4), (3, 5)], start=20):
        _minion(gs, i, 2, atk, hp, card_id=f"T{i}", taunt=True)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    max_face, prob, uses_random, top = lc.overlay_face_stats()
    assert uses_random, "factory should mark uses_random"
    assert max_face == 6, f"MC peak should be 6 end-turn face, got {max_face}"
    assert total == 6, f"display total should be 6, got {total}"
    print("OK user scenario overlay", total, max_face, prob, top)


def test_end_turn_direct_api():
    board = []
    enemy = []
    assert end_turn_face_damage(board, enemy, False)[0] == 0
    print("OK end_turn direct empty")


def _board_entities(gs, pid):
    return gs.get_board(pid)


def test_masticator_empty_board():
    """侏儒嚼嚼怪 5 攻：空场打脸 5。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "RLK_720", can_attack=False)

    face, _ = end_turn_face_damage(_board_entities(gs, 1), [], False)
    assert face == 5, f"expected 5, got {face}"
    print("OK masticator face 5", face)


def test_masticator_attacks_hero_when_lowest():
    """英雄生命低于场上随从时，回合结束应打脸而非只打随从。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "RLK_720", can_attack=False)
    _minion(gs, 20, 2, 3, 6, card_id="T1")
    opp = gs.get_hero(2)
    opp.health = 5
    opp.damage = 0
    opp.tags["HEALTH"] = 5
    enemy = [
        {"health": 6, "taunt": False, "shield": False, "kind": "minion"},
    ]
    face, _ = end_turn_face_damage(
        _board_entities(gs, 1), enemy, False,
        game_state=gs, player_id=1,
    )
    assert face == 5, f"expected 5 face on 5hp hero, got {face}"
    print("OK masticator hero lowest", face)


def test_masticator_attacks_minion_when_lower_than_hero():
    """随从生命低于英雄时仍打随从，不打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "RLK_720", can_attack=False)
    enemy = [{"health": 3, "taunt": False, "shield": False, "kind": "minion"}]
    face, _ = end_turn_face_damage(
        _board_entities(gs, 1), enemy, False,
        game_state=gs, player_id=1,
    )
    assert face == 0, f"expected 0 face hitting 3hp minion, got {face}"
    assert enemy[0]["health"] == -2
    print("OK masticator minion lowest", face)


def test_masticator_after_simulated_face_damage():
    """模拟先打脸 6 后：英雄 2 血低于 3 血随从，回合结束应打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "RLK_720", can_attack=False)
    opp = gs.get_hero(2)
    opp.health = 30
    opp.damage = 22
    opp.tags["HEALTH"] = 30
    enemy = [{"health": 3, "taunt": False, "shield": False, "kind": "minion"}]
    face, _ = end_turn_face_damage(
        _board_entities(gs, 1), enemy, False,
        game_state=gs, player_id=1,
        opponent_hero_hp=2,
    )
    assert face == 5, f"expected 5 face on 2hp hero after sim attacks, got {face}"
    print("OK masticator after sim face", face)


def test_masticator_hand_opp_turn_overlay():
    """对方回合：手牌嚼嚼怪应计入下回合打出后的回合结束 5 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=9, used=0)
    _hero(gs, 2, 2)
    hand = gs.get_entity(50)
    hand.cardtype = "MINION"
    hand.controller = 1
    hand.zone = "HAND"
    hand.card_id = "RLK_720"
    hand.cost = 6
    hand.atk = 5
    hand.health = 6
    hand.tags.update({"ZONE": "HAND", "ATK": 5, "479": 5, "HEALTH": 6, "COST": 6})

    lc = LethalChecker(gs)
    assert lc.is_opponent_turn()
    face = lc.overlay_board_face_damage()
    assert face == 5, f"expected 5 from hand muncher end-turn, got {face}"
    print("OK hand muncher opp turn overlay", face)


def test_mograine_aura_without_minion():
    """下回合：本体已离场，英雄附着 RLK_706e3 仍 +3。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    hero_eid = gs.hero_entity_ids[1]
    enc = gs.get_entity(99)
    enc.cardtype = "ENCHANTMENT"
    enc.card_id = "RLK_706e3"
    enc.zone = "PLAY"
    enc.tags["ZONE"] = "PLAY"
    enc.tags["ATTACHED"] = hero_eid
    enc.tags["CARDTYPE"] = "ENCHANTMENT"

    face, notes = end_turn_face_damage([], [], False, game_state=gs, player_id=1)
    assert face == 3, f"expected aura +3, got {face}"
    assert any("光环" in n for n in notes)
    print("OK mograine aura next turn +3", face, notes)


def test_mograine_aura_not_double_with_minion():
    """本体在场时只计一次 +3（不叠光环）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "RLK_706", can_attack=False)
    hero_eid = gs.hero_entity_ids[1]
    enc = gs.get_entity(99)
    enc.cardtype = "ENCHANTMENT"
    enc.card_id = "RLK_706e3"
    enc.tags["ATTACHED"] = hero_eid

    face, _ = end_turn_face_damage(
        gs.get_board(1), [], False, game_state=gs, player_id=1,
    )
    assert face == 3, f"expected single +3, got {face}"
    print("OK mograine no double count", face)


def test_mograine_end_turn():
    """莫格莱尼：回合结束 +3 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "RLK_706", can_attack=False)

    face, _ = end_turn_face_damage(_board_entities(gs, 1), [], False)
    assert face == 3, f"expected 3, got {face}"
    print("OK mograine +3", face)


def test_troublemaker_two_attacks():
    """问题学生：两只 3/3 空场合计 +6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "SCH_337", can_attack=False)

    face, _ = end_turn_face_damage(_board_entities(gs, 1), [], False)
    assert face == 6, f"expected 6, got {face}"
    print("OK troublemaker +6", face)


def test_thornmantle_overflow():
    """棘嗣幼龙 12/7：12 攻打 4/4 嘲，溢出 8 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "EDR_453", can_attack=False)
    enemy = [{"entity_id": 20, "atk": 4, "health": 4, "taunt": True}]

    face, _ = end_turn_face_damage(_board_entities(gs, 1), enemy, False)
    assert face == 8, f"expected overflow 8, got {face}"
    print("OK thornmantle overflow 8", face)


def test_thornmantle_overflow_through_divine_shield():
    """棘嗣幼龙 12 攻打 3/3 圣盾：溢出按血量算 9（与 Explosive Runes 一致）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "EDR_453", can_attack=False)
    enemy = [{"entity_id": 20, "atk": 3, "health": 3, "shield": True}]

    face, _ = end_turn_face_damage(_board_entities(gs, 1), enemy, False)
    assert face == 9, f"expected overflow 9 through divine shield, got {face}"
    print("OK thornmantle overflow through divine shield", face)


def test_thornmantle_seven_minion_lethal_prob():
    """7 随从仅 12/14 无溢出；3 圣盾 token 仍按血量溢出 → 约 6/7 概率斩杀。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.in_game = True
    _set_local_turn(gs, 2)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2, mana=10, used=0)
    gs.get_entity(1).health = 9
    _minion(gs, 132, 1, 12, 14, card_id="TTN_751", can_attack=False)
    _minion(gs, 17, 1, 4, 1, card_id="TSC_933", can_attack=False)
    _minion(gs, 29, 1, 6, 3, card_id="GIL_598", can_attack=False)
    _minion(gs, 259, 1, 2, 1, card_id="TIME_613", can_attack=False)
    for eid in (265, 266, 267):
        _minion(gs, eid, 1, 3, 3, card_id="GDB_139t", can_attack=False)
        gs.get_entity(eid).tags["DIVINE_SHIELD"] = 1
    m = gs.get_entity(245)
    m.cardtype = "MINION"
    m.controller = 2
    m.zone = "HAND"
    m.card_id = "EDR_453"
    m.atk = 12
    m.health = 7
    m.cost = 10
    m.tags["ZONE"] = "HAND"
    m.tags["ATK"] = 12
    m.tags["HEALTH"] = 7
    m.tags["COST"] = 10

    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    mc_max, prob, uses_random, _ = lc.overlay_face_stats()
    assert uses_random
    assert mc_max >= 11
    assert prob >= 0.75, f"expected ~6/7 lethal prob, got {prob:.2%}"
    print("OK thornmantle seven minion lethal prob", prob)


def test_thornmantle_ignores_dormant_enemy():
    """棘嗣幼龙：敌方仅有休眠随从时无法攻击，溢出为 0。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "EDR_453", can_attack=False)
    enemy = [{"entity_id": 20, "atk": 6, "health": 6, "dormant": True}]

    face, _ = end_turn_face_damage(_board_entities(gs, 1), enemy, False)
    assert face == 0, f"expected 0 vs dormant-only board, got {face}"
    print("OK thornmantle ignores dormant enemy", face)


def test_thornmantle_skips_dormant_picks_awake():
    """棘嗣幼龙：休眠 6/6 不可选，仅能打醒着的 2/2，溢出 10。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "EDR_453", can_attack=False)
    enemy = [
        {"entity_id": 20, "atk": 6, "health": 6, "dormant": True},
        {"entity_id": 21, "atk": 2, "health": 2, "dormant": False},
    ]

    face, _ = end_turn_face_damage(_board_entities(gs, 1), enemy, False)
    assert face == 10, f"expected overflow 10 on awake 2/2, got {face}"
    print("OK thornmantle skips dormant picks awake", face)


def test_scalecleaver_warden():
    """破鳞盾卫：回合结束 +2 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "CATA_475", can_attack=False)

    face, _ = end_turn_face_damage(_board_entities(gs, 1), [], False)
    assert face == 2, f"expected 2, got {face}"
    print("OK scalecleaver +2", face)


def test_brasswing():
    """亮铜之翼：回合结束对所有敌人 +2 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "AV_340", can_attack=False)

    face, notes = end_turn_face_damage(_board_entities(gs, 1), [], False)
    assert face == 2, f"expected 2, got {face}"
    assert any("亮铜之翼" in n for n in notes), notes
    print("OK brasswing +2", face)


def test_priestess_of_fury():
    """愤怒的女祭司：乐观上界 +6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "CORE_BT_493", can_attack=False)

    face, _ = end_turn_face_damage(_board_entities(gs, 1), [], False)
    assert face == 6, f"expected 6, got {face}"
    print("OK priestess +6", face)


def test_runaway_blackwing_end_turn_never_faces():
    """窜逃的黑翼龙：回合结束随机打敌方随从，不得计入对英雄场攻。"""
    from hdt_python.end_turn_board import EtKind, _resolve_end_turn_def

    for cid in ("YOP_034", "CORE_YOP_034"):
        defn = _resolve_end_turn_def(cid)
        assert defn is not None, cid
        assert defn.kind == EtKind.RANDOM_ENEMY_MINION, (cid, defn.kind)

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    # 空场 / 有嘲讽随从：回合结束均不应产生打脸
    _minion_db(gs, 10, 1, "CORE_YOP_034", can_attack=False)
    face_empty, notes = end_turn_face_damage(_board_entities(gs, 1), [], False)
    assert face_empty == 0, face_empty
    assert not any("+10" in n or "打脸" in n for n in notes), notes

    enemy = [{"kind": "minion", "health": 12, "atk": 3, "taunt": True, "shield": False}]
    face_board, _ = end_turn_face_damage(_board_entities(gs, 1), enemy, False)
    assert face_board == 0, face_board

    checker = LethalChecker(gs)
    _set_local_turn(gs)
    gs.active_player_id = 2  # 对方回合 → 下回合预览不应把 10 算进场攻
    total = checker.overlay_board_face_damage()
    # 刚打出不能攻，且 ET 不打脸 → 场攻 0
    assert total == 0, (total, checker.overlay_spell_note(), checker.overlay_board_breakdown())
    print("OK runaway blackwing ET never faces", face_empty, face_board, total)


def test_earthen_dragon():
    """土石幼龙：回合结束 +4 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "CATA_999", can_attack=False)

    face, _ = end_turn_face_damage(_board_entities(gs, 1), [], False)
    assert face == 4, f"expected 4, got {face}"
    print("OK earthen dragon +4", face)


def test_thornmantle_hand_hold_attack_overlay():
    """手牌棘嗣幼龙：不攻击，打出后回合结束 12 打 4/4 嘲溢出 8。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M1", can_attack=True)
    _minion(gs, 20, 2, 4, 4, card_id="T1", taunt=True)
    m = gs.get_entity(30)
    m.cardtype = "MINION"
    m.controller = 1
    m.zone = "HAND"
    m.card_id = "EDR_453"
    m.atk = 12
    m.health = 7
    m.cost = 10
    m.tags["ZONE"] = "HAND"
    m.tags["ATK"] = 12
    m.tags["HEALTH"] = 7
    m.tags["COST"] = 10

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    assert total == 8, f"expected 8 from hand thornmantle hold line, got {total}"
    print("OK thornmantle hand hold overlay", total)


def test_thornmantle_partial_attack_subset_overlay():
    """6/6 不攻、2/2+1/1 磨嘲至 1 血，手牌幼龙回合结束溢出 11。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M1", can_attack=True)
    _minion(gs, 11, 1, 2, 2, card_id="M2", can_attack=True)
    _minion(gs, 12, 1, 1, 1, card_id="M3", can_attack=True)
    _minion(gs, 20, 2, 4, 4, card_id="T1", taunt=True)
    m = gs.get_entity(30)
    m.cardtype = "MINION"
    m.controller = 1
    m.zone = "HAND"
    m.card_id = "EDR_453"
    m.atk = 12
    m.health = 7
    m.cost = 10
    m.tags["ZONE"] = "HAND"
    m.tags["ATK"] = 12
    m.tags["HEALTH"] = 7
    m.tags["COST"] = 10

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    assert total == 11, f"expected 11 from partial attack subset, got {total}"
    print("OK thornmantle partial attack subset overlay", total)


def test_thornmantle_hand_two_fives_no_taunt_overlay():
    """对方 6/6+2/2 无嘲，我方 2×5/5 + 手牌棘嗣幼龙：5+5 打脸 + 回合结束溢出 50%→20 / 50%→16。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 5, 5, card_id="M55a")
    _minion(gs, 11, 1, 5, 5, card_id="M55b")
    _minion(gs, 20, 2, 6, 6, card_id="E66")
    _minion(gs, 21, 2, 2, 2, card_id="E22")
    m = gs.get_entity(30)
    m.cardtype = "MINION"
    m.controller = 1
    m.zone = "HAND"
    m.card_id = "EDR_453"
    m.atk = 12
    m.health = 7
    m.cost = 10
    m.tags["ZONE"] = "HAND"
    m.tags["ATK"] = 12
    m.tags["HEALTH"] = 7
    m.tags["COST"] = 10

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    mc_max, prob, uses_random, top = lc.overlay_face_stats()
    assert total == 20, f"expected peak 20, got {total}"
    assert uses_random, "hatchling end-turn overflow should be random"
    assert mc_max == 20, f"mc peak should be 20, got {mc_max}"
    assert "棘嗣幼龙" in note, f"expected hatchling in note, got {note!r}"
    totals = {dmg for dmg, _ in top}
    assert 20 in totals and 16 in totals, f"expected top outcomes 20 and 16, got {top}"
    for dmg, p in top:
        if dmg == 20:
            assert 0.35 <= p <= 0.65, f"expected ~50% for 20, got {p}"
        if dmg == 16:
            assert 0.35 <= p <= 0.65, f"expected ~50% for 16, got {p}"
    print("OK thornmantle hand two fives no taunt overlay", total, note, top)


def test_thornmantle_plague_strike_rush_five_overlay():
    """对方 5/5+2/2+3/3，2×5/5 + 7费幼龙 + 凋零打击：突袭换 5/5，50%→20 / 50%→19。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 5, 5, card_id="M55a")
    _minion(gs, 11, 1, 5, 5, card_id="M55b")
    _minion(gs, 20, 2, 5, 5, card_id="E55")
    _minion(gs, 21, 2, 2, 2, card_id="E22")
    _minion(gs, 22, 2, 3, 3, card_id="E33")
    m = gs.get_entity(30)
    m.cardtype = "MINION"
    m.controller = 1
    m.zone = "HAND"
    m.card_id = "EDR_453"
    m.atk = 12
    m.health = 7
    m.cost = 7
    m.tags["ZONE"] = "HAND"
    m.tags["ATK"] = 12
    m.tags["HEALTH"] = 7
    m.tags["COST"] = 7
    sp = gs.get_entity(31)
    sp.cardtype = "SPELL"
    sp.controller = 1
    sp.zone = "HAND"
    sp.card_id = "RLK_018"
    sp.cost = 2
    sp.tags["ZONE"] = "HAND"
    sp.tags["COST"] = 2

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    mc_max, _prob, uses_random, top = lc.overlay_face_stats()
    seq = getattr(lc, "_overlay_best_seq", [])
    assert total == 20, f"expected peak 20, got {total}"
    assert uses_random
    assert mc_max == 20
    assert len(seq) == 2, f"expected wither+hatchling, got {seq!r}"
    assert "凋零打击" in note and "棘嗣幼龙" in note, note
    totals = {dmg for dmg, _ in top}
    assert 20 in totals and 19 in totals, f"expected 20 and 19 in top, got {top}"
    for dmg, p in top:
        if dmg == 20:
            assert 0.35 <= p <= 0.65, f"expected ~50% for 20, got {p}"
        if dmg == 19:
            assert 0.35 <= p <= 0.65, f"expected ~50% for 19, got {p}"
    print("OK thornmantle plague strike rush five overlay", total, note, top)


def test_thornmantle_on_board_hold_attack_overlay():
    """场上棘嗣幼龙：6/6 不攻击，回合结束溢出 8。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "EDR_453", can_attack=False)
    _minion(gs, 11, 1, 6, 6, card_id="M1", can_attack=True)
    _minion(gs, 20, 2, 4, 4, card_id="T1", taunt=True)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    assert total == 8, f"expected 8 from board thornmantle hold, got {total}"
    print("OK thornmantle board hold overlay", total)


def test_pure_board_face_includes_end_turn_on_summon():
    """刚上场/变形、当回合不能攻击：pure 场攻仍应计入回合结束伤害。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "EDR_453", can_attack=False)
    _minion(gs, 20, 2, 5, 2, card_id="CATA_158")

    lc = LethalChecker(gs)
    board_view = gs.get_overlay_board(1)
    pure = lc._compute_pure_board_face(board_view, 1, [], False)
    assert pure == 10, f"expected pure 10 (12-2 overflow), got {pure}"
    immediate = lc._compute_immediate_board_face(board_view, 1, [], False)
    assert immediate == 0, f"expected immediate 0, got {immediate}"
    print("OK pure board includes thornmantle end turn", pure)


def test_pure_board_face_magtheridon_dormant():
    """休眠玛瑟里顿刚上场：pure 场攻应立刻含 +3。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion_db(gs, 10, 1, "TOY_647", dormant=True)

    lc = LethalChecker(gs)
    board_view = gs.get_overlay_board(1)
    pure = lc._compute_pure_board_face(board_view, 1, [], False)
    assert pure == 3, f"expected pure 3 from dormant Magtheridon, got {pure}"
    print("OK pure board includes magtheridon +3", pure)


def test_quick_lethal_includes_end_turn():
    """快速斩杀估算也应计入回合结束可预估伤害。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _set_local_turn(gs)
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    h2 = gs.get_entity(2)
    h2.health = 4
    _minion_db(gs, 10, 1, "CATA_999", can_attack=False)

    lc = LethalChecker(gs)
    total, sources, has_lethal = lc._calculate_quick_lethal_for_player(
        1, 2, include_hand=False, board_active_turn=True, use_overlay_board=True,
    )
    assert total == 4, f"expected quick total 4, got {total}"
    assert has_lethal, f"expected lethal vs 4 hp, got {has_lethal}"
    assert any("回合结束" in s.description for s in sources), sources
    print("OK quick lethal includes end turn", total, has_lethal)


def test_end_turn_p1_registered():
    for cid in (
        "RLK_720", "RLK_706", "SCH_337", "EDR_453",
        "CATA_475", "AV_340", "CORE_BT_493", "CATA_999",
    ):
        assert cid in END_TURN_BY_CARD, cid
    print("OK p1 end turn 7 registered")


def test_end_turn_registered_cards_in_card_db():
    """已注册 card_id 均能在 cards.json 查到身材。"""
    db = _load_card_db()
    for cid in END_TURN_BY_CARD:
        if cid.startswith("CORE_"):
            continue
        card = db.get(cid)
        assert card is not None, cid
        assert card.get("type") == "MINION", cid
        assert "attack" in card and "health" in card, cid
    print("OK end turn cards in card db")


if __name__ == "__main__":
    test_end_turn_direct_api()
    test_current_player_handoff_at_turn_start()
    test_end_turn_p1_registered()
    test_end_turn_registered_cards_in_card_db()
    test_magtheridon_dormant_end_turn()
    test_magtheridon_awake_no_end_turn()
    test_factory_bot_no_taunt()
    test_factory_bot_with_taunt_random_upper_bound()
    test_factory_bot_with_taunt_random_mc()
    test_factory_bot_user_scenario_overlay()
    test_masticator_empty_board()
    test_masticator_attacks_hero_when_lowest()
    test_masticator_attacks_minion_when_lower_than_hero()
    test_masticator_hand_opp_turn_overlay()
    test_mograine_end_turn()
    test_mograine_aura_without_minion()
    test_mograine_aura_not_double_with_minion()
    test_troublemaker_two_attacks()
    test_thornmantle_overflow()
    test_thornmantle_overflow_through_divine_shield()
    test_thornmantle_seven_minion_lethal_prob()
    test_thornmantle_ignores_dormant_enemy()
    test_thornmantle_skips_dormant_picks_awake()
    test_thornmantle_hand_hold_attack_overlay()
    test_thornmantle_partial_attack_subset_overlay()
    test_thornmantle_hand_two_fives_no_taunt_overlay()
    test_thornmantle_plague_strike_rush_five_overlay()
    test_thornmantle_on_board_hold_attack_overlay()
    test_pure_board_face_includes_end_turn_on_summon()
    test_pure_board_face_magtheridon_dormant()
    test_quick_lethal_includes_end_turn()
    test_scalecleaver_warden()
    test_brasswing()
    test_priestess_of_fury()
    test_runaway_blackwing_end_turn_never_faces()
    test_earthen_dragon()
    print("all passed")
