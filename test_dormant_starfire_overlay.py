#!/usr/bin/env python3
"""休眠随从不计场攻；手牌星火术应计入法术分项。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_spell_board import _hero, _minion, _hand_spell
from hdt_python.power_parser import GameState, Entity
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import is_dormant, build_board_card


def test_dormant_enchant_marks_host():
    gs = GameState()
    host = gs.get_entity(10)
    host.cardtype = "MINION"
    host.card_id = "CATA_201"
    host.zone = "PLAY"
    host.tags["ZONE"] = "PLAY"
    host.atk = 4
    host.tags["ATK"] = 4
    host.tags["479"] = 4

    enc = gs.get_entity(11)
    enc.cardtype = "ENCHANTMENT"
    enc.zone = "PLAY"
    enc.tags["ATTACHED"] = 10
    enc.tags["DORMANT_AWAKEN_CONDITION_ENCHANT"] = 1

    assert is_dormant(host, gs)
    view = build_board_card(host, True, gs)
    assert view.attack == 0
    assert not view.can_attack_hero


def test_dormant_dragon_starfire_overlay():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=7)
    _hero(gs, 2, 2)

    dragon = _minion(gs, 10, 1, 4, 12, card_id="CATA_201")
    dragon.tags["DORMANT"] = 1
    dragon.tags["479"] = 4

    star = _hand_spell(gs, 30, 1, "EX1_173", 6)
    star.tags["CURRENT_SPELLPOWER_BASE"] = 1

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    pure, minion, weapon, spell, hp = lc.overlay_board_breakdown()
    assert minion == 0, f"dormant dragon must not count as minion face, got {minion}"
    assert spell == 6, f"starfire with +1 spell power should be 6, got {spell}"
    assert total == 6
    assert "星火" in lc.overlay_spell_note()


if __name__ == "__main__":
    test_dormant_enchant_marks_host()
    test_dormant_dragon_starfire_overlay()
    print("all passed")
