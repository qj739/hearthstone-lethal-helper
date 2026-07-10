#!/usr/bin/env python3
"""昨晚 Logs 拆分 + 我方胜局详细表格（手牌/场攻/回合初斩杀/引擎判定）。"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyze_user_logs_lethal import (
    analyze_split_file,
    find_kill_turn_main_action,
    parse_to_line,
    scan_winner,
    split_power_logs,
)
from hdt_python.board_damage import build_player_board, entity_has_taunt
from hdt_python.lethal_checker import LethalChecker

LOGS_ROOT = Path(r"C:\Users\hp\Desktop\HS\Logs")
SPLIT_ROOT = LOGS_ROOT / "split_games"
CARDS = json.loads(
    (Path(__file__).resolve().parent.parent / "json" / "cards_zhCN.json").read_text(encoding="utf-8")
)
NAMES = {c["id"]: c.get("name", c["id"]) for c in CARDS if c.get("id")}


def fmt_hand(gs, pid) -> str:
    cards = gs.get_hand(pid)
    parts = []
    for c in sorted(cards, key=lambda x: x.tags.get("ZONE_POSITION", 0)):
        cid = c.card_id or "?"
        nm = NAMES.get(cid, cid)
        cost = c.tags.get("COST", c.cost)
        parts.append(f"{nm}({cost})")
    return "、".join(parts) if parts else "(空)"


def fmt_board(gs, pid) -> str:
    ms = gs.get_board(pid)
    if not ms:
        return "(空)"
    parts = []
    for m in sorted(ms, key=lambda x: x.tags.get("ZONE_POSITION", 0)):
        taunt = "嘲" if entity_has_taunt(m) else ""
        cid = m.card_id or "?"
        nm = NAMES.get(cid, cid)[:4]
        parts.append(f"{nm}{m.atk}/{m.current_health}{taunt}")
    return " ".join(parts)


def fmt_mana(gs, pid) -> str:
    h = gs.get_hero(pid)
    if not h:
        return "?"
    res = int(h.tags.get("RESOURCES", 0))
    used = int(h.tags.get("RESOURCES_USED", 0))
    return f"{res - used}/{res}"


def opp_effective(gs) -> str:
    lc = LethalChecker(gs)
    eff = lc.get_opponent_effective_hp()
    opp = gs.opponent_player_id
    h = gs.get_hero(opp) if opp else None
    if not h:
        return str(eff)
    hp = max(0, h.current_health - int(h.tags.get("DAMAGE", 0)))
    armor = int(h.tags.get("ARMOR", 0))
    return f"{eff}({hp}+{armor}甲)" if armor else str(eff)


def snapshot_at(lines, label, line_idx):
    gs = parse_to_line(lines, label, line_idx)
    if gs.local_player_id is None:
        return None
    lc = LethalChecker(gs)
    _, _, lethal = lc.calculate_lethal()
    overlay = lc.overlay_board_face_damage()
    prob = getattr(lc, "_overlay_lethal_prob", 0.0)
    note = lc.overlay_spell_note() or ""
    uses_random = getattr(lc, "_overlay_uses_random", False)
    top = getattr(lc, "_overlay_top_outcomes", [])
    pb = build_player_board(gs, gs.local_player_id, active_turn=True)
    minion_only = sum(c.attack for c in pb.cards if c.can_attack_hero)
    return {
        "overlay": overlay,
        "lethal": lethal,
        "prob": prob,
        "note": note,
        "uses_random": uses_random,
        "top": top,
        "minion_only": minion_only,
        "hand": fmt_hand(gs, gs.local_player_id),
        "board": fmt_board(gs, gs.local_player_id),
        "opp_board": fmt_board(gs, gs.opponent_player_id),
        "mana": fmt_mana(gs, gs.local_player_id),
        "opp_eff": opp_effective(gs),
    }


def fmt_overlay(snap) -> str:
    if snap["uses_random"] and snap["top"]:
        parts = [f"{d}({p*100:.0f}%)" for d, p in snap["top"][:2]]
        return " ".join(parts)
    return str(snap["overlay"])


def engine_ok(rep) -> str:
    j = rep.final_judge or rep.verdict or ""
    if j.startswith("✅"):
        return "正常"
    if j.startswith("❌"):
        return "漏算"
    if j.startswith("—"):
        return "投降未达斩"
    if j.startswith("⚠️"):
        return "待查"
    return j or "?"


def main():
    n = split_power_logs(LOGS_ROOT, SPLIT_ROOT)
    print(f"已拆分 {n} 场 -> {SPLIT_ROOT}\n")

    rows = []
    for path in sorted(SPLIT_ROOT.glob("*/game_*.log")):
        rep = analyze_split_file(path)
        if not rep.local_won:
            continue
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        label = f"{path.parent.name}/{path.name}"
        sess = path.parent.name.replace("Hearthstone_", "")
        turn_idx = None
        if rep.kill_turn_start is not None:
            # find_kill_turn_main_action returns line after MAIN_ACTION
            won_idx, _ = scan_winner(lines)
            before = len(lines)
            if won_idx is not None:
                from analyze_user_logs_lethal import find_kill_events

                gs_meta = parse_to_line(lines, label, len(lines))
                local, opp = gs_meta.local_player_id, gs_meta.opponent_player_id
                send_idx, kill_idx = find_kill_events(lines, local, opp, won_idx)
                before = send_idx or kill_idx or won_idx
            turn_idx = find_kill_turn_main_action(lines, rep.local_name, before)

        turn_snap = snapshot_at(lines, label, turn_idx) if turn_idx else None
        pre_snap = None
        if rep.pre_kill:
            # pre_kill snapshot line from analyze - re-parse at send_idx
            won_idx, _ = scan_winner(lines)
            if won_idx is not None:
                from analyze_user_logs_lethal import find_kill_events

                gs_meta = parse_to_line(lines, label, len(lines))
                send_idx, _ = find_kill_events(
                    lines, gs_meta.local_player_id, gs_meta.opponent_player_id, won_idx,
                )
                if send_idx is not None:
                    pre_snap = snapshot_at(lines, label, send_idx)

        rows.append({
            "sess": sess,
            "game": rep.game_index,
            "end": rep.end_type,
            "turn_snap": turn_snap,
            "pre_snap": pre_snap,
            "turn_lethal": rep.kill_turn_start.lethal if rep.kill_turn_start else None,
            "pre_lethal": rep.pre_kill.lethal if rep.pre_kill else None,
            "turn_overlay": rep.kill_turn_start.overlay if rep.kill_turn_start else None,
            "pre_overlay": rep.pre_kill.overlay if rep.pre_kill else None,
            "judge": rep.final_judge,
            "engine": engine_ok(rep),
            "note": (rep.note or "")[:40],
        })

    print(f"我方胜 **{len(rows)}** 局\n")
    print("| # | 会话 | 局 | 结束 | 手牌(回合初) | 我方场面 | 法力 | 对手血 | 场攻(回合初) | 回合初斩 | 场攻(斩杀前) | 斩杀前斩 | 引擎 | 判定 |")
    print("|---:|---|---:|---|---|---|---|---|---:|---|---:|---|---|---|")
    for i, r in enumerate(rows, 1):
        ts = r["turn_snap"] or {}
        ps = r["pre_snap"] or {}
        hand = ts.get("hand", "-")
        board = ts.get("board", "-")
        mana = ts.get("mana", "-")
        opp = ts.get("opp_eff", ps.get("opp_eff", "-"))
        ov_turn = fmt_overlay(ts) if ts else (str(r["turn_overlay"]) if r["turn_overlay"] is not None else "-")
        ov_pre = fmt_overlay(ps) if ps else (str(r["pre_overlay"]) if r["pre_overlay"] is not None else "-")
        lt = "Y" if r["turn_lethal"] else ("N" if r["turn_lethal"] is False else "-")
        lp = "Y" if r["pre_lethal"] else ("N" if r["pre_lethal"] is False else "-")
        print(
            f"| {i} | {r['sess'][-14:]} | {r['game']} | {r['end']} | {hand} | {board} | "
            f"{mana} | {opp} | {ov_turn} | {lt} | {ov_pre} | {lp} | {r['engine']} | {r['judge']} |"
        )

    ok = sum(1 for r in rows if r["engine"] == "正常")
    concede = sum(1 for r in rows if r["engine"] == "投降未达斩")
    miss = sum(1 for r in rows if r["engine"] == "漏算")
    warn = sum(1 for r in rows if r["engine"] == "待查")
    print(f"\n**汇总**：正常 {ok} | 投降未达斩 {concede} | 漏算 {miss} | 待查 {warn}")


if __name__ == "__main__":
    main()
