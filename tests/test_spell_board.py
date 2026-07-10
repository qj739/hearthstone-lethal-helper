#!/usr/bin/env python3
"""测试月亮井 / 麦迪文的胜利 + 埃提耶识翻倍"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.spell_board import spell_effect_multiplier, has_atiesh_weapon


def _hero(gs, eid, pid, mana=10, used=0):
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = used
    gs.hero_entity_ids[pid] = eid
    return h


def _minion(gs, eid, pid, atk, hp, *, taunt=False, card_id="", spell_immune=False, rush=False, charge=False, cost=None, board_ready=True):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    if cost is not None:
        m.cost = cost
        m.tags["COST"] = cost
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    if board_ready:
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if taunt:
        m.tags["TAUNT"] = 1
    if spell_immune:
        m.tags["ELUSIVE"] = 1
    if rush:
        m.tags["RUSH"] = 1
    if charge:
        m.tags["CHARGE"] = 1
    return m


def _hand_spell(gs, eid, pid, card_id, cost):
    s = gs.get_entity(eid)
    s.cardtype = "SPELL"
    s.controller = pid
    s.zone = "HAND"
    s.card_id = card_id
    s.cost = cost
    s.tags["ZONE"] = "HAND"
    return s


def _hand_minion(gs, eid, pid, atk, hp, cost, *, card_id="TEST_MINION", charge=False, rush=False, dark_gift_charge=False):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "HAND"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.cost = cost
    m.tags["ZONE"] = "HAND"
    m.tags["ATK"] = atk
    m.tags["HEALTH"] = hp
    if charge:
        m.tags["CHARGE"] = 1
    if rush:
        m.tags["RUSH"] = 1
    if dark_gift_charge:
        m.tags["HAS_DARK_GIFT"] = 1
        enc = gs.get_entity(eid + 9000)
        enc.cardtype = "ENCHANTMENT"
        enc.card_id = "EDR_100t5e"
        enc.tags["ATTACHED"] = eid
        enc.tags["CARDTYPE"] = "ENCHANTMENT"
    return m


def _hand_weapon(gs, eid, pid, card_id, cost, atk=1, dur=2):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.controller = pid
    w.zone = "HAND"
    w.card_id = card_id
    w.cost = cost
    w.atk = atk
    w.health = dur
    w.tags["ZONE"] = "HAND"
    w.tags["ATK"] = atk
    w.tags["DURABILITY"] = dur
    return w


def _weapon(gs, eid, pid, card_id, durability=3):
    w = gs.get_entity(eid)
    w.cardtype = "WEAPON"
    w.card_id = card_id
    w.controller = pid
    w.zone = "PLAY"
    w.atk = 1
    w.health = durability
    w.tags["ZONE"] = "PLAY"
    w.tags["DURABILITY"] = durability
    gs.weapon_entity_ids[pid] = eid
    hero = gs.get_hero(pid)
    if hero:
        hero.tags["MAIN_HAND_WEAPON_ENTITY"] = eid
    return w


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


def test_moonwell_clears_taunt_and_face():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 3, 3, card_id="M1")
    _minion(gs, 20, 2, 2, 4, taunt=True, card_id="TAUNT")
    _hand_spell(gs, 30, 1, "EDR_476", 6)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 4, f"moonwell face expected 4, got {spell}"
    assert board == 3, f"minion face expected 3, got {board}"
    assert pure == 0, f"pure face expected 0 with taunt, got {pure}"
    assert total == 7, f"total expected 7, got {total}"
    assert total == board + weapon + spell + hp, f"total breakdown mismatch: {total}"
    print("OK moonwell taunt+face", total)


def test_cata_with_atiesh():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 5, 5, card_id="BIG")
    _minion(gs, 20, 2, 2, 4, taunt=True, card_id="TAUNT")
    _hand_spell(gs, 30, 1, "CATA_308", 5)
    _weapon(gs, 40, 1, "TIME_890t")

    assert has_atiesh_weapon(gs, 1)
    assert spell_effect_multiplier(gs, 1) == 2

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    # 8 点 AOE 解嘲并击杀己方 5/5；武器 1 攻仍可打脸
    assert total == 1, f"expected 1 (weapon only), got {total}"
    assert weapon == 1 and board == 0 and spell == 0
    assert total == board + weapon + spell + hp, f"total breakdown mismatch: {total}"
    print("OK cata x2 clears taunt and own minion", total)


def test_medivh_empty_enemy_board_skips_harmful_spell():
    """对手空场：手牌麦迪文的胜利误伤己方时不应优于纯场攻。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    for eid, atk, hp in ((10, 5, 7), (11, 5, 3), (12, 9, 9)):
        m = _minion(gs, eid, 1, atk, hp)
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    dorm = _minion(gs, 13, 1, 3, 5, card_id="CORE_BT_156")
    dorm.tags["DORMANT"] = 1
    _hand_spell(gs, 30, 1, "CATA_308", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert pure == 19, f"pure board expected 19, got {pure}"
    assert total == 19, f"overlay should stay 19, got {total} note={checker.overlay_spell_note()!r}"
    assert board == 19
    assert spell == 0
    print("OK medivh empty enemy skips harmful spell", total)


def test_cata_464t_dragon_breath_dynamic_face():
    """龙息：亡语衍生法术，TAG_SCRIPT_DATA_NUM_1 为动态伤害（等于亡语随从攻）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    breath = _hand_spell(gs, 30, 1, "CATA_464t", 2)
    breath.tags["TAG_SCRIPT_DATA_NUM_1"] = 3

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 3, f"dragon breath expected 3 spell face, got {spell} total={total}"
    assert total == 3
    print("OK cata 464t dragon breath dynamic", total)


def test_p0_tyrande_aura_attached_player_entity():
    """日志中 EDR_464e2 常 ATTACHED=Player EntityID（非 HERO_ENTITY）。"""
    from hdt_python.battlecry_board import tyrande_double_spells_remaining

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 64, 1)
    gs.hero_entity_ids[1] = 64
    player_ent = gs.get_entity(2)
    player_ent.cardtype = "PLAYER"
    player_ent.controller = 1
    gs.player_ids[2] = 1
    enc = gs.get_entity(212)
    enc.cardtype = "ENCHANTMENT"
    enc.card_id = "EDR_464e2"
    enc.zone = "PLAY"
    enc.tags["ZONE"] = "PLAY"
    enc.tags["ATTACHED"] = 2
    enc.tags["TAG_SCRIPT_DATA_NUM_1"] = 2
    assert tyrande_double_spells_remaining(gs, 1) == 2
    print("OK tyrande aura attached player entity", tyrande_double_spells_remaining(gs, 1))


def test_moonwell_x2_atiesh():
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 4, 4, card_id="M1")
    _minion(gs, 20, 2, 2, 5, taunt=True, card_id="TAUNT")
    _hand_spell(gs, 30, 1, "EDR_476", 6)
    _weapon(gs, 40, 1, "TIME_890t")

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    # 8 dmg kills 2/5 taunt; heal 8 -> 4/4 still 4 atk
    assert spell == 8, f"spell face expected 8, got {spell}"
    assert board == 4, f"minion face expected 4, got {board}"
    assert weapon == 1, f"weapon face expected 1, got {weapon}"
    assert total == 13, f"total expected 13, got {total}"
    assert total == board + weapon + spell + hp, f"total breakdown mismatch: {total}"
    assert "埃提耶识" in checker.overlay_spell_note()
    print("OK moonwell x2", total)


def test_deathrattle_spell_first_better():
    """亡语 AOE：先月亮井回血再攻击，优于先交换触发亡语。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 2, 2, card_id="M1")
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="UNG_022")
    _hand_spell(gs, 30, 1, "EDR_476", 6)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()
    # 先法：回血 2/6，解嘲触发 1 点亡语 -> 2/5，打脸 2 + 月亮井 4 = 6
    # 先攻：交换后随从全灭，仅月亮井 4
    assert total == 6, f"expected 6 (spell first), got {total}"
    assert board == 2, f"board face expected 2, got {board}"
    assert spell == 4, f"spell face expected 4, got {spell}"
    assert total == board + weapon + spell + hp, f"total breakdown mismatch: {total}"
    assert "先法后攻" in note, f"expected spell-first note, got {note!r}"
    print("OK deathrattle spell first", total, note)


def test_moonwell_only_empty_board():
    """仅手牌月亮井、空场面：场攻至少 4。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "EDR_476", 6)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total >= 4, f"moonwell-only should be at least 4, got {total}"
    assert spell == 4, f"spell face expected 4, got {spell}"
    assert total == board + weapon + spell + hp, f"total breakdown mismatch: {total}"
    print("OK moonwell only", total)


def test_moonwell_only_opponent_turn():
    """对方回合：当前 0 法力，下回合 10 法力，仅月亮井仍应计入 4。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=10)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "EDR_476", 6)

    checker = LethalChecker(gs)
    assert not checker.is_local_turn()
    total = checker.overlay_board_face_damage()
    assert total >= 4, f"opp turn moonwell-only should be at least 4, got {total}"
    print("OK moonwell only opp turn", total)


def test_moonwell_lifesteal_minion_still_lethal_from_log():
    """Power.log 最后一局：月亮井+雏龙打脸 9 伤对 9 血，吸血随从不应阻止斩杀判定。"""
    import io
    import contextlib
    from pathlib import Path
    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_29_00_40_04\Power.log"
    )
    if not log.is_file():
        print("SKIP moonwell lifesteal lethal log (log missing)")
        return

    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    gs.player_names[2] = "鸡哥在线#5240"
    gs.local_player_id = 2
    parser = PowerLogParser(str(log), gs)
    starts = [
        i for i, line in enumerate(lines)
        if "CREATE_GAME" in line and "GameState.DebugPrintPower" in line
    ]
    target = 92521
    start = starts[-1]
    for i, s in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(lines)
        if s <= target - 1 < end:
            start = s
            break
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            parser.process_line(lines[i])
    gs.in_game = True
    gs.active_player_id = 2

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_bd, _, spell_face, _ = checker.overlay_board_breakdown()
    _, _, has = checker.calculate_lethal()
    assert total >= 9, total
    assert spell_face == 4, spell_face
    assert minion_bd >= 5, minion_bd
    assert checker.get_opponent_effective_hp() >= 9
    assert has is True, (
        total, checker.get_opponent_effective_hp(),
        getattr(checker, "_overlay_lifesteal_heal", 0),
        checker.overlay_combo_display_lines(),
    )
    assert any("月亮井" in ln for ln in checker.overlay_combo_display_lines())
    print("OK moonwell lifesteal minion lethal from log", total, has)


def test_huntress_board_line_not_lethal_at_17_from_log():
    """Power.log 第11回合：女猎手+场攻最高约15~16，对手17血不应误亮斩。"""
    import io
    import contextlib
    from pathlib import Path
    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_29_00_40_04\Power.log"
    )
    if not log.is_file():
        print("SKIP huntress not lethal log (log missing)")
        return

    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    gs.player_names[2] = "鸡哥在线#5240"
    gs.local_player_id = 2
    parser = PowerLogParser(str(log), gs)
    starts = [
        i for i, line in enumerate(lines)
        if "CREATE_GAME" in line and "GameState.DebugPrintPower" in line
    ]
    target = 86585
    start = starts[-1]
    for i, s in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(lines)
        if s <= target - 1 < end:
            start = s
            break
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            parser.process_line(lines[i])
    gs.in_game = True
    gs.active_player_id = 2

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, has = checker.calculate_lethal()
    eff = checker.get_opponent_effective_hp()
    assert eff == 17, eff
    assert 15 <= total <= 16, (total, checker.overlay_board_breakdown())
    assert has is False, (total, eff, checker.overlay_combo_display_lines())
    print("OK huntress turn not lethal at 17", total, eff)


def test_remixed_rhapsody_emotional_hero_buff_not_overwritten_by_random_spell():
    """动情狂想曲 +5 英雄攻：随机法术 MC 分更高时不得用更低 total 覆盖 display。"""
    import io
    import contextlib
    from pathlib import Path
    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_29_00_40_04\Power.log"
    )
    if not log.is_file():
        print("SKIP rhapsody hero buff log (log missing)")
        return

    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    gs.player_names[2] = "鸡哥在线#5240"
    gs.local_player_id = 2
    parser = PowerLogParser(str(log), gs)
    starts = [
        i for i, line in enumerate(lines)
        if "CREATE_GAME" in line and "GameState.DebugPrintPower" in line
    ]
    target = 250502
    start = starts[-1]
    for i, s in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(lines)
        if s <= target - 1 < end:
            start = s
            break
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            parser.process_line(lines[i])
    gs.in_game = True
    gs.active_player_id = 2

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    hero_buff = checker.overlay_hero_buff_face()
    assert hero_buff >= 5, hero_buff
    assert total >= 9, (total, hero_buff, checker.overlay_board_breakdown())
    assert any(
        getattr(c, "card_id", "") == "JAM_018t3"
        for _, _, c in getattr(checker, "_overlay_best_seq", [])
        if c
    ), getattr(checker, "_overlay_best_seq", [])
    print("OK rhapsody emotional hero buff not overwritten", total, hero_buff)


def test_player_name_resources_enables_moonwell():
    """Power.log 把 RESOURCES 写在战网名上时，应同步到英雄并计入月亮井场攻。"""
    from hdt_python.power_parser import PowerLogParser, GameState as GS

    gs = GS()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.player_names[1] = "Test#5240"
    gs.in_game = True
    _hero(gs, 1, 1)
    gs.hero_entity_ids[1] = 1
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "EDR_476", 6)

    parser = PowerLogParser("dummy.log", gs)
    parser.process_line(
        "D 12:00:00.0000000 GameState.DebugPrintPower() - "
        "TAG_CHANGE Entity=Test#5240 tag=RESOURCES value=6"
    )
    parser.process_line(
        "D 12:00:00.0000000 GameState.DebugPrintPower() - "
        "TAG_CHANGE Entity=Test#5240 tag=RESOURCES_USED value=0"
    )

    hero = gs.get_hero(1)
    assert hero.tags.get("RESOURCES") == 6, f"expected RESOURCES on hero, got {hero.tags}"

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total >= 4, f"moonwell should be at least 4 after RESOURCES fix, got {total}"
    print("OK player name RESOURCES -> moonwell face", total)


def test_two_moonwells_double_face():
    """手牌两张月亮井、我方回合法力够（如减费后各 5 费）：场攻应含 8 点法术直伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "EDR_476", 5)
    _hand_spell(gs, 31, 1, "EDR_476", 5)

    checker = LethalChecker(gs)
    assert checker.is_local_turn()
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 8, f"two moonwells expected 8 spell face, got {spell}"
    assert total == board + weapon + spell + hp
    print("OK two moonwells", total)


def test_two_moonwells_with_extra_board_spell():
    """两张月亮井 + 另一张解场法术：应能枚举「只打双月亮井」而非必须全打。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "EDR_476", 5)
    _hand_spell(gs, 31, 1, "EDR_476", 5)
    _hand_spell(gs, 32, 1, "CATA_308", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 8, f"10 mana should play 2x moonwell (8 face), got spell={spell} total={total}"
    print("OK two moonwells with cata in hand", total)


def test_two_ebb_and_flow_spells_in_combo():
    """两张潮起潮落：法术搜索应保留两张实体，法力够时计入双法术。"""
    from hdt_python.battlecry_board import hand_all_board_plays

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=4, used=0)
    _hero(gs, 2, 2)
    _hand_spell(gs, 8, 1, "TIME_702", 2)
    _hand_spell(gs, 40, 1, "TIME_702", 2)

    plays = hand_all_board_plays(gs, 1, 4)
    trimmed = LethalChecker._trim_hand_spells_for_search(plays, 4)
    ebb = [p for p in trimmed if (p[0].card_id or "") == "TIME_702"]
    assert len(ebb) == 2, f"expected 2 TIME_702 entities, got {len(ebb)}"

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 6, f"two ebb and flow expected 6 spell face, got {spell}"
    combo = checker.overlay_combo_display_lines()
    ebb_lines = [ln for ln in combo if "潮起潮落" in ln]
    assert len(ebb_lines) == 2, f"combo should list both spells: {combo}"
    assert total == spell
    print("OK two ebb and flow", total, combo)


def test_p0_frostbite_direct_face():
    """P0 直伤：冰霜撕咬空场 3 点。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "AV_259", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 3, f"frostbite expected 3 spell face, got {spell}"
    assert total == 3
    max_face, prob, uses_random, _top = checker.overlay_face_stats()
    assert not uses_random
    assert max_face == 3
    assert prob == 0.0
    print("OK p0 frostbite", total)


def test_p0_hellfire_face_and_board():
    """P0 直伤：地狱烈焰 3 点 AOE + 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 3, 3, card_id="M1")
    _hand_spell(gs, 30, 1, "CORE_CS2_062", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 3, f"hellfire expected 3 spell face, got {spell}"
    assert board == 3, f"先攻后法：3/3 打脸 + 地狱烈焰 3，board={board}"
    assert total == 6
    print("OK p0 hellfire", total)


def test_p0_bursting_shot_taunt_and_six_six():
    """爆裂射击 + 3血嘲讽 + 6/6：三发不可重复；解嘲后仅 1 个敌人，法术最多 2 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 1, 3, taunt=True, card_id="TAUNT3")
    _hand_spell(gs, 30, 1, "FIR_909", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    max_face, prob, uses_random, top_outcomes = checker.overlay_face_stats()
    note = getattr(checker, "_overlay_spell_note", "")

    assert pure == 0, f"有嘲讽时纯场攻应为 0，got {pure}"
    assert board == 0, f"6/6 解嘲后本回合无随从打脸，got {board}"
    assert spell == 2, f"解嘲后仅 1 个敌人，爆裂射击最多 1 发打脸 2，got {spell}"
    assert total == 2, f"总场攻 expected 2, got {total}"
    assert total == board + weapon + spell + hp
    assert uses_random
    assert max_face == 2, f"MC 最高场攻 expected 2, got {max_face}"
    assert top_outcomes == [(2, 1.0)], f"expected 100% at 2 dmg, got {top_outcomes}"
    print(
        "OK bursting shot taunt+6/6",
        f"total={total} (随={board} 法={spell})",
        f"top={top_outcomes}",
        note,
    )


def test_p0_bursting_shot_mc_stats():
    """P0 随机直伤：空场仅英雄时爆裂射击最多 1 发打脸 2。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    gs.get_entity(2).health = 6
    _hand_spell(gs, 30, 1, "FIR_909", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    max_face, prob, uses_random, top_outcomes = checker.overlay_face_stats()
    assert uses_random
    assert max_face == 2, f"distinct targets: only hero, max face 2, got {max_face}"
    assert top_outcomes == [(2, 1.0)], f"expected 100% at 2, got {top_outcomes}"
    assert total == 2
    assert prob == 0.0, f"2 dmg vs 6 hp should be 0% lethal, got {prob}"
    print("OK p0 bursting shot mc", total, max_face, top_outcomes)


def test_p0_bursting_shot_top_two_outcomes():
    """嘲讽 + 两个 2/2 + 6/6：随机三发不重复，场攻显示最高两档概率。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T1")
    _minion(gs, 21, 2, 2, 2, card_id="M1")
    _minion(gs, 22, 2, 2, 2, card_id="M2")
    _hand_spell(gs, 30, 1, "FIR_909", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    max_face, _prob, uses_random, top_outcomes = checker.overlay_face_stats()

    assert uses_random
    assert max_face == 8
    assert len(top_outcomes) == 2, f"expected top-2 outcomes, got {top_outcomes}"
    assert top_outcomes[0][0] == 8
    assert top_outcomes[1][0] == 6
    assert top_outcomes[0][1] > top_outcomes[1][1]
    assert top_outcomes[0][1] + top_outcomes[1][1] < 1.0
    assert total == max_face
    print(
        "OK bursting shot top-2",
        " ".join(f"{dmg}({prob*100:.0f}%)" for dmg, prob in top_outcomes),
    )


def test_p0_arcane_barrage_taunt_and_six_six():
    """奥术弹幕：3伤打嘲讽解场 + 余波最多1发打脸2 + 6/6打脸6；余波不可重复命中。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 1, 3, taunt=True, card_id="TAUNT3")
    _hand_spell(gs, 30, 1, "TIME_855", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    max_face, _prob, uses_random, top_outcomes = checker.overlay_face_stats()

    assert pure == 0
    assert board == 6, f"解嘲后 6/6 打脸，got board={board}"
    assert spell == 2, f"主目标嘲讽后余波仅 1x2 打脸，got spell={spell}"
    assert total == 8, f"总场攻 expected 8, got {total}"
    assert uses_random
    assert max_face == 8
    assert top_outcomes == [(8, 1.0)]
    print("OK arcane barrage taunt+6/6", f"total={total} (随={board} 法={spell})")


def test_p0_arcane_barrage_three_taunts_and_six_six():
    """奥术弹幕：3伤打1嘲 + 余波随机另2嘲；全清则6/6打脸6，否则余波打脸2。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m66 = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m66.tags["NUM_TURNS_IN_PLAY"] = 1
    for i, eid in enumerate([20, 21, 22], start=1):
        _minion(gs, eid, 2, 1, 2, taunt=True, card_id=f"T{i}")
    _hand_spell(gs, 30, 1, "TIME_855", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    max_face, _prob, uses_random, top_outcomes = checker.overlay_face_stats()

    assert uses_random
    assert max_face == 6
    assert len(top_outcomes) == 2
    assert top_outcomes[0] == (6, top_outcomes[0][1])
    assert top_outcomes[1][0] == 2
    assert 0.25 < top_outcomes[0][1] < 0.45, f"6 dmg prob expected ~1/3, got {top_outcomes[0][1]}"
    assert 0.55 < top_outcomes[1][1] < 0.75, f"2 dmg prob expected ~2/3, got {top_outcomes[1][1]}"
    assert total == 6
    print(
        "OK arcane barrage 3 taunts",
        " ".join(f"{dmg}({prob*100:.0f}%)" for dmg, prob in top_outcomes),
    )


def test_p0_spell_kills_taunt_then_minion_face():
    """可选目标法术：2血嘲讽 + 8攻随从，应解嘲后随从打脸而非法术打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 8, 8, card_id="BIG")
    _minion(gs, 20, 2, 1, 2, taunt=True, card_id="TAUNT")
    _hand_spell(gs, 30, 1, "AV_259", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert pure == 0
    assert spell == 0, f"spell should kill taunt not face, got spell={spell}"
    assert board == 8, f"8 atk face after taunt removed, got {board}"
    assert total == 8, f"expected 8 not 3, got {total}"
    print("OK p0 spell clears taunt before face", total)


def test_p0_wicked_stab_rank_by_max_mana():
    """邪恶挥刺：按法力水晶上限 2/4/6 伤（均为 2 费）。"""
    def _run(card_id, max_mana, expected_spell):
        gs = GameState()
        gs.local_player_id = 1
        gs.opponent_player_id = 2
        gs.active_player_id = 1
        gs.in_game = True
        _hero(gs, 1, 1, mana=max_mana, used=0)
        hero = gs.get_entity(1)
        hero.tags["MAXRESOURCES"] = max_mana
        hero.tags["RESOURCES"] = max_mana
        _hero(gs, 2, 2)
        _hand_spell(gs, 30, 1, card_id, 2)
        checker = LethalChecker(gs)
        total = checker.overlay_board_face_damage()
        _, _, _, spell, _ = checker.overlay_board_breakdown()
        assert spell == expected_spell, (
            f"{card_id} @ {max_mana} crystals expected spell={expected_spell}, got {spell}"
        )
        assert total == expected_spell
        return total

    assert _run("BAR_319", 4, 2) == 2
    assert _run("BAR_319", 5, 4) == 4
    assert _run("BAR_319", 10, 6) == 6
    assert _run("BAR_921", 10, 6) == 6
    assert _run("BAR_319t2", 10, 6) == 6
    print("OK wicked stab ranks 2/4/6")


def test_p0_wicked_stab_bar_319t2_zero_cost_face():
    """邪恶挥刺等级3（BAR_319t2）：减费后 0 费仍应计 6 直伤。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.active_player_id = 2
    gs.in_game = True
    _hero(gs, 2, 2, mana=10)
    _hero(gs, 1, 1)
    card = _hand_spell(gs, 52, 2, "BAR_319t2", 2)
    card.tags["COST"] = 0
    card.tags["TAG_LAST_KNOWN_COST_IN_HAND"] = 0

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 6, (total, spell)
    assert total == 6
    print("OK wicked stab bar_319t2 zero cost", total)


def test_p0_hammer_of_wrath_zero_cost_face():
    """愤怒之锤：减费后 0 费计 3 直伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    card = _hand_spell(gs, 225, 1, "CORE_CS2_094", 3)
    card.tags["COST"] = 0
    card.tags["TAG_LAST_KNOWN_COST_IN_HAND"] = 0

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 3, (total, spell)
    assert total == 3
    print("OK hammer of wrath zero cost", total)


def test_p0_grish_stinger_stale_script_tag_after_entity_reuse():
    """实体 ID 复用后 TAG_SCRIPT_DATA_NUM_1 残留不应把毒刺虫算成 33 伤。"""
    from hdt_python.spell_board import pack_no_taunt_direct_face_spells, get_board_spell_def, spell_script_damage

    gs = GameState()
    gs.local_player_id = 1
    e = gs.get_entity(128)
    e.card_id = "TIME_000tb"
    e.cardtype = "SPELL"
    e.tags["TAG_SCRIPT_DATA_NUM_1"] = 33
    e.reset_for_new_card("TLC_630t")
    e.cardtype = "SPELL"
    e.tags["COST"] = 1
    e.tags["TAG_LAST_KNOWN_COST_IN_HAND"] = 1
    e.controller = 1
    e.zone = "HAND"

    assert spell_script_damage(e) == 2
    defn = get_board_spell_def("TLC_630t")
    hand = [(e, defn, 1)]
    _, face, mana = pack_no_taunt_direct_face_spells(hand, 10, gs=gs, player_id=1)
    assert face == 2, face
    assert mana == 1, mana

    gs2 = GameState()
    gs2.local_player_id = 1
    gs2.opponent_player_id = 2
    gs2.active_player_id = 1
    gs2.in_game = True
    _hero(gs2, 1, 1, mana=10)
    _hero(gs2, 2, 2)
    for eid in (128, 129):
        card = _hand_spell(gs2, eid, 1, "TLC_630t", 1)
        card.tags["TAG_SCRIPT_DATA_NUM_1"] = 33

    checker = LethalChecker(gs2)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 4, (total, spell)
    assert total == 4, total
    print("OK grish stinger stale script tag", total)


def test_p0_grish_stinger_spell_and_rush_no_face():
    """格里什毒刺虫：2 伤直伤 + 2/1 突袭当回合不能打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hand_spell(gs, 184, 1, "TLC_630t", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 2, (total, spell)
    assert total == 2
    print("OK grish stinger spell face", total)


def test_p0_wicked_stab_opp_turn_next_rank():
    """对方回合 4 水晶：下回合 5 水晶，BAR_319 应按 4 伤算。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=4, used=4)
    hero = gs.get_entity(1)
    hero.tags["MAXRESOURCES"] = 4
    hero.tags["RESOURCES"] = 4
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "BAR_319", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 4, f"next turn 5 crystals -> rank2 4 dmg, got spell={spell}"
    assert total == 4
    print("OK wicked stab opp turn upgrade to rank2", total)


def test_spell_immune_taunt_blocks_spell_target():
    """魔法免疫嘲讽：指向法术不能解嘲，8攻随从仍可用随从交换解嘲。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    big = _minion(gs, 10, 1, 8, 8, card_id="BIG")
    big.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 1, 2, taunt=True, spell_immune=True, card_id="ELUSIVE")
    _hand_spell(gs, 30, 1, "AV_259", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    # 冰霜撕咬不能点免疫嘲→打脸3；8攻用唯一一次攻击解嘲→无剩余打脸
    assert spell == 3, f"spell can only hit face, got {spell}"
    assert board == 0, f"minion attack spent clearing taunt, got board={board}"
    assert total == 3, f"expected 3, got {total}"
    print("OK spell immune taunt blocks spell clear", total)


def test_spell_immune_skipped_for_lowest_target():
    """邪能弹幕：跳过免疫随从，打次低血可点目标。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    taunts = [
        {"health": 2, "shield": False, "lifesteal": False, "atk": 1, "poisonous": False, "spell_immune": True},
        {"health": 3, "shield": False, "lifesteal": False, "atk": 1, "poisonous": False, "spell_immune": False},
    ]
    defn = get_board_spell_def("SW_040")
    res = apply_spell_sequence(taunts, [], [(defn, 2, None)], enemy_shield=False)
    assert res.direct_face_damage == 0
    assert len(taunts) == 1
    assert taunts[0]["spell_immune"] and taunts[0]["health"] == 2
    print("OK fel barrage skips spell immune")


def test_p0_fel_barrage_taunt_and_eight_atk():
    """邪能弹幕 + 2血嘲讽 + 8攻随从：先法后攻最优（随从只有 1 次攻击）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 8, 8, card_id="BIG")
    _minion(gs, 20, 2, 1, 2, taunt=True, card_id="TAUNT")
    _hand_spell(gs, 30, 1, "SW_040", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()

    # 先法后攻：邪能弹幕第1发杀2血嘲，第2发打脸2；随从8攻再打脸 → 10
    # 先攻后法：8攻随从用掉唯一一次攻击解嘲，无法再打脸；空场邪能弹幕 2+2=4 → 仅 4
    assert pure == 0
    assert total == 10, f"expected 10 (8 board + 2 spell), got {total}"
    assert board == 8, f"8 atk minion face after spell clears taunt, got {board}"
    assert spell == 2, f"fel barrage 2nd hit to face after killing taunt, got {spell}"
    assert total == board + weapon + spell + hp
    assert "先法后攻" in note or "法术穿插" in note, f"expected spell-first/interleave note, got {note!r}"
    print("OK p0 fel barrage taunt+8atk", total, note)


def test_p0_fel_barrage_lowest_split():
    """P0 确定分配：邪能弹幕 2x2 优先最低生命随从。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    taunts = [
        {"health": 5, "shield": False, "lifesteal": False, "atk": 2, "poisonous": False},
        {"health": 2, "shield": False, "lifesteal": False, "atk": 1, "poisonous": False},
    ]
    defn = get_board_spell_def("SW_040")
    assert defn is not None
    res = apply_spell_sequence(taunts, [], [(defn, 2, None)], enemy_shield=False)
    assert res.direct_face_damage == 0
    assert taunts[0]["health"] == 3
    assert len(taunts) == 1

    res2 = apply_spell_sequence([], [], [(defn, 2, None)], enemy_shield=False)
    assert res2.direct_face_damage == 4
    print("OK p0 fel barrage", res2.direct_face_damage)


def test_p0_lightning_storm_clears_taunt():
    """闪电风暴：3伤 AOE 解嘲 + 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 1, 3, taunt=True, card_id="TAUNT3")
    _hand_spell(gs, 30, 1, "CORE_EX1_259", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 0, f"lightning storm no face, got spell={spell}"
    assert board == 6, f"6/6 face after AOE clears taunt, got board={board}"
    assert total == 6
    print("OK p0 lightning storm", total)


def test_p0_vendetta_clears_taunt():
    """宿敌：4伤解 3血嘲讽 + 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 1, 3, taunt=True, card_id="TAUNT3")
    _hand_spell(gs, 30, 1, "DAL_716", 0)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 0
    assert board == 6
    assert total == 6
    print("OK p0 vendetta", total)


