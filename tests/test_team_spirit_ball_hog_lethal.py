#!/usr/bin/env python3
"""回归：休眠敌不挡球霸打脸；团队之灵英雄 ATK 计入武器挥击；手牌打出 +2。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import (
    count_board_team_spirit,
    hero_weapon_strike_damage,
)
from hdt_python.battlecry_board import get_battlecry_def


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10, atk=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = hp
    h.damage = dmg
    h.atk = atk
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    if atk:
        h.tags["ATK"] = atk
        h.tags["479"] = atk
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, card_id="M", dormant=False, turns=1):
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
        "NUM_ATTACKS_THIS_TURN": 0, "EXHAUSTED": 0 if turns else 1,
        "NUM_TURNS_IN_PLAY": turns,
    })
    if dormant:
        m.tags["DORMANT"] = 1
        m.tags["UNTOUCHABLE"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    return m


def _weapon(gs, eid, pid, atk=4, dur=2):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "PLAY"
    w.card_id = "ETC_405"
    w.atk = atk
    w.health = dur
    w.durability = dur
    w.tags.update({"ZONE": "PLAY", "ATK": atk, "HEALTH": dur, "DURABILITY": dur})
    gs.weapon_entity_ids[pid] = eid
    return w


def _hand_bc(gs, eid, pid, card_id, cost):
    c = gs.get_entity(eid)
    c.cardtype = "MINION"
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = cost


def test_ball_hog_skips_dormant_hits_face():
    """对手低血休眠随从 + 14 血英雄：球霸战吼应打脸 3，不算休眠。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, hp=30, dmg=16)  # 14 血
    _minion(gs, 20, 2, 1, 3, card_id="JAIL_912", dormant=True)
    _hand_bc(gs, 30, 1, "TOY_642", 4)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 3, f"Ball Hog should face for 3 vs dormant board; got {face}"
    print("OK ball hog skips dormant", face)


def test_team_spirit_hero_atk_counts_with_weapon():
    """武器 4 + 英雄 ATK 6（团队之灵）：挥击应按 6 计。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 1, 1, atk=6)
    weapon = _weapon(gs, 40, 1, atk=4, dur=2)
    assert hero_weapon_strike_damage(hero, weapon) == 6

    _hero(gs, 2, 2, hp=30, dmg=20)
    _minion(gs, 10, 1, 3, 3, card_id="A")
    _minion(gs, 11, 1, 3, 3, card_id="B")
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face == 12, f"expected 3+3+6=12, got {face}"
    pure, minion, weapon, spell, hp = lc.overlay_board_breakdown()
    assert minion == 6 and weapon == 6, f"breakdown minion/weapon {minion}/{weapon}"
    print("OK team spirit weapon strike", face)


def test_team_spirit_aura_missing_from_hero_atk():
    """场上有团队之灵但英雄 ATK 仍=武器攻：应补 +2。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    hero = _hero(gs, 1, 1, atk=4)  # 仅同步了武器攻，漏光环
    weapon = _weapon(gs, 40, 1, atk=4, dur=1)
    _minion(gs, 12, 1, 0, 3, card_id="TOY_028", turns=1)
    _hero(gs, 2, 2, hp=30, dmg=24)  # 6 血

    assert count_board_team_spirit(gs, 1) == 1
    assert hero_weapon_strike_damage(hero, weapon, team_spirit_count=1) == 6

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 6, f"expected weapon+spirit >=6, got {face}"
    _, _, weapon_f, _, _ = lc.overlay_board_breakdown()
    assert weapon_f >= 6, f"weapon face should be 6, got {weapon_f}"
    print("OK team spirit fills missing hero ATK", face, weapon_f)


def test_team_spirit_from_hand():
    """手牌打出团队之灵：空场+武器应计 +2 英雄攻。"""
    assert get_battlecry_def("TOY_028") is not None
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, atk=4)
    _weapon(gs, 40, 1, atk=4, dur=1)
    _hero(gs, 2, 2, hp=30, dmg=24)  # 6 血
    _hand_bc(gs, 30, 1, "TOY_028", 2)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    buff = lc.overlay_hero_buff_face()
    assert face >= 6, f"expected >=6 (武4+英2), got {face} buff={buff}"
    assert buff >= 2 or face >= 6, (face, buff)
    print("OK team spirit from hand", face, buff)


def test_final_lethal_board_approx():
    """近似终局：随从6 + 英雄6 + 球霸战吼3 >= 14。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, atk=6)
    _hero(gs, 2, 2, hp=30, dmg=16)
    _weapon(gs, 40, 1, atk=4, dur=2)
    _minion(gs, 10, 1, 3, 3, card_id="TOY_642")
    _minion(gs, 11, 1, 3, 6, card_id="ETC_400")
    _minion(gs, 12, 1, 0, 3, card_id="TOY_028", turns=0)
    _minion(gs, 20, 2, 1, 3, card_id="JAIL_912", dormant=True)
    _hand_bc(gs, 30, 1, "TOY_642", 4)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, _, lethal = lc.calculate_lethal_potential()
    assert face >= 14, f"expected lethal face>=14, got {face}"
    assert lethal, f"should detect lethal, face={face}"
    print("OK approx final lethal", face, lethal)


if __name__ == "__main__":
    test_ball_hog_skips_dormant_hits_face()
    test_team_spirit_hero_atk_counts_with_weapon()
    test_team_spirit_aura_missing_from_hero_atk()
    test_team_spirit_from_hand()
    test_final_lethal_board_approx()
    print("all passed")
