#!/usr/bin/env python3
"""演示斩杀步骤 Combo 窗口（game_04 七张法术用例）。"""
import contextlib
import io
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState, PowerLogParser
from overlay_win import ComboOverlay

LOG = ROOT / "Logs/split_games/Hearthstone_2026_06_09_21_22_05/game_04.log"
LINE = 28004
DISPLAY_SEC = 45


def load_state():
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines(True)
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(LINE):
            ln = lines[i].rstrip("\n\r")
            if ln:
                p.process_line(ln)
    return gs


def main():
    gs = load_state()
    lc = LethalChecker(gs)
    lc.overlay_board_face_damage()
    combo_lines = lc.overlay_combo_display_lines()
    if not combo_lines:
        print("未找到斩杀步骤")
        return 1

    text = "\n".join(combo_lines)
    print("斩杀步骤 Combo 窗口内容：")
    print(text)
    print()
    print(f"窗口将显示 {DISPLAY_SEC} 秒（深红底 + 金黄大字，置顶）…")

    overlay = ComboOverlay(title_hint="炉石传说", use_layered=False, opacity=245)
    if not overlay.start(wait_ready=8.0):
        print(f"窗口创建失败: {overlay._last_error}")
        return 1

    overlay.set_text(text, theme=ComboOverlay.THEME_COMBO_LETHAL)
    rect = None
    for _ in range(20):
        time.sleep(0.5)
        rect = overlay.window_rect()
        if rect and rect.get("visible"):
            break

    if rect:
        print(
            f"窗口已显示: left={rect['left']} top={rect['top']} "
            f"{rect['width']}x{rect['height']}"
        )
    else:
        print("窗口可能未可见，请检查是否被其他窗口遮挡")

    try:
        time.sleep(DISPLAY_SEC)
    except KeyboardInterrupt:
        pass
    finally:
        overlay.stop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
