# tests/test_requiem_dino417.py — 安魂仪式 DINO_417

from __future__ import annotations

from copy import deepcopy

from hdt_python.combat_sim import project_board_face_after_spell
from hdt_python.spell_board import BOARD_CLEAR_SPELLS, get_board_spell_def


def test_requiem_registered():
    defn = get_board_spell_def("DINO_417")
    assert defn is not None
    assert defn.name == "安魂仪式"
    assert "DINO_417" in BOARD_CLEAR_SPELLS


def test_requiem_buffs_and_wakes_tired_minions():
    defn = get_board_spell_def("DINO_417")
    fighters = [
        {
            "kind": "minion", "entity_id": 1, "card_id": "TLC_468t1",
            "atk": 2, "health": 2, "attacks_left": 0, "can_face": False,
            "poisonous": True,
        },
        {
            "kind": "minion", "entity_id": 2, "card_id": "TLC_468",
            "atk": 1, "health": 1, "attacks_left": 1, "can_face": True,
        },
    ]
    taunts = [
        {"kind": "minion", "health": 5, "atk": 1, "shield": False, "taunt": True},
        {"kind": "minion", "health": 5, "atk": 1, "shield": False, "taunt": True},
    ]
    defn.apply(taunts, fighters, mult=1, enemy_shield=False)
    tired = next(f for f in fighters if f["entity_id"] == 1)
    ready = next(f for f in fighters if f["entity_id"] == 2)
    assert tired["atk"] == 3
    assert tired["attacks_left"] == 1
    assert tired["can_face"] is False  # 突袭唤醒：只能打怪
    assert tired.get("rush") is True
    assert ready["atk"] == 2
    assert ready["can_face"] is True  # 原本可打脸则保留


def test_requiem_enables_poison_clear_then_face_lethal():
    """复现本局：疲劳剧毒清嘲讽后，可打脸随从斩杀低血。"""
    defn = get_board_spell_def("DINO_417")
    fighters = [
        {
            "kind": "minion", "entity_id": 1, "card_id": "TLC_468t1",
            "atk": 2, "health": 2, "attacks_left": 0, "can_face": False,
            "poisonous": True,
        },
        {
            "kind": "minion", "entity_id": 2, "card_id": "TLC_468t1",
            "atk": 2, "health": 2, "attacks_left": 0, "can_face": False,
            "poisonous": True,
        },
        {
            "kind": "minion", "entity_id": 3, "card_id": "TLC_468t1",
            "atk": 2, "health": 2, "attacks_left": 1, "can_face": True,
            "poisonous": True,
        },
        {
            "kind": "minion", "entity_id": 4, "card_id": "TLC_468",
            "atk": 1, "health": 1, "attacks_left": 1, "can_face": True,
        },
    ]
    taunts = [
        {"kind": "minion", "health": 3, "atk": 1, "shield": False, "taunt": True},
        {"kind": "minion", "health": 3, "atk": 1, "shield": False, "taunt": True},
    ]
    fs = deepcopy(fighters)
    ts = deepcopy(taunts)
    defn.apply(ts, fs, mult=1, enemy_shield=False)
    face = project_board_face_after_spell(ts, fs, False)
    # 剧毒突袭清两嘲讽后，打脸约 3+2（各 +1）= 5
    assert face >= 5, face
