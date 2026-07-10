#!/usr/bin/env python3
"""疯狂药水 CFM_603：偷取攻≤2 敌方随从、未冰冻可当回合打脸、亡语按我方触发。"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.deathrattle import on_minion_died
from hdt_python.spell_board import (
    get_board_spell_def,
    apply_spell_sequence,
    _SyntheticSpellCard,
)


def _hero(gs, eid, pid, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    h.tags["NUM_ATTACKS_THIS_TURN"] = 0
    h.tags["EXHAUSTED"] = 0
    gs.hero_entity_ids[pid] = eid


def _minion(gs, eid, pid, atk, hp, *, taunt=False, card_id="", frozen=False):
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
    m.tags["HEALTH"] = hp
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if taunt:
        m.tags["TAUNT"] = 1
    if frozen:
        m.tags["FROZEN"] = 1


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"


def test_potion_steal_2_1_face():
    """偷 2/1 未冰冻：当回合打脸 2（计入法术分项，不算随从）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 2, 1)
    _hand_spell(gs, 30, 1, "CFM_603", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, _, spell, _ = checker.overlay_board_breakdown()
    assert total == 2, f"expected 2 face, got {total}"
    assert board == 0, board
    assert spell == 2, spell
    print("OK potion 2/1 face", total)


def test_potion_zero_board_stolen_in_spell_not_minion():
    """我方 0 随从 + 对手 1 攻 + 手牌疯狂药水：偷来伤害进法术，不进随从。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=3)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 1, 2, card_id="CORE_UNG_809")
    _hand_spell(gs, 30, 1, "CFM_603", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, _, spell, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()
    assert len(gs.get_board(1)) == 0
    assert total == 1, total
    assert board == 0, board
    assert spell == 1, spell
    assert "疯狂药水" in note
    print("OK potion zero board spell breakdown", total, board, spell)


def test_potion_frozen_no_attack():
    """冰冻的 2/1 被偷后不能当回合攻击。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 2, 1, frozen=True)
    _hand_spell(gs, 30, 1, "CFM_603", 1)

    total = LethalChecker(gs).overlay_board_face_damage()
    assert total == 0, f"frozen stolen minion should not face, got {total}"
    print("OK potion frozen no attack", total)


