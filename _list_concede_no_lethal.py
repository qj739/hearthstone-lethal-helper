#!/usr/bin/env python3
"""列出：我方胜 + 对手投降 + 引擎未判斩杀 的对局，附手牌/场攻。"""
from __future__ import annotations

import contextlib
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from analyze_user_logs_lethal import (
    analyze_split_file,
    opponent_conceded,
    parse_to_line,
    scan_winner,
    find_kill_events,
    find_kill_turn_main_action,
    lethal_snapshot,
)
from verify_all_power_logs import discover_split_games, local_battletag
from hdt_python.board_damage import entity_has_taunt
from hdt_python.lethal_checker import LethalChecker

CARDS_ZH = Path(__file__).parent / "json" / "cards_zhCN.json"


def load_card_names() -> dict:
    if not CARDS_ZH.is_file():
        return {}
    data = json.loads(CARDS_ZH.read_text(encoding="utf-8"))
    if isinstance(data, list):
        return {c.get("id", ""): c.get("name", c.get("id", "")) for c in data if c.get("id")}
    return {cid: info.get("name", cid) for cid, info in data.items()}


def fmt_hand(gs, pid, names: dict) -> str:
    cards = gs.get_hand(pid)
    parts = []
    for c in sorted(cards, key=lambda x: x.tags.get("ZONE_POSITION", 0)):
        cid = c.card_id or "?"
        nm = names.get(cid, cid)
        cost = c.tags.get("COST", c.cost)
        parts.append(f"{nm}({cost}费)")
    return " | ".join(parts) if parts else "(空)"


def fmt_board(gs, pid) -> str:
    ms = gs.get_board(pid)
    if not ms:
        return "(空)"
    parts = []
    for m in sorted(ms, key=lambda x: x.tags.get("ZONE_POSITION", 0)):
        taunt = "嘲" if entity_has_taunt(m) else ""
        cid = m.card_id or "?"
        parts.append(f"{cid} {m.atk}/{m.current_health}{taunt}")
    return " ".join(parts)


def fmt_opp_hero(gs, opp_pid) -> str:
    h = gs.get_hero(opp_pid)
    if not h:
        return "?"
    hp = h.current_health
    armor = h.tags.get("ARMOR", 0)
    return f"{hp}血+{armor}甲" if armor else f"{hp}血"


def fmt_mana(gs, pid) -> str:
    h = gs.get_hero(pid)
    if not h:
        return "?"
    res = h.tags.get("RESOURCES", 0)
    used = h.tags.get("RESOURCES_USED", 0)
    return f"{res - used}/{res}"


def snapshot_detail(gs, names: dict) -> dict:
    lc = LethalChecker(gs)
    snap = lethal_snapshot(gs)
    pure, board, weapon, spell, _ = lc.overlay_board_breakdown()
    max_f, prob, rnd, top = lc.overlay_face_stats()
    local = gs.local_player_id
    opp = gs.opponent_player_id
    return {
        "overlay": snap.overlay,
        "lethal": snap.lethal,
        "opp_hp": snap.opp_hp,
        "prob": snap.prob,
        "note": snap.note,
        "breakdown": f"纯{pure}+随{board}+武{weapon}+法{spell}",
        "max_face": max_f,
        "random": rnd,
        "top": top,
        "mana": fmt_mana(gs, local) if local else "?",
        "opp_hero": fmt_opp_hero(gs, opp) if opp else "?",
        "my_board": fmt_board(gs, local) if local else "?",
        "opp_board": fmt_board(gs, opp) if opp else "?",
        "hand": fmt_hand(gs, local, names) if local else "?",
    }


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--split-root",
        action="append",
        default=[],
        help="可多次指定；默认 HS_new/Logs/split_games + LOGS(1)/split_games",
    )
    args = ap.parse_args()
    roots = [Path(p) for p in args.split_root] if args.split_root else [
        Path(__file__).parent / "Logs" / "split_games",
        Path(r"C:\Users\hp\Desktop\LOGS(1)\LOGS\split_games"),
    ]
    files = []
    seen = set()
    for split_root in roots:
        if not split_root.is_dir():
            continue
        for p in sorted(split_root.glob("*/game_*.log")):
            key = (p.parent.name, p.name)
            if key in seen:
                continue
            seen.add(key)
            files.append(p)
    hits = []

    names = load_card_names()
    for path in files:
        rep = analyze_split_file(path)
        if not rep.local_won:
            continue
        if rep.end_type != "对手投降":
            continue

        ts = rep.kill_turn_start
        pk = rep.pre_kill
        turn_miss = ts is not None and not ts.lethal
        pre_miss = pk is not None and not pk.lethal
        if not turn_miss and not pre_miss:
            continue
        if ts is None and pk is None:
            continue

        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
        won_line, _ = scan_winner(lines)
        label = f"{path.parent.name}/{path.name}"
        gs_meta = parse_to_line(lines, label, (won_line or 0) + 1)
        local = gs_meta.local_player_id
        opp = gs_meta.opponent_player_id
        send_idx, kill_idx = find_kill_events(lines, local, opp, won_line or 0)
        before = send_idx or kill_idx or won_line or 0
        turn_idx = find_kill_turn_main_action(
            lines, rep.local_name or local_battletag(gs_meta), before,
        )

        turn_detail = None
        pre_detail = None
        if turn_idx is not None:
            turn_detail = snapshot_detail(parse_to_line(lines, label, turn_idx), names)
        if send_idx is not None:
            pre_detail = snapshot_detail(parse_to_line(lines, label, send_idx), names)

        hits.append({
            "session": path.parent.name.replace("Hearthstone_", ""),
            "game": rep.game_index,
            "path": str(path),
            "turn_line": (turn_idx + 1) if turn_idx is not None else None,
            "turn_detail": turn_detail,
            "pre_detail": pre_detail,
        })

    print(f"共扫描 {len(files)} 场，命中「胜+投降+未判斩」{len(hits)} 场\n")
    for i, h in enumerate(hits, 1):
        print("=" * 72)
        print(f"{i}. {h['session']} / game_{h['game']:02d}  (回合初 line {h['turn_line']})")
        if h["turn_detail"]:
            t = h["turn_detail"]
            print(f"   【回合初】场攻 {t['overlay']} / 对手有效血 {t['opp_hp']} / lethal={t['lethal']}")
            print(f"            {t['breakdown']}  法力 {t['mana']}")
            print(f"            对手 {t['opp_hero']}  对手场 {t['opp_board']}")
            print(f"            我方场 {t['my_board']}")
            print(f"            手牌 {t['hand']}")
            if t["note"]:
                print(f"            线路 {t['note']}")
            if t["random"] and t["top"]:
                print(f"            随机档 {t['top']}")
        if h["pre_detail"]:
            p = h["pre_detail"]
            print(f"   【动手前】场攻 {p['overlay']} / 对手有效血 {p['opp_hp']} / lethal={p['lethal']}")
            print(f"            手牌 {p['hand']}")
            if p["note"]:
                print(f"            线路 {p['note']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
