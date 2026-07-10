#!/usr/bin/env python3
"""
斩杀 Combo 提示窗口演示 / 诊断脚本。

用法:
  python test_show_combo_overlay.py          # 内置斩杀场面 + 主 HUD + Combo 窗
  python test_show_combo_overlay.py --sample   # 仅硬编码文案（不跑斩杀计算）
  python test_show_combo_overlay.py --seconds 60

窗口会置顶显示约 45 秒，按 Ctrl+C 可提前关闭。
若炉石未开，窗口会出现在屏幕左上角附近（与 overlay_win 回退坐标一致）。
"""
from __future__ import annotations

import argparse
import contextlib
import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState, PowerLogParser
from overlay_win import ComboOverlay, Overlay

DISPLAY_SEC_DEFAULT = 45

# 可选：从本地 win 日志回放（有则优先）
_LOG_CANDIDATES = [
    (ROOT / "Logs/wins/Hearthstone_2026_06_10_00_09_22/game_04_win.log", None),
    (ROOT / "Logs/split_games/Hearthstone_2026_06_10_00_09_22/game_04.log", None),
    (ROOT / "Logs/split_games/Hearthstone_2026_06_09_19_01_18/game_04.log", None),
]

SAMPLE_COMBO_TEXT = """⚔ 斩杀步骤
（战吼穿插）
1. 战吼 凶恶的入侵者 → 全体
2. 地狱烈焰 → 敌方英雄
3. 阳炎耀斑 → 3/3·嘲讽"""

SAMPLE_HUD_TEXT = """场攻 6 (随6)
我 30+0  敌 6+0
⚔️ 斩杀 6≥6"""


def _hero(gs: GameState, eid: int, pid: int, *, mana: int = 10) -> None:
    h = gs.get_entity(eid)
    h.cardtype = "HERO"
    h.controller = pid
    h.health = 30
    h.tags["ARMOR"] = 0
    h.tags["RESOURCES"] = mana
    h.tags["RESOURCES_USED"] = 0
    gs.hero_entity_ids[pid] = eid


def _minion(
    gs: GameState,
    eid: int,
    pid: int,
    atk: int,
    hp: int,
    *,
    taunt: bool = False,
    card_id: str = "TEST",
):
    m = gs.get_entity(eid)
    m.cardtype = "MINION"
    m.controller = pid
    m.zone = "PLAY"
    m.card_id = card_id
    m.atk = atk
    m.health = hp
    m.damage = 0
    m.tags["ZONE"] = "PLAY"
    m.tags["NUM_ATTACKS_THIS_TURN"] = 0
    m.tags["EXHAUSTED"] = 0
    m.tags["NUM_TURNS_IN_PLAY"] = 1
    pos = len(gs.board_slots.setdefault(pid, {})) + 1
    m.tags["ZONE_POSITION"] = pos
    gs.board_slots[pid][pos] = eid
    if taunt:
        m.tags["TAUNT"] = 1
    return m


def _hand_minion(
    gs: GameState,
    eid: int,
    pid: int,
    atk: int,
    hp: int,
    cost: int,
    *,
    card_id: str = "GDB_226",
) -> None:
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


def build_builtin_lethal_state() -> tuple[GameState, LethalChecker]:
    """入侵者战吼穿插 + 6/6 打脸 6（与 test_spell_board 用例一致）。"""
    gs = GameState()
    gs.local_player_id = 1
    gs.opponent_player_id = 2
    gs.in_game = True
    gs.active_player_id = 1
    _hero(gs, 1, 1, mana=10)
    _hero(gs, 2, 2)
    gs.get_entity(2).health = 6  # 敌英雄 6 血，6 场攻可斩
    for eid, atk, hp in ((10, 6, 6), (11, 1, 1)):
        _minion(gs, eid, 1, atk, hp)
    for eid in (20, 21, 22):
        _minion(gs, eid, 2, 2, 2, taunt=True)
    _minion(gs, 23, 2, 3, 3, taunt=True)
    _hand_minion(gs, 30, 1, 5, 5, 5, card_id="GDB_226")
    lc = LethalChecker(gs)
    return gs, lc


def try_load_from_log() -> tuple[GameState, LethalChecker] | None:
    for log_path, max_line in _LOG_CANDIDATES:
        if not log_path.is_file():
            continue
        lines = log_path.read_text(encoding="utf-8", errors="ignore").splitlines(True)
        gs = GameState()
        p = PowerLogParser(str(log_path), gs)
        end = max_line if max_line is not None else len(lines)
        with contextlib.redirect_stdout(io.StringIO()):
            for i in range(end):
                ln = lines[i].rstrip("\n\r")
                if ln:
                    p.process_line(ln)
        if gs.local_player_id is None:
            continue
        lc = LethalChecker(gs)
        return gs, lc
    return None


def _calc_overlay_text(gs: GameState, lc: LethalChecker) -> tuple[str, str, list, bool]:
    total, _, has_lethal = lc.calculate_lethal_potential()
    combo_lines = lc.overlay_combo_display_lines()
    opp_h, opp_a, _ = lc.get_opponent_health()
    my_h, my_a, _ = lc.get_my_health()
    board_atk = lc.overlay_board_face_damage()
    opp_total = lc.get_opponent_effective_hp()
    if has_lethal:
        lethal_line = f"⚔️ 斩杀 {total}≥{opp_total}"
        hud_theme = Overlay.THEME_MY_LETHAL
    else:
        lethal_line = f"{total}/{opp_total} 差{opp_total - total}"
        hud_theme = Overlay.THEME_NORMAL
    hud_text = "\n".join([
        f"场攻 {board_atk}",
        f"我 {my_h}+{my_a}  敌 {opp_h}+{opp_a}",
        lethal_line,
    ])
    return hud_text, hud_theme, combo_lines, has_lethal