def test_potion_skip_high_atk():
    """攻>2 的随从不能被偷，场攻为 0。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 3, 3)
    _hand_spell(gs, 30, 1, "CFM_603", 1)

    total = LethalChecker(gs).overlay_board_face_damage()
    assert total == 0, f"atk>2 should not be stolen, got {total}"
    print("OK potion skip high atk", total)


def test_potion_sludge_interleave_face():
    """对方 3/5 淤泥，我方 6/6+2/2，手牌疯狂药水：穿插后 2/2+偷来 1/2 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6)
    _minion(gs, 11, 1, 2, 2)
    _minion(gs, 20, 2, 3, 5, taunt=True, card_id="FP1_012")
    _hand_spell(gs, 30, 1, "CFM_603", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, _, spell, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()

    assert total == 3, f"expected 3 face (2/2+stolen 1/2), got {total}"
    assert board == 2, f"board face expected 2 (own 2/2), got {board}"
    assert spell == 1, f"spell face expected 1 (stolen 1/2), got {spell}"
    assert "疯狂药水" in note
    assert "法术穿插" in note
    print("OK potion sludge interleave", total, note)


def test_potion_sludge_and_22_taunt_interleave_face():
    """对方 3/5 淤泥+2/2嘲，我方 6/6+2/2，手牌疯狂药水：先偷 2/2 打脸 2。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6)
    _minion(gs, 11, 1, 2, 2)
    _minion(gs, 20, 2, 3, 5, taunt=True, card_id="FP1_012")
    _minion(gs, 21, 2, 2, 2, taunt=True)
    _hand_spell(gs, 30, 1, "CFM_603", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, _, spell, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()

    assert total == 2, f"expected 2 face (steal 2/2 taunt), got {total}"
    assert board == 0, f"board face expected 0, got {board}"
    assert spell == 2, f"spell face expected 2 (stolen), got {spell}"
    assert "疯狂药水" in note
    assert "法术穿插" in note
    print("OK potion sludge+22 taunt interleave", total, note)


def test_potion_plague_strike_sludge_22_taunt_face():
    """对方 3/5 淤泥+2/2嘲，我方 6/6+2/2，手牌疯狂药水+凋零打击：场攻 8。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6)
    _minion(gs, 11, 1, 2, 2)
    _minion(gs, 20, 2, 3, 5, taunt=True, card_id="FP1_012")
    _minion(gs, 21, 2, 2, 2, taunt=True)
    _hand_spell(gs, 30, 1, "CFM_603", 1)
    _hand_spell(gs, 31, 1, "RLK_018", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, _, spell, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()

    assert total == 8, f"expected 8 face, got {total}"
    assert board == 6, f"board face expected 6 (own 6/6), got {board}"
    assert spell == 2, f"spell face expected 2 (stolen+plague), got {spell}"
    assert "疯狂药水" in note and "凋零打击" in note
    assert "法术穿插" in note
    print("OK potion+plague strike sludge+22", total, note)


def test_potion_stolen_on_board_after_played():
    """药水已打出：偷来的随从在我方场面，EXHAUSTED+NON_KEYWORD_CHARGE 仍可当回合打脸。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.player_ids[2] = 1
    gs.player_ids[3] = 2
    gs.in_game = True
    gs.active_player_id = 2
    _hero(gs, 66, 2, mana=5, used=1)
    _hero(gs, 64, 1)
    _minion(gs, 35, 2, 3, 3, card_id="TID_716")
    # 暗影升腾者 2/3：已被疯狂药水偷到己方
    m = gs.get_entity(18)
    m.cardtype = "MINION"
    m.controller = 2
    m.zone = "PLAY"
    m.card_id = "CORE_ICC_210"
    m.atk = 2
    m.health = 3
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["CONTROLLER"] = 2
    m.tags["ATK"] = 2
    m.tags["HEALTH"] = 3
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 1
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    m.tags["NON_KEYWORD_CHARGE"] = 1
    m.tags["887"] = 1
    m.tags["ZONE_POSITION"] = 3
    gs.board_slots.setdefault(2, {})[3] = 18
    # CFM_603e 附魔
    ench = gs.get_entity(255)
    ench.card_id = "CFM_603e"
    ench.cardtype = "ENCHANTMENT"
    ench.tags["ATTACHED"] = 18
    ench.tags["ZONE"] = "PLAY"

    view = m.board_card_view(True)
    assert view.can_attack_hero, "stolen minion should attack face"
    assert view.can_attack_minion

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, _, spell, _ = checker.overlay_board_breakdown()
    assert total == 5, f"expected 3+2 face from board, got {total}"
    assert board == 3, board
    assert spell == 2, spell
    print("OK potion stolen on board after played", total)


def test_potion_controller_tag_change_player_id():
    """TAG_CHANGE CONTROLLER=2 对随从应解析为 PlayerID 2，而非 Player Entity 2→1。"""
    import tempfile
    from hdt_python.power_parser import PowerLogParser

    gs = GameState()
    gs.player_ids[2] = 1
    gs.player_ids[3] = 2
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    m = gs.get_entity(18)
    m.cardtype = "MINION"
    m.zone = "PLAY"
    m.card_id = "CORE_ICC_210"
    m.atk = 2
    m.health = 3
    m.tags["ZONE"] = "PLAY"
    m.tags["ATK"] = 2
    m.tags["HEALTH"] = 3
    m.tags["ZONE_POSITION"] = 3
    m.tags["CONTROLLER"] = 1
    m.controller = 1
    gs.board_slots.setdefault(1, {})[3] = 18

    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        parser = PowerLogParser(tmp.name, gs)
    parser._apply_tag(18, "CONTROLLER", "2", controller_from_tag_change=True)

    assert gs.get_entity_player_id(m) == 2, gs.get_entity_player_id(m)
    assert 18 in gs.board_slots.get(2, {}).values()
    assert 18 not in gs.board_slots.get(1, {}).values()
    print("OK potion controller tag change")


def test_potion_with_board_minion_face():
    """我方 6/6 + 偷来的 2/1：合计打脸 8。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6)
    _minion(gs, 20, 2, 2, 1)
    _hand_spell(gs, 30, 1, "CFM_603", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, _, spell, _ = checker.overlay_board_breakdown()
    assert total == 8, f"expected 8 face (6+2), got {total}"
    assert board == 6, board
    assert spell == 2, spell
    print("OK potion with board 6/6", total)


def test_potion_stolen_deathrattle_summons_friendly():
    """被偷随从死亡：亡语在我方场面召唤（淤泥喷射者 → 1/2 嘲讽）。"""
    enemy_board = [
        {"entity_id": 99, "atk": 3, "health": 5, "taunt": True, "card_id": "BLOCK"},
    ]
    fighters = [
        {
            "kind": "minion",
            "entity_id": 20,
            "card_id": "FP1_012",
            "atk": 2,
            "health": 2,
            "stolen_turn": True,
            "attacks_left": 1,
            "can_face": True,
            "taunt": False,
            "shield": False,
            "poisonous": False,
            "lifesteal": False,
        },
    ]
    stolen = fighters[0]
    stolen["health"] = 0
    on_minion_died(stolen, enemy_board, fighters)

    summoned = [
        f for f in fighters
        if f.get("health", 0) > 0 and f.get("entity_id") != 20
    ]
    assert len(summoned) == 1, f"expected 1 friendly summon, got {summoned}"
    assert summoned[0]["atk"] == 1 and summoned[0]["health"] == 2
    assert summoned[0].get("taunt") is True
    assert summoned[0].get("attacks_left", 0) == 0
    print("OK potion stolen sludge DR friendly", summoned[0])


def test_potion_registered():
    assert get_board_spell_def("CFM_603") is not None
    print("OK CFM_603 registered")


def test_potion_apply_steal_direct():
    """直接施放：敌方 2/2 离场，加入 fighters 且可打脸。"""
    taunts = [
        {"entity_id": 1, "atk": 2, "health": 2, "taunt": False, "card_id": "E22"},
    ]
    fighters: list = []
    defn = get_board_spell_def("CFM_603")
    apply_spell_sequence(
        taunts, fighters,
        [(defn, 1, _SyntheticSpellCard("CFM_603", 1))],
    )
    assert not any(t.get("health", 0) > 0 for t in taunts)
    assert len(fighters) == 1
    assert fighters[0]["atk"] == 2
    assert fighters[0]["attacks_left"] == 1
    assert fighters[0].get("can_face") is True
    assert fighters[0].get("stolen_turn") is True
    print("OK potion apply steal")


def test_potion_steal_does_not_drop_friendly_board_slot():
    """疯狂药水夺取后，不应把同槽位友方随从从场面表挤掉（日志 20_39_29 ~46010）。"""
    import contextlib
    import io
    from pathlib import Path

    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_23_20_39_29\Power.log"
    )
    if not log.is_file():
        print("SKIP potion board slot log replay (log missing)")
        return

    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[:46010]:
            if line.strip():
                parser.process_line(line.rstrip())

    board_ids = {m.entity_id for m in gs.get_board(1)}
    assert 199 in board_ids, (board_ids, dict(gs.board_slots.get(1, {})))
    assert gs.get_entity(199).tags.get("ATK") == 4

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    _, _, lethal = checker.calculate_lethal_potential()
    assert total >= 12, (total, spell, lethal, checker.overlay_spell_note())
    assert lethal, (total, spell, checker.overlay_spell_note())
    print("OK potion steal keeps friendly board slot", total, lethal)


