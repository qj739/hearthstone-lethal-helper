#!/usr/bin/env python3
"""漏斩打脸相关 12 张未注册卡：注册存在 + 核心数值回归。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.power_parser import GameState
from hdt_python.spell_board import (
    SpellSimTier,
    apply_spell_sequence,
    get_board_spell_def,
    spell_sim_tier_for_card,
)


def _spell(cid: str, *, powered: int = 0, num1: int = 0, num2: int = 0, eid: int = 30):
    card = GameState().get_entity(eid)
    card.cardtype = "SPELL"
    card.card_id = cid
    card.tags["POWERED_UP"] = powered
    if num1:
        card.tags["TAG_SCRIPT_DATA_NUM_1"] = num1
    if num2:
        card.tags["TAG_SCRIPT_DATA_NUM_2"] = num2
    return card


def _minion_card(cid: str, *, powered: int = 0, eid: int = 40, **tags):
    card = GameState().get_entity(eid)
    card.cardtype = "MINION"
    card.card_id = cid
    card.tags["POWERED_UP"] = powered
    card.tags.update(tags)
    return card


def test_batch12_registered():
    spells = [
        "JAIL_801", "TLC_440", "TTN_477", "JAIL_892",
        "EDR_263", "JAIL_201", "MEND_500",
    ]
    battlecries = ["TLC_522", "EDR_430", "FIR_956", "TLC_903", "END_006"]
    missing_s = [c for c in spells if get_board_spell_def(c) is None]
    missing_b = [c for c in battlecries if get_battlecry_def(c) is None]
    assert not missing_s, missing_s
    assert not missing_b, missing_b


def test_jail_801_and_tlc_440_face_4():
    for cid in ("JAIL_801", "TLC_440"):
        defn = get_board_spell_def(cid)
        res = apply_spell_sequence([], [], [(defn, defn.base_cost, _spell(cid))], enemy_shield=False)
        assert res.direct_face_damage == 4, (cid, res.direct_face_damage)


def test_ttn_477_forge_double_face_6():
    defn = get_board_spell_def("TTN_477")
    off = _spell("TTN_477", powered=0)
    on = _spell("TTN_477", powered=1, eid=31)
    res_off = apply_spell_sequence([], [], [(defn, 3, off)], enemy_shield=False)
    res_on = apply_spell_sequence([], [], [(defn, 3, on)], enemy_shield=False)
    assert res_off.direct_face_damage == 3
    assert res_on.direct_face_damage == 6


def test_jail_892_outcast_double_face_4():
    defn = get_board_spell_def("JAIL_892")
    off = _spell("JAIL_892", powered=0)
    on = _spell("JAIL_892", powered=1, eid=31)
    res_off = apply_spell_sequence([], [], [(defn, 2, off)], enemy_shield=False)
    res_on = apply_spell_sequence([], [], [(defn, 2, on)], enemy_shield=False)
    assert res_off.direct_face_damage == 2
    assert res_on.direct_face_damage == 4


def test_edr_263_empty_board_takes_face_4():
    defn = get_board_spell_def("EDR_263")
    spell_sim_tier_for_card.cache_clear()
    assert spell_sim_tier_for_card("EDR_263") == SpellSimTier.CLEAR_AND_FACE
    res = apply_spell_sequence([], [], [(defn, 4, _spell("EDR_263"))], enemy_shield=False)
    assert res.direct_face_damage == 4


def test_edr_263_taunt_may_summon_wolves():
    defn = get_board_spell_def("EDR_263")
    taunts = [{
        "entity_id": 18, "health": 2, "atk": 1, "taunt": True,
        "shield": False, "kind": "minion",
    }]
    # 已有 5 攻可打脸：狼解嘲后场面 5 > 纯 4 脸 → 取狼
    fighters = [{
        "kind": "minion", "atk": 5, "health": 5, "attacks_left": 1, "can_face": True,
    }]
    res = apply_spell_sequence(
        taunts, fighters, [(defn, 4, _spell("EDR_263"))], enemy_shield=False,
    )
    wolves = [
        f for f in fighters
        if f.get("kind") == "minion" and f.get("rush") and f.get("atk") == 3
    ]
    assert len(wolves) == 2, (res.direct_face_damage, fighters)
    assert res.direct_face_damage == 0


def test_jail_201_hero_plus_2():
    defn = get_board_spell_def("JAIL_201")
    fighters = [{
        "kind": "weapon", "atk": 3, "health": 2, "attacks_left": 1,
        "can_face": True, "durability": 2,
    }]
    apply_spell_sequence([], fighters, [(defn, 0, _spell("JAIL_201"))], enemy_shield=False)
    assert fighters[0]["atk"] == 5


def test_tlc_522_fan_clears_1hp_taunt():
    defn = get_battlecry_def("TLC_522")
    taunts = [{
        "entity_id": 18, "health": 1, "atk": 5, "taunt": True,
        "shield": False, "kind": "minion",
    }]
    fighters = [{
        "kind": "minion", "atk": 4, "health": 3, "attacks_left": 1, "can_face": True,
    }]
    card = _minion_card("TLC_522", powered=0)
    apply_spell_sequence(taunts, fighters, [(defn, 6, card)], enemy_shield=False)
    assert all(t.get("health", 0) <= 0 for t in taunts) or not taunts


def test_tlc_522_combo_double_fan():
    defn = get_battlecry_def("TLC_522")
    taunts = [
        {
            "entity_id": 18, "health": 2, "atk": 1, "taunt": False,
            "shield": False, "kind": "minion",
        },
    ]
    card = _minion_card("TLC_522", powered=1)
    apply_spell_sequence(taunts, [], [(defn, 6, card)], enemy_shield=False)
    assert all(t.get("health", 0) <= 0 for t in taunts) or not taunts


def test_fir_956_dark_gift_hero_plus_3():
    defn = get_battlecry_def("FIR_956")
    gs = GameState()
    gs.local_player_id = 1
    gift = gs.get_entity(50)
    gift.cardtype = "MINION"
    gift.card_id = "EDR_100t"
    gift.controller = 1
    gift.zone = "HAND"
    gift.tags["ZONE"] = "HAND"
    gift.tags["HAS_DARK_GIFT"] = 99
    turtle = gs.get_entity(51)
    turtle.cardtype = "MINION"
    turtle.card_id = "FIR_956"
    turtle.controller = 1
    turtle.zone = "HAND"

    fighters = [{
        "kind": "hero", "atk": 0, "health": 10**9, "attacks_left": 1, "can_face": True,
    }]
    apply_spell_sequence(
        [], fighters, [(defn, 4, turtle)], enemy_shield=False, gs=gs, player_id=1,
    )
    assert fighters[0]["atk"] == 3

    fighters2 = [{
        "kind": "hero", "atk": 0, "health": 10**9, "attacks_left": 1, "can_face": True,
    }]
    # 无黑暗之赐：不加攻
    gs2 = GameState()
    gs2.local_player_id = 1
    turtle2 = gs2.get_entity(52)
    turtle2.cardtype = "MINION"
    turtle2.card_id = "FIR_956"
    apply_spell_sequence(
        [], fighters2, [(defn, 4, turtle2)], enemy_shield=False, gs=gs2, player_id=1,
    )
    assert fighters2[0]["atk"] == 0


def test_tlc_903_kindred_hero_plus_5():
    defn = get_battlecry_def("TLC_903")
    card = _minion_card("TLC_903", powered=1)
    card.tags["ATK"] = 5
    card.tags["HEALTH"] = 2
    fighters: list = []
    apply_spell_sequence([], fighters, [(defn, 5, card)], enemy_shield=False)
    assert any(f.get("rush") and f.get("atk") == 5 for f in fighters)
    hero = next(f for f in fighters if f.get("kind") == "hero")
    assert hero["atk"] == 5


def test_end_006_hero_plus_3():
    defn = get_battlecry_def("END_006")
    fighters = [{
        "kind": "hero", "atk": 1, "health": 10**9, "attacks_left": 1, "can_face": True,
    }]
    apply_spell_sequence(
        [], fighters, [(defn, 5, _minion_card("END_006"))], enemy_shield=False,
    )
    assert fighters[0]["atk"] == 4


def test_edr_430_not_ready_no_damage():
    defn = get_battlecry_def("EDR_430")
    card = _minion_card("EDR_430", powered=0)
    card.tags["TAG_SCRIPT_DATA_NUM_1"] = 5  # 还剩 5
    taunts = [{
        "entity_id": 18, "health": 30, "atk": 1, "taunt": False,
        "shield": False, "kind": "minion",
    }]
    res = apply_spell_sequence(taunts, [], [(defn, 8, card)], enemy_shield=False)
    assert res.direct_face_damage == 0
    assert taunts[0]["health"] == 30


def test_edr_430_ready_total_20():
    defn = get_battlecry_def("EDR_430")
    card = _minion_card("EDR_430", powered=1)
    import random
    taunts = [{
        "entity_id": 18, "health": 5, "atk": 1, "taunt": False,
        "shield": False, "kind": "minion",
    }]
    res = apply_spell_sequence(
        taunts, [], [(defn, 8, card)], enemy_shield=False, rng=random.Random(0),
    )
    # 总伤 20：随从最多承 5，其余打脸（战吼进 battlecry_face_damage）
    face = res.battlecry_face_damage or res.direct_face_damage
    minion_taken = 5 if not taunts else (
        5 - max(0, int(taunts[0].get("health", 0) or 0))
    )
    assert minion_taken + face == 20, (minion_taken, face, taunts, res)


def test_mend_500_overflow_to_face():
    defn = get_board_spell_def("MEND_500")
    spell_sim_tier_for_card.cache_clear()
    assert spell_sim_tier_for_card("MEND_500") == SpellSimTier.CLEAR_AND_FACE
    card = _spell("MEND_500", num1=4)
    taunts = [{
        "entity_id": 18, "health": 1, "atk": 1, "taunt": False,
        "shield": False, "kind": "minion",
    }]
    # 无 rng：乐观溢出 → 3 打脸（1 血随从死后从列表移除）
    res = apply_spell_sequence(taunts, [], [(defn, 4, card)], enemy_shield=False, rng=None)
    assert res.direct_face_damage == 3
    alive = [t for t in taunts if int(t.get("health", 0) or 0) > 0]
    assert not alive


def test_mend_500_no_minion_full_face():
    defn = get_board_spell_def("MEND_500")
    card = _spell("MEND_500", num1=4)
    res = apply_spell_sequence([], [], [(defn, 4, card)], enemy_shield=False, rng=None)
    assert res.direct_face_damage == 4


def test_cata_525_herald_hero_plus_1():
    """装甲放血纳迦：突袭 3/1 + 兆示士兵英雄 +1 攻（默认未升级）。"""
    defn = get_battlecry_def("CATA_525")
    assert defn is not None
    card = _minion_card("CATA_525")
    card.tags["ATK"] = 3
    card.tags["HEALTH"] = 1
    fighters: list = []
    apply_spell_sequence([], fighters, [(defn, 3, card)], enemy_shield=False)
    assert any(f.get("rush") and f.get("atk") == 3 and f.get("card_id") == "CATA_525" for f in fighters)
    assert any(f.get("card_id") == "CATA_525t" and f.get("attacks_left", 0) == 0 for f in fighters)
    hero = next(f for f in fighters if f.get("kind") == "hero")
    assert hero["atk"] == 1
    assert hero.get("can_face") is True


def test_cata_525_herald_bonus_from_setaside():
    """SETASIDE 预览 TAG_SCRIPT_DATA_NUM_1=2 → 英雄 +2。"""
    defn = get_battlecry_def("CATA_525")
    gs = GameState()
    gs.local_player_id = 1
    preview = gs.get_entity(900)
    preview.card_id = "CATA_525t"
    preview.controller = 1
    preview.zone = "SETASIDE"
    preview.tags["CONTROLLER"] = 1
    preview.tags["ZONE"] = "SETASIDE"
    preview.tags["TAG_SCRIPT_DATA_NUM_1"] = 2
    card = _minion_card("CATA_525", eid=41)
    card.tags["ATK"] = 3
    card.tags["HEALTH"] = 1
    fighters: list = []
    apply_spell_sequence(
        [], fighters, [(defn, 3, card)], enemy_shield=False, gs=gs, player_id=1,
    )
    hero = next(f for f in fighters if f.get("kind") == "hero")
    assert hero["atk"] == 2
    soldier = next(f for f in fighters if f.get("card_id") == "CATA_525t")
    assert soldier["atk"] == 4 and soldier["health"] == 2


def test_cata_530_herald_hero_plus_1_lifesteal():
    defn = get_board_spell_def("CATA_530")
    assert defn is not None
    fighters = [{
        "kind": "hero", "atk": 2, "health": 10**9, "attacks_left": 1, "can_face": True,
    }]
    apply_spell_sequence(
        [], fighters, [(defn, 2, _spell("CATA_530"))], enemy_shield=False,
    )
    assert fighters[0]["atk"] == 3
    assert fighters[0].get("lifesteal") is True


if __name__ == "__main__":
    test_batch12_registered()
    test_jail_801_and_tlc_440_face_4()
    test_ttn_477_forge_double_face_6()
    test_jail_892_outcast_double_face_4()
    test_edr_263_empty_board_takes_face_4()
    test_edr_263_taunt_may_summon_wolves()
    test_jail_201_hero_plus_2()
    test_tlc_522_fan_clears_1hp_taunt()
    test_tlc_522_combo_double_fan()
    test_fir_956_dark_gift_hero_plus_3()
    test_tlc_903_kindred_hero_plus_5()
    test_end_006_hero_plus_3()
    test_edr_430_not_ready_no_damage()
    test_edr_430_ready_total_20()
    test_mend_500_overflow_to_face()
    test_mend_500_no_minion_full_face()
    test_cata_525_herald_hero_plus_1()
    test_cata_525_herald_bonus_from_setaside()
    test_cata_530_herald_hero_plus_1_lifesteal()
    print("OK face_gap_batch12")