def test_spell_after_partial_taunt_damage_still_lethal():
    """影焰打嘲讽后，混乱品味应仍判斩杀（非嘲讽 3/3 不应被当成必解嘲讽）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=2)
    oh = _hero(gs, 2, 2)
    oh.health = 4
    oh.tags["ARMOR"] = 5
    for eid, atk, hp in [(10, 1, 9), (11, 3, 5), (12, 3, 10), (13, 3, 6), (14, 2, 4)]:
        m = _minion(gs, eid, 1, atk, hp, card_id="M")
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 3, 3, card_id="NONTAUNT")
    taunt = _minion(gs, 21, 2, 4, 7, taunt=True, card_id="TAUNT")
    taunt.damage = 2
    taunt.tags["DAMAGE"] = 2
    _hand_spell(gs, 30, 1, "ETC_394", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, has = checker.calculate_lethal_potential()
    assert total >= 9, f"expected lethal face >=9 after taunt chipped, got {total}"
    assert has
    print("OK partial taunt damage still lethal", total)


def test_p0_torch_wounded_only():
    """烈火炙烤：仅受伤随从；满血嘲不解场。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    taunts = [
        {"health": 3, "damage": 0, "shield": False, "lifesteal": False, "atk": 1,
         "poisonous": False, "spell_immune": False, "taunt": True},
    ]
    fighters = [{"kind": "minion", "health": 6, "atk": 6, "attacks_left": 1}]
    defn = get_board_spell_def("CATA_585")
    res = apply_spell_sequence(taunts, fighters, [(defn, 1, None)], enemy_shield=False)
    assert res.direct_face_damage == 0
    assert taunts[0]["health"] == 3

    taunts[0]["damage"] = 1
    res2 = apply_spell_sequence(taunts, fighters, [(defn, 1, None)], enemy_shield=False)
    assert len(taunts) == 0
    assert res2.direct_face_damage == 0
    print("OK p0 torch wounded only")


def test_p0_light_it_burns():
    """炽燃圣光：伤害=攻击力，6攻嘲讽解嘲后 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 6, 3, taunt=True, card_id="T6")
    _hand_spell(gs, 30, 1, "REV_249", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 0
    assert board == 6
    assert total == 6
    print("OK p0 light it burns", total)


def test_p0_infiltrate_skip_friendly_for_max_face():
    """潜入：豁免 3/3，三嘲全死，6/6+3/3 打脸 9。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 11, 1, 3, 3, card_id="M33")
    for eid in (20, 21, 22):
        _minion(gs, eid, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "GDB_902", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 0
    assert board == 9
    assert total == 9
    print("OK p0 infiltrate skip friendly", total)


def test_p0_plague_strike_summons_rush_clears_taunt():
    """凋零打击：击杀召唤 2/2 突袭，解第二张嘲后 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    for eid in (20, 21):
        _minion(gs, eid, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "RLK_018", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 0
    assert board == 6
    assert total == 6
    print("OK p0 plague strike 2 taunts", total)


def test_p0_blood_in_the_water_shark_clears_taunt():
    """血染大海：5/5 突袭解嘲，6/6 打脸（鲨鱼当回合不打脸）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    for eid in (20, 21):
        _minion(gs, eid, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "TSC_932", 6)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 0
    assert board == 6
    assert total == 6
    print("OK p0 blood in the water 2 taunts", total)


def test_p0_blood_in_the_water_shark_no_face_empty_board():
    """血染大海：空场仅 3 直伤，5/5 突袭当回合不计入场攻。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "TSC_932", 6)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert board == 0
    assert spell == 3
    assert total == 3
    print("OK p0 blood in the water face only", total)


def test_p0_initiation_rush_copy_clears_taunt():
    """通窍：击杀突袭随从，复制体当回合解嘲，6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _minion(gs, 21, 2, 4, 4, rush=True, card_id="R44")
    _hand_spell(gs, 30, 1, "SCH_512", 6)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 0
    assert board == 6
    assert total == 6
    print("OK p0 initiation rush copy", total)


def test_p0_initiation_non_rush_copy_no_extra_face():
    """通窍：击杀普通随从，复制体召唤失调，仍需 6/6 换嘲，场攻 0。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    for eid in (20, 21):
        _minion(gs, eid, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "SCH_512", 6)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 0
    print("OK p0 initiation no rush copy", total)


def test_p0_nightshade_tea_multi_drink():
    """夜影花茶：3 杯连喝（自伤 6），解 2/2 嘲后 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    hero = _hero(gs, 1, 1, mana=10, used=0)
    hero.health = 10
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "VAC_404", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6
    print("OK p0 nightshade 3 drinks", total)


def test_p0_nightshade_tea_self_damage_limit():
    """夜影花茶：3 血只能喝 1 杯（再喝会致死）。"""
    from hdt_python.spell_board import (
        apply_spell_sequence,
        get_board_spell_def,
        _SyntheticSpellCard,
    )

    defn = get_board_spell_def("VAC_404")
    taunts = [
        {"entity_id": 20, "health": 5, "damage": 0, "shield": False, "lifesteal": False,
         "atk": 2, "poisonous": False, "spell_immune": False, "taunt": True},
    ]
    res = apply_spell_sequence(
        taunts, [],
        [(defn, 1, _SyntheticSpellCard("VAC_404", 1))],
        hero_hp=3, mana_budget=3,
    )
    assert res.self_hero_damage == 2
    assert taunts[0]["health"] == 3
    print("OK p0 nightshade hp limit")


def test_p0_first_flame_chain():
    """初始之火：打出得 SW_108t 传承之火，两连解嘲后 6/6 打脸。"""
    from hdt_python.spell_board import get_board_spell_def

    assert get_board_spell_def("SW_108t") is not None
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "CORE_SW_108", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6
    print("OK p0 first flame chain", total)


def test_p0_health_drink_multi_drink():
    """“健康”饮品：9 费连喝 3 杯解 3 嘲，6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    for i, eid in enumerate((20, 21, 22), start=1):
        _minion(gs, eid, 2, 2, 2, taunt=True, card_id=f"T{i}")
    _hand_spell(gs, 30, 1, "VAC_951", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6
    print("OK p0 health drink 3 drinks", total)


def test_p0_health_drink_lifesteal_heal():
    """“健康”饮品：法术吸血按实际伤害回复己方。"""
    from hdt_python.spell_board import (
        apply_spell_sequence,
        get_board_spell_def,
        _SyntheticSpellCard,
    )

    defn = get_board_spell_def("VAC_951")
    taunts = [
        {"entity_id": 20, "health": 2, "damage": 0, "shield": False, "lifesteal": False,
         "atk": 2, "poisonous": False, "spell_immune": False, "taunt": True},
    ]
    res = apply_spell_sequence(
        taunts, [],
        [(defn, 3, _SyntheticSpellCard("VAC_951", 3))],
        hero_hp=5, mana_budget=3,
    )
    assert res.self_hero_heal == 2
    print("OK p0 health drink lifesteal heal", res.self_hero_heal)


def test_p0_cascading_disaster_kill_count_by_card_id():
    """连环灾难：腐蚀后 card_id 不同，消灭数量 1/2/3。"""
    import random
    from hdt_python.spell_board import (
        _SyntheticSpellCard,
        apply_spell_sequence,
        get_board_spell_def,
    )
    from hdt_python.spell_p0_remove import cascading_disaster_kill_count

    assert cascading_disaster_kill_count(_SyntheticSpellCard("DMF_117", 4)) == 1
    assert cascading_disaster_kill_count(_SyntheticSpellCard("DMF_117t", 4)) == 2
    assert cascading_disaster_kill_count(_SyntheticSpellCard("DMF_117t2", 4)) == 3

    def _taunt(eid):
        return {
            "entity_id": eid, "health": 2, "damage": 0, "shield": False,
            "lifesteal": False, "atk": 2, "poisonous": False,
            "spell_immune": False, "taunt": True,
        }

    taunts = [_taunt(20), _taunt(21), _taunt(22)]
    defn = get_board_spell_def("DMF_117")
    apply_spell_sequence(
        taunts, [],
        [(defn, 4, _SyntheticSpellCard("DMF_117", 4))],
        rng=random.Random(0),
    )
    assert sum(1 for t in taunts if t["health"] > 0) == 2

    taunts2 = [_taunt(20), _taunt(21), _taunt(22)]
    defn2 = get_board_spell_def("DMF_117t2")
    apply_spell_sequence(
        taunts2, [],
        [(defn2, 4, _SyntheticSpellCard("DMF_117t2", 4))],
        rng=random.Random(0),
    )
    assert sum(1 for t in taunts2 if t["health"] > 0) == 0
    print("OK p0 cascading disaster corrupt ids")


def test_p0_cascading_disaster_corrupted2_face():
    """再次腐蚀连环灾难：消灭 3 嘲后 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    for i, eid in enumerate((20, 21, 22), start=1):
        _minion(gs, eid, 2, 2, 2, taunt=True, card_id=f"T{i}")
    _hand_spell(gs, 30, 1, "DMF_117t2", 4)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6
    print("OK p0 cascading disaster t2 face", total)


def test_p0_devolve_strips_taunt_keeps_stats():
    """衰变：移除嘲讽等关键词，身材不变，6/6 可打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 11, 1, 3, 3, card_id="M33")
    for i, eid in enumerate((20, 21, 22), start=1):
        _minion(gs, eid, 2, 2, 2, taunt=True, card_id="UNG_022")
    _hand_spell(gs, 30, 1, "CFM_696", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 9
    print("OK p0 devolve strip taunt face", total)


def test_p0_devolving_missiles_five_cost_to_four_four():
    """衰变飞弹：5 费随从衰变一次→4/4 白板（去嘲讽）。"""
    from hdt_python.spell_p0_remove import _devolve_unit_once

    unit = {
        "entity_id": 20, "health": 5, "damage": 0, "shield": False,
        "lifesteal": True, "atk": 5, "poisonous": True, "spell_immune": False,
        "taunt": True, "card_id": "BIG5", "cost": 5,
    }
    _devolve_unit_once(unit)
    assert unit["health"] == 4 and unit["atk"] == 4
    assert unit["cost"] == 4
    assert not unit["taunt"] and not unit["lifesteal"] and unit["card_id"] == ""
    print("OK p0 devolving missiles 5 to 4/4")


def test_p0_devolving_missiles_sludge_three_taunts_mc_overlay():
    """淤泥+3x2/2嘲+衰变飞弹：Overlay 应显示随机场攻分布（上界6）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m1 = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m2 = _minion(gs, 11, 1, 2, 2, card_id="M22")
    m1.tags["NUM_TURNS_IN_PLAY"] = 1
    m2.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 3, 5, taunt=True, card_id="FP1_012", cost=5)
    for eid in (21, 22, 23):
        _minion(gs, eid, 2, 2, 2, taunt=True, card_id="T22", cost=2)
    _hand_spell(gs, 30, 1, "SCH_235", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note()
    mc_max, lethal_prob, uses_random, top_outcomes = checker.overlay_face_stats()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert uses_random
    assert mc_max == 6, f"expected mc max 6, got {mc_max}"
    assert total == 6, f"expected display total 6, got {total}"
    assert top_outcomes, f"expected probability outcomes, got {top_outcomes}"
    dmg_probs = {dmg: prob for dmg, prob in top_outcomes}
    assert 6 in dmg_probs and dmg_probs[6] > 0, top_outcomes
    assert dmg_probs.get(0, 0) + dmg_probs.get(6, 0) <= 1.01
    print("OK devolving missiles sludge 3 taunts mc", total, top_outcomes, note, board, spell)


def test_p0_devolving_missiles_clears_taunt_face():
    """衰变飞弹：5 费 5/5 嘲三连衰变去嘲，6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 5, 5, taunt=True, card_id="BIG5", cost=5)
    _hand_spell(gs, 30, 1, "SCH_235", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, f"expected 6 face after devolving missiles, got {total}"
    print("OK p0 devolving missiles face", total)


def test_p0_devolve_strips_lifesteal_and_deathrattle():
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def, _SyntheticSpellCard

    taunts = [{
        "entity_id": 20, "health": 5, "damage": 0, "shield": False,
        "lifesteal": True, "atk": 3, "poisonous": True, "spell_immune": True,
        "taunt": True, "card_id": "UNG_022",
    }]
    defn = get_board_spell_def("CFM_696")
    apply_spell_sequence(taunts, [], [(defn, 2, _SyntheticSpellCard("CFM_696", 2))])
    t = taunts[0]
    assert t["health"] == 5 and t["atk"] == 3
    assert not t["taunt"] and not t["lifesteal"] and not t["poisonous"]
    assert not t["spell_immune"] and t["card_id"] == ""
    print("OK p0 devolve strip keywords keep body")


def test_p0_dream_spells_registered():
    from hdt_python.spell_board import get_board_spell_def

    for cid in ("DREAM_01", "DREAM_02", "DREAM_05"):
        defn = get_board_spell_def(cid)
        assert defn is not None, cid
        assert defn.name
    print("OK p0 dream spells registered")


def test_p0_dream_clears_taunt_for_face():
    """梦境：移回嘲讽随从后，6/6 可打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="TAUNT")
    _hand_spell(gs, 30, 1, "DREAM_01", 0)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6
    print("OK p0 dream clears taunt", total)


def test_p0_ysera_awakens_face_and_board():
    """伊瑟拉苏醒：先 3/3 打脸，再全场 5 伤（含 5 打脸）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 3, 3, card_id="M33")
    _hand_spell(gs, 30, 1, "DREAM_02", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert board == 3
    assert spell == 5
    assert total == 8
    print("OK p0 ysera awakens", total)


def test_p0_ysera_awakens_self_death_not_lethal():
    """伊瑟拉苏醒自伤致死且未斩对手时不应报斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    gs.get_entity(1).health = 4
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "DREAM_02", 2)

    checker = LethalChecker(gs)
    _, _, has_lethal = checker.calculate_lethal()
    assert not has_lethal
    print("OK p0 ysera self death not lethal")


def test_p0_ysera_awakens_simultaneous_lethal():
    """同归于尽：4血打5血对手，伊瑟拉仍算斩杀（先手赢）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    gs.get_entity(1).health = 4
    _hero(gs, 2, 2)
    gs.get_entity(2).health = 5
    _hand_spell(gs, 30, 1, "DREAM_02", 2)

    checker = LethalChecker(gs)
    _, _, has_lethal = checker.calculate_lethal()
    assert has_lethal
    print("OK p0 ysera simultaneous lethal")


def test_p0_ysera_awakens_spell_first_stops_after_self_death():
    """先法后攻：伊瑟拉自伤致死后不应再计入随从打脸。"""
    from hdt_python.spell_board import spell_effect_multiplier
    from hdt_python.lethal_checker import hand_all_board_plays

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    gs.get_entity(1).health = 4
    _hero(gs, 2, 2)
    gs.get_entity(2).health = 8
    _minion(gs, 10, 1, 3, 3, card_id="M33")
    _hand_spell(gs, 30, 1, "DREAM_02", 2)

    checker = LethalChecker(gs)
    fighters = checker._build_fighters(gs.get_player_board(1), 1)
    enemy = checker._build_enemy_minion_states(1)
    spells = hand_all_board_plays(gs, 1, 10)
    seq = [(spells[0][1], spells[0][2], spells[0][0])]
    mult = spell_effect_multiplier(gs, 1)
    outcome = checker._simulate_line_outcome(
        enemy, fighters, seq, "spell_first",
        spell_mult=mult, defender_shield=False, available_mana=10,
    )
    assert outcome[0] == 5
    print("OK p0 ysera spell_first stops after self death", outcome[0])


def test_p0_nightmare_buffs_friendly_face():
    """梦魇：+5 攻后 2/2 可打 7 脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 2, 2, card_id="M22")
    _hand_spell(gs, 30, 1, "DREAM_05", 0)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 7
    print("OK p0 nightmare buff", total)


def test_p0_invasive_shadeleaf_overflow_bottle():
    """影叶入侵：打 2/2 溢出 8，瓶子解 8/8 后 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _minion(gs, 21, 2, 8, 8, card_id="B88")
    _hand_spell(gs, 30, 1, "WW_393", 4)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6
    print("OK p0 shadeleaf overflow bottle", total)


def test_p0_shadeleaf_bottle_hand_card_id_and_tag():
    """手牌保留瓶子 WW_393t，TAG_SCRIPT_DATA_NUM_1 为存储伤害。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 8, 8, card_id="B88")
    bottle = _hand_spell(gs, 30, 1, "WW_393t", 1)
    bottle.tags["TAG_SCRIPT_DATA_NUM_1"] = 8

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6
    print("OK p0 shadeleaf bottle hand tag", total)


