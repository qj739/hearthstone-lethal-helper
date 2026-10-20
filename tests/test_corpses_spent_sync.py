#!/usr/bin/env python3
"""回归：Power.log 只涨 CORPSES_SPENT 不减 CORPSES 时，不可误算残骸/双吻斩杀。"""

import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.spell_board import player_corpses
from hdt_python.lethal_checker import LethalChecker
from hdt_python.hero_power_board import list_usable_hero_powers


def test_corpses_spent_decrements_corpses_tag():
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.player_names[2] = "冷静的獾#511450"
    gs.player_ids[3] = 2
    hero = gs.get_entity(64)
    hero.cardtype = "HERO"
    hero.controller = 2
    hero.tags["CORPSES"] = 7
    gs.hero_entity_ids[2] = 64

    parser = PowerLogParser("dummy.log", gs)
    parser._handle_corpses_spent(2, "3")
    assert player_corpses(gs, 2) == 4
    assert int(hero.tags["CORPSES_SPENT_THIS_GAME"]) == 3

    parser._handle_corpses_spent(2, "6")
    assert player_corpses(gs, 2) == 1
    assert int(hero.tags["CORPSES_SPENT_THIS_GAME"]) == 6


def _setup_dual_kiss_board(gs, *, corpses: int, opp_hp: int = 19):
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True

    def hero(eid, pid, *, mana=7, corpses_n=3, dmg=0, health=30):
        h = gs.get_entity(eid)
        h.cardtype = "HERO"
        h.controller = pid
        h.health = health
        h.damage = dmg
        h.tags.update({
            "DAMAGE": dmg, "RESOURCES": mana, "RESOURCES_USED": 0,
            "CORPSES": corpses_n, "EXHAUSTED": 0, "NUM_ATTACKS_THIS_TURN": 0,
        })
        gs.hero_entity_ids[pid] = eid

    def minion(eid, pid, atk, hp, card_id):
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

    def hp(eid, pid, card_id, *, cost=2, corpse=False):
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

    def hand_spell(eid, card_id, cost):
        s = gs.get_entity(eid)
        s.cardtype = "SPELL"
        s.controller = 1
        s.zone = "HAND"
        s.card_id = card_id
        s.cost = cost
        s.tags.update({"ZONE": "HAND", "COST": cost})

    hero(10, 1, mana=7, corpses_n=corpses)
    hero(11, 2, dmg=30 - opp_hp, health=30)
    minion(20, 1, 3, 4, "TIME_614")
    minion(21, 1, 9, 2, "JAIL_446")
    hp(40, 1, "HERO_11bp", cost=2)
    hp(41, 1, "JAIL_446hp", cost=3, corpse=True)
    hand_spell(50, "JAIL_441", 2)


def test_drink_blood_double_kiss_needs_six_corpses():
    """残骸 4：只能吻一次，饮血术刷新后不能再吻，19 血不斩；残骸 7 才会误斩。"""
    gs_ok = GameState()
    _setup_dual_kiss_board(gs_ok, corpses=4, opp_hp=19)
    assert any(
        e.card_id == "JAIL_446hp"
        for e, *_ in list_usable_hero_powers(gs_ok, 1, 7)
    )
    lc_ok = LethalChecker(gs_ok)
    face_ok = lc_ok.overlay_board_face_damage()
    total_ok, _, lethal_ok = lc_ok.calculate_lethal_potential()
    assert not lethal_ok, (
        f"false lethal with 4 corpses: face={face_ok} total={total_ok} "
        f"note={lc_ok.overlay_spell_note()!r}"
    )

    gs_bad = GameState()
    _setup_dual_kiss_board(gs_bad, corpses=7, opp_hp=19)
    lc_bad = LethalChecker(gs_bad)
    face_bad = lc_bad.overlay_board_face_damage()
    total_bad, _, lethal_bad = lc_bad.calculate_lethal_potential()
    assert lethal_bad or face_bad >= 19, (
        f"sanity: 7 corpses should reach 19, face={face_bad} total={total_bad}"
    )
    print(
        "OK dual-kiss corpse gate",
        f"corpses4 face={face_ok} lethal={lethal_ok}",
        f"corpses7 face={face_bad} lethal={lethal_bad}",
    )


def test_last_game_corpses_after_kiss_spent():
    """回放末局：吻耗残骸后 CORPSES 应从 7 扣到正确剩余。"""
    log = Path(r"C:\Program Files (x86)\Hearthstone\Logs\Hearthstone_2026_10_05_23_18_33\Power.log")
    if not log.is_file():
        print("SKIP log missing")
        return
    lines = log.read_text(encoding="utf-8", errors="replace").splitlines()
    start = 112454
    upto = 124862
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[start:upto]:
            if line:
                parser.process_line(line)
    corpses = player_corpses(gs, gs.local_player_id)
    assert corpses == 1, f"expected 1 corpse after two kisses, got {corpses}"

    # 回合开始（第二次吻之前）：spent=3 → 剩余 4，不应误斩 19 血
    gs2 = GameState()
    parser2 = PowerLogParser(str(log), gs2)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[start:124593]:
            if line:
                parser2.process_line(line)
    assert player_corpses(gs2, gs2.local_player_id) == 4
    lc = LethalChecker(gs2)
    _face, _total, lethal = lc.calculate_lethal_potential()
    assert not lethal, (
        f"turn-start false lethal: corpses={player_corpses(gs2, gs2.local_player_id)} "
        f"face={_face} total={_total} note={lc.overlay_spell_note()!r}"
    )
    print("OK log corpses sync + no false lethal at turn start")


if __name__ == "__main__":
    test_corpses_spent_decrements_corpses_tag()
    test_drink_blood_double_kiss_needs_six_corpses()
    test_last_game_corpses_after_kiss_spent()
    print("all ok")
