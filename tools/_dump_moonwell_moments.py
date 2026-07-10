#!/usr/bin/env python3
"""列出该对局月亮井+龙息可打时，双方场面与解析身材。"""
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_24_12_01_30\Power.log"
)


def dump_moment(gs, ts, lineno):
    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    _, mn, _, sp, _ = lc.overlay_board_breakdown()
    _, _, has = lc.calculate_lethal_potential()
    _, _, hp = lc.get_opponent_health()
    local, opp = gs.local_player_id, gs.opponent_player_id
    print(f"\n=== {ts} line {lineno} | 对手{hp}血 | 场攻{face}(随{mn}+法{sp}) | 斩杀={has} ===")
    for label, pid in [("我方", local), ("对方", opp)]:
        print(f"  {label}:")
        for m in gs.get_board(pid):
            print(
                f"    {m.card_id} 攻{m.atk} 血{m.current_health}/{m.health}"
                f" dmg={m.tags.get('DAMAGE',0)}"
                f" tags479={m.tags.get('479')} tags3557={m.tags.get('3557')}"
                f" {'嘲' if m.tags.get('TAUNT') else ''}"
                f" {'冻' if m.tags.get('FROZEN') else ''}"
            )
    hand = gs.get_hand(local)
    rel = [c.card_id for c in hand if c.card_id in ("EDR_476", "CATA_464t", "RLK_915")]
    print(f"  相关手牌: {rel}")


def main():
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    start = next(
        i
        for i, l in enumerate(lines)
        if "15:08:29" in l
        and "爱吃土豆的刘苗苗#5475" in l
        and "MULLIGAN" in l
    )
    gs = GameState()
    parser = PowerLogParser(str(LOG), gs)
    key_times = {
        "15:21:30.0152512",
        "15:21:36.8876134",
        "15:21:42.1581709",
        "15:22:09.6972710",
        "15:22:28.1614003",
    }
    found = set()
    with contextlib.redirect_stdout(io.StringIO()):
        for lineno, line in enumerate(lines[start:], start=start):
            if not line.strip():
                continue
            parser.process_line(line.rstrip())
            if "DebugPrintOptions()" not in line:
                continue
            ts = line.split()[1] if line.startswith("D ") else ""
            if ts not in key_times or ts in found:
                continue
            found.add(ts)
            dump_moment(gs, ts, lineno)


if __name__ == "__main__":
    main()