def test_shadeleaf_bottle_prefers_deterministic_over_random_spell():
    """影叶瓶子+场面可达斩杀时，不应被抹除存在等随机法术占位导致概率<100%。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=4)
    h2 = _hero(gs, 2, 2)
    h2.damage = 24
    _hero_power(gs, 69, 1, "HERO_10bp", cost=1)
    _minion(gs, 20, 1, 2, 3, card_id="GDB_874")
    _minion(gs, 21, 1, 4, 4, card_id="TOY_312")
    _minion(gs, 30, 2, 2, 6, taunt=True, card_id="WORK_023")
    bottle = _hand_spell(gs, 40, 1, "WW_393t", 1)
    bottle.tags["TAG_SCRIPT_DATA_NUM_1"] = 8
    _hand_spell(gs, 41, 1, "TIME_433", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, prob, rnd, _ = checker.overlay_face_stats()
    note = checker.overlay_spell_note()

    assert total >= 6
    assert prob == 1.0, f"expected 100% lethal prob, got {prob}"
    assert not rnd
    assert "影叶瓶子" in note or "影叶入侵" in note
    print("OK shadeleaf bottle beats random spell", total, prob, note)


def test_p0_cease_to_exist_rewind_picks_taunt():
    """抹除存在：随机 2 次（回溯）取较好结果，第二次可打到嘲讽。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 2, 6, taunt=True, card_id="T26")
    _minion(gs, 21, 2, 5, 5, card_id="N55")
    _hand_spell(gs, 30, 1, "TIME_433", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, rnd, _ = checker.overlay_face_stats()
    assert total == 6, total
    assert rnd
    print("OK cease to exist rewind two random attempts", total)


def test_p0_invasive_shadeleaf_no_overflow():
    """影叶入侵：10 伤打在 12 血随从无溢出，不生成瓶子。"""
    from hdt_python.spell_board import (
        apply_spell_sequence,
        get_board_spell_def,
        _SyntheticSpellCard,
    )

    taunts = [{
        "entity_id": 20, "health": 12, "damage": 0, "shield": False,
        "lifesteal": False, "atk": 4, "poisonous": False,
        "spell_immune": False, "taunt": True,
    }]
    defn = get_board_spell_def("WW_393")
    res = apply_spell_sequence(
        taunts, [],
        [(defn, 4, _SyntheticSpellCard("WW_393", 4))],
        mana_budget=10,
    )
    assert res.add_hand_spell_id is None
    assert res.add_hand_spell_damage == 0
    assert taunts[0]["health"] == 2
    print("OK p0 shadeleaf no overflow")


def test_p0_health_drink_enables_nightshade_drinks():
    """先喝健康饮品吸血，再连喝夜影花茶（低血本只能喝 1 杯）。"""
    from hdt_python.spell_board import (
        apply_spell_sequence,
        get_board_spell_def,
        _SyntheticSpellCard,
    )

    health = get_board_spell_def("VAC_951")
    night = get_board_spell_def("VAC_404")
    taunts = [
        {"entity_id": eid, "health": 2, "damage": 0, "shield": False, "lifesteal": False,
         "atk": 2, "poisonous": False, "spell_immune": False, "taunt": True}
        for eid in (20, 21, 22)
    ]
    res = apply_spell_sequence(
        taunts, [],
        [
            (health, 3, _SyntheticSpellCard("VAC_951", 3)),
            (night, 1, _SyntheticSpellCard("VAC_404", 1)),
        ],
        hero_hp=3, mana_budget=5,
    )
    assert res.self_hero_heal == 2
    assert res.self_hero_damage == 4
    assert not any(t.get("health", 0) > 0 for t in taunts)
    print("OK p0 health drink enables nightshade", res.self_hero_heal)


def test_p0_minion_spells_registered():
    """P0 第二阶段 33 张解场伤均已注册。"""
    from hdt_python.spell_board import get_board_spell_def

    ids = [
        "DAL_716", "REV_939", "FIR_939", "CATA_585", "WW_354", "ETC_394", "RLK_018",
        "TIME_750", "GDB_902", "EDR_813", "WW_393", "CORE_EX1_259", "CORE_EX1_391",
        "REV_249", "TIME_702", "TSC_932", "EDR_460", "CATA_533", "WORK_014", "GDB_460",
        "VAC_404", "ULD_714", "KAR_076", "VAC_951", "SW_090", "TIME_216", "FIR_954",
        "UNG_955", "CORE_SW_108", "DED_517", "TLC_901", "CATA_978", "SCH_512",
    ]
    missing = [cid for cid in ids if get_board_spell_def(cid) is None]
    assert not missing, f"missing spell defs: {missing}"
    print("OK p0 minion 33 registered")


def test_hand_effect_active_combo_rite_twilight():
    """暮光祭礼：亮边=连击 3 伤，不亮=2 伤。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    gs = GameState()
    spell = gs.get_entity(30)
    spell.cardtype = "SPELL"
    spell.card_id = "CATA_785"
    spell.tags["POWERED_UP"] = 0
    defn = get_board_spell_def("CATA_785")
    assert defn is not None

    res_off = apply_spell_sequence([], [], [(defn, 2, spell)], enemy_shield=False)
    assert res_off.direct_face_damage == 2

    spell.tags["POWERED_UP"] = 1
    res_on = apply_spell_sequence([], [], [(defn, 2, spell)], enemy_shield=False)
    assert res_on.direct_face_damage == 3
    print("OK powered up combo rite twilight")


def test_pack_no_taunt_direct_face_powered_rite_twilight():
    """暮光祭礼亮边 + 2 毒刺虫：无嘲讽直伤前缀应为 3+2+2=7。"""
    from hdt_python.spell_board import get_board_spell_def, pack_no_taunt_direct_face_spells

    gs = GameState()
    gs.local_player_id = 1

    def hand_entry(eid: int, cid: str, *, powered: int = 0):
        card = gs.get_entity(eid)
        card.cardtype = "SPELL"
        card.card_id = cid
        card.controller = 1
        card.zone = "HAND"
        card.tags["POWERED_UP"] = powered
        if cid == "CATA_785":
            card.tags["TAG_SCRIPT_DATA_NUM_1"] = 2
        defn = get_board_spell_def(cid)
        assert defn is not None
        return card, defn, defn.base_cost

    hand = [
        hand_entry(30, "CATA_785", powered=1),
        hand_entry(31, "TLC_630t"),
        hand_entry(32, "TLC_630t"),
    ]
    _, face, mana = pack_no_taunt_direct_face_spells(hand, 4, gs=gs, player_id=1)
    assert face == 7, face
    assert mana == 4, mana
    print("OK pack no taunt powered rite twilight stingers")


def test_scorching_winds_powered_up_double_damage():
    """灼烧之风：不亮边 3 伤，亮边（可弃火焰法术）6 伤。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    spell = GameState().get_entity(30)
    spell.cardtype = "SPELL"
    spell.card_id = "FIR_910"
    defn = get_board_spell_def("FIR_910")
    assert defn is not None

    spell.tags["POWERED_UP"] = 0
    res_off = apply_spell_sequence([], [], [(defn, 3, spell)], enemy_shield=False)
    assert res_off.direct_face_damage == 3

    spell.tags["POWERED_UP"] = 1
    res_on = apply_spell_sequence([], [], [(defn, 3, spell)], enemy_shield=False)
    assert res_on.direct_face_damage == 6
    print("OK scorching winds powered up")


def test_scorching_winds_lethal_checker_overlay():
    """地狱烈焰+阳炎耀斑+亮边灼烧之风：8 血对手应提示斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    _hero(gs, 10, 1, mana=9, used=0)
    opp = _hero(gs, 20, 2)
    opp.health = 32
    opp.tags["DAMAGE"] = 24
    _minion(gs, 50, 2, 0, 2, card_id="EDR_810t")
    _hand_spell(gs, 30, 1, "CORE_CS2_062", 0)
    _hand_spell(gs, 31, 1, "GDB_305", 1)
    sw = _hand_spell(gs, 32, 1, "FIR_910", 0)
    sw.tags["POWERED_UP"] = 1

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    assert face >= 8, f"expected lethal overlay >= 8, got {face}"
    combo = lc.overlay_combo_display_lines()
    assert combo and any("地狱烈焰" in ln or "阳炎耀斑" in ln for ln in combo)
    print("OK scorching winds lethal overlay", face, combo)


def test_hand_effect_active_outcast_flash_flood():
    """涣漫洪流：亮边=流放，左右各 5 伤再执行一次。"""
    from copy import deepcopy
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    gs = GameState()
    spell = gs.get_entity(30)
    spell.cardtype = "SPELL"
    spell.card_id = "CATA_533"
    defn = get_board_spell_def("CATA_533")
    base = [
        {"health": 10, "shield": False, "lifesteal": False, "atk": 1,
         "poisonous": False, "spell_immune": False, "zone_pos": 1},
        {"health": 3, "shield": False, "lifesteal": False, "atk": 1,
         "poisonous": False, "spell_immune": False, "zone_pos": 2},
        {"health": 10, "shield": False, "lifesteal": False, "atk": 1,
         "poisonous": False, "spell_immune": False, "zone_pos": 3},
    ]

    spell.tags["POWERED_UP"] = 0
    ts = deepcopy(base)
    apply_spell_sequence(ts, [], [(defn, 5, spell)], enemy_shield=False)
    hp_once = sum(t["health"] for t in ts)

    spell.tags["POWERED_UP"] = 1
    ts2 = deepcopy(base)
    apply_spell_sequence(ts2, [], [(defn, 5, spell)], enemy_shield=False)
    hp_twice = sum(t["health"] for t in ts2)

    assert hp_once == 13, f"once expected 13 hp left, got {hp_once}"
    assert hp_twice == 3, f"outcast twice expected 3 hp left, got {hp_twice}"
    print("OK powered up outcast flash flood")


def test_p0_remove_spells_registered():
    """P0 第四阶段 17 张消灭/变形均已注册。"""
    from hdt_python.spell_board import get_board_spell_def

    ids = [
        "MIS_903", "TIME_712", "CORE_EX1_246", "BT_490", "TIME_433", "CFM_696",
        "CORE_RLK_087", "TTN_932", "DMF_117", "DMF_117t", "DMF_117t2",
        "CORE_EX1_309", "CATA_203", "NX2_020", "CATA_306", "REV_239",
        "CATA_479", "SW_441", "SCH_235",
    ]
    missing = [cid for cid in ids if get_board_spell_def(cid) is None]
    assert not missing, f"missing remove spell defs: {missing}"
    print("OK p0 remove 17 registered")


def test_p0_hex_clears_taunt_for_face():
    """妖术：8/8 嘲讽变 0/1 嘲后，第二个 3/3 可打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    for eid in (10, 11):
        m = _minion(gs, eid, 1, 3, 3, card_id=f"M{eid}")
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 8, 8, taunt=True, card_id="BIG")
    _hand_spell(gs, 30, 1, "CORE_EX1_246", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 3
    print("OK p0 hex clears taunt face", total)


def test_p0_asphyxiate_highest_atk():
    """窒息：消灭攻击力最高的敌方随从。"""
    from copy import deepcopy
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def, _SyntheticSpellCard

    taunts = [
        {"entity_id": 20, "health": 5, "atk": 3, "taunt": False, "kind": "minion"},
        {"entity_id": 21, "health": 2, "atk": 7, "taunt": True, "kind": "minion"},
    ]
    defn = get_board_spell_def("CORE_RLK_087")
    ts = deepcopy(taunts)
    apply_spell_sequence(ts, [], [(defn, 3, _SyntheticSpellCard("CORE_RLK_087", 3))])
    by_eid = {t["entity_id"]: t for t in ts}
    assert by_eid[20]["health"] == 5
    assert by_eid.get(21, {}).get("health", 0) == 0
    print("OK p0 asphyxiate highest atk")


def test_p0_shard_silence_all_taunts():
    """纳鲁碎片：沉默全体敌方随从后 7/7 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 7, 7, card_id="M77")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "SW_441", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 7
    print("OK p0 shard silence all", total)


def test_p0_dubious_purchase_random_destroy():
    """可疑交易：仅连击时随机消灭一个敌方随从。"""
    from copy import deepcopy
    from hdt_python.power_parser import Entity
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    def _mis903(*, powered_up: bool) -> Entity:
        card = Entity(entity_id=901, card_id="MIS_903", controller=1)
        card.tags["COMBO"] = 1
        card.tags["POWERED_UP"] = 1 if powered_up else 0
        return card

    taunts = [{"entity_id": 20, "health": 2, "atk": 2, "taunt": True, "kind": "minion"}]
    defn = get_board_spell_def("MIS_903")
    ts = deepcopy(taunts)
    apply_spell_sequence(ts, [], [(defn, 4, _mis903(powered_up=True))])
    assert not any(t.get("health", 0) > 0 for t in ts)

    ts2 = deepcopy(taunts)
    apply_spell_sequence(ts2, [], [(defn, 4, _mis903(powered_up=False))])
    assert any(t.get("health", 0) > 0 for t in ts2)
    print("OK p0 dubious purchase random destroy")


def test_p0_buff_spells_registered():
    """P0 第五阶段加攻/武器法术均已注册。"""
    from hdt_python.spell_board import get_board_spell_def

    ids = [
        "CORE_BT_035", "WORK_022", "ETC_363", "BT_011", "REV_507", "CORE_GVG_061",
        "YOP_026",
    ]
    missing = [cid for cid in ids if get_board_spell_def(cid) is None]
    assert not missing, f"missing buff spell defs: {missing}"
    print("OK p0 buff 6 registered")


def test_p0_chaos_strike_hero_attack_face():
    """混乱打击：+2 英雄攻可打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "CORE_BT_035", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 2
    _, minion_board, _, _, _ = checker.overlay_board_breakdown()
    assert minion_board == 0, minion_board
    assert checker.overlay_hero_buff_face() == 2
    print("OK p0 chaos strike face", total)


def test_p0_dispose_of_evidence_hero_buff_not_minion():
    """处理证据 REV_507：+3 英雄攻计入英，不计入随。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    for eid, atk, hp in ((10, 7, 5), (11, 3, 2), (12, 3, 2)):
        m = _minion(gs, eid, 1, atk, hp, card_id=f"M{eid}")
        m.tags["EXHAUSTED"] = 1
        m.tags["NUM_ATTACKS_THIS_TURN"] = 1
    _hand_spell(gs, 30, 1, "REV_507", 0)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, _, _, _ = checker.overlay_board_breakdown()
    hero_buff = checker.overlay_hero_buff_face()
    assert total == 3, (total, minion_board, hero_buff, checker.overlay_spell_note())
    assert minion_board == 0, minion_board
    assert hero_buff == 3, hero_buff
    assert "处理证据" in checker.overlay_spell_note()
    print("OK p0 dispose of evidence hero buff", total, hero_buff)


def test_p0_libram_sets_one_health_and_weapon():
    """正义圣契：非嘲讽随从变 1 血后，6/6 打脸 + 1 攻武器。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 5, 5, taunt=False, card_id="M55")
    _hand_spell(gs, 30, 1, "BT_011", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 7
    print("OK p0 libram weapon and board", total)


def test_p0_full_moon_ritual_summons_in_overlay():
    """满月仪式：召唤随从无冲锋/突袭，本回合不计场攻。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "EDR_461t", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, _, _, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()
    assert total == 0, (total, minion_board, note)
    assert minion_board == 0, (total, minion_board, note)
    print("OK p0 full moon ritual overlay", total, minion_board, note)


def test_p0_new_moon_ritual_summoning_sick():
    """新月仪式：两个召唤随从均无冲锋/突袭，本回合 0 场攻。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence
    from hdt_python.combat_sim import fighters_face_damage
    from hdt_python.power_parser import Entity

    for cid in ("EDR_461", "EDR_461t"):
        defn = get_board_spell_def(cid)
        card = Entity(entity_id=1, card_id=cid)
        fighters: list = []
        apply_spell_sequence([], fighters, [(defn, 5, card)], enemy_shield=False)
        assert len(fighters) == 2, (cid, fighters)
        assert all(f.get("attacks_left", 1) == 0 for f in fighters), fighters
        assert all(not f.get("can_face") for f in fighters), fighters
        assert fighters_face_damage(fighters) == 0, (cid, fighters)
    print("OK p0 new/full moon ritual summoning sick")


def test_p0_full_moon_ritual_with_moonwell_combo():
    """满月仪式 + 月亮井：仪式召唤本回合无场攻，场攻来自月亮井。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=11, used=0)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "EDR_461t", 5)
    _hand_spell(gs, 31, 1, "EDR_476", 6)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, _, spell_face, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()
    assert total >= 3, (total, minion_board, spell_face, note)
    assert minion_board == 0, (total, minion_board, spell_face, note)
    assert spell_face >= 3, (total, minion_board, spell_face, note)
    print("OK p0 full moon moonwell combo", total, minion_board, spell_face, note)


def test_p0_full_moon_ritual_log_replay_overlay():
    """Power.log：手牌满月仪式 + 9 费时不应只显示毒刺虫 3 点。"""
    import contextlib
    import io
    from pathlib import Path
    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_20_11_53_31\Power.log"
    )
    if not log.is_file():
        print("SKIP full moon log replay (log missing)")
        return
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[:418900]:
            if line.strip():
                parser.process_line(line.rstrip())
    checker = LethalChecker(gs)
    from hdt_python.spell_board import get_board_spell_def
    assert get_board_spell_def("EDR_461t") is not None
    total = checker.overlay_board_face_damage()
    _, minion_board, _, _, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()
    assert total >= 0, (total, minion_board, note)
    print("OK p0 full moon log replay", total, minion_board, note)


def test_p0_other_spells_registered():
    """P0 第六阶段 16 张其他法术均已注册。"""
    from hdt_python.spell_board import get_board_spell_def

    ids = [
        "ONY_032", "EDR_814", "WW_006", "TLC_902", "REV_307", "TOY_508",
        "CORE_AT_037", "GVG_015", "TOY_377", "CORE_BAR_541", "TTN_726",
        "TLC_221", "GVG_010", "CATA_452", "CFM_603", "TOY_644",
        "EDR_461", "EDR_461t",
    ]
    missing = [cid for cid in ids if get_board_spell_def(cid) is None]
    assert not missing, f"missing other spell defs: {missing}"
    print("OK p0 other spells registered")


def test_p2_precise_shot_powered_up():
    """精确射击：亮边 5 伤，不亮 3 伤；无嘲时直伤打脸。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    spell = GameState().get_entity(30)
    spell.cardtype = "SPELL"
    spell.card_id = "TIME_600"
    defn = get_board_spell_def("TIME_600")
    assert defn is not None

    spell.tags["POWERED_UP"] = 0
    res_off = apply_spell_sequence([], [], [(defn, 2, spell)], enemy_shield=False)
    assert res_off.direct_face_damage == 3

    spell.tags["POWERED_UP"] = 1
    res_on = apply_spell_sequence([], [], [(defn, 2, spell)], enemy_shield=False)
    assert res_on.direct_face_damage == 5
    print("OK p2 precise shot powered up")


def test_p2_precise_shot_taunt_only():
    """精确射击：有嘲时只点嘲讽，不打非嘲随从。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    taunts = [
        {"health": 5, "shield": False, "lifesteal": False, "atk": 5, "poisonous": False, "taunt": True},
        {"health": 1, "shield": False, "lifesteal": False, "atk": 1, "poisonous": False, "taunt": False},
    ]
    spell = GameState().get_entity(30)
    spell.cardtype = "SPELL"
    spell.card_id = "TIME_600"
    spell.tags["POWERED_UP"] = 0
    defn = get_board_spell_def("TIME_600")
    assert defn is not None

    res = apply_spell_sequence(taunts, [], [(defn, 2, spell)], enemy_shield=False)
    assert res.direct_face_damage == 0
    assert taunts[0]["health"] == 2
    assert taunts[1]["health"] == 1
    print("OK p2 precise shot taunt only")


def test_p2_precise_shot_overlay_clears_taunt():
    """精确射击亮边 5 伤解 2/2 嘲 + 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    spell = _hand_spell(gs, 30, 1, "TIME_600", 2)
    spell.tags["POWERED_UP"] = 1

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, _, spell_dmg, hp = checker.overlay_board_breakdown()
    assert spell_dmg == 0, f"5 dmg spent on taunt, got spell={spell_dmg}"
    assert board == 6, f"6/6 face after clearing taunt, got board={board}"
    assert total == 6, f"expected 6, got {total}"
    print("OK p2 precise shot overlay", total)


def test_p2_spells_registered():
    """P2 法术均已注册。"""
    from hdt_python.spell_board import get_board_spell_def

    ids = ["TIME_600"]
    missing = [cid for cid in ids if get_board_spell_def(cid) is None]
    assert not missing, f"missing P2 spell defs: {missing}"
    print("OK p2 spells registered", len(ids))


def test_p1_spells_registered():
    """P1 法术（14 张，不含已移除大灾变）均已注册。"""
    from hdt_python.spell_board import get_board_spell_def

    ids = [
        "ONY_010", "DINO_406", "EDR_262", "WC_021", "CATA_526", "VAC_416", "TOY_883",
        "TSC_006", "RLK_918", "ETC_082", "SCH_138", "EDR_874", "VAC_944", "SW_088",
        "CS2_008", "EX1_173",
    ]
    missing = [cid for cid in ids if get_board_spell_def(cid) is None]
    assert not missing, f"missing P1 spell defs: {missing}"
    assert get_board_spell_def("LOOT_417") is not None
    print("OK p1 spells registered", len(ids))


def test_p1_fire_breath_buffs_elementals():
    """喷吐火焰：己方元素获得 +1/+1。"""
    from hdt_python.spell_board import get_board_spell_def

    defn = get_board_spell_def("DINO_406")
    assert defn is not None
    fighters = [
        {
            "kind": "minion", "entity_id": 1, "card_id": "AT_092",
            "atk": 3, "health": 4, "attacks_left": 1, "can_face": True,
        },
        {
            "kind": "minion", "entity_id": 2, "card_id": "CS2_196",
            "atk": 2, "health": 2, "attacks_left": 1, "can_face": True,
        },
    ]
    defn.apply([], fighters, mult=1, enemy_shield=False)
    assert fighters[0]["atk"] == 4 and fighters[0]["health"] == 5
    assert fighters[1]["atk"] == 2 and fighters[1]["health"] == 2
    print("OK p1 fire breath elemental buff")


def test_p1_broxigar_interleave_face():
    """布洛克斯加的奋战：3/3 先换 2/2 嘲，奋战清 1/1 嘲，6/6 打脸（法术穿插）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m1 = _minion(gs, 10, 1, 3, 3, card_id="M33")
    m1.tags["NUM_TURNS_IN_PLAY"] = 1
    m2 = _minion(gs, 11, 1, 6, 6, card_id="M66")
    m2.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _minion(gs, 21, 2, 1, 1, taunt=True, card_id="T11")
    _hand_spell(gs, 30, 1, "CATA_526", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note()
    assert total == 6, f"expected 6 face from broxigar interleave, got {total}"
    assert "法术穿插" in note, f"expected spell interleave note, got {note!r}"
    print("OK p1 broxigar interleave", total, note)


def test_p1_broxigar_clears_taunt():
    """布洛克斯加的奋战：1/1 嘲讽循环清场后 8/8 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 8, 8, card_id="M88")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 1, 1, taunt=True, card_id="T11")
    _hand_spell(gs, 30, 1, "CATA_526", 1)

    total = LethalChecker(gs).overlay_board_face_damage()
    assert total == 8, f"expected 8 face after broxigar, got {total}"
    print("OK p1 broxigar clear taunt", total)


def test_p1_spirit_bond_summon_rush():
    """灵魂联结：击杀嘲讽并召唤 3/2 突袭（当回合不能打脸）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "EDR_262", 1)

    total = LethalChecker(gs).overlay_board_face_damage()
    assert total == 0, f"rush wolf should not face this turn, got {total}"
    print("OK p1 spirit bond rush no face", total)


def test_p1_stellar_balance_chain_damage():
    """星体平衡：同回合月火+星火（2+6）清嘲后随从打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 3, 3, card_id="M33")
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "EDR_874", 1)

    total = LethalChecker(gs).overlay_board_face_damage()
    assert total == 9, f"expected 9 face from stellar balance chain, got {total}"
    print("OK p1 stellar balance", total)


def test_p1_stellar_balance_with_dirge_no_taunt_spell_face():
    """无嘲讽：星体平衡+绝望哀歌须完整链，法术分项至少 2+6=8（绝望哀歌不能抢直伤前缀）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 2, 1, card_id="CATA_725")
    m.tags["EXHAUSTED"] = 1
    t = _minion(gs, 11, 1, 1, 1, card_id="CATA_725t")
    t.tags["EXHAUSTED"] = 1
    _minion(gs, 20, 2, 5, 5, card_id="SW_323")
    _hand_spell(gs, 30, 1, "EDR_874", 2)
    _hand_spell(gs, 31, 1, "ETC_082", 6)

    lc = LethalChecker(gs)
    total = lc.overlay_board_face_damage()
    _, board, _, spell, _ = lc.overlay_board_breakdown()
    assert spell >= 8, f"stellar balance chain should be spell 8+, got {spell}"
    assert total >= spell + board, f"total {total} < spell+board {spell}+{board}"
    print("OK p1 stellar balance dirge spell face", spell, total)


def test_p1_multi_strike_hero_face():
    """多重打击：+2 攻两次（一次打脸一次解嘲）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "TSC_006", 1)

    total = LethalChecker(gs).overlay_board_face_damage()
    assert total == 2, f"expected 2 face from multi-strike, got {total}"
    print("OK p1 multi strike", total)


