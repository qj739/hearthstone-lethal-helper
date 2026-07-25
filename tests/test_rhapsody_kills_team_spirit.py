#!/usr/bin/env python3
"""回归：动情狂想曲 AOE 杀死友方团队之灵后，英雄攻须扣回光环 +2。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence


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


def _minion(gs, eid, pid, atk, hp, *, card_id="M", turns=1):
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
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
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
    c.tags["ZONE_POSITION"] = 1
    return c


def _hero_power(gs, eid, pid, card_id, cost=1, *, exhausted=False):
    p = gs.get_entity(eid)
    p.cardtype = "HERO_POWER"
    p.controller = pid
    p.zone = "PLAY"
    p.card_id = card_id
    p.cost = cost
    p.tags["ZONE"] = "PLAY"
    p.tags["COST"] = cost
    if exhausted:
        p.tags["EXHAUSTED"] = 1
    return p


def test_rhapsody_aoe_revokes_team_spirit_aura():
    """
    场上 0/3 团队之灵 + 5/6 随从；英雄 ATK=2（光环）。
    动情狂想曲：全体 3 伤（杀光环）+ 英雄本回合 +5。
    斩杀伤害应为 5（随从）+5（狂想曲），不得再含团队之灵 +2。
    """
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, atk=2)
    _hero(gs, 2, 2, hp=30, dmg=12)  # 18 血
    _minion(gs, 10, 1, 0, 3, card_id="TOY_028", turns=1)
    _minion(gs, 11, 1, 5, 6, card_id="TOY_526", turns=1)
    card = _hand_spell(gs, 30, 1, "JAM_018t3", 5)

    defn = get_board_spell_def("JAM_018t3")
    assert defn is not None

    lc = LethalChecker(gs)
    board_view = gs.get_overlay_board(1)
    fighters = lc._build_fighters(board_view, 1)
    assert any(
        f.get("card_id") == "TOY_028" and f.get("health", 0) > 0 for f in fighters
    ), "0 攻团队之灵须进入 fighters，否则 AOE 打不到"
    hero_before = sum(
        int(f.get("atk", 0) or 0)
        for f in fighters
        if f.get("kind") in ("hero", "weapon")
    )
    assert hero_before == 2
    assert any(int(f.get("_team_spirit_bonus", 0) or 0) for f in fighters)

    taunts = lc._build_enemy_minion_states(1)
    apply_spell_sequence(
        taunts,
        fighters,
        [(defn, 5, card)],
        enemy_shield=False,
        gs=gs,
        player_id=1,
    )

    spirit = next(f for f in fighters if f.get("card_id") == "TOY_028")
    assert spirit.get("health", 0) <= 0, "狂想曲 3 伤应杀死 0/3 团队之灵"

    hero_after = sum(
        int(f.get("atk", 0) or 0)
        for f in fighters
        if f.get("kind") in ("hero", "weapon") and int(f.get("atk", 0) or 0) > 0
    )
    # 光环 +2 撤销后只剩狂想曲 +5
    assert hero_after == 5, (
        f"expected hero atk 5 after spirit dies, got {hero_after}; "
        f"fighters={[ {k: f.get(k) for k in ('kind','card_id','atk','health','_team_spirit_bonus')} for f in fighters ]}"
    )
    assert not any(
        int(f.get("_team_spirit_bonus", 0) or 0) > 0 for f in fighters
    )

    face = lc._fighters_face_hits(fighters)
    total = sum(face)
    # 随从 5 + 英雄 5 = 10；对手 18，不应斩杀
    assert total == 10, f"expected face 10, got {total} hits={face}"
    print("OK rhapsody kills team spirit aura", total)


def test_claw_plus_rhapsody_not_false_lethal():
    """恶魔之爪 +1 + 狂想曲后杀灵：英6+场5=11 < 18，不得报斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, atk=2)
    _hero(gs, 2, 2, hp=30, dmg=12)  # 18 血
    _minion(gs, 10, 1, 0, 3, card_id="TOY_028", turns=1)
    _minion(gs, 11, 1, 5, 6, card_id="TOY_526", turns=1)
    _hand_spell(gs, 30, 1, "JAM_018t3", 5)
    _hero_power(gs, 50, 1, "HERO_10bp", 1)

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    buff = lc.overlay_hero_buff_face()
    _, _, lethal = lc.calculate_lethal_potential()
    # 假斩杀曾算 13（含灵 +2）；正确为场5+爪1+狂想曲5=11
    assert face <= 11, f"expected face<=11 after spirit dies, got {face} buff={buff}"
    assert not lethal, f"should NOT lethal vs 18, face={face} buff={buff}"
    print("OK no false lethal", face, buff, lethal)


if __name__ == "__main__":
    test_rhapsody_aoe_revokes_team_spirit_aura()
    test_claw_plus_rhapsody_not_false_lethal()
