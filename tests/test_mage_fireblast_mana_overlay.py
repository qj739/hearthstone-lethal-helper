#!/usr/bin/env python3
"""回归：10 费双火球+冰冻之触+场攻 7 时，法术占满法力，不得再叠火焰冲击显示 23 伤。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from test_spell_board import _hero, _minion, _hand_spell, _hero_power
from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker


def _mage_fireball_board_setup(*, active_player: int) -> GameState:
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = active_player
    _hero(gs, 1, 1, mana=10, used=0)
    opp = _hero(gs, 2, 2)
    opp.health = 23
    opp.tags["HEALTH"] = 23
    deck_card = gs.get_entity(99)
    deck_card.controller = 2
    deck_card.zone = "DECK"
    deck_card.tags["ZONE"] = "DECK"
    deck_card.tags["CONTROLLER"] = 2
    for eid, atk, hp, cid in (
        (10, 3, 6, "CS2_033"),
        (11, 4, 4, "ETC_088"),
    ):
        m = _minion(gs, eid, 1, atk, hp, card_id=cid)
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs, 30, 1, "CS2_029", 4)
    _hand_spell(gs, 31, 1, "CS2_029", 4)
    _hand_spell(gs, 32, 1, "REV_601", 2)
    return gs


def test_opponent_turn_preview_no_unaffordable_fireblast():
    """对方回合下回合预览：随7+法15=22，不能额外+火冲1 凑成 23。"""
    gs = _mage_fireball_board_setup(active_player=2)
    _hero_power(gs, 50, 1, "HERO_08bp", 2, exhausted=True)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    pure, board, weapon, spell, hp = lc.overlay_board_breakdown()

    assert total == 22, (total, pure, board, weapon, spell, hp, lc.overlay_spell_note())
    assert board == 7 and spell == 15 and hp == 0
    assert getattr(lc, "_overlay_mana_spent", 99) == 10
    _, _, has_lethal = lc.calculate_lethal_potential()
    assert has_lethal is False


def test_local_turn_no_unaffordable_fireblast():
    """我方 10 费回合：同样不得把火冲叠进展示场攻。"""
    gs = _mage_fireball_board_setup(active_player=1)
    _hero_power(gs, 50, 1, "HERO_08bp", 2)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    _, board, _, spell, hp = lc.overlay_board_breakdown()

    assert total == 22, (total, board, spell, hp, lc.overlay_spell_note())
    assert hp == 0
    assert getattr(lc, "_overlay_mana_spent", 99) == 10


if __name__ == "__main__":
    test_opponent_turn_preview_no_unaffordable_fireblast()
    test_local_turn_no_unaffordable_fireblast()
    print("OK mage fireblast mana overlay")