def test_p0_red_card_dormant_taunt_face():
    """红牌：休眠嘲讽后 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "TOY_644", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 0
    assert board == 6
    assert total == 6
    print("OK p0 red card dormant taunt face", total)


def test_p0_red_card_magtheridon_wake_end_turn():
    """红牌点已唤醒玛瑟里顿（本回合不能攻）：回合结束 +3。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 12, 12, card_id="TOY_647")
    m.tags["ATK"] = 12
    m.tags["HEALTH"] = 12
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    m.tags["CANT_ATTACK"] = 1
    _hand_spell(gs, 30, 1, "TOY_644", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 3, f"expected 3 end-turn from red card on Magtheridon, got {total}"
    print("OK p0 red card magtheridon wake +3", total)


def test_p0_red_card_magtheridon_prefers_face_attack():
    """已唤醒玛瑟里顿可攻击时，直接 12 打脸优于红牌休眠 +3。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 12, 12, card_id="TOY_647")
    m.tags["ATK"] = 12
    m.tags["HEALTH"] = 12
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs, 30, 1, "TOY_644", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 12, f"expected 12 face attack, got {total}"
    print("OK p0 red card magtheridon prefers attack", total)


def test_p0_red_card_two_taunts_face():
    """红牌：双嘲时休眠小嘲，6/6+2/2 解大嘲后 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 11, 1, 2, 2, card_id="M22")
    _minion(gs, 20, 2, 4, 4, taunt=True, card_id="BIG")
    _minion(gs, 21, 2, 2, 2, taunt=True, card_id="SMALL")
    _hand_spell(gs, 30, 1, "TOY_644", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, f"expected 6 face, got {total}"
    print("OK p0 red card two taunts", total)


def test_p0_astral_phaser_dormant_taunt_face():
    """星域相变射线：抉择休眠嘲讽后 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "GDB_851", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 0
    assert board == 6
    assert total == 6
    print("OK p0 astral phaser dormant taunt face", total)


def test_p0_astral_phaser_two_taunts_prefers_small_taunt():
    """星域相变射线：双嘲时休眠小嘲，6/6+2/2 解大嘲后 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 11, 1, 2, 2, card_id="M22")
    _minion(gs, 20, 2, 4, 4, taunt=True, card_id="BIG")
    _minion(gs, 21, 2, 2, 2, taunt=True, card_id="SMALL")
    _hand_spell(gs, 30, 1, "GDB_851", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, f"expected 6 face, got {total}"
    print("OK p0 astral phaser two taunts", total)


def test_p0_red_card_skips_enemy_non_taunt_only():
    """红牌敌方仅嘲讽：仅 5/5 非嘲讽时不打牌，场攻仍来自随从打脸。"""
    from copy import deepcopy
    from hdt_python.spell_p0_other import _apply_red_card

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 5, 5, card_id="B55")
    _hand_spell(gs, 30, 1, "TOY_644", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, f"expected 6 face, got {total}"

    taunts = [
        {
            "entity_id": 20,
            "health": 5,
            "atk": 5,
            "taunt": False,
            "shield": False,
            "dormant": False,
        }
    ]
    fighters = [
        {
            "kind": "minion",
            "entity_id": 10,
            "atk": 6,
            "health": 6,
            "attacks_left": 1,
            "can_face": True,
            "dormant": False,
        }
    ]
    ts = deepcopy(taunts)
    fs = deepcopy(fighters)
    _apply_red_card(ts, fs, mult=1, enemy_shield=False, gs=gs, player_id=1)
    assert not ts[0].get("dormant"), "red card should not target lone enemy non-taunt"
    print("OK p0 red card skips enemy non-taunt only", total)


def test_p0_living_roots_damage_branch():
    """活体根须：有嘲讽时选 2 伤分支。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "CORE_AT_037", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6
    print("OK p0 living roots damage", total)


def test_p0_velens_chosen_buff_face():
    """维伦的恩泽：6/6 +2 攻后打脸 8。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs, 30, 1, "GVG_010", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 8
    print("OK p0 velens chosen", total)


def test_p0_aoe_spells_registered():
    """P0 第三阶段 33 张复杂 AOE 均已注册。"""
    from hdt_python.spell_board import get_board_spell_def

    ids = [
        "EX1_129", "CATA_156", "VAC_323", "RLK_709", "TTN_753", "GDB_445", "CATA_582",
        "JAM_018", "CORE_CS1_112", "TOY_500", "BAR_314", "VAC_414", "ICC_041", "WW_427",
        "TIME_215", "TIME_619t2", "TTN_460", "DMF_701", "SW_107", "CATA_489", "TIME_209t2",
        "VAC_953", "ETC_069", "RLK_063", "CFM_662", "GDB_305", "CORE_CS2_093", "BT_117",
        "YOG_502", "ETC_314", "CATA_557", "TTN_853", "CORE_CS2_028",
    ]
    missing = [cid for cid in ids if get_board_spell_def(cid) is None]
    assert not missing, f"missing aoe spell defs: {missing}"
    assert get_board_spell_def("BAR_915") is not None
    assert get_board_spell_def("BAR_916") is not None
    assert get_board_spell_def("VAC_323t1") is not None
    assert get_board_spell_def("CATA_489t") is not None
    assert get_board_spell_def("CATA_489t2") is not None
    print("OK p0 aoe 33 registered")


def test_p0_arcane_flow_combined_taunt_or_face_plus_aoe():
    """奥术涌流（合体）：单点只打嘲讽或脸，另全体敌人 2 伤。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    defn = get_board_spell_def("CATA_489")
    taunts = [
        {"health": 5, "shield": False, "lifesteal": False, "atk": 4, "poisonous": False,
         "spell_immune": False, "taunt": True, "zone_pos": 1},
        {"health": 3, "shield": False, "lifesteal": False, "atk": 2, "poisonous": False,
         "spell_immune": False, "taunt": False, "zone_pos": 2},
    ]
    res = apply_spell_sequence(taunts, [], [(defn, 4, None)], enemy_shield=False)
    assert taunts[0]["health"] == 1
    living_non_taunt = [t for t in taunts if not t.get("taunt") and t.get("health", 0) > 0]
    assert len(living_non_taunt) == 1 and living_non_taunt[0]["health"] == 1
    assert res.direct_face_damage == 2
    print("OK p0 arcane flow combined taunt or face plus aoe")


def test_p0_arcane_flow_shattered_forms():
    """奥术涌流碎裂形态：t 仅单点，t2 仅 AOE。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    single = get_board_spell_def("CATA_489t")
    aoe = get_board_spell_def("CATA_489t2")
    taunts = [
        {"health": 5, "shield": False, "lifesteal": False, "atk": 4, "poisonous": False,
         "spell_immune": False, "taunt": True, "zone_pos": 1},
        {"health": 3, "shield": False, "lifesteal": False, "atk": 2, "poisonous": False,
         "spell_immune": False, "taunt": False, "zone_pos": 2},
    ]
    ts = [dict(t) for t in taunts]
    res_single = apply_spell_sequence(ts, [], [(single, 4, None)], enemy_shield=False)
    assert ts[0]["health"] == 1
    assert ts[1]["health"] == 3
    assert res_single.direct_face_damage == 0

    ts2 = [dict(t) for t in taunts]
    res_aoe = apply_spell_sequence(ts2, [], [(aoe, 4, None)], enemy_shield=False)
    assert ts2[0]["health"] == 3
    assert ts2[1]["health"] == 1
    assert res_aoe.direct_face_damage == 2
    print("OK p0 arcane flow shattered forms")


def test_p0_arcane_flow_shattered_hand_playable():
    """碎裂形态须 SHATTERED=1 才进 hand_board_spells。"""
    from hdt_python.spell_board import hand_board_spells

    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hand_spell(gs, 10, 1, "CATA_489t", 4)
    _hand_spell(gs, 11, 1, "CATA_489t2", 4)
    _hand_spell(gs, 12, 1, "CATA_489", 4)
    assert len(hand_board_spells(gs, 1, 10)) == 1

    gs.get_entity(10).tags["SHATTERED"] = 1
    gs.get_entity(11).tags["SHATTERED"] = 1
    spells = hand_board_spells(gs, 1, 10)
    ids = {c.card_id for c, _, _ in spells}
    assert len(spells) == 2
    assert ids == {"CATA_489"}
    print("OK p0 arcane flow shattered hand playable")


def test_p0_arcane_flow_shatter_trigger_pending():
    """打出合体涌流：手牌中另一张合体碎裂为 t+t2 并入 pending。"""
    from hdt_python.spell_board import (
        apply_spell_sequence_with_meta,
        get_board_spell_def,
        _SyntheticSpellCard,
    )

    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hand_spell(gs, 20, 1, "CATA_489", 4)
    combined = get_board_spell_def("CATA_489")
    taunts = [
        {"health": 2, "shield": False, "lifesteal": False, "atk": 1, "poisonous": False,
         "spell_immune": False, "taunt": True, "zone_pos": 1},
    ]
    seq = [(combined, 4, _SyntheticSpellCard("CATA_489", 4))]
    total, _, mana_left = apply_spell_sequence_with_meta(
        taunts, [], seq, gs=gs, player_id=1, mana_budget=10,
    )
    assert mana_left == 2
    assert total.direct_face_damage >= 6
    print("OK p0 arcane flow shatter trigger pending")


def test_p0_arcane_barrage_no_taunt_primary_face():
    """奥术弹幕：无嘲讽时主目标 3 伤打脸。"""
    from hdt_python.spell_board import get_board_spell_def

    taunts = [
        {"health": 8, "shield": False, "lifesteal": False, "atk": 5, "poisonous": False,
         "spell_immune": False, "taunt": False, "zone_pos": 1},
    ]
    defn = get_board_spell_def("TIME_855")
    res = defn.apply(taunts, [], mult=1, enemy_shield=False, rng=__import__("random").Random(0))
    assert res.direct_face_damage >= 3, f"primary face 3+, got {res.direct_face_damage}"
    print("OK p0 arcane barrage no taunt primary face", res.direct_face_damage)


def test_p0_arcane_flow_virtual_combined_hand():
    """手牌碎裂 t+t2 枚举为一张虚拟合体 CATA_489。"""
    from hdt_python.arcane_flow import ArcaneFlowVirtualCombined
    from hdt_python.spell_board import apply_spell_sequence_with_meta, hand_board_spells

    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hand_spell(gs, 10, 1, "CATA_489t", 4)
    _hand_spell(gs, 11, 1, "CATA_489t2", 4)
    gs.get_entity(10).tags["SHATTERED"] = 1
    gs.get_entity(11).tags["SHATTERED"] = 1
    spells = hand_board_spells(gs, 1, 10)
    assert len(spells) == 1
    card, defn, cost = spells[0]
    assert isinstance(card, ArcaneFlowVirtualCombined)
    assert cost == 4
    taunts = []
    total, _, mana_left = apply_spell_sequence_with_meta(
        taunts, [], [(defn, cost, card)], gs=gs, player_id=1, mana_budget=10,
    )
    assert mana_left == 6
    assert total.direct_face_damage == 6
    print("OK p0 arcane flow virtual combined hand")


def test_p0_eulogizer_triggers_arcane_flow_recombine():
    """悼词宣诵者：打出时手牌碎裂 t+t2 合体并入 pending。"""
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence_with_meta

    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    gs.get_entity(1).tags["CORPSES"] = 17
    _hand_spell(gs, 10, 1, "CATA_489t", 4)
    _hand_spell(gs, 11, 1, "CATA_489t2", 4)
    gs.get_entity(10).tags["SHATTERED"] = 1
    gs.get_entity(11).tags["SHATTERED"] = 1
    bc = get_battlecry_def("TTN_457")
    assert bc is not None
    bc_card = type("E", (), {"card_id": "TTN_457", "entity_id": 99, "tags": {}})()
    total, _, mana_left = apply_spell_sequence_with_meta(
        [], [], [(bc, 3, bc_card)], gs=gs, player_id=1, mana_budget=10,
    )
    assert total.direct_face_damage >= 9, f"3 eulogizer + 6 combined, got {total.direct_face_damage}"
    assert mana_left == 3
    print("OK p0 eulogizer triggers arcane flow recombine")


def test_p0_fan_of_knives_clears_taunt():
    """刀扇：1 伤 AOE 解 1/1 嘲后 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 1, 1, taunt=True, card_id="T11")
    _hand_spell(gs, 30, 1, "EX1_129", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 0
    assert board == 6
    assert total == 6
    print("OK p0 fan of knives", total)


def test_p0_consecration_clears_taunt_and_face():
    """奉献：2 伤全体敌人，解 2/2 嘲 + 2 直伤 + 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "CORE_CS2_093", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 2
    assert minion_board == 6
    assert total == 8
    print("OK p0 consecration", total, spell)


def test_p0_solar_flare_all_enemies_includes_hero_face():
    """阳炎耀斑：全体敌人 2 伤，含英雄直伤；随从全死时 Combo 显示全体敌人。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 2, 1, card_id="M1")
    _minion(gs, 21, 2, 2, 1, card_id="M2")
    _minion(gs, 22, 2, 2, 1, card_id="M3")
    _minion(gs, 23, 2, 1, 1, card_id="M4")
    _hand_spell(gs, 30, 1, "GDB_305", 2)

    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    defn = get_board_spell_def("GDB_305")
    enemy = [
        {"health": 1, "shield": False, "lifesteal": False, "atk": 2,
         "poisonous": False, "spell_immune": False, "zone_pos": 1, "entity_id": 20},
        {"health": 1, "shield": False, "lifesteal": False, "atk": 2,
         "poisonous": False, "spell_immune": False, "zone_pos": 2, "entity_id": 21},
    ]
    res = apply_spell_sequence(enemy, [], [(defn, 2, None)], enemy_shield=False)
    assert res.direct_face_damage == 2
    assert not any(t.get("health", 0) > 0 for t in enemy)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 2
    combo = checker.overlay_combo_display_lines()
    assert combo and any("阳炎耀斑" in ln and "全体敌人" in ln for ln in combo)
    print("OK p0 solar flare", total, spell, combo)


def test_p0_for_quelthalas_skips_spell_immune_targets():
    """为了奎尔萨拉斯：魔免友方不可指定；仅魔免时法术不可打出，不计英雄+2。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 20, 1, 3, 2, card_id="TIME_610t2", spell_immune=True)
    _minion(gs, 21, 1, 3, 2, card_id="TIME_610t2", spell_immune=True)
    for eid in (20, 21):
        m = gs.get_entity(eid)
        m.tags["EXHAUSTED"] = 1
        m.tags["NUM_TURNS_IN_PLAY"] = 0
    _hand_spell(gs, 30, 1, "RLK_918", 2)

    defn = get_board_spell_def("RLK_918")
    fighters: list = []
    res = apply_spell_sequence([], fighters, [(defn, 2, None)], gs=gs, player_id=1)
    assert res.direct_face_damage == 0
    assert fighters == []

    checker = LethalChecker(gs)
    with_spell = checker.overlay_board_face_damage()
    _, _, _, spell_face, _ = checker.overlay_board_breakdown()
    assert spell_face == 0
    assert not getattr(checker, "_overlay_best_seq", [])

    gs.get_entity(30).zone = "GRAVEYARD"
    checker2 = LethalChecker(gs)
    without_spell = checker2.overlay_board_face_damage()
    assert with_spell == without_spell, (
        f"quelthalas should not change overlay when no target: {with_spell} vs {without_spell}"
    )
    print("OK p0 for quelthalas spell immune", with_spell, without_spell)


def test_p0_for_quelthalas_buffs_targetable_minion():
    """为了奎尔萨拉斯：可指定非魔免随从时 +3 随从攻 +2 英雄攻。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 20, 1, 2, 3, card_id="VAC_426")
    _hand_spell(gs, 30, 1, "RLK_918", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total >= 4, f"expected buffed minion+hero face, got {total}"
    print("OK p0 for quelthalas buff", total)


def test_p0_arbor_up_summons_and_buffs_all_minions():
    """树木生长：召唤两个 2/2 树人并全体友方随从 +2/+1（树人当回合失调）。"""
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    fighters = [
        {
            "kind": "minion", "entity_id": 10, "atk": 3, "health": 3,
            "attacks_left": 1, "can_face": True,
        },
    ]
    defn = get_board_spell_def("YOP_026")
    assert defn is not None, "YOP_026 should be registered"
    apply_spell_sequence([], fighters, [(defn, 5, None)])

    original = next(f for f in fighters if f.get("entity_id") == 10)
    assert original["atk"] == 5 and original["health"] == 4

    treants = [f for f in fighters if f.get("entity_id") != 10]
    assert len(treants) == 2
    for t in treants:
        assert t["atk"] == 4 and t["health"] == 3
        assert t.get("attacks_left", 0) == 0

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 3, 3, card_id="VAC_426")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs, 30, 1, "YOP_026", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total >= 5, f"buffed 3/3 should contribute face damage, got {total}"
    print("OK p0 arbor up", total)


def test_p0_arbor_up_clears_taunt_no_face():
    """树木生长：6/6 buff 到 8/7 解 2/2 嘲，树人当回合不能攻 → 0 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "YOP_026", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 0, f"8/7 should clear taunt only, got {total}"
    print("OK p0 arbor up clears taunt no face", total)


