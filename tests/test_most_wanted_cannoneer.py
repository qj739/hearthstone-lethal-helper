# tests/test_most_wanted_cannoneer.py — CAP_ 火炮手体系

from __future__ import annotations

from hdt_python import spell_board  # noqa: F401
from hdt_python.battlecry_board import get_battlecry_def
from hdt_python.end_turn_board import end_turn_face_from_fighters
from hdt_python.most_wanted_p0 import register_most_wanted
from hdt_python.spell_board import BOARD_CLEAR_SPELLS, SpellApplyResult
from hdt_python.weapon_board import get_weapon_def
from hdt_python.weapon_p0 import after_hero_weapon_attack

register_most_wanted()


def test_cannoneer_end_turn_face():
    fighters = [
        {"kind": "minion", "card_id": "CAP_107t", "atk": 1, "health": 1},
        {"kind": "minion", "card_id": "CAP_107t", "atk": 1, "health": 1},
    ]
    assert end_turn_face_from_fighters(fighters, [], False) == 2


def test_crowley_doubles_cannoneer_shots():
    fighters = [
        {"kind": "minion", "card_id": "CAP_107t", "atk": 1, "health": 1},
        {"kind": "minion", "card_id": "CAP_107t", "atk": 1, "health": 1},
        {"kind": "minion", "card_id": "CAP_106", "atk": 4, "health": 5},
    ]
    assert end_turn_face_from_fighters(fighters, [], False) == 4


def test_crowley_battlecry_summons_cannoneers():
    defn = get_battlecry_def("CAP_106")
    assert defn is not None
    fighters: list = []
    res = defn.apply([], fighters, mult=1, enemy_shield=False)
    assert isinstance(res, SpellApplyResult)
    cans = [f for f in fighters if f.get("card_id") == "CAP_107t"]
    assert len(cans) == 2
    assert any(f.get("card_id") == "CAP_106" for f in fighters)
    assert end_turn_face_from_fighters(fighters, [], False) == 4


def test_land_ho_summons_cannoneers():
    defn = BOARD_CLEAR_SPELLS["CAP_102"]
    fighters: list = []
    defn.apply([], fighters, mult=1, enemy_shield=False)
    assert sum(1 for f in fighters if f.get("card_id") == "CAP_107t") == 2
    assert end_turn_face_from_fighters(fighters, [], False) == 2


def test_hand_cannon_fires_cannoneers_to_face():
    defn = get_weapon_def("CAP_103")
    assert defn is not None
    fighters: list = [
        {"kind": "minion", "card_id": "CAP_107t", "atk": 1, "health": 1},
        {"kind": "minion", "card_id": "CAP_107t", "atk": 1, "health": 1},
    ]
    defn.apply([], fighters, mult=1, enemy_shield=False)
    weapon = next(f for f in fighters if f.get("kind") == "weapon")
    assert weapon.get("cannoneers_fire")
    before_face = sum(
        int(f.get("atk", 0) or 0)
        for f in fighters
        if f.get("kind") == "hero" and f.get("can_face")
    )
    after_hero_weapon_attack(
        weapon, {"kind": "hero"}, [], fighters, enemy_shield=False,
    )
    after_face = sum(
        int(f.get("atk", 0) or 0) * int(f.get("attacks_left", 0) or 0)
        for f in fighters
        if f.get("kind") == "hero" and f.get("can_face")
    )
    assert after_face - before_face == 2


def test_tricks_of_trade_base_damage():
    defn = BOARD_CLEAR_SPELLS["CAP_006"]
    res = defn.apply([], [], mult=1, enemy_shield=False, card=None)
    assert res.direct_face_damage == 1


def test_cards_json_has_cap_collectibles():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "json" / "cards.json").read_text(encoding="utf-8"))
    caps = [
        c for c in data
        if str(c.get("id", "")).startswith("CAP_") and c.get("collectible")
    ]
    assert len(caps) == 29