def test_decimation_not_recommended_when_attack_first_lethal_without_it():
    """屠灭会杀己方随从：若先攻已够斩，不应推荐只打屠灭。"""
    import contextlib
    import io
    from pathlib import Path

    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_23_20_39_29\Power.log"
    )
    if not log.is_file():
        print("SKIP decimation lethal log replay (log missing)")
        return

    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[:93450]:
            if line.strip():
                parser.process_line(line.rstrip())

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note()
    combo = checker.overlay_combo_display_lines()
    _, _, lethal = checker.calculate_lethal_potential()
    best_seq = getattr(checker, "_overlay_best_seq", [])

    assert lethal, (total, note, combo)
    assert total >= 25, (total, note)
    assert "屠灭" not in note, note
    assert not any(
        getattr(card, "card_id", None) == "CATA_581"
        for _, _, card in best_seq
    ), (note, best_seq)
    assert any("全部随从打脸" in ln for ln in combo) or not best_seq, combo
    print("OK decimation not in lethal combo when attack enough", total, note)


if __name__ == "__main__":
    test_potion_registered()
    test_potion_apply_steal_direct()
    test_potion_controller_tag_change_player_id()
    test_potion_stolen_on_board_after_played()
    test_potion_sludge_interleave_face()
    test_potion_sludge_and_22_taunt_interleave_face()
    test_potion_plague_strike_sludge_22_taunt_face()
    test_potion_steal_2_1_face()
    test_potion_zero_board_stolen_in_spell_not_minion()
    test_potion_frozen_no_attack()
    test_potion_skip_high_atk()
    test_potion_with_board_minion_face()
    test_potion_stolen_deathrattle_summons_friendly()
    print("all passed")
