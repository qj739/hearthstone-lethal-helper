#!/usr/bin/env python3
"""虫害侵扰斩杀：须校验剩余法力，且 combo 与场攻分项一致。"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from test_spell_board import _hero, _hand_spell
from hdt_python.power_parser import PowerLogParser, GameState, Entity
from hdt_python.lethal_checker import LethalChecker
from hdt_python.overlay_combo_format import overlay_combo_mana_affordable


def _weapon_setup(gs: GameState, player_id: int = 1) -> None:
    w = Entity(
        entity_id=7, card_id="EDR_842", controller=player_id, zone="PLAY",
        cardtype="WEAPON", cost=4, atk=2, health=3,
    )
    w.tags.update({
        "CONTROLLER": player_id, "ZONE": "PLAY", "ATK": 2, "HEALTH": 3,
        "EXHAUSTED": 0, "NUM_ATTACKS_THIS_TURN": 0,
    })
    gs.entities[7] = w
    hero = gs.get_hero(player_id)
    hero.tags["479"] = 2
    hero.tags["ATK"] = 2
    hero.tags["EXHAUSTED"] = 0
    hero.tags["NUM_ATTACKS_THIS_TURN"] = 0


def _demon_claw_setup(gs: GameState, player_id: int = 1) -> None:
    hp = Entity(
        entity_id=69, card_id="HERO_10bp", controller=player_id, zone="PLAY",
        cardtype="HERO_POWER", cost=1,
    )
    hp.tags.update({"CONTROLLER": player_id, "ZONE": "PLAY", "COST": 1, "EXHAUSTED": 0})
    gs.entities[69] = hp
    gs.get_hero(player_id).tags["HERO_POWER"] = 69


def test_no_lethal_infestation_only_two_mana_vs_seven_hp():
    """剩 2 费：虫害侵扰(4 直伤)+武器(2)=6，不够 7 血。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=7, used=5)
    opp = _hero(gs, 2, 2)
    opp.health = 7
    opp.tags["HEALTH"] = 7
    _weapon_setup(gs)
    _hand_spell(gs, 10, 1, "TLC_902", 2)

    lc = LethalChecker(gs)
    _, _, has = lc.calculate_lethal()
    assert has is False
    assert getattr(lc, "_overlay_total_face", 0) < 7


def test_no_lethal_after_all_mana_spent_replay_91645():
    """Power.log 倒数第二回合末：0 费剩，虫害侵扰不可打，不得报斩杀。"""
    log = Path(
        os.environ.get(
            "HS_POWER_LOG",
            r"C:\Program Files (x86)\Hearthstone\Logs\Hearthstone_2026_06_28_17_05_13\Power.log",
        )
    )
    if not log.is_file():
        return
    os.environ.setdefault("HS_PLAYER_NAME", "鸡哥在线#5240")
    with open(log, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    for i in range(81293, 91645):
        p.process_line(lines[i])
    lc = LethalChecker(gs)
    _, _, has = lc.calculate_lethal()
    assert lc._available_mana(1) == 0
    assert has is False
    combo = " ".join(lc.overlay_combo_display_lines())
    assert "虫害侵扰" not in combo


def test_lethal_penultimate_turn_replay_91587():
    """Power.log L91587：3 费剩，技能+虫害侵扰+武器可杀 7 血。"""
    log = Path(
        os.environ.get(
            "HS_POWER_LOG",
            r"C:\Program Files (x86)\Hearthstone\Logs\Hearthstone_2026_06_28_17_05_13\Power.log",
        )
    )
    if not log.is_file():
        return
    os.environ.setdefault("HS_PLAYER_NAME", "鸡哥在线#5240")
    with open(log, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    for i in range(81293, 91587):
        p.process_line(lines[i])
    lc = LethalChecker(gs)
    _, _, has = lc.calculate_lethal()
    assert lc._available_mana(1) == 3
    assert lc.get_opponent_effective_hp() == 7
    assert has is True
    assert getattr(lc, "_overlay_mana_spent", 0) <= 3
    assert overlay_combo_mana_affordable(lc)
    combo = lc.overlay_combo_display_lines()
    assert any("虫害侵扰" in line for line in combo)
    assert any("武器" in line for line in combo)


if __name__ == "__main__":
    test_no_lethal_infestation_only_two_mana_vs_seven_hp()
    test_no_lethal_after_all_mana_spent_replay_91645()
    test_lethal_penultimate_turn_replay_91587()
    print("all passed")
