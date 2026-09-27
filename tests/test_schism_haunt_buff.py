#!/usr/bin/env python3
"""幽魂不散 / 教派分歧：友方加攻，裂变编号不能当成伤害。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import Entity
import hdt_python.most_wanted_p0  # noqa: F401  注册幽魂不散
from hdt_python.spell_board import get_board_spell_def, spell_script_damage


def _fighter(atk: int, eid: int = 1) -> dict:
    return {
        "kind": "minion",
        "entity_id": eid,
        "card_id": "TIME_100",
        "atk": atk,
        "health": 5,
        "attacks_left": 1,
        "can_face": True,
    }


def test_schism_script_dbf_is_not_damage():
    card = Entity(entity_id=1, card_id="CATA_306")
    card.tags["TAG_SCRIPT_DATA_NUM_1"] = 122876
    assert spell_script_damage(card) == 0


def test_haunt_and_schism_stack_attack():
    haunt = get_board_spell_def("CAP_801")
    schism = get_board_spell_def("CATA_306")
    buff = get_board_spell_def("CATA_306t1")
    copy = get_board_spell_def("CATA_306t2")
    assert haunt and schism and buff and copy

    fighters = [_fighter(2)]
    haunt.apply([], fighters, mult=1, enemy_shield=False)
    schism.apply([], fighters, mult=1, enemy_shield=False)
    assert fighters[0]["atk"] == 6, fighters
    copies = [f for f in fighters if f.get("entity_id") != 1]
    assert len(copies) == 1
    assert int(copies[0].get("attacks_left", 0) or 0) == 0

    only = [_fighter(2, eid=2)]
    buff.apply([], only, mult=1, enemy_shield=False)
    assert only[0]["atk"] == 4
    assert len(only) == 1
    print("OK haunt+schism buff")


if __name__ == "__main__":
    test_schism_script_dbf_is_not_damage()
    test_haunt_and_schism_stack_attack()