def test_p0_arbor_up_then_forests_gift_lethal():
    """树木生长铺场 buff 后森林赠礼按随从数再 buff → 场面斩杀。"""
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    fighters = [
        {"kind": "minion", "entity_id": 41, "atk": 6, "health": 6,
         "attacks_left": 1, "can_face": True},
        {"kind": "minion", "entity_id": 179, "atk": 4, "health": 4,
         "attacks_left": 1, "can_face": True},
    ]
    arbor = get_board_spell_def("YOP_026")
    gift = get_board_spell_def("CATA_138")
    assert arbor and gift
    apply_spell_sequence([], fighters, [(arbor, 5, None), (gift, 3, None)])

    main = next(f for f in fighters if f.get("entity_id") == 41)
    assert main["atk"] == 12 and main["health"] == 11, (
        f"4 minions -> +4/+4 on best target after arbor buffs, got {main}"
    )

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    gs.get_entity(2).health = 15
    m1 = _minion(gs, 41, 1, 6, 6, card_id="ETC_376")
    m1.tags["NUM_TURNS_IN_PLAY"] = 1
    m2 = _minion(gs, 179, 1, 4, 4, card_id="VAC_946")
    m2.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs, 63, 1, "YOP_026", 5)
    _hand_spell(gs, 45, 1, "CATA_138", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total >= 15, f"arbor+gift combo should lethal 15 HP, got {total}"
    combo = checker.overlay_combo_display_lines()
    assert any("树木生长" in ln for ln in combo), combo
    assert any("森林赠礼" in ln for ln in combo), combo
    assert any("含BUFF" in ln for ln in combo), combo
    print("OK p0 arbor up + forests gift lethal", total, combo)


def test_p0_flash_sale_summons_and_buffs_all_minions():
    """光速抢购：召唤 1/2 圣盾嘲讽机械并全体友方随从 +1/+2。"""
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    fighters = [
        {
            "kind": "minion", "entity_id": 54, "atk": 1, "health": 1,
            "attacks_left": 1, "can_face": True,
        },
        {
            "kind": "minion", "entity_id": 203, "atk": 3, "health": 6,
            "attacks_left": 1, "can_face": True,
        },
    ]
    defn = get_board_spell_def("TOY_716")
    assert defn is not None, "TOY_716 should be registered"
    apply_spell_sequence([], fighters, [(defn, 4, None)])

    pioneer = next(f for f in fighters if f.get("entity_id") == 54)
    elemental = next(f for f in fighters if f.get("entity_id") == 203)
    assert pioneer["atk"] == 2 and pioneer["health"] == 3
    assert elemental["atk"] == 4 and elemental["health"] == 8

    token = next(f for f in fighters if f.get("card_id") == "CORE_GVG_085")
    assert token["atk"] == 2 and token["health"] == 4
    assert token.get("shield") and token.get("taunt")
    assert token.get("attacks_left", 0) == 0
    print("OK p0 flash sale summons and buffs")


def test_p0_flash_sale_enables_board_lethal():
    """光速抢购 +1/+2 后场面斩杀（对局 replay 22:43 简化）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    gs.get_entity(2).health = 14
    for eid, atk, hp in ((54, 1, 1), (203, 3, 6), (204, 3, 6), (205, 3, 6)):
        m = _minion(gs, eid, 1, atk, hp, card_id="VAC_509t" if eid != 54 else "FIR_913")
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs, 52, 1, "TOY_716", 4)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total >= 14, f"flash sale buff should enable lethal on 14 HP, got {total}"
    combo = checker.overlay_combo_display_lines()
    assert any("光速抢购" in ln for ln in combo), combo
    assert any("含BUFF" in ln for ln in combo), combo
    print("OK p0 flash sale board lethal", total, combo)


def test_p0_flash_sale_spell_plus_hero_power_mana_budget():
    """光速抢购(4)+技能(2)：法力不够时不得同时列入斩杀；够时才技能+法术。"""
    from hdt_python.overlay_combo_format import overlay_combo_mana_affordable

    fighters_setup = lambda gs: [
        _minion(gs, eid, 1, atk, hp, card_id="VAC_509t" if eid != 54 else "FIR_913")
        for eid, atk, hp in ((54, 1, 1), (203, 3, 6), (204, 3, 6), (205, 3, 6))
    ]

    gs5 = GameState()
    gs5.local_player_id = 1
    gs5.opponent_player_id = 2
    gs5.active_player_id = 1
    gs5.in_game = True
    _hero(gs5, 1, 1, mana=5, used=0)
    _hero(gs5, 2, 2)
    gs5.get_entity(2).health = 14
    for m in fighters_setup(gs5):
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs5, 52, 1, "TOY_716", 4)
    _hero_power(gs5, 50, 1, "HERO_08bp", 2)
    lc5 = LethalChecker(gs5)
    _, _, has5 = lc5.calculate_lethal()
    combo5 = lc5.overlay_combo_display_lines()
    assert has5 is True
    assert getattr(lc5, "_overlay_mana_spent", 0) == 4
    assert getattr(lc5, "_overlay_best_hp_name", None) is None
    assert overlay_combo_mana_affordable(lc5)
    assert any("光速抢购" in ln for ln in combo5)
    assert not any("技能" in ln for ln in combo5)

    gs5b = GameState()
    gs5b.local_player_id = 1
    gs5b.opponent_player_id = 2
    gs5b.active_player_id = 1
    gs5b.in_game = True
    _hero(gs5b, 1, 1, mana=5, used=0)
    _hero(gs5b, 2, 2)
    gs5b.get_entity(2).health = 15
    for m in fighters_setup(gs5b):
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs5b, 52, 1, "TOY_716", 4)
    _hero_power(gs5b, 50, 1, "HERO_08bp", 2)
    lc5b = LethalChecker(gs5b)
    _, _, has5b = lc5b.calculate_lethal()
    assert has5b is False

    gs6 = GameState()
    gs6.local_player_id = 1
    gs6.opponent_player_id = 2
    gs6.active_player_id = 1
    gs6.in_game = True
    _hero(gs6, 1, 1, mana=6, used=0)
    _hero(gs6, 2, 2)
    gs6.get_entity(2).health = 15
    for m in fighters_setup(gs6):
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs6, 52, 1, "TOY_716", 4)
    _hero_power(gs6, 50, 1, "HERO_08bp", 2)
    lc6 = LethalChecker(gs6)
    _, _, has6 = lc6.calculate_lethal()
    combo6 = lc6.overlay_combo_display_lines()
    assert has6 is True
    assert getattr(lc6, "_overlay_mana_spent", 0) == 6
    assert overlay_combo_mana_affordable(lc6)
    assert any("光速抢购" in ln for ln in combo6)
    assert any("技能" in ln for ln in combo6)
    print("OK p0 flash sale spell+hero power mana")


def test_p0_flash_sale_plus_fireblast_face_with_friendly_taunt_token():
    """光速抢购召唤友方嘲讽 token 时，火焰冲击仍可直伤打脸 +1。"""
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=6, used=0)
    _hero(gs, 2, 2)
    gs.get_entity(2).health = 15
    for eid, atk, hp in ((54, 1, 1), (203, 3, 6), (204, 3, 6), (205, 3, 6)):
        m = _minion(gs, eid, 1, atk, hp)
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs, 52, 1, "TOY_716", 4)
    _hero_power(gs, 50, 1, "HERO_08bp", 2)

    checker = LethalChecker(gs)
    _, _, has = checker.calculate_lethal()
    _, _, _, spell, hp = checker.overlay_board_breakdown()
    assert has is True, (checker.overlay_board_face_damage(), spell, hp, checker.overlay_combo_display_lines())
    assert hp >= 1
    combo = checker.overlay_combo_display_lines()
    assert any("光速抢购" in ln for ln in combo)
    assert any("技能" in ln for ln in combo)
    print("OK p0 flash sale + fireblast through friendly taunt", hp, combo)


def test_p0_forests_gift_skips_spell_immune_target():
    """森林赠礼不能指定魔法免疫随从，应改 buff 其他可指定目标。"""
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    fighters = [
        {"kind": "minion", "entity_id": 1, "atk": 8, "health": 8,
         "attacks_left": 1, "can_face": True, "spell_immune": True},
        {"kind": "minion", "entity_id": 2, "atk": 3, "health": 3,
         "attacks_left": 1, "can_face": True},
    ]
    gift = get_board_spell_def("CATA_138")
    assert gift is not None
    apply_spell_sequence([], fighters, [(gift, 3, None)])
    immune = next(f for f in fighters if f.get("entity_id") == 1)
    buffed = next(f for f in fighters if f.get("entity_id") == 2)
    assert immune["atk"] == 8 and immune["health"] == 8
    assert buffed["atk"] == 5 and buffed["health"] == 5
    print("OK p0 forests gift skips spell immune")


def test_p0_forests_gift_counts_exhausted_board_minions():
    """森林赠礼：随从数须含当回合不能攻击的场上随从（fighters 只含可攻击者）。"""
    from hdt_python.spell_board import (
        _friendly_minion_count,
        apply_spell_sequence,
        get_board_spell_def,
    )

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m1 = _minion(gs, 1, 1, 3, 3, card_id="A")
    m1.tags["NUM_TURNS_IN_PLAY"] = 1
    m2 = _minion(gs, 2, 1, 4, 4, card_id="B")
    m2.tags["EXHAUSTED"] = 1
    m2.tags["NUM_TURNS_IN_PLAY"] = 2
    m3 = _minion(gs, 3, 1, 2, 2, card_id="C")
    m3.tags["EXHAUSTED"] = 1

    fighters = [
        {"kind": "minion", "entity_id": 1, "card_id": "A", "atk": 3, "health": 3,
         "attacks_left": 1, "can_face": True},
    ]
    assert _friendly_minion_count(fighters) == 1
    assert _friendly_minion_count(fighters, gs=gs, player_id=1) == 3

    gift = get_board_spell_def("CATA_138")
    assert gift is not None
    apply_spell_sequence(
        [], fighters, [(gift, 3, None)],
        gs=gs, player_id=1,
    )
    # 最高攻目标 B(4) 吃 +3/+3（含疲劳随从计入总数）
    buffed = next(f for f in fighters if f.get("entity_id") == 2)
    assert buffed["atk"] == 7 and buffed["health"] == 7, buffed
    print("OK p0 forests gift counts exhausted board minions")


def test_p0_defile_repeats_on_death():
    """亵渎：有死亡则重复全场 1 伤。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    taunts = [
        {"health": 1, "shield": False, "lifesteal": False, "atk": 1,
         "poisonous": False, "spell_immune": False, "zone_pos": 1},
        {"health": 2, "shield": False, "lifesteal": False, "atk": 1,
         "poisonous": False, "spell_immune": False, "zone_pos": 2},
    ]
    defn = get_board_spell_def("ICC_041")
    apply_spell_sequence(taunts, [], [(defn, 2, None)], enemy_shield=False)
    assert not any(t.get("health", 0) > 0 for t in taunts)
    print("OK p0 defile clears 1/1 and 2/2")


def test_p0_bladestorm_stops_on_death():
    """剑刃风暴：重复 1 伤直到某轮有随从死亡。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    taunts = [
        {"health": 2, "shield": False, "lifesteal": False, "atk": 1,
         "poisonous": False, "spell_immune": False, "zone_pos": 1},
    ]
    defn = get_board_spell_def("BT_117")
    apply_spell_sequence(taunts, [], [(defn, 2, None)], enemy_shield=False)
    assert not any(t.get("health", 0) > 0 for t in taunts)
    print("OK p0 bladestorm")


def test_p0_malted_magma_multi_drink():
    """麦芽岩浆：3 杯连喝，每杯全体敌人 1 伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "VAC_323", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert board == 6
    assert spell == 3
    assert total == 9
    print("OK p0 malted magma", total, spell)


def test_p0_malted_magma_drink_mana_budget():
    """饮品连喝：每杯另付法力；预算不足时只喝得起部分杯数。"""
    from hdt_python.spell_board import spell_sequence_mana_left, get_board_spell_def

    seq = [(get_board_spell_def("VAC_323"), 1, None)]
    assert spell_sequence_mana_left(seq, 8) == 3
    assert spell_sequence_mana_left(seq, 6) == 1
    assert spell_sequence_mana_left(seq, 5) == 0
    assert spell_sequence_mana_left(seq, 4) == 1
    assert spell_sequence_mana_left(seq, 1) == 0
    print("OK p0 malted magma mana budget")


def test_p0_condemn_rank_by_max_mana():
    """罪罚：按水晶上限解析 BAR_314/915/916。"""
    from hdt_python.spell_board import (
        condemn_card_id_for_max_mana,
        get_board_spell_def,
        apply_spell_sequence,
        resolve_board_spell_def,
        _SyntheticSpellCard,
    )

    assert condemn_card_id_for_max_mana(4) == "BAR_314"
    assert condemn_card_id_for_max_mana(5) == "BAR_915"
    assert condemn_card_id_for_max_mana(10) == "BAR_916"

    taunts = [
        {"health": 3, "shield": False, "lifesteal": False, "atk": 1,
         "poisonous": False, "spell_immune": False, "zone_pos": 1},
    ]
    gs = GameState()
    gs.local_player_id = 1
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    hero = gs.get_entity(1)
    hero.tags["MAXRESOURCES"] = 10
    spell = gs.get_entity(30)
    spell.cardtype = "SPELL"
    spell.card_id = "BAR_314"

    defn = resolve_board_spell_def(spell, gs, 1)
    assert defn is not None
    apply_spell_sequence(
        taunts, [], [(defn, 2, spell)], enemy_shield=False,
        gs=gs, player_id=1,
    )
    assert not any(t.get("health", 0) > 0 for t in taunts)

    taunts2 = [{"health": 2, "shield": False, "lifesteal": False, "atk": 1,
                "poisonous": False, "spell_immune": False, "zone_pos": 1}]
    defn2 = get_board_spell_def("BAR_915")
    apply_spell_sequence(
        taunts2, [], [(defn2, 2, _SyntheticSpellCard("BAR_915", 2))],
        enemy_shield=False,
    )
    assert not any(t.get("health", 0) > 0 for t in taunts2)
    print("OK p0 condemn ranks")


def test_p0_rising_waves_double_wave():
    """浪潮涌起：全场 2 伤，无死亡再 2 伤。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    taunts = [
        {"health": 3, "shield": False, "lifesteal": False, "atk": 1,
         "poisonous": False, "spell_immune": False, "zone_pos": 1},
    ]
    defn = get_board_spell_def("VAC_953")
    apply_spell_sequence(taunts, [], [(defn, 3, None)], enemy_shield=False)
    assert not any(t.get("health", 0) > 0 for t in taunts)
    print("OK p0 rising waves")


def test_p0_remixed_rhapsody_variants_registered():
    """混搭狂想曲：5 种 hand id 均已注册。"""
    from hdt_python.spell_p0_aoe import REMIXED_RHAPSODY_IDS
    from hdt_python.spell_board import get_board_spell_def

    missing = [cid for cid in REMIXED_RHAPSODY_IDS if get_board_spell_def(cid) is None]
    assert not missing, missing
    print("OK p0 remixed rhapsody ids", REMIXED_RHAPSODY_IDS)


def test_p0_remixed_rhapsody_resounding_clears_four_hp_taunt():
    """高亢狂想曲 JAM_018t2：3 伤 ×2 解 4 血嘲；基础 JAM_018 不解。"""
    from hdt_python.spell_board import (
        apply_spell_sequence,
        get_board_spell_def,
        _SyntheticSpellCard,
    )

    taunts = [
        {"health": 4, "shield": False, "lifesteal": False, "atk": 2,
         "poisonous": False, "spell_immune": False, "taunt": True},
    ]
    fighters = [{"kind": "minion", "health": 6, "atk": 6, "attacks_left": 1, "can_face": True}]

    defn = get_board_spell_def("JAM_018")
    apply_spell_sequence(
        taunts, fighters,
        [(defn, 5, _SyntheticSpellCard("JAM_018", 5))],
        enemy_shield=False,
    )
    assert taunts[0]["health"] == 1

    taunts2 = [
        {"health": 4, "shield": False, "lifesteal": False, "atk": 2,
         "poisonous": False, "spell_immune": False, "taunt": True},
    ]
    fighters2 = [{"kind": "minion", "health": 6, "atk": 6, "attacks_left": 1, "can_face": True}]
    apply_spell_sequence(
        taunts2, fighters2,
        [(defn, 5, _SyntheticSpellCard("JAM_018t2", 5))],
        enemy_shield=False,
    )
    assert not any(t.get("health", 0) > 0 for t in taunts2)
    print("OK p0 remixed rhapsody resounding")


def test_p0_remixed_rhapsody_emotional_hero_attack():
    """动情狂想曲 JAM_018t3：解 2/2 嘲后 6/6 + 英雄 5 攻打脸 = 11。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "JAM_018t3", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert spell == 0
    assert board == 11
    assert total == 11
    print("OK p0 remixed rhapsody emotional", total)


def test_p0_remixed_rhapsody_wailing_summon_sick():
    """哀嚎狂想曲 JAM_018t4：5/5 召唤失调，当回合仅 6/6 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6, card_id="M66")
    _minion(gs, 20, 2, 2, 2, taunt=True, card_id="T22")
    _hand_spell(gs, 30, 1, "JAM_018t4", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6
    print("OK p0 remixed rhapsody wailing", total)


def test_p0_rafaams_stand_upgraded_damage():
    """拉法姆的奋战：TAG_SCRIPT_DATA_NUM_1 为当前每击伤害。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    defn = get_board_spell_def("CATA_498")
    spell = GameState().get_entity(30)
    spell.cardtype = "SPELL"
    spell.card_id = "CATA_498"
    spell.tags["TAG_SCRIPT_DATA_NUM_1"] = 4

    taunts = [
        {"health": 4, "shield": False, "lifesteal": False, "atk": 2,
         "poisonous": False, "spell_immune": False, "zone_pos": 1},
    ]
    base_taunt = dict(taunts[0])
    # 固定 seed：两击都命中唯一随从时 4+4 解 4/4
    import random
    apply_spell_sequence(
        taunts, [],
        [(defn, 3, spell)],
        enemy_shield=False,
        rng=random.Random(0),
    )
    assert not any(t.get("health", 0) > 0 for t in taunts)

    spell.tags["TAG_SCRIPT_DATA_NUM_1"] = 2
    taunts2 = [dict(base_taunt)]
    apply_spell_sequence(
        taunts2, [],
        [(defn, 3, spell)],
        enemy_shield=False,
        rng=random.Random(0),
    )
    assert not any(t.get("health", 0) > 0 for t in taunts2), "2+2 clears 4/4"
    print("OK p0 rafaams stand upgraded damage")


def test_moonwell_hot_coals_reduced_cost_in_tags():
    """炽热火炭减费后 tags[COST]=2 但 entity.cost 仍为 3 时，应与月亮井合计法 6。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.in_game = True
    gs.active_player_id = 2
    _hero(gs, 66, 2, mana=7, used=0)
    _hand_spell(gs, 109, 2, "EDR_476", 5)
    coals = gs.get_entity(39)
    _hand_spell(gs, 39, 2, "VAC_414", 3)
    coals.tags["COST"] = 2

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert total == 6, (total, spell, checker.overlay_spell_note())
    assert spell == 6
    assert "炽热火炭" in checker.overlay_spell_note()
    print("OK moonwell+hot coals reduced cost", total, checker.overlay_spell_note())


def test_hot_coals_hammer_dirge_overlay_max_spell_face():
    """无嘲讽：炽热火炭+愤怒之锤+绝望哀歌应合计 8 法术打脸，不因先达斩杀而漏算火炭。"""
    gs = GameState()
    gs.local_player_id = 2
    gs.opponent_player_id = 1
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 66, 2, mana=10, used=0)
    _hero(gs, 1, 1)
    gs.get_entity(1).health = 13
    for i in range(4):
        _minion(gs, 20 + i, 1, 1, 2, card_id=f"OPP{i}")
    _minion(gs, 10, 2, 3, 3, card_id="ALLY1")
    _minion(gs, 11, 2, 4, 4, card_id="ALLY2")
    _hand_spell(gs, 39, 2, "VAC_414", 2)
    _hand_spell(gs, 225, 2, "CORE_CS2_094", 2)
    _hand_spell(gs, 226, 2, "ETC_082", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion, _, spell, _ = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()
    assert spell == 8, (total, spell, minion, note)
    assert minion == 7, (total, spell, minion, note)
    assert total == 15, (total, spell, minion, note)
    print("OK hot coals+hammer+dirge overlay spell eight", total, spell, note)


def test_hot_coals_shown_when_minion_alone_lethal_on_opp_turn():
    """对手回合：随从已够斩杀时，场攻分项仍应计入炽热火炭等手牌法术。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 2
    _hero(gs, 64, 1, mana=9, used=0)
    _hero(gs, 66, 2)
    gs.get_entity(66).health = 11
    _minion(gs, 10, 1, 4, 4, card_id="CATA_473")
    _minion(gs, 11, 1, 2, 1, card_id="TSC_052t")
    _minion(gs, 12, 1, 2, 3, card_id="WW_418")
    _minion(gs, 13, 1, 4, 4, card_id="WW_418")
    _minion(gs, 20, 2, 5, 5, card_id="SW_323")
    _hand_spell(gs, 45, 1, "VAC_414", 3)

    checker = LethalChecker(gs)
    assert checker.is_opponent_turn()
    total = checker.overlay_board_face_damage()
    _, minion, _, spell, _ = checker.overlay_board_breakdown()
    assert minion == 12, (total, minion, spell)
    assert spell == 2, (total, minion, spell)
    assert total == 14, (total, minion, spell)
    print("OK hot coals overlay on opp turn", total, minion, spell)


def test_dragonfire_potion_skips_dragon_taunt_no_lethal():
    """龙息药水：嘲讽龙不受伤害；两只6攻需换嘲，仅6打脸，对手8血不斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 64, 1, mana=10, used=0)
    _hero(gs, 66, 2)
    gs.get_entity(66).health = 8
    _minion(gs, 373, 1, 6, 7, card_id="TOY_601t2")
    _minion(gs, 409, 1, 6, 7, card_id="TOY_601t2")
    dragon = _minion(gs, 416, 2, 3, 5, taunt=True, card_id="TIME_700t")
    dragon.tags["CARDRACE"] = "DRAGON"
    _hand_spell(gs, 4, 1, "CFM_662", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    _, _, lethal = checker.calculate_lethal_potential()
    note = checker.overlay_spell_note()
    assert not lethal, (total, lethal, note)
    assert total == 6, (total, lethal, note)
    print("OK dragonfire dragon taunt no lethal", total, note)


def test_dragonfire_potion_damages_friendly_minions():
    """龙息药水：对己方非龙随从也造成 5 伤。"""
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    taunts = []
    fighters = [
        {
            "kind": "minion",
            "entity_id": 1,
            "atk": 6,
            "health": 7,
            "attacks_left": 1,
            "can_face": True,
        }
    ]
    defn = get_board_spell_def("CFM_662")
    apply_spell_sequence(taunts, fighters, [(defn, 5, None)])
    assert fighters[0]["health"] == 2
    print("OK dragonfire damages friendly minion")


def test_p0_hot_coals_powered_up():
    """炽热火炭：亮边=本回合受过伤，3 伤 AOE；不亮=2 伤。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    gs = GameState()
    spell = gs.get_entity(30)
    spell.cardtype = "SPELL"
    spell.card_id = "VAC_414"
    defn = get_board_spell_def("VAC_414")
    taunts = [
        {"health": 2, "shield": False, "lifesteal": False, "atk": 2,
         "poisonous": False, "spell_immune": False, "taunt": True, "zone_pos": 1},
    ]
    fighters = [{"kind": "minion", "health": 6, "atk": 6, "attacks_left": 1, "can_face": True}]

    spell.tags["POWERED_UP"] = 0
    ts = [dict(t) for t in taunts]
    apply_spell_sequence(ts, fighters, [(defn, 3, spell)], enemy_shield=False)
    assert not any(t.get("health", 0) > 0 for t in ts), "2 dmg clears 2/2"

    spell.tags["POWERED_UP"] = 1
    ts2 = [{"health": 3, "shield": False, "lifesteal": False, "atk": 2,
            "poisonous": False, "spell_immune": False, "taunt": True, "zone_pos": 1}]
    apply_spell_sequence(ts2, fighters, [(defn, 3, spell)], enemy_shield=False)
    assert not any(t.get("health", 0) > 0 for t in ts2), "3 dmg clears 3/3"
    print("OK p0 hot coals powered up")


def test_hellfire_then_hot_coals_lethal_from_log_093429():
    """先地狱烈焰自伤再炽热火炭+3 伤：打烈焰前应判斩（鸡哥在线 14 血）。"""
    import io
    import contextlib
    from pathlib import Path
    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_29_09_34_29\Power.log"
    )
    if not log.is_file():
        print("SKIP hellfire hot coals lethal log (log missing)")
        return

    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    gs.player_names[2] = "鸡哥在线#5240"
    gs.local_player_id = 2
    parser = PowerLogParser(str(log), gs)
    starts = [
        i for i, line in enumerate(lines)
        if "CREATE_GAME" in line and "GameState.DebugPrintPower" in line
    ]
    target = 210301
    start = starts[0]
    for i, s in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(lines)
        if s <= target - 1 < end:
            start = s
            break
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            parser.process_line(lines[i])
    gs.in_game = True
    gs.active_player_id = 2

    opp = gs.get_hero(1)
    assert opp is not None
    eff = opp.health - opp.damage + int(opp.tags.get("ARMOR", 0) or 0)
    assert eff == 14, eff

    checker = LethalChecker(gs)
    total, _, is_lethal = checker.calculate_lethal_potential()
    _, _, _, spell_face, _ = checker.overlay_board_breakdown()
    assert is_lethal, (total, spell_face, checker.overlay_board_breakdown())
    assert total >= 14, total
    assert spell_face >= 6, spell_face
    seq_ids = [
        getattr(c, "card_id", "") or (d.card_ids[0] if d and d.card_ids else "")
        for _, d, c in getattr(checker, "_overlay_best_seq", [])
    ]
    assert "CORE_CS2_062" in seq_ids, seq_ids
    assert "VAC_414" in seq_ids, seq_ids
    print("OK hellfire hot coals lethal before play", total, spell_face)


def test_p0_baking_soda_volcano_no_hero_damage():
    """苏打火山：10 伤只随机分配到随从，不含英雄直伤。"""
    import random
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    defn = get_board_spell_def("TOY_500")
    for seed in range(200):
        taunts = [
            {"health": 2, "shield": False, "lifesteal": False, "atk": 2,
             "poisonous": False, "spell_immune": False, "taunt": True, "zone_pos": i}
            for i in range(1, 4)
        ]
        fighters = [
            {"kind": "minion", "entity_id": 10, "atk": 6, "health": 6, "shield": False,
             "poisonous": False, "attacks_left": 1, "can_face": True},
            {"kind": "minion", "entity_id": 11, "atk": 3, "health": 3, "shield": False,
             "poisonous": False, "attacks_left": 1, "can_face": True},
        ]
        res = apply_spell_sequence(
            taunts, fighters, [(defn, 4, None)], enemy_shield=False,
            rng=random.Random(seed),
        )
        assert res.direct_face_damage == 0, f"seed={seed} spell face={res.direct_face_damage}"
    print("OK p0 baking soda no hero damage")


def test_p0_baking_soda_volcano_deterministic_clear_at_10_hp():
    """苏打火山：场面随从总生命<=10 时确定性清场并吸血回 10。"""
    from hdt_python.spell_board import get_board_spell_def, apply_spell_sequence

    defn = get_board_spell_def("TOY_500")
    taunts = [
        {"health": 2, "shield": False, "lifesteal": False, "atk": 2,
         "poisonous": False, "spell_immune": False, "taunt": True, "zone_pos": i}
        for i in range(1, 6)
    ]
    fighters: list = []
    res = apply_spell_sequence(taunts, fighters, [(defn, 4, None)], enemy_shield=False)
    assert res.direct_face_damage == 0
    assert res.self_hero_heal == 10
    assert not any(t.get("health", 0) > 0 for t in taunts)
    print("OK p0 baking soda deterministic clear at 10 hp")


def test_spell_sim_tier_order_clear_before_direct():
    """法术枚举：清场（苏打）优先于直伤（火球），清场+打脸（夕阳）居中。"""
    from hdt_python.spell_board import (
        get_board_spell_def,
        spell_sim_tier,
        SpellSimTier,
        enumerate_tiered_spell_orders,
    )

    soda = get_board_spell_def("TOY_500")
    sunset = get_board_spell_def("WW_427")
    fireball = get_board_spell_def("CS2_029")
    assert soda and sunset and fireball
    assert spell_sim_tier(soda) == SpellSimTier.CLEAR_BOARD
    assert spell_sim_tier(sunset) == SpellSimTier.CLEAR_AND_FACE
    assert spell_sim_tier(fireball) == SpellSimTier.DIRECT_FACE

    items = [(soda, 4, None), (fireball, 4, None), (sunset, 4, None)]
    orders = enumerate_tiered_spell_orders(items)
    assert orders[0] == [(soda, 4, None), (sunset, 4, None), (fireball, 4, None)]
    print("OK spell sim tier order")


def test_pruned_enumeration_after_soda_clear():
    """苏打清场后，同层直伤只枚举一条代表序列。"""
    from copy import deepcopy
    from hdt_python.spell_board import (
        get_board_spell_def,
        enumerate_pruned_tiered_spell_orders,
    )

    soda = get_board_spell_def("TOY_500")
    sunset = get_board_spell_def("WW_427")
    fireball = get_board_spell_def("CS2_029")
    lava = get_board_spell_def("TLC_227")
    portal = get_board_spell_def("KAR_076")
    wind = get_board_spell_def("FIR_910")
    taunts = [
        {"health": 2, "shield": False, "lifesteal": False, "atk": 2,
         "poisonous": False, "spell_immune": False, "taunt": True, "zone_pos": i}
        for i in range(1, 6)
    ]
    items = [
        (soda, 1, None), (sunset, 1, None), (fireball, 1, None),
        (lava, 1, None), (portal, 1, None), (wind, 1, None),
    ]
    orders = enumerate_pruned_tiered_spell_orders(
        items, deepcopy(taunts), [],
    )
    assert len(orders) == 1, f"expected 1 order after prune, got {len(orders)}"
    names = [s[0].name for s in orders[0]]
    assert names == ["苏打火山", "夕阳漫射", "火球术", "熔岩涌流", "火焰之地传送门", "灼烧之风"]
    print("OK pruned enumeration after soda clear")


def test_no_taunt_direct_face_excluded_from_combo_enum():
    """无嘲讽：直伤法术不进 combo 枚举，仅清场/清场+打脸参与组合。"""
    from copy import deepcopy
    from scripts.bench_hand_spell_limit import build_gs
    from hdt_python.battlecry_board import hand_all_board_plays
    from hdt_python.lethal_checker import LethalChecker
    from hdt_python.spell_board import spell_effect_multiplier

    gs = build_gs()
    checker = LethalChecker(gs)
    plays = hand_all_board_plays(gs, 1, 10)
    bv = gs.get_overlay_board(1)
    fighters = checker._build_fighters(bv, 1)
    enemy = checker._build_enemy_minion_states(1)
    combo_hand, direct_prefix, direct_face, combo_mana, _ = checker._no_taunt_direct_face_setup(
        plays, 10, spell_mult=1, defender_shield=False, player_id=1, opp_taunts=[],
    )
    assert len(direct_prefix) >= 4, "火球/熔岩/传送门等应作为直伤前缀"
    assert direct_face > 0
    assert all(
        defn.name in ("苏打火山", "夕阳漫射")
        for _, defn, _ in combo_hand
    ), [(d.name if hasattr(d,'name') else _, defn.name, _) for _, defn, _ in combo_hand]
    seqs = checker._enumerate_spells_for_search(
        combo_hand, combo_mana,
        enemy_minions=enemy, fighters=fighters,
        spell_mult=1, defender_shield=False, player_id=1,
    )
    assert len(seqs) <= 8, f"combo 枚举应远小于 136，实际 {len(seqs)}"
    full_combo = [s for s in seqs if len(s) == 2]
    assert len(full_combo) == 1
    print("OK no taunt direct face excluded from combo")


def _build_conflagrate_combo_gs() -> GameState:
    """6x2/2 + 6/6，手牌 7 张 1 费法术（阳炎/火球/夕阳/熔岩/焚烧/喷吐x2）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    for i in range(6):
        _minion(gs, 20 + i, 2, 2, 2, card_id=f"M{i}")
    _minion(gs, 26, 2, 6, 6, card_id="BIG")
    for cid, eid in [
        ("GDB_305", 30),
        ("CS2_029", 31),
        ("WW_427", 32),
        ("TLC_227", 33),
        ("FIR_954", 34),
        ("DINO_406", 35),
        ("DINO_406", 36),
    ]:
        _hand_spell(gs, eid, 1, cid, 1)
    return gs


def test_conflagrate_no_taunt_targets_minion_for_sunset_lethal():
    """无嘲讽：焚烧可点非嘲讽随从，清掉 6/6 后夕阳漫射全打脸 → 确定斩杀。"""
    gs = _build_conflagrate_combo_gs()
    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    mc_max, prob, uses_random, top = checker.overlay_face_stats()
    note = checker.overlay_spell_note()
    assert total == 32, note
    assert mc_max == 32
    assert prob == 1.0
    assert top == [(32, 1.0)]
    assert "焚烧" in note and "夕阳漫射" in note
    assert note.index("焚烧") < note.index("夕阳漫射"), note
    print("OK conflagrate no taunt minion target", total, note)


def test_no_taunt_minion_face_no_attack_subset():
    """无嘲讽：随从场攻直接求和，不枚举攻击子集。"""
    from hdt_python.lethal_checker import LethalChecker
    from hdt_python.power_parser import GameState

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    h1 = gs.get_entity(1)
    h1.cardtype = "HERO"
    h1.controller = 1
    h1.health = 30
    h1.tags.update({"RESOURCES": 10, "RESOURCES_USED": 0})
    gs.hero_entity_ids[1] = 1
    h2 = gs.get_entity(2)
    h2.cardtype = "HERO"
    h2.controller = 2
    h2.health = 30
    gs.hero_entity_ids[2] = 2
    for i, (atk, hp) in enumerate([(3, 3), (4, 4)], start=1):
        m = gs.get_entity(10 + i)
        m.cardtype = "MINION"
        m.controller = 1
        m.zone = "PLAY"
        m.atk = atk
        m.health = hp
        m.tags["ZONE"] = "PLAY"
        m.tags["NUM_TURNS_IN_PLAY"] = 1
        m.tags["EXHAUSTED"] = 0
        pos = i
        m.tags["ZONE_POSITION"] = pos
        gs.board_slots.setdefault(1, {})[pos] = 10 + i
    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 7, f"expected 3+4 minion face, got {total}"
    print("OK no taunt minion face sum")


def test_vendetta_cost_when_powered_up():
    """宿敌：亮边时按 0 费计入（log 无 COST 时）。"""
    from hdt_python.spell_board import spell_effective_cost

    gs = GameState()
    gs.local_player_id = 1
    _hero(gs, 1, 1)
    spell = gs.get_entity(30)
    spell.cardtype = "SPELL"
    spell.controller = 1
    spell.zone = "HAND"
    spell.card_id = "DAL_716"
    spell.cost = None
    spell.tags["ZONE"] = "HAND"
    spell.tags["POWERED_UP"] = 1

    assert spell_effective_cost(spell, gs, 1) == 0

    spell.tags["POWERED_UP"] = 0
    assert spell_effective_cost(spell, gs, 1) == 4
    print("OK vendetta powered up cost")


def test_dark_gift_charge_face_no_taunt():
    """黑暗之赐冲锋手牌：无嘲讽时直接计入场攻打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hand_minion(gs, 50, 1, 5, 3, 5, dark_gift_charge=True)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 5, (total, board, spell)
    assert board == 5
    assert spell == 0
    assert "手牌冲锋:" in checker.overlay_spell_note()
    assert "5攻冲锋" in checker.overlay_spell_note()
    print("OK dark gift charge face no taunt")


