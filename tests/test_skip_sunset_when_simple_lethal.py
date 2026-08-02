#!/usr/bin/env python3
"""已有随从+火冲确定斩杀时，不应再模拟/展示夕阳漫射。

复盘：对手 6 血，场面可打 5，火冲 1 已够斩；手牌有 9 费夕阳漫射。
旧逻辑用夕阳抬高场攻并跑 MC，步骤面板也会写上夕阳漫射。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def _hero(gs, eid, pid, *, hp=30, dmg=0, mana=10, used=0, card_id="HERO_08"):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.card_id = card_id
    h.health = hp
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    h.tags["ATK"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _hero_power(gs, eid, pid, card_id="HERO_08bp", cost=2):
    p = gs.get_entity(eid)
    p.cardtype = "HERO_POWER"
    p.controller = pid
    p.zone = "PLAY"
    p.card_id = card_id
    p.cost = cost
    p.tags["ZONE"] = "PLAY"
    p.tags["COST"] = cost
    p.tags["EXHAUSTED"] = 0
    return p


def _minion(gs, eid, pid, atk, hp, *, card_id="M", pos=1):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.zone_pos = pos
    m.tags["ZONE"] = "PLAY"
    m.tags["ZONE_POSITION"] = pos
    m.tags["ATK"] = atk
    m.tags["479"] = atk
    m.tags["HEALTH"] = hp
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    return m


def _hand_spell(gs, eid, pid, card_id, cost):
    c = gs.get_entity(eid)
    c.cardtype = "SPELL"
    c.controller = pid
    c.zone = "HAND"
    c.card_id = card_id
    c.cost = cost
    c.tags["ZONE"] = "HAND"
    c.tags["COST"] = cost
    return c


def test_skip_sunset_when_board_plus_fireblast_lethal():
    """对手 6 血：场面 5 + 火冲 1 已斩，勿推荐夕阳漫射。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0, card_id="HERO_08")
    _hero(gs, 2, 2, hp=30, dmg=24, card_id="HERO_10")  # 6 血
    _hero_power(gs, 3, 1, "HERO_08bp", 2)
    _minion(gs, 10, 1, 2, 5, card_id="REV_000", pos=1)
    _minion(gs, 11, 1, 3, 1, card_id="TOY_520", pos=2)
    _hand_spell(gs, 40, 1, "WW_427", 9)  # 夕阳漫射

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    combo = "\n".join(lc.overlay_combo_display_lines())
    uses_random = getattr(lc, "_overlay_uses_random", False)
    seq = getattr(lc, "_overlay_best_seq", None) or []
    seq_names = [getattr(d, "name", str(d)) for d, *_ in seq]

    assert face >= 6, (face, note, combo)
    assert face == 6, f"不应被夕阳抬高: face={face} note={note}"
    assert "夕阳" not in note, note
    assert "夕阳" not in combo, combo
    assert not any("夕阳" in n for n in seq_names), seq_names
    assert not uses_random, (uses_random, note, combo)
    assert "火焰冲击" in note or "火焰冲击" in combo, (note, combo)
    print("OK board+fireblast lethal skips sunset", face, note)


def test_skip_sunset_when_fireblast_alone_lethal():
    """对手 1 血：单火冲已斩，勿模拟夕阳。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0, card_id="HERO_08")
    _hero(gs, 2, 2, hp=30, dmg=29, card_id="HERO_10")  # 1 血
    _hero_power(gs, 3, 1, "HERO_08bp", 2)
    _minion(gs, 10, 1, 2, 5, card_id="REV_000", pos=1)
    _minion(gs, 11, 1, 3, 1, card_id="TOY_520", pos=2)
    _hand_spell(gs, 40, 1, "WW_427", 9)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    note = lc.overlay_spell_note()
    combo = "\n".join(lc.overlay_combo_display_lines())
    uses_random = getattr(lc, "_overlay_uses_random", False)

    assert face >= 1, (face, note)
    assert "夕阳" not in note, note
    assert "夕阳" not in combo, combo
    assert not uses_random, (uses_random, note)
    print("OK fireblast-alone lethal skips sunset", face, note)


if __name__ == "__main__":
    test_skip_sunset_when_board_plus_fireblast_lethal()
    test_skip_sunset_when_fireblast_alone_lethal()
    print("ALL PASS")
