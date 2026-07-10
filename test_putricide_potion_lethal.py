#!/usr/bin/env python3
"""普崔塞德调配药剂 + 场面攻击应识别斩杀（最后一局回归）。"""

import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from test_spell_board import _hero, _minion, _hand_spell, _weapon
from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker


def test_putricide_potion_plus_board_lethal_synthetic():
    """场攻 8 + 3 伤调好的药剂，对手 10 血应提示斩杀。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    gs.player_ids[1] = 1
    gs.player_ids[2] = 2
    _hero(gs, 1, 1, mana=10, used=3)
    opp = _hero(gs, 2, 2)
    opp.health = 10
    opp.tags["HEALTH"] = 10
    _minion(gs, 10, 1, 1, 4, card_id="RLK_572")
    _minion(gs, 11, 1, 2, 1, card_id="ETC_209")
    _minion(gs, 12, 1, 3, 3, card_id="WW_364")
    _minion(gs, 13, 1, 1, 1, card_id="CATA_780t")
    _weapon(gs, 14, 1, "CS2_082", durability=2)
    _hand_spell(gs, 30, 1, "RLK_570t1t3", 3)
    _minion(gs, 20, 2, 3, 2, card_id="RLK_845")

    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    total, _, has_lethal = lc.calculate_lethal_potential()
    assert lc._available_mana(1) == 7
    assert lc.get_opponent_effective_hp() == 10
    assert lc.cached_overlay_face() >= 10, f"expected overlay>=10, got {lc.cached_overlay_face()}"
    assert has_lethal is True, f"board+potion lethal missed, total={total}"


def test_putricide_potion_lethal_from_power_log():
    """回放最后一局斩杀回合起点（Power.log L61400）。"""
    log = Path(r"C:\Program Files (x86)\Hearthstone\Logs\Hearthstone_2026_06_27_00_01_42\Power.log")
    if not log.exists():
        return
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    starts = [
        i for i, l in enumerate(lines)
        if "CREATE_GAME" in l and "GameState.DebugPrintPower" in l
    ]
    start = starts[0]
    for s in starts:
        if s >= 61400:
            break
        start = s
    gs = GameState()
    p = PowerLogParser(str(log), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(start, 61400):
            p.process_line(lines[i])
    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    _, _, has_lethal = lc.calculate_lethal_potential()
    assert lc.get_opponent_effective_hp() == 10
    assert has_lethal is True, f"log replay lethal missed, overlay={lc.cached_overlay_face()}"


def test_all_concoction_damage_tokens_registered():
    """RLK_570 所有含 3 伤/消灭的调配药剂均应注册进斩杀模拟。"""
    from hdt_python.spell_board import get_board_spell_def
    from hdt_python.spell_p0_concoction import _concoction_handler_from_text
    import json
    from pathlib import Path

    data = json.loads(Path("json/cards.json").read_text(encoding="utf-8"))
    for card in data:
        cid = card.get("id") or ""
        if not cid.startswith("RLK_570t") or card.get("type") != "SPELL":
            continue
        if _concoction_handler_from_text(card.get("text") or "") is None:
            continue
        assert get_board_spell_def(cid) is not None, f"missing spell def for {cid}"


if __name__ == "__main__":
    test_putricide_potion_plus_board_lethal_synthetic()
    test_putricide_potion_lethal_from_power_log()
    test_all_concoction_damage_tokens_registered()
    print("all passed")