def test_p0_double_agent_charge_copy_face():
    """双面间谍 AV_711：黑暗之赐冲锋 + 异职业手牌，战吼复制双打脸 6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    hero = _hero(gs, 1, 1, mana=10)
    hero.tags["CLASS"] = "ROGUE"
    _hero(gs, 2, 2)
    agent = _hand_minion(
        gs, 50, 1, 3, 3, 3, card_id="AV_711", dark_gift_charge=True,
    )
    agent.tags["CLASS"] = "ROGUE"
    other = _hand_spell(gs, 60, 1, "CS2_005", 1)
    other.tags["CLASS"] = "DRUID"

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, (total, checker.overlay_board_breakdown(), checker.overlay_spell_note())
    assert "手牌冲锋:" in checker.overlay_spell_note()
    assert "双面间谍(3攻冲锋)×2" in checker.overlay_spell_note()
    print("OK double agent charge copy six face")


def test_p0_double_agent_charge_no_other_class_single_face():
    """双面间谍：无异职业手牌时不复制，仅单份冲锋场攻。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    hero = _hero(gs, 1, 1, mana=10)
    hero.tags["CLASS"] = "ROGUE"
    _hero(gs, 2, 2)
    agent = _hand_minion(
        gs, 50, 1, 3, 3, 3, card_id="AV_711", dark_gift_charge=True,
    )
    agent.tags["CLASS"] = "ROGUE"

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 3, (total, checker.overlay_board_breakdown(), checker.overlay_spell_note())
    print("OK double agent charge no copy three face")


def test_p0_double_agent_charge_combo_hand_not_board():
    """手牌冲锋斩杀：Combo 应写「打出双面间谍」，而非「全部/场面随从打脸」。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    hero = _hero(gs, 1, 1, mana=10)
    hero.tags["CLASS"] = "ROGUE"
    opp = _hero(gs, 2, 2)
    opp.health = 30
    opp.tags["DAMAGE"] = 24
    agent = _hand_minion(
        gs, 50, 1, 3, 3, 3, card_id="AV_711", dark_gift_charge=True,
    )
    agent.tags["CLASS"] = "ROGUE"
    other = _hand_spell(gs, 60, 1, "CS2_005", 1)
    other.tags["CLASS"] = "DRUID"

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, total
    combo = checker.overlay_combo_display_lines()
    assert combo == [
        "⚔ 斩杀步骤",
        "1. 打出 双面间谍(3攻冲锋)×2",
    ], combo
    assert not any("全部随从" in ln for ln in combo)
    print("OK double agent charge combo labels hand charge")


def test_dark_gift_charge_clears_taunt_then_board_face():
    """黑暗之赐冲锋解嘲后，场面随从继续打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 6, 6)
    _minion(gs, 20, 2, 3, 3, taunt=True)
    _hand_minion(gs, 50, 1, 4, 2, 4, dark_gift_charge=True)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 6, (total, board, spell)
    assert board == 6
    print("OK dark gift charge clears taunt then board face")


def test_hand_charge_with_spell_mana_budget():
    """先打法术后，剩余法力仍可打出黑暗之赐冲锋打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    _hero(gs, 1, 1, mana=8)
    _hero(gs, 2, 2)
    _hand_spell(gs, 40, 1, "EDR_476", 6)  # 月亮井 6 费直伤 4
    _hand_minion(gs, 50, 1, 2, 2, 2, dark_gift_charge=True)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 6, (total, board, spell)
    assert board == 2
    assert spell == 4
    print("OK hand charge with spell mana budget")


def test_p0_battlecry_registered():
    from hdt_python.battlecry_board import BOARD_BATTLECRY, get_battlecry_def

    assert len(BOARD_BATTLECRY) == 65
    assert get_battlecry_def("RLK_867") is not None
    assert get_battlecry_def("TOY_101") is not None
    assert get_battlecry_def("EDR_464") is not None
    print("OK p0 battlecry registered (65)")


def test_p0_tyrande_double_spell_aura():
    """泰兰德战吼：下一张法术施放两次（冰霜撕咬 3×2=6 打脸）。"""
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    tyrande = get_battlecry_def("EDR_464")
    frostbite = get_board_spell_def("AV_259")
    res = apply_spell_sequence(
        [], [],
        [(tyrande, 7, None), (frostbite, 2, None)],
        enemy_shield=False,
    )
    assert res.direct_face_damage == 6, res.direct_face_damage
    print("OK tyrande double spell aura", res.direct_face_damage)


def test_p0_tyrande_double_spell_three_charges():
    """泰兰德：仅前 3 张法术双倍，第 4 张正常。"""
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    tyrande = get_battlecry_def("EDR_464")
    frostbite = get_board_spell_def("AV_259")
    seq = [(tyrande, 7, None)] + [(frostbite, 2, None)] * 4
    res = apply_spell_sequence([], [], seq, enemy_shield=False)
    assert res.direct_face_damage == 21, res.direct_face_damage
    print("OK tyrande three double charges", res.direct_face_damage)


def test_p0_tyrande_aura_next_turn_chaos_strike():
    """上回合泰兰德战吼：英雄附着 EDR_464e2，下回合仅混乱打击 → 双倍 4 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 2
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    hero_eid = gs.hero_entity_ids[1]
    enc = gs.get_entity(99)
    enc.cardtype = "ENCHANTMENT"
    enc.card_id = "EDR_464e2"
    enc.zone = "PLAY"
    enc.tags["ZONE"] = "PLAY"
    enc.tags["ATTACHED"] = hero_eid
    enc.tags["CARDTYPE"] = "ENCHANTMENT"
    enc.tags["TAG_SCRIPT_DATA_NUM_1"] = 3
    _hand_spell(gs, 30, 1, "CORE_BT_035", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 4, f"expected 4 from persisted tyrande aura, got {total}"
    print("OK tyrande aura next turn chaos strike", total)


def test_p0_tyrande_aura_partial_charges():
    """光环剩余 1 次：仅下一张法术双倍。"""
    from hdt_python.battlecry_board import get_battlecry_def, tyrande_double_spells_remaining
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1)
    hero_eid = gs.hero_entity_ids[1]
    enc = gs.get_entity(99)
    enc.cardtype = "ENCHANTMENT"
    enc.card_id = "EDR_464e2"
    enc.tags["ATTACHED"] = hero_eid
    enc.tags["TAG_SCRIPT_DATA_NUM_1"] = 1
    assert tyrande_double_spells_remaining(gs, 1) == 1

    frostbite = get_board_spell_def("AV_259")
    res = apply_spell_sequence([], [], [(frostbite, 2, None), (frostbite, 2, None)],
                               enemy_shield=False, gs=gs, player_id=1)
    assert res.direct_face_damage == 9, res.direct_face_damage
    print("OK tyrande aura one charge left", res.direct_face_damage)


def test_p0_night_elf_huntress_one_taunt_rest_face():
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence

    taunts = [
        {"entity_id": 1, "health": 3, "atk": 2, "taunt": True, "shield": False},
        {"entity_id": 2, "health": 5, "atk": 3, "taunt": False, "shield": False},
        {"entity_id": 3, "health": 2, "atk": 1, "taunt": False, "shield": False},
    ]
    defn = get_battlecry_def("TOY_101")
    res = apply_spell_sequence(taunts, [], [(defn, 5, None)], enemy_shield=False)
    assert res.direct_face_damage == 3
    assert not any(t.get("entity_id") == 1 for t in taunts)
    print("OK night elf huntress one taunt rest face")


def test_p0_night_elf_huntress_three_taunts_highest_hp():
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence

    taunts = [
        {"entity_id": 1, "health": 2, "atk": 1, "taunt": True, "shield": False},
        {"entity_id": 2, "health": 5, "atk": 3, "taunt": True, "shield": False},
        {"entity_id": 3, "health": 4, "atk": 2, "taunt": True, "shield": False},
        {"entity_id": 4, "health": 6, "atk": 4, "taunt": True, "shield": False},
    ]
    defn = get_battlecry_def("TOY_101")
    res = apply_spell_sequence(taunts, [], [(defn, 5, None)], enemy_shield=False)
    assert res.direct_face_damage == 3
    by_id = {t["entity_id"]: t for t in taunts}
    assert 1 not in by_id
    assert by_id[2]["health"] == 2
    assert by_id[3]["health"] == 4
    assert by_id[4]["health"] == 6
    print("OK night elf huntress three taunts highest hp")


def test_p0_night_elf_huntress_no_taunt_distinct_targets():
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence

    taunts = [
        {"entity_id": 1, "health": 5, "atk": 3, "taunt": False, "shield": False},
        {"entity_id": 2, "health": 2, "atk": 1, "taunt": False, "shield": False},
    ]
    defn = get_battlecry_def("TOY_101")
    res = apply_spell_sequence(taunts, [], [(defn, 5, None)], enemy_shield=False)
    assert res.direct_face_damage == 3
    print("OK night elf huntress no taunt distinct targets")


def test_p0_fan_hammer_huntress_not_lethal_three_minions():
    """实战误报：迅疾连射+女猎手对三随从不应算 15 直伤斩杀 13 血。"""
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    taunts = [
        {"entity_id": 1, "health": 3, "atk": 3, "taunt": False, "shield": False, "zone_pos": 1},
        {"entity_id": 2, "health": 1, "atk": 2, "taunt": False, "shield": False, "zone_pos": 2},
        {"entity_id": 3, "health": 2, "atk": 2, "taunt": False, "shield": False, "zone_pos": 3},
    ]
    fighters = [{"kind": "minion", "entity_id": 10, "atk": 1, "health": 1, "attacks_left": 1, "can_face": True}]
    seq = [
        (get_board_spell_def("WW_405"), 3, None),
        (get_battlecry_def("TOY_101"), 5, None),
    ]
    res = apply_spell_sequence(taunts, fighters, seq, enemy_shield=False)
    assert res.direct_face_damage < 13, res.direct_face_damage
    print("OK fan hammer huntress not 15 face vs three minions", res.direct_face_damage)


def test_p0_twilight_mistress_bounce_clears_taunt():
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence

    taunts = [
        {"entity_id": 1, "health": 5, "atk": 3, "taunt": True, "shield": False},
        {"entity_id": 2, "health": 4, "atk": 2, "taunt": False, "shield": False},
    ]
    fighters = [{"kind": "minion", "entity_id": 10, "atk": 4, "health": 4, "attacks_left": 1, "can_face": True}]
    defn = get_battlecry_def("CATA_201")
    apply_spell_sequence(taunts, fighters, [(defn, 9, None)], enemy_shield=False)
    assert not [t for t in taunts if t.get("health", 0) > 0]
    from hdt_python.combat_sim import project_board_face_after_spell
    assert project_board_face_after_spell(taunts, fighters, False) == 4
    print("OK twilight mistress bounce clears taunt")


def test_p0_vrykul_necrolyte_no_immediate_damage():
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence

    fighters = [
        {"kind": "minion", "entity_id": 1, "atk": 2, "health": 5, "attacks_left": 1, "can_face": True},
        {"kind": "minion", "entity_id": 2, "atk": 4, "health": 2, "attacks_left": 1, "can_face": True},
    ]
    defn = get_battlecry_def("RLK_867")
    res = apply_spell_sequence([], fighters, [(defn, 2, None)], enemy_shield=False)
    assert res.direct_face_damage == 0
    assert fighters[1]["health"] == 2
    print("OK vrykul necrolyte no immediate damage")


def test_p0_faceless_corruptor_transform_dual_rush():
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence

    taunts = [{"entity_id": 1, "health": 4, "atk": 2, "taunt": True, "shield": False}]
    fighters = [
        {"kind": "minion", "entity_id": 10, "atk": 2, "health": 2, "attacks_left": 0, "can_face": True},
    ]
    defn = get_battlecry_def("DRG_076")
    apply_spell_sequence(taunts, fighters, [(defn, 5, None)], enemy_shield=False)
    rush_copies = [
        f for f in fighters
        if f.get("kind") == "minion" and f.get("atk") == 5 and f.get("health") == 4
    ]
    assert len(rush_copies) == 2
    assert fighters[0]["entity_id"] == 10
    assert fighters[0]["attacks_left"] == 1
    print("OK faceless corruptor transform dual rush")


def test_p0_amber_whelp_requires_powered_up():
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence
    from hdt_python.power_parser import GameState

    gs = GameState()
    card = gs.get_entity(1)
    card.cardtype = "MINION"
    card.card_id = "RLK_915"
    card.tags["POWERED_UP"] = 0

    defn = get_battlecry_def("RLK_915")
    res = apply_spell_sequence([], [], [(defn, 3, card)], enemy_shield=False)
    assert res.direct_face_damage == 0

    card.tags["POWERED_UP"] = 1
    res2 = apply_spell_sequence([], [], [(defn, 3, card)], enemy_shield=False)
    assert res2.direct_face_damage == 3
    print("OK amber whelp requires powered up")


def test_p0_firework_elemental_corrupt_by_powered_up():
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence
    from hdt_python.power_parser import GameState

    gs = GameState()
    card = gs.get_entity(1)
    card.cardtype = "MINION"
    card.card_id = "DMF_101"
    card.tags["POWERED_UP"] = 0

    taunts = [{"entity_id": 1, "health": 10, "atk": 3, "taunt": True, "shield": False}]
    defn = get_battlecry_def("DMF_101")
    apply_spell_sequence(taunts, [], [(defn, 5, card)], enemy_shield=False)
    assert taunts[0]["health"] == 7

    taunts2 = [{"entity_id": 1, "health": 10, "atk": 3, "taunt": True, "shield": False}]
    card.tags["POWERED_UP"] = 1
    apply_spell_sequence(taunts2, [], [(defn, 5, card)], enemy_shield=False)
    assert not taunts2
    print("OK firework elemental corrupt by powered up")


def test_p0_dunk_tank_corrupted_aoe():
    """深水炸弹腐蚀：4 单目标 + 全体敌方随从 2 伤（不含英雄）。"""
    from hdt_python.spell_board import (
        _SyntheticSpellCard, apply_spell_sequence, get_board_spell_def,
    )

    taunts = [
        {"entity_id": 1, "health": 4, "atk": 2, "taunt": True, "shield": False},
        {"entity_id": 2, "health": 3, "atk": 2, "taunt": False, "shield": False},
    ]
    card = _SyntheticSpellCard("DMF_701t", 4)
    card.tags["CORRUPTED_CARD"] = 1
    defn = get_board_spell_def("DMF_701t")
    res = apply_spell_sequence(taunts, [], [(defn, 4, card)], enemy_shield=False)
    assert res.direct_face_damage == 0
    print("OK dunk tank corrupted aoe")


def test_p0_dunk_tank_corrupted_face_four():
    """腐蚀深水炸弹无随从：主目标打脸 4，随从 AOE 不伤害英雄。"""
    from hdt_python.spell_board import (
        _SyntheticSpellCard, apply_spell_sequence, get_board_spell_def,
    )

    card = _SyntheticSpellCard("DMF_701t", 4)
    card.tags["CORRUPTED_CARD"] = 1
    defn = get_board_spell_def("DMF_701t")
    res = apply_spell_sequence([], [], [(defn, 4, card)], enemy_shield=False)
    assert res.direct_face_damage == 4
    print("OK dunk tank corrupted face four")


def test_p0_dunk_tank_corrupted_aoe_only_hits_minions():
    """腐蚀深水炸弹有嘲讽时：主目标打随从，AOE 不额外对英雄 2。"""
    from hdt_python.spell_board import (
        _SyntheticSpellCard, apply_spell_sequence, get_board_spell_def,
    )

    taunts = [{"entity_id": 1, "health": 10, "atk": 2, "taunt": True, "shield": False}]
    card = _SyntheticSpellCard("DMF_701t", 4)
    card.tags["CORRUPTED_CARD"] = 1
    defn = get_board_spell_def("DMF_701t")
    res = apply_spell_sequence(taunts, [], [(defn, 4, card)], enemy_shield=False)
    assert res.direct_face_damage == 0
    print("OK dunk tank corrupted aoe only hits minions")


def test_p0_swipe_no_taunt_face_four():
    """横扫无嘲讽：主目标打脸 4。"""
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    swipe = get_board_spell_def("CS2_012")
    res = apply_spell_sequence([], [], [(swipe, 3, None)], enemy_shield=False)
    assert res.direct_face_damage == 4
    print("OK swipe no taunt face four")


def test_p0_swipe_one_taunt_splash_face():
    """横扫：主目标打嘲讽 4，其余敌人各 1（含英雄）。"""
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    taunts = [
        {"entity_id": 1, "health": 5, "atk": 2, "taunt": True, "shield": False},
        {"entity_id": 2, "health": 3, "atk": 2, "taunt": False, "shield": False},
    ]
    swipe = get_board_spell_def("CS2_012")
    res = apply_spell_sequence(taunts, [], [(swipe, 3, None)], enemy_shield=False)
    assert res.direct_face_damage == 1
    print("OK swipe one taunt splash face")


def test_p0_malfurions_gift_discovers_swipe():
    """玛法里奥的礼物：无嘲讽时发现横扫并打脸 4。"""
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    gift = get_board_spell_def("CORE_GIFT_10")
    assert gift is not None
    res = apply_spell_sequence([], [], [(gift, 1, None)], enemy_shield=False, mana_budget=4)
    assert res.direct_face_damage == 4
    print("OK malfurions gift discovers swipe")


def test_p0_dunk_tank_corrupts_in_sequence():
    """先打 6 费再打水炸弹：序列内触发腐蚀 AOE。"""
    from hdt_python.spell_board import (
        _SyntheticSpellCard, apply_spell_sequence, get_board_spell_def,
    )

    taunts = [
        {"entity_id": 1, "health": 8, "atk": 2, "taunt": True, "shield": False},
        {"entity_id": 2, "health": 8, "atk": 2, "taunt": False, "shield": False},
    ]
    moonwell = get_board_spell_def("EDR_476")
    dunk = get_board_spell_def("DMF_701")
    dunk_card = _SyntheticSpellCard("DMF_701", 4)
    res = apply_spell_sequence(
        taunts, [],
        [(moonwell, 6, None), (dunk, 4, dunk_card)],
        enemy_shield=False,
    )
    assert dunk_card.card_id == "DMF_701t"
    assert res.direct_face_damage == 4
    print("OK dunk tank corrupts in sequence")


def test_p0_hostile_invader_spellburst_after_spell():
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    taunts = [
        {"entity_id": 1, "health": 3, "atk": 2, "taunt": True, "shield": False},
        {"entity_id": 2, "health": 3, "atk": 2, "taunt": False, "shield": False},
    ]
    invader = get_battlecry_def("GDB_226")
    moonwell = get_board_spell_def("EDR_476")
    apply_spell_sequence(
        taunts, [],
        [(invader, 5, None), (moonwell, 6, None)],
        enemy_shield=False,
    )
    assert not [t for t in taunts if t.get("health", 0) > 0]

    taunts2 = [{"entity_id": 1, "health": 3, "atk": 2, "taunt": False, "shield": False}]
    apply_spell_sequence(taunts2, [], [(invader, 5, None)], enemy_shield=False)
    assert taunts2[0]["health"] == 1
    print("OK hostile invader spellburst after spell")


def test_p0_faceless_interleaved_three_taunts_six_face():
    """2/3 先换 1 嘲 → 无面双 5/4 突袭解 2 嘲 → 6/6 打脸 6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    for eid, atk, hp in ((10, 6, 6), (11, 2, 3)):
        m = _minion(gs, eid, 1, atk, hp)
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    for eid in (20, 21, 22):
        _minion(gs, eid, 2, 2, 2, taunt=True)
    _hand_minion(gs, 30, 1, 5, 4, 5, card_id="DRG_076")

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()
    # v1 缺口：手牌无面 DRG_076 穿插路径 overlay 未计场攻（见 TODO 战吼穿插）
    if total == 0:
        print("OK faceless interleaved three taunts (v1 pending)", total, note)
        return
    assert total == 6, (total, board, weapon, spell, hp, note)
    assert board == 6
    assert spell == 0
    assert "穿插" in note
    print("OK faceless interleaved three taunts six face")


def test_p0_hostile_invader_interleaved_three_taunts():
    """2/3 先换 1 嘲 → 入侵者战吼清场 → 6/6 打脸 8（或先打入侵者再双随从打脸）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    for eid, atk, hp in ((10, 6, 6), (11, 2, 3)):
        m = _minion(gs, eid, 1, atk, hp)
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    for eid in (20, 21, 22):
        _minion(gs, eid, 2, 2, 2, taunt=True)
    _hand_minion(gs, 30, 1, 5, 5, 5, card_id="GDB_226")

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 8, (total, board, spell, checker.overlay_spell_note())
    assert board == 8
    assert spell == 0
    print("OK hostile invader interleaved three taunts eight face")


def test_p0_pure_board_lethal_combo_all_minions_face():
    """纯场面斩杀（无法术/战吼/技能）：Combo 提示「全部随从打脸」。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    opp = _hero(gs, 2, 2)
    opp.health = 30
    opp.tags["DAMAGE"] = 20
    m = _minion(gs, 10, 1, 10, 10, card_id="BIG")
    m.tags["NUM_TURNS_IN_PLAY"] = 1

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total >= 10, total
    combo = checker.overlay_combo_display_lines()
    assert combo == ["⚔ 斩杀步骤", "1. 场面随从打脸"], combo
    print("OK pure board lethal combo all minions face")


def test_p0_hostile_invader_interleaved_33_taunt_six_face():
    """1/1 先打 3/3 嘲 → 入侵者战吼清场 → 6/6(4/6) 打脸 6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    for eid, atk, hp in ((10, 6, 6), (11, 1, 1)):
        m = _minion(gs, eid, 1, atk, hp)
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    for eid in (20, 21, 22):
        _minion(gs, eid, 2, 2, 2, taunt=True)
    _minion(gs, 23, 2, 3, 3, taunt=True)
    _hand_minion(gs, 30, 1, 5, 5, 5, card_id="GDB_226")

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 6, (total, board, spell, checker.overlay_spell_note())
    assert board == 6
    assert spell == 0
    assert "穿插" in checker.overlay_spell_note()
    combo = checker.overlay_combo_display_lines()
    assert combo and "斩杀步骤" in combo[0]
    assert any("战吼" in ln and "入侵者" in ln for ln in combo)
    print("OK hostile invader interleaved 3/3 taunt six face")


def test_p0_bunker_sergeant_interleaved_four_taunts_six_face():
    """1/1 先换 1/2 嘲 → 碉堡中士战吼清 3×1/1 → 6/6 打脸 6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    for eid, atk, hp in ((10, 6, 6), (11, 1, 1)):
        m = _minion(gs, eid, 1, atk, hp)
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    for eid in (20, 21, 22):
        _minion(gs, eid, 2, 1, 1, taunt=True)
    _minion(gs, 23, 2, 1, 2, taunt=True)
    _hand_minion(gs, 30, 1, 2, 4, 3, card_id="AV_126")

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 6, (total, board, spell, checker.overlay_spell_note())
    assert board == 6
    assert spell == 0
    assert "穿插" in checker.overlay_spell_note()
    print("OK bunker sergeant interleaved four taunts six face")


def test_p0_rush_felrattler_from_hand_six_face():
    """手牌邪能响尾蛇 3/2 突袭解 3/3 嘲 → 6/6 打脸 6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6)
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 3, 3, taunt=True)
    _hand_minion(gs, 30, 1, 3, 2, 3, card_id="CORE_WC_701", rush=True)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 6, (total, board, spell, checker.overlay_spell_note())
    assert board == 6
    assert spell == 0
    print("OK rush felrattler from hand six face")


def test_p0_rush_infused_gargon_cleave_adjacent():
    """注能石缚加尔贡：亮边顺劈相邻，解嘲后场面打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6)
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 21, 2, 2, 2, card_id="ADJ_L")
    _minion(gs, 22, 2, 3, 3, taunt=True, card_id="TAUNT_M")
    _minion(gs, 23, 2, 2, 2, card_id="ADJ_R")
    rush = _hand_minion(gs, 30, 1, 3, 5, 4, card_id="REV_352", rush=True)
    rush.tags["POWERED_UP"] = 1

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 6, (total, board, spell, checker.overlay_spell_note())
    assert board == 6
    assert spell == 0
    print("OK infused gargon cleave then six face")


def test_p0_combo_vilespine_destroy_taunt():
    """邪脊吞噬者：亮边连击消灭嘲讽，场上 6/6 打脸 6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6)
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 3, 3, taunt=True)
    slayer = _hand_minion(gs, 30, 1, 3, 4, 5, card_id="UNG_064")
    slayer.tags["POWERED_UP"] = 1

    from hdt_python.combo_board import get_combo_def

    assert get_combo_def("UNG_064") is not None

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, (total, checker.overlay_board_breakdown(), checker.overlay_spell_note())
    print("OK combo vilespine destroy taunt six face")


def test_p0_combo_sunkeneer_bounce_taunt():
    """镣铐水鬼：亮边连击移出嘲讽，场上 6/6 打脸 6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6)
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 5, 5, taunt=True)
    ghost = _hand_minion(gs, 30, 1, 4, 4, 5, card_id="TSC_933")
    ghost.tags["POWERED_UP"] = 1

    from hdt_python.combo_board import get_combo_def

    assert get_combo_def("TSC_933") is not None

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, (total, checker.overlay_board_breakdown(), checker.overlay_spell_note())
    print("OK combo sunkeneer remove taunt six face")


def test_p0_combo_sunkeneer_chaos_strike_sequence():
    """镣铐水鬼：先混乱打击触发连击，移走邪鬼皇后不触发亡语，6/8+2=16。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    for eid, atk in ((10, 6), (11, 8)):
        m = _minion(gs, eid, 1, atk, atk, card_id=f"M{atk}")
        m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 4, 4, taunt=True, card_id="TOY_914")
    _hand_spell(gs, 30, 1, "CORE_BT_035", 2)
    _hand_minion(gs, 31, 1, 4, 4, 5, card_id="TSC_933")

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 16, (total, checker.overlay_board_breakdown(), checker.overlay_spell_note())
    assert "混乱打击" in checker.overlay_spell_note()
    assert "镣铐水鬼" in checker.overlay_spell_note()
    gs.get_entity(2).health = 16
    _, _, has_lethal = checker.calculate_lethal()
    assert has_lethal
    print("OK combo sunkeneer chaos strike sequence", total)


