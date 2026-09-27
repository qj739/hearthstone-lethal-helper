#!/usr/bin/env python3
"""吸血鬼之吻 + 饮血术刷新双英雄技能斩杀。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.hero_power_board import (
    get_hero_power_def,
    list_usable_hero_powers,
    apply_all_usable_hero_powers,
    hero_power_cost,
)
from hdt_python.spell_board import get_board_spell_def, SpellApplyResult


def _hero(gs, eid, pid, *, mana=10, used=0, corpses=20, dmg=0, health=30):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = health
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["CORPSES"] = corpses
    h.tags["EXHAUSTED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="m"):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags.update({
        "ZONE": "PLAY", "ATK": atk, "479": atk, "HEALTH": hp,
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0, "NUM_TURNS_IN_PLAY": 1,
    })
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hp(gs, eid, pid, card_id, *, cost=2, corpse=False):
    e = gs.get_entity(eid)
    e.cardtype = "HERO_POWER"
    e.controller = pid
    e.zone = "PLAY"
    e.card_id = card_id
    e.cost = cost
    e.tags.update({
        "ZONE": "PLAY", "COST": cost, "EXHAUSTED": 0,
        "HEROPOWER_ACTIVATIONS_THIS_TURN": 0, "CARDTYPE": "HERO_POWER",
    })
    if corpse:
        e.tags["CORPSE_SPENDER"] = 1
        e.tags["CARD_ALTERNATE_COST"] = 3
    return e


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags.update({"ZONE": "HAND", "COST": cost})
    return s


def test_kiss_registered():
    assert get_hero_power_def("JAIL_446hp") is not None
    assert get_hero_power_def("JAIL_446hp").name == "吸血鬼之吻"


def test_drink_blood_refreshes():
    defn = get_board_spell_def("JAIL_441")
    assert defn is not None
    taunts = [{"atk": 5, "health": 1, "damage": 0, "entity_id": 1}]
    res = defn.apply(taunts, [], mult=1, enemy_shield=False)
    assert res.refresh_hero_powers == 1


def test_corpse_kiss_mana_zero():
    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 10, 1, corpses=5)
    kiss = _hp(gs, 20, 1, "JAIL_446hp", cost=3, corpse=True)
    assert hero_power_cost(kiss, gs, 1) == 0
    kiss2 = _hp(gs, 21, 1, "JAIL_446hp", cost=3, corpse=True)
    # 残骸不够
    h = gs.get_hero(1)
    h.tags["CORPSES"] = 2
    assert hero_power_cost(kiss2, gs, 1) == 999


def test_dual_hp_drink_blood_lethal():
    """对手 14 血；场面 1+2+5；吻×2 + 食尸鬼×2 + 饮血术刷新可斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 64, 1, mana=10, corpses=20)
    opp = _hero(gs, 66, 2, dmg=16, health=30)  # 14 hp
    _minion(gs, 58, 1, 1, 3, card_id="JAIL_703")
    _minion(gs, 268, 1, 2, 1, card_id="TIME_017")
    _minion(gs, 270, 1, 5, 4, card_id="CATA_615")
    _minion(gs, 262, 2, 5, 1, card_id="CORE_CS3_005")  # 饮血术击杀目标
    _hp(gs, 67, 1, "HERO_11bp", cost=2)
    _hp(gs, 196, 1, "JAIL_446hp", cost=3, corpse=True)
    _hand_spell(gs, 43, 1, "JAIL_441", 2)

    rows = list_usable_hero_powers(gs, 1, 10)
    assert len(rows) >= 2
    assert any(e.card_id == "JAIL_446hp" for e, *_ in rows)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    total, _, lethal = lc.calculate_lethal_potential()
    assert face >= 14 or lethal, (
        f"expected lethal face>={14}, got face={face} total={total} lethal={lethal} "
        f"note={lc.overlay_spell_note()!r}"
    )
    print("OK dual hp drink blood", face, total, lethal, lc.overlay_spell_note())


if __name__ == "__main__":
    test_kiss_registered()
    test_drink_blood_refreshes()
    test_corpse_kiss_mana_zero()
    test_dual_hp_drink_blood_lethal()
    print("all ok")
