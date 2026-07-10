#!/usr/bin/env python3
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser


def scan_game(lines, start, end):
    gs = GameState()
    parser = PowerLogParser("", gs)
    hits = []
    with contextlib.redirect_stdout(io.StringIO()):
        for lineno in range(start, end):
            line = lines[lineno]
            if not line.strip():
                continue
            parser.process_line(line.rstrip())
            if "DebugPrintOptions()" not in line:
                continue
            local, opp = gs.local_player_id, gs.opponent_player_id
            if local is None or opp is None:
                continue
            p1 = gs.get_board(local)
            p2 = gs.get_board(opp)
            if len(p1) != 2 or len(p2) != 2:
                continue
            p1s = sorted((m.atk, m.current_health, m.card_id) for m in p1)
            p2s = sorted((m.atk, m.current_health, m.card_id, bool(m.tags.get("TAUNT"))) for m in p2)
            if p1s[0][0] == 3 and p1s[1][0] == 6:
                hits.append((lineno, line.split()[1], p1s, p2s))
    return hits


def main():
    log = Path(
        r"C:\Program Files (x86)\Hearthstone\Logs"
        r"\Hearthstone_2026_06_24_12_01_30\Power.log"
    )
    lines = log.read_text(encoding="utf-8", errors="ignore").splitlines()
    start = next(
        i
        for i, l in enumerate(lines)
        if "15:08:29" in l
        and "爱吃土豆的刘苗苗#5475" in l
        and "MULLIGAN" in l
    )
    hits = scan_game(lines, start, len(lines))
    print(f"2v2 with 6+3 atk friendly: {len(hits)}")
    for h in hits[:20]:
        print(h)


if __name__ == "__main__":
    main()
