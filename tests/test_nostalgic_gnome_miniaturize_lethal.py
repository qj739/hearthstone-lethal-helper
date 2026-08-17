#!/usr/bin/env python3
"""回归：恋旧的侏儒微缩 TOY_312t 参与清嘲斩杀。

场面：卡洛夫 6/6、伊瑟拉 5/1、欢笑姐妹 3/5；
对手 18 血，1/1 圣盾嘲讽 + 3/5 嘲讽。
手牌：恋旧侏儒(4)、梦魇(0)、神圣之拥(2)。10 费。
微缩 1/1 突袭清圣盾后，梦魇+黑暗之拥应可斩。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.rush_board import get_rush_def
from hdt_python.spell_board import resolve_playable_defn


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10, used=0, card_id="HERO_09"):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.card_id = card_id
    h.health = hp
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["HEALTH"] = hp
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(
    gs, eid, pid, atk, hp, *, card_id="", taunt=False, divine_shield=False,
    exhausted=False, cant_target_spells=False,
):
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
    m.tags["479"] = atk
    m.tags["HEALTH"] = hp
    m.tags["EXHAUSTED"] = 1 if exhausted else 0
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 2
    if taunt:
        m.tags["TAUNT"] = 1
    if divine_shield:
        m.tags["DIVINE_SHIELD"] = 1
    if cant_target_spells:
        m.tags["CANT_BE_TARGETED_BY_SPELLS"] = 1
        m.tags["CANT_BE_TARGETED_BY_HERO_POWERS"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _hand(gs, eid, pid, card_id, cost, *, cardtype="SPELL", atk=0, hp=0, rush=False):
    c = gs.get_entity(eid)
    c.cardtype = cardtype
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.atk = atk
    c.health = hp
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = cost
    c.tags["ATK"] = atk
    c.tags["HEALTH"] = hp
    if rush:
        c.tags["RUSH"] = 1
        c.tags["CARDTYPE"] = "MINION"
    return c


def test_miniaturize_gnome_registered():
    assert get_rush_def("TOY_312") is not None
    assert get_rush_def("TOY_312t") is not None
    assert resolve_playable_defn("TOY_312t") is get_rush_def("TOY_312t")
    res = get_rush_def("TOY_312").apply([], [], mult=1, enemy_shield=False, card=None)
    assert res.add_hand_pending == [("TOY_312t", 1, 0)], res.add_hand_pending
    print("OK miniaturize registration")


def test_nostalgic_gnome_miniaturize_lethal():
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 2
    gs.in_game = True
    _hero(gs, 70, 2, mana=10, used=0)
    _hero(gs, 68, 1, hp=30, dmg=12)  # 18 HP

    _minion(gs, 47, 2, 6, 6, card_id="JAIL_448")
    _minion(gs, 350, 2, 5, 1, card_id="LEG_CS3_033")
    _minion(
        gs, 311, 2, 3, 5, card_id="DREAM_01", cant_target_spells=True,
    )

    _minion(gs, 24, 1, 5, 4, card_id="JAM_007")
    _minion(gs, 360, 1, 1, 3, card_id="CORE_ONY_022")
    _minion(gs, 362, 1, 3, 5, card_id="TIME_700t", taunt=True)
    _minion(
        gs, 361, 1, 1, 1, card_id="CORE_ICC_038", taunt=True, divine_shield=True,
    )
    _minion(gs, 218, 1, 3, 4, card_id="TOY_340t1")

    _hand(gs, 43, 2, "TOY_312", 4, cardtype="MINION", atk=4, hp=4, rush=True)
    _hand(gs, 309, 2, "DREAM_05", 0)
    _hand(gs, 58, 2, "JAIL_941", 2)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    red = lc.overlay_red_prompt_ok()
    note = getattr(lc, "_overlay_spell_note", "")
    assert face >= 18, (face, note)
    assert red, (face, note)
    print("OK miniaturize lethal", face, note)


if __name__ == "__main__":
    test_miniaturize_gnome_registered()
    test_nostalgic_gnome_miniaturize_lethal()
