#!/usr/bin/env python3
"""我方胜局：回合初未判斩杀的局，输出详细快照供人工复核。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analyze_user_logs_lethal import (
    analyze_split_file,
    find_kill_events,
    find_kill_turn_main_action,
    parse_to_line,
    scan_winner,
)
from hdt_python.board_damage import build_player_board, entity_has_taunt
from hdt_python.lethal_checker import LethalChecker

SPLIT_ROOT = Path(r"C:\Users\hp\Desktop\HS\Logs\split_games")
CARDS = json.loads(
    (Path(__file__).resolve().parent.parent / "json" / "cards_zhCN.json").read_text(encoding="utf-8")
)
NAMES = {c["id"]: c.get("name", c["id"]) for c in CARDS if c.get("id")}


def fmt_hand(gs, pid) -> str:
    cards = gs.get_hand(pid)
    parts = []
    for c in sorted(cards, key=lambda x: x.tags.get("ZONE_POSITION", 0)):
        nm = NAMES.get(c.card_id or "?", c.card_id or "?")
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
        nm = NAMES.get(m.card_id or "?", m.card_id or "?")
        parts.append(f"{nm}{m.atk}/{m.current_health}{taunt}")
    return " ".join(parts)


def fmt_mana(gs, pid) -> str:
    h = gs.get_hero(pid)
    if not h:
        return "?"
    res = int(h.tags.get("RESOURCES", 0))
    used = int(h.tags.get("RESOURCES_USED", 0))
    return f"{res - used}/{res}"


def fmt_opp_hp(gs) -> str:
    lc = LethalChecker(gs)
    eff = lc.get_opponent_effective_hp()
    opp = gs.opponent_player_id
    h = gs.get_hero(opp) if opp else None
    if not h:
        return str(eff)
    hp = max(0, h.current_health - int(h.tags.get("DAMAGE", 0)))
    armor = int(h.tags.get("ARMOR", 0))
    shield = "圣盾" if h.tags.get("DIVINE_SHIELD", 0) else ""
    base = f"{eff}有效"
    detail = f"({hp}血"
    if armor:
        detail += f"+{armor}甲"
    detail += ")"
    if shield:
        detail += shield
    return base + detail


def fmt_overlay(lc: LethalChecker) -> str:
    total = lc.overlay_board_face_damage()
    uses_random = getattr(lc, "_overlay_uses_random", False)
    top = getattr(lc, "_overlay_top_outcomes", [])
    if uses_random and top:
        parts = [f"{d}({p*100:.0f}%)" for d, p in top[:2]]
        return " ".join(parts)
    return str(total)


def engine_play_line(lc: LethalChecker) -> str:
    note = lc.overlay_spell_note() or ""
    lines = lc.overlay_combo_display_lines()
    steps = [ln for ln in lines if ln and not ln.startswith("⚔") and not ln.startswith("（")]
    combo = " → ".join(steps) if steps else "(无步骤，纯场面攻击)"
    order = getattr(lc, "_overlay_best_order", "")
    order_cn = {
        "spell_first": "先法后攻",
        "attack_first": "先攻后法",
        "attack_interleaved": "穿插",
    }.get(order, order)
    if note:
        return f"{note}；步骤: {combo}" + (f" [{order_cn}]" if order_cn else "")
    if combo != "(无步骤，纯场面攻击)":
        return combo + (f" [{order_cn}]" if order_cn else "")
    return f"纯场面打脸 [{order_cn}]" if order_cn else "纯场面打脸"


def snapshot_at(lines, label, line_idx):
    gs = parse_to_line(lines, label, line_idx)
    if gs.local_player_id is None:
        return None
    lc = LethalChecker(gs)
    _, _, lethal = lc.calculate_lethal()
    overlay = fmt_overlay(lc)
    prob = getattr(lc, "_overlay_lethal_prob", 0.0)
    pb = build_player_board(gs, gs.local_player_id, active_turn=True)
    minion_only = sum(c.attack for c in pb.cards if c.can_attack_hero)
    return {
        "gs": gs,
        "lc": lc,
        "overlay": overlay,
        "lethal": lethal,
        "prob": prob,
        "minion_only": minion_only,
        "hand": fmt_hand(gs, gs.local_player_id),
        "board": fmt_board(gs, gs.local_player_id),
        "opp_board": fmt_board(gs, gs.opponent_player_id),
        "mana": fmt_mana(gs, gs.local_player_id),
        "opp_hp": fmt_opp_hp(gs),
        "play_line": engine_play_line(lc),
        "note": lc.overlay_spell_note() or "",
    }


def turn_start_line(lines, rep, label):
    won_idx, _ = scan_winner(lines)
    if won_idx is None:
        return None
    gs_meta = parse_to_line(lines, label, len(lines))
    send_idx, kill_idx = find_kill_events(
        lines, gs_meta.local_player_id, gs_meta.opponent_player_id, won_idx,
    )
    before = send_idx or kill_idx or won_idx
    return find_kill_turn_main_action(lines, rep.local_name, before)


def main():
    selected = []
    for path in sorted(SPLIT_ROOT.glob("*/game_*.log")):
        rep = analyze_split_file(path)
        if not rep.local_won:
            continue
        if rep.kill_turn_start is None:
            continue
        if rep.kill_turn_start.lethal:
            continue  # 回合初已斩，跳过

        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        label = f"{path.parent.name}/{path.name}"
        tidx = turn_start_line(lines, rep, label)
        if tidx is None:
            continue

        turn = snapshot_at(lines, label, tidx)
        pre = None
        won_idx, _ = scan_winner(lines)
        if won_idx is not None:
            gs_meta = parse_to_line(lines, label, len(lines))
            send_idx, _ = find_kill_events(
                lines, gs_meta.local_player_id, gs_meta.opponent_player_id, won_idx,
            )
            if send_idx is not None:
                pre = snapshot_at(lines, label, send_idx)

        sess = path.parent.name.replace("Hearthstone_", "")
        selected.append({
            "sess": sess,
            "game": rep.game_index,
            "path": str(path),
            "end": rep.end_type,
            "turn": turn,
            "pre": pre,
            "turn_snap": rep.kill_turn_start,
            "pre_snap": rep.pre_kill,
        })

    print(f"回合初未判斩杀 · 我方胜局共 **{len(selected)}** 局\n")
    print("---\n")

    for i, r in enumerate(selected, 1):
        t = r["turn"]
        p = r["pre"]
        ts = r["turn_snap"]
        ps = r["pre_snap"]
        print(f"### {i}. {r['sess']} · 第{r['game']}局 · {r['end']}")
        print(f"- 日志: `{Path(r['path']).name}`")
        print(f"- **对手血量**: {t['opp_hp']}")
        print(f"- **法力**: {t['mana']}")
        print(f"- **我方场面**: {t['board']}")
        print(f"- **对方场面**: {t['opp_board']}")
        print(f"- **手牌**: {t['hand']}")
        print(f"- **场攻(Overlay)**: {t['overlay']} | 纯随从可打脸: {t['minion_only']}")
        if t["prob"] > 0 and t["prob"] < 1:
            print(f"- **概率斩**: {t['prob']*100:.0f}%")
        print(f"- **回合初斩杀**: ❌ (overlay={ts.overlay}, opp={ts.opp_hp})")
        print(f"- **引擎推荐打法**: {t['play_line']}")
        if p:
            pre_lethal = "✅" if ps and ps.lethal else "❌"
            print(f"- **出牌后(斩杀前)**: 场攻={p['overlay']} 斩={pre_lethal} 对手={p['opp_hp']}")
            if p["play_line"] != t["play_line"]:
                print(f"- **出牌后推荐**: {p['play_line']}")
        else:
            print(f"- **出牌后(斩杀前)**: 无检查点（投降/非标准击杀）")
        print()


if __name__ == "__main__":
    main()
