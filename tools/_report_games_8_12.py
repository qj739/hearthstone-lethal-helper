#!/usr/bin/env python3
"""Detailed report for arena games 8-12 (06_15 run)."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyze_user_logs_lethal import (
    analyze_split_file,
    find_kill_turn_main_action,
    is_local_winner,
    lethal_snapshot,
    local_battletag,
    opponent_conceded,
    parse_to_line,
    scan_winner,
)
from hdt_python.board_damage import build_player_board, entity_has_taunt
from hdt_python.lethal_checker import LethalChecker

CARDS = json.loads(
    (Path(__file__).resolve().parent.parent / "json" / "cards_zhCN.json").read_text(encoding="utf-8")
)
NAMES = {c["id"]: c.get("name", c["id"]) for c in CARDS if c.get("id")}

SESSION_A = Path(
    r"c:\Users\hp\Desktop\LOGS(1)\LOGS\split_games\Hearthstone_2026_06_15_20_33_51"
)
SESSION_B = Path(
    r"c:\Users\hp\Desktop\LOGS(1)\LOGS\split_games\Hearthstone_2026_06_15_23_18_06"
)

# Arena game number -> (session, split index, note)
ARENA_MAP = [
    (8, SESSION_A, 8, "20_33 日志"),
    (9, SESSION_A, 9, "20_33 日志"),
    (10, SESSION_A, 10, "20_33 日志（此文件在 23:17 截断，可能未完）"),
    (11, SESSION_B, 1, "23_18 续日志（竞技第11局）"),
    (12, SESSION_B, 2, "23_18 续日志（竞技第12局）"),
]


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
        nm = NAMES.get(cid, cid)
        parts.append(f"{nm}{m.atk}/{m.current_health}{taunt}")
    return " ".join(parts)


def fmt_mana(gs, pid) -> str:
    h = gs.get_hero(pid)
    if not h:
        return "?"
    res = int(h.tags.get("RESOURCES", 0))
    used = int(h.tags.get("RESOURCES_USED", 0))
    return f"{res - used}/{res}"


def board_face(gs) -> int:
    lc = LethalChecker(gs)
    return lc.overlay_board_face_damage()


def snapshot_at_line(lines, label, line_idx, gs_ref=None):
    gs = parse_to_line(lines, label, line_idx + 1)
    if gs.local_player_id is None:
        return None
    snap = lethal_snapshot(gs)
    pb = build_player_board(gs, gs.local_player_id, active_turn=True)
    minion_face = sum(c.attack for c in pb.cards if c.can_attack_hero)
    return {
        "gs": gs,
        "overlay": snap.overlay,
        "lethal": snap.lethal,
        "opp_eff": snap.opp_hp,
        "spell_note": snap.note,
        "board_face": minion_face,
        "hand": fmt_hand(gs, gs.local_player_id),
        "board": fmt_board(gs, gs.local_player_id),
        "opp_board": fmt_board(gs, gs.opponent_player_id),
        "mana": fmt_mana(gs, gs.local_player_id),
        "opp_hero": fmt_opp_hero(gs, gs.opponent_player_id),
    }


def fmt_opp_hero(gs, pid) -> str:
    h = gs.get_hero(pid)
    if not h:
        return "?"
    hp = h.current_health
    armor = int(h.tags.get("ARMOR", 0))
    dmg = int(h.tags.get("DAMAGE", 0))
    eff = max(0, hp - dmg) + armor
    if armor:
        return f"{eff}有效({hp - dmg}血+{armor}甲)"
    return f"{eff}有效({hp - dmg}血)"


def hand_from_concede_log(lines, won_idx, opp_pid):
    """Parse opponent hand from raw concede wrap-up lines (player=1)."""
    cards = []
    for i in range(max(0, won_idx - 5), min(len(lines), won_idx + 15)):
        m = re.search(
            r"entityName=([^\]]+) id=\d+ zone=HAND zonePos=\d+ cardId=(\S+) player="
            + str(opp_pid),
            lines[i],
        )
        if m and "NUM_TURNS_IN_HAND" in lines[i]:
            cards.append(f"{m.group(1)}/{NAMES.get(m.group(2), m.group(2))}")
    return "、".join(cards) if cards else None


def last_local_play(lines, won_idx, local_pid):
    """Find last card played by local before win/concede."""
    plays = []
    for i in range(max(0, won_idx - 3000), won_idx):
        m = re.search(
            r"BLOCK_START BlockType=PLAY Entity=\[entityName=([^\]]+) id=\d+ zone=HAND zonePos=\d+ cardId=(\S+) player="
            + str(local_pid),
            lines[i],
        )
        if m:
            plays.append(NAMES.get(m.group(2), m.group(2)))
    return plays[-1] if plays else None


def analyze_mapped(arena_n, session, split_idx, sess_note):
    path = session / f"game_{split_idx:02d}.log"
    if not path.is_file():
        return {"arena": arena_n, "error": f"文件不存在: {path}"}

    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    label = path.name
    report = analyze_split_file(path)
    won_idx, winner = scan_winner(lines)
    gs0 = parse_to_line(lines, label, len(lines))
    local = local_battletag(gs0)
    local_pid = gs0.local_player_id
    opp_pid = gs0.opponent_player_id
    opp_name = (gs0.player_names.get(opp_pid) or "?").split("#")[0]

    out = {
        "arena": arena_n,
        "file": f"{session.name}/{path.name}",
        "note": sess_note,
        "opponent": opp_name,
        "result": "胜" if report.local_won else ("负" if winner and not report.local_won else "未完成"),
        "end_type": report.end_type or report.final_judge,
    }

    if won_idx is None:
        out["reason"] = "日志无胜负记录（可能对局未录完）"
        ma = find_kill_turn_main_action(lines, local, len(lines))
        if ma:
            st = snapshot_at_line(lines, label, ma)
            if st:
                out["turn_start"] = pack_snap(st)
        return out

    conceded = opponent_conceded(lines, won_idx, winner)
    send_idx = None
    if report.local_won and gs0.opponent_player_id:
        from analyze_user_logs_lethal import find_kill_events

        send_idx, _ = find_kill_events(
            lines, local_pid, gs0.opponent_player_id, won_idx
        )
    before = send_idx or won_idx
    ma_line = find_kill_turn_main_action(lines, local, before)

    # Snapshot at kill/concede turn MAIN_ACTION (your visible overlay moment)
    turn_snap = None
    if ma_line is not None:
        turn_snap = snapshot_at_line(lines, label, ma_line)

    pre_snap = None
    if report.pre_kill and hasattr(report, "split_path"):
        pass
    # use analyze report snapshots if available
    if report.kill_turn_start:
        out["engine_turn_overlay"] = report.kill_turn_start.overlay
        out["engine_turn_lethal"] = report.kill_turn_start.lethal
        out["engine_turn_opp"] = report.kill_turn_start.opp_hp

    if turn_snap:
        out["turn_start"] = pack_snap(turn_snap)

    # State just before opponent conceded (scan back for last MAIN_ACTION on local turn before concede)
    pre_concede = None
    for i in range(won_idx, max(0, won_idx - 5000), -1):
        if "STEP value=MAIN_ACTION" in lines[i]:
            st = snapshot_at_line(lines, label, i)
            if st and st["gs"].local_player_id:
                pre_concede = st
                break
    if pre_concede:
        out["before_concede_or_kill"] = pack_snap(pre_concede)

    out["last_played"] = last_local_play(lines, won_idx, local_pid)
    oh = hand_from_concede_log(lines, won_idx, opp_pid)
    if oh:
        out["opp_hand_at_concede_log"] = oh

    if conceded:
        out["why_concede"] = infer_concede_reason(out, turn_snap, conceded)
    elif not report.local_won:
        out["why_concede"] = "你被斩杀，非对手投降"
        # 致命回合：找斩杀前最后一个我方回合初
        for i in range(won_idx, max(0, won_idx - 8000), -1):
            if f"player={local_pid}" in lines[i] and "HERO_" in lines[i] and "ZONE value=GRAVEYARD" in lines[i]:
                ma_death = find_kill_turn_main_action(lines, local, i)
                if ma_death is not None:
                    st = snapshot_at_line(lines, label, ma_death)
                    if st:
                        out["turn_start"] = pack_snap(st)
                break
    else:
        out["why_concede"] = "正常击杀胜利（非投降）"

    return out


def pack_snap(st):
    return {
        "mana": st["mana"],
        "overlay场攻": st["overlay"],
        "场面可打脸": st["board_face"],
        "对手有效血": st["opp_eff"],
        "引擎斩杀": st["lethal"],
        "手牌": st["hand"],
        "场面": st["board"],
        "对手场面": st["opp_board"],
        "对手血线": st["opp_hero"],
        "法术备注": st["spell_note"] or "",
    }


def infer_concede_reason(out, turn_snap, conceded):
    ts = out.get("turn_start") or {}
    bc = out.get("before_concede_or_kill") or {}
    ov = ts.get("overlay场攻", 0)
    opp = ts.get("对手有效血", 0)
    if turn_snap and turn_snap["lethal"]:
        return f"回合初已判斩杀（场攻+法术≥{opp}血）"
    if ov >= opp and opp > 0:
        return f"回合初场攻/overlay({ov})已≥对手有效血({opp})，压力极大"
    if ov >= opp - 3 and opp <= 10:
        return f"回合初overlay {ov}，对手仅{opp}有效血，下回合几乎必死"
    last = out.get("last_played")
    if last:
        return f"非空投降；回合初overlay={ov} 对手={opp}血；你末手打出「{last}」后对手认输（可能场面/下回合伤害）"
    return f"非没牌投降；回合初overlay={ov} 对手有效血={opp}"


def main():
    results = []
    for arena_n, session, split_idx, note in ARENA_MAP:
        results.append(analyze_mapped(arena_n, session, split_idx, note))

    print("=" * 70)
    print("06_15 竞技 第8-12局 详细整理（繁忙的雄鹿#59725）")
    print("说明：第8局之前（如第4-7局）才有「对手投降且引擎未判斩」；第8局是你被斩杀。")
    print("=" * 70)
    for r in results:
        print()
        print(f"【竞技第 {r['arena']} 局】 {r.get('file','?')}")
        if "error" in r:
            print(f"  错误: {r['error']}")
            continue
        print(f"  对手: {r.get('opponent')} | 结果: {r.get('result')} | 结束: {r.get('end_type')}")
        if r.get("note"):
            print(f"  日志: {r['note']}")
        if ts := r.get("turn_start"):
            print("  --- 关键回合开始（你方视角 overlay 时刻）---")
            print(f"  法力: {ts['mana']} | overlay场攻: {ts['overlay场攻']} | 场面打脸: {ts['场面可打脸']}")
            print(f"  对手: {ts['对手血线']} | 引擎斩杀: {ts['引擎斩杀']}")
            print(f"  手牌: {ts['手牌']}")
            print(f"  场面: {ts['场面']}")
            print(f"  对手场面: {ts['对手场面']}")
            if ts.get("法术备注"):
                print(f"  法术: {ts['法术备注']}")
        if bc := r.get("before_concede_or_kill"):
            print("  --- 胜负前最近回合开始 ---")
            print(f"  overlay: {bc['overlay场攻']} | 对手: {bc['对手血线']} | 手牌: {bc['手牌']}")
        if r.get("last_played"):
            print(f"  你最后一手牌: {r['last_played']}")
        if r.get("opp_hand_at_concede_log"):
            print(f"  对手投降时手牌(日志): {r['opp_hand_at_concede_log']}")
        print(f"  分析: {r.get('why_concede', r.get('reason', ''))}")


if __name__ == "__main__":
    main()