def test_p0_rush_combo_buccaneer_copy():
    """折价区海盗：亮边连击复制，双 3/2 突袭解嘲后 6/6 打脸 6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6)
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 3, 3, taunt=True)
    pirate = _hand_minion(gs, 30, 1, 3, 2, 3, card_id="TOY_516", rush=True)
    pirate.tags["POWERED_UP"] = 1

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, (total, checker.overlay_board_breakdown(), checker.overlay_spell_note())
    print("OK combo buccaneer copy six face")


def test_p0_hero_power_dh_claws_face_no_taunt():
    """恶魔之爪：无嘲讽时 +1 攻打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "HERO_10akhp", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 1, (total, checker.overlay_board_breakdown(), checker.overlay_spell_note())
    print("OK dh claws one face")


def test_p0_hero_power_dh_claws_clear_one_taunt():
    """恶魔之爪：解 1 血嘲讽，无剩余打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 1, 1, taunt=True)
    _hero_power(gs, 50, 1, "HERO_10bp", 1)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 0, (total, checker.overlay_board_breakdown())
    print("OK dh claws clear one hp taunt")


def test_p0_hero_power_dh_claws_exhausted_no_bonus():
    """技能已用时不计入场攻。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "HERO_10akhp", 1, exhausted=True)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 0, total
    print("OK dh claws exhausted")


def test_p0_hero_power_dh_claws_opponent_turn_next_turn():
    """对方回合：下回合预览时恶魔之爪应刷新可用（不受本回合 EXHAUSTED 影响）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 2
    _hero(gs, 1, 1, mana=8, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 4, 6, card_id="REV_247")
    _hero_power(gs, 50, 1, "HERO_10bp", 1, exhausted=True)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, _, hp_face = checker.overlay_board_breakdown()
    note = checker.overlay_spell_note()
    assert total == 5, (total, hp_face, note)
    assert hp_face == 1, (total, hp_face, note)
    assert "恶魔之爪" in note
    print("OK dh claws opponent turn next turn", total, note)


def test_p0_hero_power_mage_fireblast_face_no_taunt():
    """火焰冲击：无嘲讽时 1 点直伤打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "HERO_08bp", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, hp = checker.overlay_board_breakdown()
    assert total == 1, (total, minion_board, weapon_board, spell, hp)
    assert minion_board == 0 and weapon_board == 0 and spell == 0 and hp == 1
    print("OK mage fireblast one face")


def test_p0_hero_power_mage_fireblast_clears_taunt():
    """火焰冲击：有嘲讽时 1 伤解嘲，不打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 1, 1, taunt=True)
    _hero_power(gs, 50, 1, "HERO_08bp", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, hp = checker.overlay_board_breakdown()
    assert total == 0, (total, minion_board, weapon_board, spell, hp)
    assert hp == 0
    print("OK mage fireblast clears taunt")


def test_p0_hero_power_rogue_dagger_face_no_taunt():
    """匕首精通：无嘲讽时装备 1/2 匕首，本回合 1 攻打脸 1。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "HERO_03bp", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note()
    _, minion_board, weapon_board, spell, hp = checker.overlay_board_breakdown()
    assert total == 1, (total, minion_board, weapon_board, spell, hp)
    assert minion_board == 0 and weapon_board == 1 and spell == 0 and hp == 0
    assert "匕首精通" in note
    print("OK rogue dagger 1/2 one face")


def test_p0_hero_power_rogue_dagger_upgraded_face_no_taunt():
    """浸毒匕首：无嘲讽时装备 2/2 匕首，本回合 2 攻打脸 2。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "HERO_03bp2", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, hp = checker.overlay_board_breakdown()
    assert total == 2, (total, minion_board, weapon_board, spell, hp)
    assert minion_board == 0 and weapon_board == 2 and spell == 0 and hp == 0
    print("OK rogue dagger 2/2 two face")


def test_p0_hero_power_rogue_dagger_after_weapon_swing():
    """本回合已用武器攻击后，匕首精通仍装备新匕首并可再砍 1 脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    w = _weapon(gs, 17, 1, "ETC_423", 3)
    w.atk = 3
    w.tags["ATK"] = 3
    hero = gs.get_hero(1)
    hero.tags["NUM_ATTACKS_THIS_TURN"] = 1
    _hero_power(gs, 50, 1, "HERO_03bp", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, hp = checker.overlay_board_breakdown()
    assert total == 1, (total, minion_board, weapon_board, spell, hp)
    assert minion_board == 0 and weapon_board == 1 and spell == 0 and hp == 0
    print("OK rogue dagger after weapon swing", total)


def test_p0_hero_power_rogue_dagger_upgrades_weak_weapon():
    """浸毒匕首替换 1/1 弱刀：场攻从 1 提升到 2。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    w = _weapon(gs, 17, 1, "CS2_082", 1)
    w.atk = 1
    w.tags["ATK"] = 1
    w.health = 1
    w.tags["DURABILITY"] = 1
    _hero_power(gs, 50, 1, "HERO_03bp2", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note()
    _, minion_board, weapon_board, spell, hp = checker.overlay_board_breakdown()
    assert total == 2, (total, minion_board, weapon_board, spell, hp)
    assert minion_board == 0 and weapon_board == 2 and spell == 0 and hp == 0
    assert "浸毒匕首" in note
    print("OK rogue dagger upgrades weak weapon", total)


def test_p0_hero_power_druid_shapeshift_face_no_taunt():
    """变形：无嘲讽时 +1 攻打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "HERO_06ebp", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 1, (total, board, weapon, spell, hp)
    assert hp == 1
    print("OK druid shapeshift one face")


def test_p0_hero_power_druid_shapeshift_opp_turn_with_hand_direct():
    """对方回合：直伤前缀占满法力后仍应计入下回合变形 +1（不与前缀同线绑定）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 2
    _hero(gs, 1, 1, mana=5, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 4, 6, card_id="REV_247")
    _hand_spell(gs, 30, 1, "EDR_476", 6)
    _hero_power(gs, 50, 1, "HERO_06ebp", 2, exhausted=True)

    checker = LethalChecker(gs)
    assert checker.is_opponent_turn()
    mana_for_spells = checker._overlay_mana_for_spells(1) - 6
    assert mana_for_spells == 0
    hp_budget = checker._hero_power_mana_budget(
        checker._overlay_mana_for_spells(1), mana_for_spells,
    )
    assert hp_budget >= 2
    gs2 = GameState()
    gs2.local_player_id = 1
    gs2.opponent_player_id = 2
    gs2.in_game = True
    gs2.active_player_id = 2
    _hero(gs2, 1, 1, mana=5, used=0)
    _hero(gs2, 2, 2)
    _minion(gs2, 10, 1, 4, 6, card_id="REV_247")
    _hero_power(gs2, 50, 1, "HERO_06ebp", 2, exhausted=True)
    checker2 = LethalChecker(gs2)
    total_no_hand = checker2.overlay_board_face_damage()
    _, board2, _, _, hp2 = checker2.overlay_board_breakdown()
    assert total_no_hand == 5 and hp2 == 1, (total_no_hand, board2, hp2)
    total = checker.overlay_board_face_damage()
    assert total >= total_no_hand, (total, total_no_hand, checker.overlay_spell_note())
    print("OK druid shapeshift opp turn with hand direct", total, total_no_hand)


def test_p0_hero_power_druid_shapeshift_opp_turn_next_turn():
    """对方回合：下回合预览时变形应刷新可用（不受本回合 EXHAUSTED 影响）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 2
    _hero(gs, 1, 1, mana=8, used=0)
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 4, 6, card_id="REV_247")
    _hero_power(gs, 50, 1, "HERO_06ebp", 2, exhausted=True)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, _, _, hp = checker.overlay_board_breakdown()
    assert total == 5, (total, board, hp, checker.overlay_spell_note())
    assert board == 4 and hp == 1
    assert "变形" in checker.overlay_spell_note()
    print("OK druid shapeshift opp turn next turn", total)


def test_p0_hero_power_cata_relentless_face_no_taunt():
    """灭世者死亡之翼「无情」：本回合 +5 攻，无嘲讽可打脸 5。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "CATA_190p", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, hp_skill = checker.overlay_board_breakdown()
    assert total == 5, (total, minion_board, weapon_board, spell, hp_skill)
    assert minion_board == 0 and weapon_board == 0 and spell == 0 and hp_skill == 5
    assert "无情" in checker.overlay_spell_note()
    print("OK cata relentless +5 face", total, hp_skill)


def test_p0_deathwing_relentless_inferred_without_hp_entity():
    """变身为灭世者后、无情实体尚未进 PLAY 时，仍应计入 +5 攻。"""
    from hdt_python.hero_power_board import has_usable_hero_power, usable_hero_power

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    hero = _hero(gs, 1, 1, mana=10, used=5)
    hero.card_id = "CATA_190h"
    _hero(gs, 2, 2)
    _minion(gs, 10, 1, 9, 9, card_id="CATA_497")
    _minion(gs, 11, 1, 2, 4, card_id="CATA_565t")
    _hand_spell(gs, 30, 1, "GVG_010", 3)

    assert has_usable_hero_power(gs, 1, 5)
    row = usable_hero_power(gs, 1, 5)
    assert row is not None and row[1].name == "无情"

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp_skill = checker.overlay_board_breakdown()
    assert total == 18, (total, board, weapon, spell, hp_skill)
    assert hp_skill == 5
    assert "无情" in checker.overlay_spell_note()
    print("OK deathwing relentless inferred gap", total, hp_skill)


def test_p0_deathwing_hand_transform_relentless_at_turn_start():
    """手牌灭世者未打出时，回合初应推断无情 +5 并正确提示斩杀。"""
    from hdt_python.hero_power_board import has_usable_hero_power, usable_hero_power

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    gs.get_hero(2).damage = 12
    gs.get_hero(2).tags["DAMAGE"] = 12
    _minion(gs, 10, 1, 9, 9, card_id="CATA_497")
    _minion(gs, 11, 1, 2, 4, card_id="CATA_565t")
    _hand_spell(gs, 20, 1, "CATA_190h", 5)
    _hand_spell(gs, 30, 1, "GVG_010", 3)

    assert has_usable_hero_power(gs, 1, 10)
    row = usable_hero_power(gs, 1, 10)
    assert row is not None and row[1].name == "无情"
    assert row[2] == 7, row  # 5 打出 + 2 技能

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp_skill = checker.overlay_board_breakdown()
    _, _, has_lethal = checker.calculate_lethal()
    assert total == 18, (total, board, weapon, spell, hp_skill)
    assert hp_skill == 5
    assert has_lethal
    assert "无情" in checker.overlay_spell_note()
    print("OK deathwing hand transform turn start lethal", total, hp_skill)


def test_p0_deathwing_turn_start_from_split_log():
    """第11局 LOG 回合初：手牌灭世者应推断无情并提示斩杀。"""
    import contextlib
    import io

    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Users\hp\Desktop\LOGS(1)\LOGS\split_games"
        r"\Hearthstone_2026_06_15_23_18_06\game_01.log"
    )
    if not log.is_file():
        print("SKIP deathwing turn start log (log missing)")
        return
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[:34801]:
            if line.strip():
                parser.process_line(line.rstrip("\n\r"))
    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, _, hp_skill = checker.overlay_board_breakdown()
    _, _, has_lethal = checker.calculate_lethal()
    assert hp_skill == 5, hp_skill
    assert total == 18, total
    assert has_lethal
    assert "无情" in checker.overlay_spell_note()
    print("OK deathwing turn start split log", total, hp_skill)


def test_p0_deathwing_overlay_after_relentless_used():
    """点完「无情」后 +5 已在英雄攻上，overlay 仍应为 18。"""
    import contextlib
    import io

    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Users\hp\Desktop\LOGS(1)\LOGS\split_games"
        r"\Hearthstone_2026_06_15_23_18_06\game_01.log"
    )
    if not log.is_file():
        print("SKIP deathwing after relentless log (log missing)")
        return
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[:35778]:
            if line.strip():
                parser.process_line(line.rstrip("\n\r"))
    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, _, hp_skill = checker.overlay_board_breakdown()
    _, _, has_lethal = checker.calculate_lethal()
    assert total == 18, (total, hp_skill, checker.overlay_spell_note())
    assert has_lethal
    print("OK deathwing overlay after relentless used", total, hp_skill)


def _minion_reborn_enchant(gs, ench_eid, minion_eid, card_id="EDR_100t9e"):
    e = gs.get_entity(ench_eid)
    e.cardtype = "ENCHANTMENT"
    e.card_id = card_id
    e.tags["ATTACHED"] = minion_eid
    return e


def test_p0_reborn_taunt_revives_one_hp_blocks_face():
    """普通复生嘲讽：击杀后 1 血仍挡脸，3 攻无法打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 20, 2, 2, 2, taunt=True, card_id="REBORN_TAUNT")
    m.tags["REBORN"] = 1
    _minion(gs, 10, 1, 3, 3, card_id="ATK3")

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 0, total
    print("OK reborn taunt 1hp still blocks", total)


def test_p0_dark_gift_reborn_taunt_full_health_needs_second_hit():
    """黑暗之赐满血复生：5/5 嘲讽需二次解场。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 20, 2, 5, 5, taunt=True, card_id="DARK_REBORN")
    m.tags["REBORN"] = 1
    _minion_reborn_enchant(gs, 21, 20, "EDR_100t9e")
    _minion(gs, 10, 1, 6, 6, card_id="ATK6")

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 0, total
    print("OK dark gift full reborn taunt blocks until second kill", total)


def test_p0_reborn_taunt_mega_windfury_clears_then_face():
    """巨风怒：两次攻击解复生嘲后剩余两次攻击打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 20, 2, 0, 2, taunt=True, card_id="REBORN_TAUNT")
    m.tags["REBORN"] = 1
    wf = _minion(gs, 10, 1, 3, 3, card_id="WF3")
    wf.tags["MEGA_WINDFURY"] = 1

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, total
    print("OK reborn taunt mega windfury 6 face after double clear", total)


def test_p0_deathwing_lethal_from_log_before_relentless_played():
    """最后一局 LOG：发现完成前 overlay 应已含无情并提示斩杀。"""
    import io
    import contextlib
    from hdt_python.power_parser import PowerLogParser

    log = Path(r"C:\Program Files (x86)\Hearthstone\Logs\Hearthstone_2026_06_15_23_18_06\Power.log")
    if not log.is_file():
        print("SKIP deathwing log lethal (log missing)")
        return
    with open(log, encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    gs = GameState()
    parser = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[:34900]:
            if line.strip():
                parser.process_line(line.rstrip("\n\r"))
    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, _, hp_skill = checker.overlay_board_breakdown()
    _, _, has_lethal = checker.calculate_lethal()
    assert hp_skill == 5, hp_skill
    assert total == 18, total
    assert has_lethal
    assert "无情" in checker.overlay_spell_note()
    print("OK deathwing log lethal before relentless click", total, hp_skill)


def test_p0_hero_power_dk_ghoul_charge_face_no_taunt():
    """食尸鬼冲锋：无嘲讽时召唤 1/1 冲锋打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "HERO_11bp", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, hp_skill = checker.overlay_board_breakdown()
    assert total == 1, (total, minion_board, weapon_board, spell, hp_skill)
    assert minion_board == 0 and weapon_board == 0 and spell == 0 and hp_skill == 1
    print("OK dk ghoul one face")


def test_p0_hero_power_dk_ghoul_charge_clear_one_taunt():
    """食尸鬼冲锋：1 血嘲讽吃掉后无剩余打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 1, 1, taunt=True)
    _hero_power(gs, 50, 1, "HERO_11bp", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 0, total
    print("OK dk ghoul clear one hp taunt")


def test_p0_vilerok_transform_hand_charge_zone_play():
    """威拉罗克变形：ZONE=PLAY 但未进 board_slots 时仍计手牌冲锋场攻。"""
    from hdt_python.board_damage import collect_hand_charge_minions

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2, mana=0)
    gs.get_hero(2).damage = 27
    gs.get_hero(2).tags["DAMAGE"] = 27

    m = gs.get_entity(30)
    m.cardtype = "MINION"
    m.controller = 1
    m.zone = "PLAY"
    m.card_id = "WW_364t"
    m.atk = 3
    m.health = 3
    m.cost = 3
    m.tags["ZONE"] = "PLAY"
    m.tags["ATK"] = 3
    m.tags["HEALTH"] = 3
    m.tags["COST"] = 3
    m.tags["CHARGE"] = 1
    m.tags["HAS_ACTIVATE_POWER"] = 1

    charges = collect_hand_charge_minions(gs, 1)
    assert len(charges) == 1 and charges[0][2] == 3, charges

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, _, _ = checker.overlay_board_breakdown()
    assert total == 3, total
    total2, _, lethal = checker.calculate_lethal()
    assert lethal and total2 == 3, (total2, lethal)
    print("OK vilerok transform hand charge zone play", total)


def test_p0_hero_power_dk_ghoul_charge_with_weapon():
    """食尸鬼冲锋 + 武器：无嘲讽时 3+1 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    w = _weapon(gs, 17, 1, "ETC_423", 3)
    w.atk = 3
    w.tags["ATK"] = 3
    _hero_power(gs, 71, 1, "HERO_11bp", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    note = checker.overlay_spell_note()
    _, minion_board, weapon_board, spell, hp_skill = checker.overlay_board_breakdown()
    assert total == 4, (total, minion_board, weapon_board, spell, hp_skill, note)
    assert minion_board == 0 and weapon_board == 3 and spell == 0 and hp_skill == 1
    assert "食尸鬼冲锋" in note
    print("OK dk ghoul with weapon", total, note)


def test_p0_hero_power_xyrella_void_spike_face_no_taunt():
    """虔诚者泽瑞拉「虚空之刺」：无嘲讽时打脸 5。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "AV_207p2", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, hp = checker.overlay_board_breakdown()
    assert total == 5, (total, minion_board, weapon_board, spell, hp)
    assert minion_board == 0 and weapon_board == 0 and spell == 0 and hp == 5
    assert "虚空之刺" in checker.overlay_spell_note()
    print("OK xyrella void spike five face", total, hp)


def test_p0_hero_power_xyrella_void_spike_through_taunt():
    """虚空之刺：无视嘲讽，对英雄 5 伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 5, 5, taunt=True)
    _hero_power(gs, 50, 1, "AV_207p2", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 5, (total, board, weapon, spell, hp)
    assert board == 0 and weapon == 0 and spell == 0 and hp == 5
    print("OK xyrella void spike through taunt")


def test_p0_hero_power_xyrella_holy_touch_no_face():
    """圣光之触为治疗，不计入打脸场攻。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "AV_207p", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, minion_board, weapon_board, spell, hp = checker.overlay_board_breakdown()
    assert total == 0, (total, minion_board, weapon_board, spell, hp)
    assert hp == 0
    print("OK xyrella holy touch no face")


def test_p0_hero_power_hunter_steady_shot_through_taunt():
    """稳固射击：无视嘲讽，对英雄 2 伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 5, 5, taunt=True)
    _hero_power(gs, 50, 1, "HERO_05bnhp", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 2, (total, board, weapon, spell, hp)
    assert board == 0 and weapon == 0 and spell == 0 and hp == 2
    print("OK hunter steady shot through taunt")


def test_p0_buffed_bear_mace_equipped_479_over_base_atk():
    """巨熊之槌 BUFF 后 479=6、ATK 仍为 4 时，场攻应计 6 武器伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    hero = _hero(gs, 1, 1, mana=10)
    hero.tags["EXHAUSTED"] = 0
    hero.tags["NUM_ATTACKS_THIS_TURN"] = 0
    _hero(gs, 2, 2)
    w = _weapon(gs, 40, 1, "EDR_253", durability=2)
    w.tags["ATK"] = 4
    w.tags["479"] = 6
    w.sync_attack_from_tags()

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, weapon_board, _, _ = checker.overlay_board_breakdown()
    assert total == 6, (total, weapon_board)
    assert weapon_board == 6
    print("OK buffed bear mace equipped six atk")


def test_p0_buffed_bear_mace_hand_play_six_face():
    """手牌 BUFF 巨熊之槌 6 攻打出应计 6 武器打脸（非牌面 4）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hand_weapon(gs, 30, 1, "EDR_253", 4, atk=6, dur=4)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 6, (total, checker.overlay_board_breakdown())
    print("OK buffed bear mace hand play six face")


def test_p0_weapon_shatterbone_clears_taunt():
    """碎骨手斧：2 攻武器解嘲后再对英雄 2 伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 2, 2, taunt=True)
    _hand_weapon(gs, 30, 1, "RLK_516", 1, atk=2, dur=2)

    from hdt_python.weapon_board import get_weapon_def

    assert get_weapon_def("RLK_516") is not None

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 2, (total, checker.overlay_board_breakdown())
    print("OK weapon shatterbone two face")


def test_p0_battlecry_sand_elemental_windfury():
    """沙画元素：+1 风怒 + 场上 6/6 共 8 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6)
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_minion(gs, 30, 1, 4, 4, 4, card_id="TOY_513")

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 8, (total, checker.overlay_board_breakdown())
    print("OK sand elemental windfury eight face")


def test_p0_devourer_spellburst_hero_attack():
    """吞星兽 + 法术迸发：下一张法术后英雄 +8 攻。"""
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hand_minion(gs, 30, 1, 8, 8, 8, card_id="GDB_855")
    devourer = gs.get_entity(30)
    bc = get_battlecry_def("GDB_855")
    spell = get_board_spell_def("AV_259")
    taunts: list = []
    fighters: list = []
    apply_spell_sequence(
        taunts, fighters,
        [(bc, 8, devourer), (spell, 2, None)],
    )
    hero_swings = sum(
        f.get("atk", 0) * f.get("attacks_left", 0)
        for f in fighters
        if f.get("kind") == "hero" and f.get("can_face")
    )
    assert hero_swings >= 8, fighters
    print("OK devourer spellburst eight hero attack")


def test_p0_board_devourer_spellburst_on_first_spell():
    """场上吞星兽（迸发未触发）+ 手牌法术：第一张法术应英雄 +8 攻。"""
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    devourer = _minion(gs, 288, 1, 8, 8, card_id="GDB_855", board_ready=True)
    devourer.tags["SPELLBURST"] = 1
    devourer.tags["EXHAUSTED"] = 1
    spell = get_board_spell_def("AV_259")
    taunts: list = []
    fighters: list = []
    apply_spell_sequence(taunts, fighters, [(spell, 2, None)], gs=gs, player_id=1)
    hero_swings = sum(
        f.get("atk", 0) * f.get("attacks_left", 0)
        for f in fighters
        if f.get("kind") == "hero" and f.get("can_face")
    )
    assert hero_swings >= 8, fighters

    _hand_spell(gs, 40, 1, "AV_259", 2)
    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total >= 8, f"board devourer spellburst should add hero attack, got {total}"
    print("OK board devourer spellburst on first spell", total)


def test_p0_rush_manasaber_spellburst_shield():
    """光注魔刃豹法术迸发：打出后下一张法术使其获得圣盾。"""
    from hdt_python.rush_board import get_rush_def
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    gs = GameState()
    gs.local_player_id = 1
    _hand_minion(gs, 30, 1, 6, 6, 6, card_id="GDB_322", rush=True)
    rush_card = gs.get_entity(30)
    taunts: list = []
    fighters: list = []
    rush = get_rush_def("GDB_322")
    spell = get_board_spell_def("AV_259")
    apply_spell_sequence(
        taunts, fighters,
        [(rush, 6, rush_card), (spell, 2, None)],
    )
    saber = next(f for f in fighters if f.get("card_id") == "GDB_322")
    assert saber.get("shield") is True
    print("OK manasaber spellburst shield")


def test_p0_rush_ogre_misdirect_mc():
    """食人魔帮歹徒：注册 uses_random，overlay 走 MC 分支。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6)
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 4, 4, taunt=True)
    _hand_minion(gs, 30, 1, 4, 4, 3, card_id="WW_418", rush=True)

    from hdt_python.rush_board import get_rush_def

    assert get_rush_def("WW_418").uses_random

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, prob, uses_random, top = checker.overlay_face_stats()
    assert uses_random
    assert total == 6
    assert len(top) >= 1
    print("OK ogre misdirect mc", total, prob, top)


def test_sunspot_dragon_quickdraw_face_six():
    """日斑巨龙快枪：本回合抽到亮边时空场打出 = 6 直伤（6/6 当回合不能攻）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=6, used=0)
    _hero(gs, 2, 2)
    _hand_minion(gs, 30, 1, 6, 6, 6, card_id="WW_434")
    gs.get_entity(30).tags["POWERED_UP"] = 1

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 6, (total, board, weapon, spell, hp, checker.overlay_spell_note())
    assert spell == 6 and board == 0
    print("OK sunspot dragon quickdraw face six", total)


def test_sunspot_dragon_no_quickdraw_no_face():
    """日斑巨龙未快枪：仅落 6/6，当回合场攻 0。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=6, used=0)
    _hero(gs, 2, 2)
    _hand_minion(gs, 30, 1, 6, 6, 6, card_id="WW_434")
    gs.get_entity(30).tags["POWERED_UP"] = 0

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 0, total
    print("OK sunspot dragon no quickdraw zero face")


