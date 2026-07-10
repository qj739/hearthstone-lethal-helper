#!/usr/bin/env python3
"""Check if opponent conceded due to empty hand/deck (games >= N)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyze_user_logs_lethal import (
    is_local_winner,
    local_battletag,
    opponent_conceded,
    parse_to_line,
    scan_winner,
)

LOG_DIR = Path(r"c:\Users\hp\Desktop\LOGS(1)\LOGS\split_games\Hearthstone_2026_06_15_20_33_51")
CARDS = json.loads(
    (Path(__file__).resolve().parent.parent / "json" / "cards_zhCN.json").read_text(encoding="utf-8")
)
NAMES = {c["id"]: c.get("name", c["id"]) for c in CARDS if c.get("id")}


def opp_state(lines: list[str], line_idx: int, opp_pid: int | None, label: str):
    gs = parse_to_line(lines, label, line_idx + 1)
    if not gs or opp_pid is None:
        return None
    hand = gs.get_hand(opp_pid)
    deck_n = sum(
        1
        for e in gs.entities.values()
        if e.tags.get("CONTROLLER") == opp_pid and e.tags.get("ZONE") == "DECK"
    )
    hero = gs.get_hero(opp_pid)
    hp = hero.current_health if hero else None
    armor = int(hero.tags.get("ARMOR", 0)) if hero else 0
    fatigue = 0
    opp_name = gs.player_names.get(opp_pid, "")
    for e in gs.entities.values():
        nm = getattr(e, "name", "") or ""
        if opp_name and opp_name in nm:
            fatigue = int(e.tags.get("FATIGUE", 0) or 0)
            break
    hand_str = []
    for c in sorted(hand, key=lambda x: x.tags.get("ZONE_POSITION", 0)):
        cid = c.card_id or "?"
        cost = c.tags.get("COST", c.cost)
        hand_str.append(f"{NAMES.get(cid, cid)}({cost})")
    return {
        "hand_n": len(hand),
        "deck_n": deck_n,
        "hand": hand_str,
        "hp": hp,
        "armor": armor,
        "fatigue": fatigue,
    }


def empty_verdict(st: dict | None) -> str:
    if not st:
        return "未知"
    if st["hand_n"] == 0 and st["deck_n"] == 0:
        return "是（手牌+牌库皆空）"
    if st["deck_n"] == 0 and st["fatigue"] > 0:
        return f"否（牌库已空、疲劳{st['fatigue']}，但手牌{st['hand_n']}张）"
    if st["deck_n"] == 0:
        return f"否（牌库空，手牌{st['hand_n']}张）"
    return f"否（手牌{st['hand_n']}张，牌库{st['deck_n']}张）"


def analyze(path: Path) -> dict:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    label = path.name
    gs0 = parse_to_line(lines, label, len(lines))
    if not gs0:
        return {"file": path.name, "error": "parse fail"}
    local = local_battletag(gs0)
    won_idx, winner = scan_winner(lines)
    local_won = is_local_winner(local, winner)
    opp_pid = gs0.opponent_player_id
    opp_name = (gs0.player_names.get(opp_pid) or "?").split("#")[0]

    out: dict = {
        "file": path.name,
        "opponent": opp_name,
        "我方": "胜" if local_won else ("负" if winner else "未完成"),
    }

    if won_idx is None:
        st = opp_state(lines, len(lines) - 1, opp_pid, label)
        out["结束方式"] = "日志中断（对局未打完）"
        if st:
            out["对手当前"] = f"手牌{st['hand_n']} 牌库{st['deck_n']} {st['hp']}血"
        return out

    conceded = opponent_conceded(lines, won_idx, winner)
    st = opp_state(lines, won_idx, opp_pid, label)
    if local_won and conceded:
        out["结束方式"] = "对手投降"
    elif local_won:
        out["结束方式"] = "正常击杀/胜利"
    else:
        out["结束方式"] = "我方被击杀" if winner else "未知"

    if st:
        hp_s = f"{st['hp']}血+{st['armor']}甲" if st["armor"] else f"{st['hp']}血"
        out["对手结束时"] = f"{hp_s}，手牌{st['hand_n']}，牌库{st['deck_n']}，疲劳{st['fatigue']}"
        if st["hand"]:
            out["对手手牌"] = " | ".join(st["hand"])
    if conceded:
        out["是否没牌投降"] = empty_verdict(st)
        # fatigue events for opponent near end
        fat = sum(
            1
            for i in range(max(0, won_idx - 800), won_idx + 1)
            if "BlockType=FATIGUE" in lines[i] and f"player={opp_pid}" in lines[i]
        )
        out["结束前对手疲劳次数"] = fat
    return out


def main():
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 8
    for n in range(start, 11):
        p = LOG_DIR / f"game_{n:02d}.log"
        if not p.exists():
            continue
        r = analyze(p)
        print("=" * 56)
        for k, v in r.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