def resolve_combo_text(*, use_sample_only: bool) -> tuple[str, str, dict]:
    """返回 (hud_text, combo_text, diagnostics)。"""
    diag: dict = {}

    if use_sample_only:
        return SAMPLE_HUD_TEXT, SAMPLE_COMBO_TEXT, {"mode": "hardcoded_sample"}

    gs, lc = build_builtin_lethal_state()
    diag["mode"] = "builtin_mock"
    hud_text, hud_theme, combo_lines, has_lethal = _calc_overlay_text(gs, lc)

    loaded = try_load_from_log()
    if loaded:
        gs_log, lc_log = loaded
        hud_log, theme_log, combo_log, lethal_log = _calc_overlay_text(gs_log, lc_log)
        if lethal_log and combo_log:
            gs, lc = gs_log, lc_log
            hud_text, hud_theme, combo_lines, has_lethal = hud_log, theme_log, combo_log, lethal_log
            diag["mode"] = "log_replay"
            diag["local_player"] = gs.local_player_id
        else:
            diag["log_skipped"] = "日志末态无斩杀步骤，改用内置场面"

    total, _, _ = lc.calculate_lethal_potential()
    diag["has_lethal"] = has_lethal
    diag["total_damage"] = total
    diag["combo_line_count"] = len(combo_lines)
    diag["is_opp_turn"] = lc.is_opponent_turn()
    diag["timed_out"] = lc.lethal_calc_timed_out()

    if not combo_lines:
        diag["fallback"] = "overlay_combo_display_lines 为空，改用硬编码示例文案"
        combo_text = SAMPLE_COMBO_TEXT
        hud_text = SAMPLE_HUD_TEXT
        hud_theme = Overlay.THEME_MY_LETHAL
    else:
        combo_text = "\n".join(combo_lines)

    diag["hud_theme"] = hud_theme
    return hud_text, combo_text, diag


def _safe_print(text: str) -> None:
    """Windows 控制台 GBK 下避免 UnicodeEncodeError。"""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        print(text)
    except UnicodeEncodeError:
        print(text.encode(enc, errors="replace").decode(enc, errors="replace"))


def print_diagnostics(diag: dict) -> None:
    print("=" * 60)
    print("斩杀 Combo 窗口 — 诊断信息")
    print("=" * 60)
    for k, v in diag.items():
        print(f"  {k}: {v}")
    print()
    print("实盘中 Combo 窗不出现的常见原因：")
    print("  1. 对方回合 (is_opp_turn=True) — tracker 故意不显示 Combo")
    print("  2. overlay_combo_display_lines() 为空 — 纯随从斩无步骤文案")
    print("  3. 主 HUD 启动失败 — hdt_tracker 会把 combo_overlay 置 None")
    print("  4. combo_overlay.start() 失败但未检查返回值")
    print("  5. 用了 --no-overlay")
    print("=" * 60)
    print()


def show_windows(hud_text: str, combo_text: str, *, hud_theme: str, seconds: int) -> int:
    _safe_print("Combo 窗口内容预览：")
    print("-" * 40)
    _safe_print(combo_text)
    print("-" * 40)
    print(f"\n正在创建主 HUD + Combo 窗口，显示 {seconds} 秒…")
    print("（若炉石未运行，窗口在屏幕左上角；有炉石则贴在游戏窗口上）\n")

    main = Overlay(title_hint="炉石传说", use_layered=False, opacity=220)
    combo = ComboOverlay(
        title_hint="炉石传说",
        use_layered=False,
        opacity=245,
        anchor_overlay=main,
    )

    if not main.start(wait_ready=8.0):
        print(f"主 HUD 创建失败: {main._last_error}")
        return 1
    if not combo.start(wait_ready=8.0):
        print(f"Combo 窗口创建失败: {combo._last_error}")
        main.stop()
        return 1

    main.set_text(hud_text, theme=hud_theme)
    combo.set_text(combo_text, theme=ComboOverlay.THEME_COMBO_LETHAL)

    for i in range(20):
        time.sleep(0.25)
        rect = combo.window_rect()
        if rect and rect.get("visible"):
            print(
                f"Combo 窗口已可见: ({rect['left']}, {rect['top']}) "
                f"{rect['width']}x{rect['height']} topmost={rect.get('topmost')}"
            )
            break
    else:
        print("警告: Combo 窗口可能未可见，请检查是否被全屏游戏或其它置顶窗遮挡")

    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        print("\n用户中断")
    finally:
        combo.stop()
        main.stop()
    print("窗口已关闭。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="演示斩杀 Combo 提示窗口")
    parser.add_argument(
        "--sample",
        action="store_true",
        help="跳过斩杀计算，仅用硬编码示例文案",
    )
    parser.add_argument(
        "--seconds",
        type=int,
        default=DISPLAY_SEC_DEFAULT,
        help=f"窗口显示秒数（默认 {DISPLAY_SEC_DEFAULT}）",
    )
    args = parser.parse_args()

    hud_text, combo_text, diag = resolve_combo_text(use_sample_only=args.sample)
    print_diagnostics(diag)
    hud_theme = diag.get("hud_theme", Overlay.THEME_MY_LETHAL)
    return show_windows(hud_text, combo_text, hud_theme=hud_theme, seconds=args.seconds)


if __name__ == "__main__":
    raise SystemExit(main())