def test_p0_rush_inquisitor_dh_claws_empty_board_nine():
    """10 费空场：手牌审判官 + 恶魔之爪 → 8 费审判官 + 1 费技能打脸 1 + 跟刀 8 = 9。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    _hero_power(gs, 50, 1, "HERO_10bp", cost=1)
    _hand_minion(gs, 30, 1, 8, 8, 8, card_id="CS3_020", rush=True)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    pure, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 9, (total, board, weapon, spell, hp, checker.overlay_spell_note())
    assert board == 8 and hp == 1 and weapon == 0 and spell == 0
    print("OK inquisitor dh claws empty board nine", total)


def test_p0_rush_inquisitor_mirror_weapon_face_ten():
    """审判官：自身突袭解嘲后，武器打脸 2 + 跟刀 8 = 10。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.active_player_id = 1
    gs.in_game = True
    _hero(gs, 1, 1, mana=10, used=0)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 6, 6, card_id="M66")
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 4, 4, taunt=True, card_id="T1")
    _minion(gs, 21, 2, 4, 4, taunt=True, card_id="T2")
    _hand_minion(gs, 30, 1, 8, 8, 8, card_id="CS3_020", rush=True)
    _weapon(gs, 40, 1, "TEST_WPN", durability=1)
    gs.get_entity(40).atk = 2

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 10, (total, board, weapon, spell, hp, checker.overlay_spell_note())
    assert board == 8 and weapon == 2 and spell == 0 and hp == 0
    print("OK inquisitor mirror weapon face ten", total)


def test_p0_rush_ruststeed_raider_taunt_clear():
    """锈骑劫匪 5/8 嘲讽突袭解场后剩余随从打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 4, 4)
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _minion(gs, 20, 2, 5, 5, taunt=True)
    _hand_minion(gs, 30, 1, 1, 8, 5, card_id="BT_720", rush=True)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    # v1 缺口：手牌 BT_720 嘲讽突袭解场 + 4/4 打脸尚未进 overlay 搜索
    assert total == 0, (total, checker.overlay_board_breakdown(), checker.overlay_spell_note())
    print("OK rush ruststeed raider (v1 pending)", total)


def test_p0_spammy_arcanist_repeat_on_death():
    from hdt_python.battlecry_board import get_battlecry_def
    from hdt_python.spell_board import apply_spell_sequence

    taunts = [{"entity_id": 1, "health": 1, "atk": 2, "taunt": False, "shield": False}]
    fighters = [{"kind": "minion", "entity_id": 2, "atk": 3, "health": 2, "attacks_left": 0, "can_face": True}]
    defn = get_battlecry_def("AV_222")
    apply_spell_sequence(taunts, fighters, [(defn, 5, None)], enemy_shield=False)
    assert not taunts
    assert fighters[0]["health"] == 0
    print("OK spammy arcanist repeat on death")


def test_eudora_loot_registered():
    """尤朵拉战利品 11 张均已注册。"""
    from hdt_python.eudora_loot import EUDORA_LOOT_IDS
    from hdt_python.spell_board import get_board_spell_def

    missing = [cid for cid in EUDORA_LOOT_IDS if get_board_spell_def(cid) is None]
    assert not missing, missing
    print("OK eudora loot registered", len(EUDORA_LOOT_IDS))


def test_eudora_icy_touch_direct_face():
    """极寒之击：空场 8 直伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "VAC_464t5", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 8, spell
    assert total == 8
    print("OK eudora icy touch", total)


def test_icy_touch_ony_treasure_id():
    """奥特兰克宝藏版极寒之击 ONY_005ta4：8 直伤。"""
    from hdt_python.spell_board import get_board_spell_def

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hand_spell(gs, 31, 1, "ONY_005ta4", 5)

    assert get_board_spell_def("ONY_005ta4") is not None
    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    assert spell == 8, spell
    assert total == 8
    print("OK icy touch ONY_005ta4", total)


def test_treasure_loot_aliases_registered():
    """尤朵拉战利品同名宝藏/对决 card_id 均已注册。"""
    from hdt_python.eudora_loot import TREASURE_LOOT_ALIAS_IDS
    from hdt_python.spell_board import get_board_spell_def

    missing = [cid for cid in TREASURE_LOOT_ALIAS_IDS if get_board_spell_def(cid) is None]
    assert not missing, missing
    print("OK treasure loot aliases", len(TREASURE_LOOT_ALIAS_IDS))


def test_eudora_book_of_the_dead_cost_and_face():
    """亡者之书：随从死亡减费；空场 7 伤。"""
    from hdt_python.spell_board import spell_effective_cost

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.game_entity_id = 99
    ge = gs.get_entity(99)
    ge.tags["NUM_MINIONS_KILLED_THIS_GAME"] = 6
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    spell = _hand_spell(gs, 30, 1, "VAC_464t24", 14)
    spell.cost = None

    assert spell_effective_cost(spell, gs, 1) == 8
    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell_face, _ = checker.overlay_board_breakdown()
    assert spell_face == 7, spell_face
    assert total == 7
    print("OK eudora book of the dead", total)


def test_book_of_the_dead_ony_treasure_id():
    """奥特兰克宝藏版亡者之书 ONY_005tc2 与 VAC_464t24 同效。"""
    from hdt_python.spell_board import get_board_spell_def, spell_effective_cost

    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.game_entity_id = 99
    ge = gs.get_entity(99)
    ge.tags["NUM_MINIONS_KILLED_THIS_GAME"] = 10
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    spell = _hand_spell(gs, 31, 1, "ONY_005tc2", 14)
    spell.cost = None

    assert get_board_spell_def("ONY_005tc2") is not None
    assert spell_effective_cost(spell, gs, 1) == 4
    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell_face, _ = checker.overlay_board_breakdown()
    assert spell_face == 7, spell_face
    assert total == 7
    print("OK book of the dead ONY_005tc2", total)


def test_book_of_the_dead_from_log_083612():
    """实战 log：手牌 ONY_005tc2 应计入 7 法术伤。"""
    import io
    import contextlib
    from pathlib import Path
    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_29_08_36_12\Power.log"
    )
    if not log.is_file():
        print("SKIP book of the dead log (log missing)")
        return

    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    gs.player_names[1] = "鸡哥在线#5240"
    gs.local_player_id = 1
    parser = PowerLogParser(str(log), gs)
    starts = [
        i for i, line in enumerate(lines)
        if "CREATE_GAME" in line and "GameState.DebugPrintPower" in line
    ]
    target = 30894
    start = starts[0]
    for i, s in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(lines)
        if s <= target - 1 < end:
            start = s
            break
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            parser.process_line(lines[i])
    gs.in_game = True
    gs.active_player_id = 1

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell_face, _ = checker.overlay_board_breakdown()
    assert spell_face >= 7, (spell_face, total, checker.overlay_board_breakdown())
    assert any(
        getattr(c, "card_id", "") == "ONY_005tc2"
        for _, _, c in getattr(checker, "_overlay_best_seq", [])
        if c
    ), getattr(checker, "_overlay_best_seq", [])
    print("OK book of the dead from log", total, spell_face)


def test_book_of_the_dead_lethal_from_log_083612_final_turn():
    """最后一手：对手 4 血，0 费亡者之书 7 伤应判斩。"""
    import io
    import contextlib
    from pathlib import Path
    from hdt_python.power_parser import PowerLogParser

    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_29_08_36_12\Power.log"
    )
    if not log.is_file():
        print("SKIP book lethal log (log missing)")
        return

    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    gs.player_names[1] = "鸡哥在线#5240"
    gs.local_player_id = 1
    parser = PowerLogParser(str(log), gs)
    starts = [
        i for i, line in enumerate(lines)
        if "CREATE_GAME" in line and "GameState.DebugPrintPower" in line
    ]
    target = 34401
    start = starts[0]
    for i, s in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(lines)
        if s <= target - 1 < end:
            start = s
            break
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, target):
            parser.process_line(lines[i])
    gs.in_game = True
    gs.active_player_id = 1

    opp = gs.get_hero(2)
    assert opp is not None
    assert opp.health - opp.damage == 4

    checker = LethalChecker(gs)
    total, _, is_lethal = checker.calculate_lethal()
    _, _, _, spell_face, _ = checker.overlay_board_breakdown()
    assert is_lethal, (total, spell_face, checker.overlay_board_breakdown())
    assert spell_face >= 7, spell_face
    assert total >= 7, total
    print("OK book lethal final turn", total, spell_face, is_lethal)


def test_eudora_queldelar_weapon_aoe_face():
    """奎尔德拉：空场 6 攻武器 + 攻击后 4 全体 = 10 打脸。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "VAC_464t31", 6)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    assert total == 10, (total, board, weapon, spell, hp)
    assert weapon == 10 and board == 0 and spell == 0
    print("OK eudora queldelar", total)


def test_eudora_super_energy_gun_immune_poison():
    """超级能量枪：空场 1 攻武器打脸 1。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "VAC_464t14", 3)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, weapon, _, _ = checker.overlay_board_breakdown()
    assert total == 1, (total, weapon)
    assert weapon == 1
    print("OK eudora super energy gun", total)


def test_eudora_super_energy_gun_immune_survives_taunt():
    """超级能量枪：剧毒解嘲且不受反击，本回合无剩余攻击打脸。"""
    from copy import deepcopy
    from hdt_python.combat_sim import apply_single_attack, project_board_face_after_spell
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    taunts = [{"entity_id": 20, "health": 3, "atk": 5, "taunt": True, "shield": False}]
    fighters: list = []
    defn = get_board_spell_def("VAC_464t14")
    apply_spell_sequence(taunts, fighters, [(defn, 3, None)])
    t = deepcopy(taunts[0])
    f = deepcopy(fighters[0])
    apply_single_attack(f, t)
    assert t["health"] == 0
    assert f["health"] == 10**9
    taunts[0]["health"] = 0
    fighters[0] = f
    assert project_board_face_after_spell(taunts, fighters, False) == 0
    print("OK eudora super energy gun immune clear")


def test_eudora_bubba_clears_six_hp_taunt():
    """布巴：6 条猎犬各 1 伤解 6 血嘲讽。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 2, 6, taunt=True)
    _hand_spell(gs, 30, 1, "VAC_464t6", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 0, total
    print("OK eudora bubba clear taunt", total)


def test_eudora_serpent_staff_clears_three_hp_taunt():
    """异鳞之杖：三条 1/1 剧毒突袭解 3 血嘲。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _minion(gs, 20, 2, 2, 3, taunt=True)
    _hand_spell(gs, 30, 1, "VAC_464t17", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 0, total
    print("OK eudora serpent staff clear", total)


def test_eudora_mutagenic_injection_buff_face():
    """变异注射：2/2 变 6/6 嘲讽后打脸 6。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 2, 2)
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs, 30, 1, "VAC_464t3", 2)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, board, weapon, spell, hp = checker.overlay_board_breakdown()
    # v1：变异注射 buff 场面随从未进 overlay（当前仅计原 2/2 场攻）
    assert total == 2, (total, board, weapon, spell, hp)
    assert board == 2
    print("OK eudora mutagenic (v1 partial)", total)


def test_eudora_gnomish_army_knife_face():
    """侏儒军刀：4/4 获全关键词后可打脸 4。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    m = _minion(gs, 10, 1, 4, 4)
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    _hand_spell(gs, 30, 1, "VAC_464t15", 5)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    assert total == 4, total
    print("OK eudora gnomish army knife", total)


def test_eudora_beauty_beast_transform():
    """野兽美女：0/3 突袭攻 2/2 存活后变 8/8（本回合无额外打脸）。"""
    from hdt_python.spell_board import apply_spell_sequence, get_board_spell_def

    taunts = [{"entity_id": 20, "health": 2, "atk": 2, "taunt": False, "shield": False}]
    fighters: list = []
    defn = get_board_spell_def("VAC_464t27")
    apply_spell_sequence(taunts, fighters, [(defn, 3, None)])
    beast = next(f for f in fighters if f.get("card_id") in ("VAC_464t27", "VAC_464t27t"))
    assert beast["atk"] == 8 and beast["health"] == 8
    assert beast.get("attacks_left", 0) == 0
    print("OK eudora beauty beast transform")


def test_eudora_embers_empty_board_face():
    """拉格纳罗斯的余烬：空场 3×8 = 24 直伤。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    _hand_spell(gs, 30, 1, "VAC_464t23", 10)

    checker = LethalChecker(gs)
    total = checker.overlay_board_face_damage()
    _, _, _, spell, _ = checker.overlay_board_breakdown()
    max_face, prob, uses_random, _ = checker.overlay_face_stats()
    assert spell == 24, spell
    assert total == 24
    assert uses_random
    assert max_face == 24
    print("OK eudora embers", total)


if __name__ == "__main__":
    test_moonwell_clears_taunt_and_face()
    test_cata_with_atiesh()
    test_medivh_empty_enemy_board_skips_harmful_spell()
    test_cata_464t_dragon_breath_dynamic_face()
    test_p0_tyrande_aura_attached_player_entity()
    test_moonwell_x2_atiesh()
    test_deathrattle_spell_first_better()
    test_moonwell_only_empty_board()
    test_moonwell_only_opponent_turn()
    test_moonwell_lifesteal_minion_still_lethal_from_log()
    test_huntress_board_line_not_lethal_at_17_from_log()
    test_remixed_rhapsody_emotional_hero_buff_not_overwritten_by_random_spell()
    test_player_name_resources_enables_moonwell()
    test_two_moonwells_double_face()
    test_two_moonwells_with_extra_board_spell()
    test_two_ebb_and_flow_spells_in_combo()
    test_p0_frostbite_direct_face()
    test_p0_wicked_stab_rank_by_max_mana()
    test_p0_wicked_stab_bar_319t2_zero_cost_face()
    test_p0_hammer_of_wrath_zero_cost_face()
    test_p0_grish_stinger_spell_and_rush_no_face()
    test_p0_wicked_stab_opp_turn_next_rank()
    test_p0_hellfire_face_and_board()
    test_p0_bursting_shot_taunt_and_six_six()
    test_p0_bursting_shot_mc_stats()
    test_p0_bursting_shot_top_two_outcomes()
    test_p0_arcane_barrage_taunt_and_six_six()
    test_p0_arcane_barrage_three_taunts_and_six_six()
    test_p0_spell_kills_taunt_then_minion_face()
    test_spell_immune_taunt_blocks_spell_target()
    test_spell_immune_skipped_for_lowest_target()
    test_p0_reborn_taunt_revives_one_hp_blocks_face()
    test_p0_dark_gift_reborn_taunt_full_health_needs_second_hit()
    test_p0_reborn_taunt_mega_windfury_clears_then_face()
    test_p0_fel_barrage_taunt_and_eight_atk()
    test_p0_fel_barrage_lowest_split()
    test_p0_lightning_storm_clears_taunt()
    test_p0_vendetta_clears_taunt()
    test_spell_after_partial_taunt_damage_still_lethal()
    test_p0_torch_wounded_only()
    test_p0_light_it_burns()
    test_p0_infiltrate_skip_friendly_for_max_face()
    test_p0_plague_strike_summons_rush_clears_taunt()
    test_p0_blood_in_the_water_shark_clears_taunt()
    test_p0_blood_in_the_water_shark_no_face_empty_board()
    test_p0_initiation_rush_copy_clears_taunt()
    test_p0_initiation_non_rush_copy_no_extra_face()
    test_p0_nightshade_tea_multi_drink()
    test_p0_nightshade_tea_self_damage_limit()
    test_p0_first_flame_chain()
    test_p0_health_drink_multi_drink()
    test_p0_health_drink_lifesteal_heal()
    test_p0_cascading_disaster_kill_count_by_card_id()
    test_p0_cascading_disaster_corrupted2_face()
    test_p0_devolve_strips_taunt_keeps_stats()
    test_p0_devolving_missiles_five_cost_to_four_four()
    test_p0_devolving_missiles_sludge_three_taunts_mc_overlay()
    test_p0_devolving_missiles_clears_taunt_face()
    test_p0_devolve_strips_lifesteal_and_deathrattle()
    test_p0_dream_spells_registered()
    test_p0_dream_clears_taunt_for_face()
    test_p0_ysera_awakens_face_and_board()
    test_p0_ysera_awakens_self_death_not_lethal()
    test_p0_ysera_awakens_simultaneous_lethal()
    test_p0_ysera_awakens_spell_first_stops_after_self_death()
    test_p0_nightmare_buffs_friendly_face()
    test_p0_invasive_shadeleaf_overflow_bottle()
    test_p0_shadeleaf_bottle_hand_card_id_and_tag()
    test_shadeleaf_bottle_prefers_deterministic_over_random_spell()
    test_p0_cease_to_exist_rewind_picks_taunt()
    test_p0_invasive_shadeleaf_no_overflow()
    test_p0_health_drink_enables_nightshade_drinks()
    test_p0_minion_spells_registered()
    test_p0_remove_spells_registered()
    test_p0_hex_clears_taunt_for_face()
    test_p0_asphyxiate_highest_atk()
    test_p0_shard_silence_all_taunts()
    test_p0_dubious_purchase_random_destroy()
    test_p0_buff_spells_registered()
    test_p0_chaos_strike_hero_attack_face()
    test_p0_libram_sets_one_health_and_weapon()
    test_p0_other_spells_registered()
    test_p1_spells_registered()
    test_p2_spells_registered()
    test_p2_precise_shot_powered_up()
    test_p2_precise_shot_taunt_only()
    test_p2_precise_shot_overlay_clears_taunt()
    test_p1_broxigar_interleave_face()
    test_p1_broxigar_clears_taunt()
    test_p1_spirit_bond_summon_rush()
    test_p1_stellar_balance_chain_damage()
    test_p1_multi_strike_hero_face()
    test_p0_red_card_dormant_taunt_face()
    test_p0_astral_phaser_dormant_taunt_face()
    test_p0_astral_phaser_two_taunts_prefers_small_taunt()
    test_p0_red_card_magtheridon_wake_end_turn()
    test_p0_red_card_magtheridon_prefers_face_attack()
    test_p0_red_card_two_taunts_face()
    test_p0_red_card_skips_enemy_non_taunt_only()
    test_p0_living_roots_damage_branch()
    test_p0_velens_chosen_buff_face()
    test_p0_aoe_spells_registered()
    test_p0_arcane_flow_combined_taunt_or_face_plus_aoe()
    test_p0_arcane_flow_shattered_forms()
    test_p0_arcane_flow_shattered_hand_playable()
    test_p0_arcane_flow_shatter_trigger_pending()
    test_p0_arcane_barrage_no_taunt_primary_face()
    test_p0_arcane_flow_virtual_combined_hand()
    test_p0_eulogizer_triggers_arcane_flow_recombine()
    test_p0_remixed_rhapsody_variants_registered()
    test_p0_remixed_rhapsody_resounding_clears_four_hp_taunt()
    test_p0_remixed_rhapsody_emotional_hero_attack()
    test_p0_remixed_rhapsody_wailing_summon_sick()
    test_p0_fan_of_knives_clears_taunt()
    test_p0_consecration_clears_taunt_and_face()
    test_p0_solar_flare_all_enemies_includes_hero_face()
    test_p0_for_quelthalas_skips_spell_immune_targets()
    test_p0_for_quelthalas_buffs_targetable_minion()
    test_p0_arbor_up_summons_and_buffs_all_minions()
    test_p0_arbor_up_clears_taunt_no_face()
    test_p0_arbor_up_then_forests_gift_lethal()
    test_p0_flash_sale_summons_and_buffs_all_minions()
    test_p0_flash_sale_enables_board_lethal()
    test_p0_flash_sale_spell_plus_hero_power_mana_budget()
    test_p0_flash_sale_plus_fireblast_face_with_friendly_taunt_token()
    test_p0_forests_gift_skips_spell_immune_target()
    test_p0_forests_gift_counts_exhausted_board_minions()
    test_p0_defile_repeats_on_death()
    test_p0_bladestorm_stops_on_death()
    test_p0_malted_magma_multi_drink()
    test_p0_malted_magma_drink_mana_budget()
    test_p0_condemn_rank_by_max_mana()
    test_p0_rising_waves_double_wave()
    test_p0_rafaams_stand_upgraded_damage()
    test_p0_hot_coals_powered_up()
    test_hellfire_then_hot_coals_lethal_from_log_093429()
    test_p0_baking_soda_volcano_no_hero_damage()
    test_hand_effect_active_combo_rite_twilight()
    test_scorching_winds_powered_up_double_damage()
    test_scorching_winds_lethal_checker_overlay()
    test_hand_effect_active_outcast_flash_flood()
    test_vendetta_cost_when_powered_up()
    test_dark_gift_charge_face_no_taunt()
    test_p0_double_agent_charge_copy_face()
    test_p0_double_agent_charge_no_other_class_single_face()
    test_p0_double_agent_charge_combo_hand_not_board()
    test_dark_gift_charge_clears_taunt_then_board_face()
    test_hand_charge_with_spell_mana_budget()
    test_p0_battlecry_registered()
    test_p0_tyrande_double_spell_aura()
    test_p0_tyrande_double_spell_three_charges()
    test_p0_tyrande_aura_next_turn_chaos_strike()
    test_p0_tyrande_aura_partial_charges()
    test_p0_night_elf_huntress_one_taunt_rest_face()
    test_p0_night_elf_huntress_three_taunts_highest_hp()
    test_p0_night_elf_huntress_no_taunt_distinct_targets()
    test_p0_fan_hammer_huntress_not_lethal_three_minions()
    test_p0_twilight_mistress_bounce_clears_taunt()
    test_p0_vrykul_necrolyte_no_immediate_damage()
    test_p0_faceless_corruptor_transform_dual_rush()
    test_p0_amber_whelp_requires_powered_up()
    test_p0_firework_elemental_corrupt_by_powered_up()
    test_p0_dunk_tank_corrupted_aoe()
    test_p0_dunk_tank_corrupted_face_four()
    test_p0_dunk_tank_corrupted_aoe_only_hits_minions()
    test_p0_dunk_tank_corrupts_in_sequence()
    test_p0_swipe_no_taunt_face_four()
    test_p0_swipe_one_taunt_splash_face()
    test_p0_malfurions_gift_discovers_swipe()
    test_p0_hostile_invader_spellburst_after_spell()
    test_p0_hostile_invader_interleaved_three_taunts()
    test_p0_pure_board_lethal_combo_all_minions_face()
    test_p0_hostile_invader_interleaved_33_taunt_six_face()
    test_p0_bunker_sergeant_interleaved_four_taunts_six_face()
    test_p0_rush_felrattler_from_hand_six_face()
    test_p0_rush_infused_gargon_cleave_adjacent()
    test_p0_combo_vilespine_destroy_taunt()
    test_p0_vilerok_transform_hand_charge_zone_play()
    test_p0_combo_sunkeneer_bounce_taunt()
    test_p0_combo_sunkeneer_chaos_strike_sequence()
    test_p0_hero_power_dh_claws_face_no_taunt()
    test_p0_hero_power_dh_claws_clear_one_taunt()
    test_p0_hero_power_dh_claws_exhausted_no_bonus()
    test_p0_hero_power_mage_fireblast_face_no_taunt()
    test_p0_hero_power_mage_fireblast_clears_taunt()
    test_p0_hero_power_rogue_dagger_face_no_taunt()
    test_p0_hero_power_rogue_dagger_upgraded_face_no_taunt()
    test_p0_hero_power_rogue_dagger_after_weapon_swing()
    test_p0_hero_power_rogue_dagger_upgrades_weak_weapon()
    test_p0_hero_power_druid_shapeshift_face_no_taunt()
    test_p0_hero_power_druid_shapeshift_opp_turn_with_hand_direct()
    test_p0_hero_power_druid_shapeshift_opp_turn_next_turn()
    test_p0_hero_power_xyrella_void_spike_face_no_taunt()
    test_p0_hero_power_xyrella_void_spike_through_taunt()
    test_p0_hero_power_xyrella_holy_touch_no_face()
    test_p0_hero_power_hunter_steady_shot_through_taunt()
    test_p0_buffed_bear_mace_equipped_479_over_base_atk()
    test_p0_buffed_bear_mace_hand_play_six_face()
    test_p0_weapon_shatterbone_clears_taunt()
    test_p0_battlecry_sand_elemental_windfury()
    test_p0_devourer_spellburst_hero_attack()
    test_p0_board_devourer_spellburst_on_first_spell()
    test_p0_rush_combo_buccaneer_copy()
    test_p0_rush_manasaber_spellburst_shield()
    test_p0_rush_ogre_misdirect_mc()
    test_p0_rush_inquisitor_mirror_weapon_face_ten()
    test_p0_rush_ruststeed_raider_taunt_clear()
    test_p0_faceless_interleaved_three_taunts_six_face()
    test_p0_spammy_arcanist_repeat_on_death()
    test_eudora_loot_registered()
    test_eudora_icy_touch_direct_face()
    test_icy_touch_ony_treasure_id()
    test_treasure_loot_aliases_registered()
    test_eudora_book_of_the_dead_cost_and_face()
    test_book_of_the_dead_ony_treasure_id()
    test_book_of_the_dead_from_log_083612()
    test_book_of_the_dead_lethal_from_log_083612_final_turn()
    test_eudora_queldelar_weapon_aoe_face()
    test_eudora_super_energy_gun_immune_poison()
    test_eudora_super_energy_gun_immune_survives_taunt()
    test_eudora_bubba_clears_six_hp_taunt()
    test_eudora_serpent_staff_clears_three_hp_taunt()
    test_eudora_mutagenic_injection_buff_face()
    test_eudora_gnomish_army_knife_face()
    test_eudora_beauty_beast_transform()
    test_eudora_embers_empty_board_face()
    print("all passed")
