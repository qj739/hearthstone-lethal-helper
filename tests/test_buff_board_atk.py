#!/usr/bin/env python3
"""BUFF 攻 / stale EXHAUSTED 场攻回归。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.board_damage import (
    build_board_card,
    is_exhausted,
    _std_attack,
    attached_enchantment_attack_bonus,
)


def _hero(gs, eid, pid):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, *, turns=1, exhausted=1, card_id="TTN_484"):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = atk
    m.tags["ZONE"] = "PLAY"
    m.tags["479"] = atk
    m.tags["ATK"] = atk
    m.tags["1196"] = 0
    m.tags["EXHAUSTED"] = exhausted
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = turns
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _enchantment(gs, eid, parent_eid, atk_bonus):
    e = gs.get_entity(eid)
    e.cardtype = "ENCHANTMENT"
    e.card_id = "CATA_153e"
    e.controller = 1
    e.zone = "PLAY"
    e.tags["ZONE"] = "PLAY"
    e.tags["ATTACHED"] = parent_eid
    e.tags["323"] = atk_bonus
    e.tags["TAG_SCRIPT_DATA_NUM_1"] = atk_bonus
    return e


def test_stale_exhausted_counts_buffed_atk():
    """回合初 EXHAUSTED=1 未刷新、NUM_TURNS>=1、BUFF 后应计入场攻。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1)
    m = _minion(gs, 10, 1, 4, turns=1, exhausted=1)
    view = build_board_card(m, True, gs)
    assert not is_exhausted(m), "stale EXHAUSTED 不应阻止已站场随从"
    assert view.can_attack_hero
    assert view.attack == 4
    assert view.std_attack == 4


def test_enchantment_attack_when_479_lags():
    """附魔 tag 323 已写入、随从 ATK 仍低于牌面时，用牌面+附魔兜底。"""
    gs = GameState()
    gs.local_player_id = 1
    # ATK=0 < 牌面 2：模拟 tag 未刷到牌面身材
    m = _minion(gs, 10, 1, 0, turns=2, exhausted=0)
    m.atk = 0
    m.tags["ATK"] = 0
    m.tags["479"] = 0
    _enchantment(gs, 20, 10, 2)
    assert attached_enchantment_attack_bonus(gs, m) == 2
    assert _std_attack(m, gs) == 4


def test_lifedrinker_set_atk_plus_auras_no_double():
    """
    吸血蚊：斗志有限变为1，再叠巴加斯特/雷欧克各+1 → ATK=3。
    不可再按牌面3+附魔2算成5。
    """
    gs = GameState()
    gs.local_player_id = 1
    m = _minion(gs, 93, 1, 3, turns=8, exhausted=0, card_id="CORE_GIL_622")
    for eid, cid, bonus in (
        (149, "REV_353t4e", 1),
        (175, "NEW1_033o", 1),
    ):
        e = gs.get_entity(eid)
        e.cardtype = "ENCHANTMENT"
        e.card_id = cid
        e.zone = "PLAY"
        e.tags.update({"ZONE": "PLAY", "ATTACHED": 93, "323": bonus})
    # 斗志有限：无 323，但存在表示 ATK 已按「变为」结算
    lim = gs.get_entity(121)
    lim.cardtype = "ENCHANTMENT"
    lim.card_id = "END_010ae"
    lim.zone = "PLAY"
    lim.tags.update({"ZONE": "PLAY", "ATTACHED": 93})

    assert attached_enchantment_attack_bonus(gs, m) == 2
    assert _std_attack(m, gs) == 3


def test_chogall_arm_synced_tags_no_double_enchant():
    """加尔手臂：ATK/479 已同步为 3 时，不应再叠附魔 +3 变成 6 攻。"""
    gs = GameState()
    gs.local_player_id = 1
    m = gs.get_entity(10)
    m.cardtype = "MINION"
    m.controller = 1
    m.zone = "PLAY"
    m.card_id = "CATA_726t1"
    m.atk = 3
    m.health = 2
    m.tags.update({
        "ZONE": "PLAY", "ATK": 3, "479": 3, "HEALTH": 2,
    })
    gs.board_slots.setdefault(1, {})[1] = 10

    def _ench(eid, parent, bonus, cid):
        e = gs.get_entity(eid)
        e.cardtype = "ENCHANTMENT"
        e.card_id = cid
        e.zone = "PLAY"
        e.tags.update({
            "ZONE": "PLAY", "ATTACHED": parent,
            "TAG_SCRIPT_DATA_NUM_1": bonus,
        })

    _ench(20, 10, 2, "CATA_726te")
    _ench(21, 10, 1, "EDR_810e")
    assert attached_enchantment_attack_bonus(gs, m) == 3
    assert _std_attack(m, gs) == 3


def test_uld_163_expired_goods_script_not_attack():
    """法老猫 ULD_163e：script=发现费用，不应把 2 攻猫算成 20+ 场攻。"""
    gs = GameState()
    gs.local_player_id = 1
    m = _minion(gs, 4, 1, 2, turns=2, exhausted=1, card_id="ULD_163")
    e = gs.get_entity(96)
    e.cardtype = "ENCHANTMENT"
    e.card_id = "ULD_163e"
    e.zone = "PLAY"
    e.tags.update({
        "ZONE": "PLAY", "ATTACHED": 4, "TAG_SCRIPT_DATA_NUM_1": 22,
    })
    assert attached_enchantment_attack_bonus(gs, m) == 0
    assert _std_attack(m, gs) == 2


def test_chogall_arm_pair_six_board_face():
    """两只 3 攻手臂 + 无武器时纯场攻应为 6（非 9）。"""
    from hdt_python.lethal_checker import LethalChecker

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)

    for eid, pos in ((150, 1), (149, 2)):
        m = gs.get_entity(eid)
        m.cardtype = "MINION"
        m.controller = 1
        m.zone = "PLAY"
        m.card_id = "CATA_726t" if eid == 150 else "CATA_726t1"
        m.atk = 3
        m.health = 3 if eid == 150 else 2
        m.tags.update({
            "ZONE": "PLAY", "ATK": 3, "479": 3, "HEALTH": m.health,
            "1196": 0, "EXHAUSTED": 0, "NUM_ATTACKS_THIS_TURN": 0,
            "NUM_TURNS_IN_PLAY": 1, "ZONE_POSITION": pos,
        })
        gs.board_slots.setdefault(1, {})[pos] = eid
        if eid == 149:
            _ench = gs.get_entity(20)
            _ench.cardtype = "ENCHANTMENT"
            _ench.card_id = "CATA_726te"
            _ench.zone = "PLAY"
            _ench.tags.update({"ZONE": "PLAY", "ATTACHED": 149, "TAG_SCRIPT_DATA_NUM_1": 2})
            _ench2 = gs.get_entity(21)
            _ench2.cardtype = "ENCHANTMENT"
            _ench2.card_id = "EDR_810e"
            _ench2.zone = "PLAY"
            _ench2.tags.update({"ZONE": "PLAY", "ATTACHED": 149, "TAG_SCRIPT_DATA_NUM_1": 1})

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, (total, checker.overlay_board_breakdown())


if __name__ == "__main__":
    test_stale_exhausted_counts_buffed_atk()
    test_enchantment_attack_when_479_lags()
    test_lifedrinker_set_atk_plus_auras_no_double()
    test_chogall_arm_synced_tags_no_double_enchant()
    test_uld_163_expired_goods_script_not_attack()
    test_chogall_arm_pair_six_board_face()
    print("all passed")
