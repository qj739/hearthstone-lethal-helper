#!/usr/bin/env python3
"""棘嗣幼龙 + 幽魂不散：buff 抬高溢出攻须能搜到斩杀。

复现 2026-10-12：对手 11 血，场上 2 血随从，棘嗣 12 攻溢出仅 10；
打出 CAP_801 给棘嗣 +2 → 14 溢 12，应识别斩杀。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.end_turn_board import (
    _attack_random_minion_overflow_face,
    end_turn_face_damage,
    sim_end_turn_entities_from_fighters,
)
from hdt_python.most_wanted_p0 import _apply_haunt, _pick_haunt_target
from hdt_python.power_parser import GameState
from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence


def test_overflow_12_atk_into_2hp_is_10():
    enemy = [{"kind": "minion", "health": 2, "shield": False, "taunt": False}]
    assert _attack_random_minion_overflow_face(12, enemy, False) == 10
    assert _attack_random_minion_overflow_face(14, enemy, False) == 12


def test_haunt_prefers_hold_et_hatchling():
    fighters = [
        {
            "kind": "minion", "entity_id": 1, "card_id": "TIME_703",
            "atk": 5, "health": 1, "attacks_left": 1, "can_face": True,
        },
        {
            "kind": "minion", "entity_id": 174, "card_id": "EDR_453",
            "atk": 12, "health": 3, "attacks_left": 0, "can_face": False,
        },
    ]
    picked = _pick_haunt_target(fighters)
    assert picked is not None
    assert picked[2]["card_id"] == "EDR_453"


def test_haunt_buff_raises_et_overflow_via_fighters():
    """CAP_801 后 fighters 上棘嗣攻 14，回合结束乐观溢出 12。"""
    gs = GameState()
    gs.local_player_id = 2
    # 场上实体仍为 12 攻；buff 只写在 fighters
    hatch = gs.get_entity(174)
    hatch.cardtype = "MINION"
    hatch.controller = 2
    hatch.zone = "PLAY"
    hatch.card_id = "EDR_453"
    hatch.atk = 12
    hatch.health = 3
    hatch.damage = 0
    hatch.tags.update({
        "ZONE": "PLAY", "ATK": 12, "HEALTH": 7, "DAMAGE": 4,
        "CONTROLLER": 2,
    })

    fighters = [{
        "kind": "minion", "entity_id": 174, "card_id": "EDR_453",
        "atk": 12, "health": 3, "attacks_left": 0, "can_face": False,
    }]
    defn = get_board_spell_def("CAP_801")
    assert defn is not None
    card = gs.get_entity(44)
    card.cardtype = "SPELL"
    card.card_id = "CAP_801"
    card.zone = "HAND"
    enemy = [{
        "kind": "minion", "entity_id": 161, "card_id": "TIME_103",
        "health": 2, "shield": False, "taunt": False,
    }]
    apply_spell_sequence(
        enemy, fighters, [(defn, 1, card)],
        enemy_shield=False, gs=gs, player_id=2,
    )
    assert fighters[0]["atk"] == 14

    extra = sim_end_turn_entities_from_fighters(fighters)
    face, notes = end_turn_face_damage(
        gs.get_board(2), enemy, False,
        game_state=gs, player_id=2,
        extra_board_entities=extra,
    )
    assert face == 12, (face, notes)
    assert any("棘嗣" in n or "12" in n for n in notes)


def test_apply_haunt_buffs_hatchling_atk():
    fighters = [{
        "kind": "minion", "entity_id": 174, "card_id": "EDR_453",
        "atk": 12, "health": 3, "attacks_left": 0, "can_face": False,
    }]
    _apply_haunt([], fighters, mult=1, enemy_shield=False)
    assert fighters[0]["atk"] == 14
    assert fighters[0].get("reborn") is True
    assert fighters[0].get("taunt") is True


if __name__ == "__main__":
    test_overflow_12_atk_into_2hp_is_10()
    test_haunt_prefers_hold_et_hatchling()
    test_haunt_buff_raises_et_overflow_via_fighters()
    test_apply_haunt_buffs_hatchling_atk()
    print("OK edr453_haunt")
