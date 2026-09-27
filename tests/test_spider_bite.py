#!/usr/bin/env python3
"""毒蛛噬咬 JAIL_436 链：+攻+护甲，并衍生美餐/盛宴。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import get_board_spell_def, hand_board_spells


def _hero(gs, eid, pid, *, dmg=0, mana=10):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.damage = dmg
    h.tags["DAMAGE"] = dmg
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    gs.hero_entity_ids[pid] = eid
    return h


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    s.tags["COST"] = cost
    return s


def test_spider_bite_registered():
    for cid in ("JAIL_436", "JAIL_436t", "JAIL_436t2"):
        assert get_board_spell_def(cid) is not None, cid
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _hand_spell(gs, 40, 1, "JAIL_436", 2)
    assert any(s.card_id == "JAIL_436" for s, _, _ in hand_board_spells(gs, 1, 10))
    print("OK spider bite registered")


def test_spider_bite_plus1_face():
    """毒蛛噬咬：+1 英雄攻可打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=2)
    _hero(gs, 2, 2, dmg=29)  # 1 hp
    _hand_spell(gs, 40, 1, "JAIL_436", 2)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    assert total >= 1, f"expected >=1 face from spider bite, got {total}"
    assert lc.overlay_hero_buff_face() >= 1
    _, _, has = lc.calculate_lethal_potential()
    assert has, "spider bite +1 should lethal vs 1 hp"
    print("OK spider bite +1 face lethal", total)


def test_spider_feast_plus4_face():
    """毒蛛盛宴：+4 英雄攻。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=2)
    _hero(gs, 2, 2, dmg=26)  # 4 hp
    _hand_spell(gs, 40, 1, "JAIL_436t2", 2)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    assert total >= 4, f"expected >=4 from feast, got {total}"
    assert lc.overlay_hero_buff_face() >= 4
    _, _, has = lc.calculate_lethal_potential()
    assert has, "feast +4 should lethal vs 4 hp"
    print("OK spider feast +4 face lethal", total)


def test_spider_bite_chain_full_lethal():
    """噬咬→美餐→盛宴：6 费叠 +1+2+4=7 攻，对手 7 血应斩。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=6)
    _hero(gs, 2, 2, dmg=23)  # 7 hp
    _hand_spell(gs, 40, 1, "JAIL_436", 2)

    lc = LethalChecker(gs)
    dmg, note, has = lc.calculate_lethal_potential()
    assert has, f"full spider chain should lethal vs 7: {note}"
    assert dmg >= 7, f"expected >=7 face, got {dmg} ({note})"
    print("OK spider bite chain lethal", dmg, note)


if __name__ == "__main__":
    test_spider_bite_registered()
    test_spider_bite_plus1_face()
    test_spider_feast_plus4_face()
    test_spider_bite_chain_full_lethal()
    print("ALL OK")
