#!/usr/bin/env python3
"""第12局投降回合详细分析"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from analyze_user_logs_lethal import (
    analyze_split_file,
    find_kill_turn_main_action,
    lethal_snapshot,
    parse_to_line,
    scan_winner,
)
from hdt_python.lethal_checker import LethalChecker

LOG = Path(
    r"C:\Users\hp\Desktop\LOGS(1)\LOGS\split_games"
    r"\Hearthstone_2026_06_15_23_18_06\game_02.log"
)
CARDS = json.loads(
    (Path(__file__).resolve().parent.parent / "json" / "cards_zhCN.json").read_text(encoding="utf-8")
)
NAMES = {c["id"]: c.get("name", c["id"]) for c in CARDS if c.get("id")}

lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
label = str(LOG)
won_idx, _ = scan_winner(lines)
rep = analyze_split_file(LOG)
gs_end = parse_to_line(lines, label, len(lines))
local_pid = gs_end.local_player_id
opp_pid = gs_end.opponent_player_id
local_name = gs_end.player_names.get(local_pid, "")

ma = find_kill_turn_main_action(lines, local_name, won_idx)
print(f"=== 第12局 === 对手: {gs_end.player_names.get(opp_pid,'?').split('#')[0]}")
print(f"投降行: {won_idx+1}  斩杀回合 MAIN_ACTION: {ma+1 if ma else None}")
print(f"引擎: {rep.end_type} | 回合初 overlay={rep.kill_turn_start.overlay if rep.kill_turn_start else '?'} "
      f"lethal={rep.kill_turn_start.lethal if rep.kill_turn_start else '?'} "
      f"opp={rep.kill_turn_start.opp_hp if rep.kill_turn_start else '?'}")


def nm(cid):
    return NAMES.get(cid, cid)


def hero_eff(gs, pid):
    h = gs.get_hero(pid)
    if not h:
        return "?"
    dmg = int(h.tags.get("DAMAGE", 0))
    armor = int(h.tags.get("ARMOR", 0))
    hp = h.current_health - dmg
    return f"{max(0, hp) + armor}有效({max(0, hp)}血+{armor}甲)"


def fmt_board(gs, pid):
    ms = gs.get_board(pid)
    if not ms:
        return "(空)"
    parts = []
    for m in sorted(ms, key=lambda x: x.tags.get("ZONE_POSITION", 0)):
        taunt = "嘲" if m.tags.get("TAUNT") else ""
        rush = "冲" if m.tags.get("CHARGE") or m.tags.get("RUSH") else ""
        parts.append(f"{nm(m.card_id)}{m.atk}/{m.current_health}{taunt}{rush}")
    return " | ".join(parts)


def fmt_hand(gs, pid):
    cards = gs.get_hand(pid)
    parts = []
    for c in sorted(cards, key=lambda x: x.tags.get("ZONE_POSITION", 0)):
        cost = c.tags.get("COST", c.cost)
        parts.append(f"{nm(c.card_id)}({cost})")
    return "、".join(parts) if parts else "(空)"


def mana(gs, pid):
    h = gs.get_hero(pid)
    res = int(h.tags.get("RESOURCES", 0))
    used = int(h.tags.get("RESOURCES_USED", 0))
    return f"{res - used}/{res}"


def snap_at(ln, title):
    gs = parse_to_line(lines, label, ln + 1)
    s = lethal_snapshot(gs)
    _, b, w, sp, hp = LethalChecker(gs).overlay_board_breakdown()
    print(f"\n--- {title} (L{ln+1}) ---")
    print(f"  我方法力: {mana(gs, local_pid)}")
    print(f"  我方场面: {fmt_board(gs, local_pid)}")
    print(f"  我方手牌: {fmt_hand(gs, local_pid)}")
    print(f"  对手场面: {fmt_board(gs, opp_pid)}")
    print(f"  对手英雄: {hero_eff(gs, opp_pid)}")
    print(f"  引擎 overlay={s.overlay} lethal={s.lethal} note={s.note!r}")
    print(f"  分解: 随从打脸={b} 武器={w} 法术={sp} 技能={hp}")


if ma is not None:
    snap_at(ma, "我方斩杀回合·回合初")

# 本回合我方出牌时间线
print("\n=== 我方斩杀回合操作 (SendOption → PLAY) ===")
if ma:
    plays = []
    for i in range(ma, won_idx):
        if "GameState.SendOption()" not in lines[i]:
            continue
        action = ""
        for j in range(i, min(i + 30, len(lines))):
            if "BLOCK_START BlockType=PLAY" in lines[j] and f"player={local_pid}" in lines[j]:
                m = re.search(r"entityName=([^\]]+).*cardId=(\S+) player=", lines[j])
                if m:
                    action = f"打出 {m.group(1)}/{nm(m.group(2))}"
                break
            if "BLOCK_START BlockType=ATTACK" in lines[j] and f"player={local_pid}" in lines[j]:
                m = re.search(r"entityName=([^\]]+).*Target=\[entityName=([^\]]+)", lines[j])
                if m:
                    action = f"攻击 {m.group(1)} → {m.group(2)}"
                break
        if "selectedOption=0" in lines[i] and "END_TURN" not in action:
            # check if end turn
            for j in range(max(0, i - 5), i):
                pass
            if not action:
                action = "结束回合"
        ts = lines[i].split()[1] if len(lines[i].split()) > 1 else ""
        if action or "selectedOption=0" in lines[i]:
            plays.append((i, ts, action or lines[i].strip()[-50:]))
    for ln, ts, act in plays:
        print(f"  {ts} L{ln+1}: {act}")

# 关键检查点
checkpoints = []
if ma:
    checkpoints.append((ma, "回合初"))
for pat, name in [
    (r"幼体风灵.*BLOCK_START BlockType=PLAY", "打出幼体风灵后"),
]:
    pass

# explicit lines from grep
for ln, name in [
    (15690, "打出第一张牌前"),
    (16955, "打出幼体风灵前"),
    (17050, "幼体风灵结算后(估)"),
    (19151, "我方结束回合后·对手回合初"),
    (19764, "对手投降前"),
]:
    if ln < len(lines):
        snap_at(ln, name)

# find line after 幼体风灵 play ends
for i, l in enumerate(lines):
    if "幼体风灵 id=198" in l and "tag=ZONE value=PLAY" in l:
        wind_end = i + 80
        break
else:
    wind_end = 17050

snap_at(min(wind_end, len(lines) - 1), "幼体风灵上场后")

# After end turn - opponent turn start
for i in range(won_idx, max(0, won_idx - 3000), -1):
    if "CURRENT_PLAYER value=1" in lines[i] and "繁忙的雄鹿" in lines[i-2] if i >= 2 else False:
        pass

print("\n=== 投降时刻 ===")
print(f"  时间: 23:41:38 — 对手在你方上回合结束后、自己回合中投降")
print(f"  投降前最后操作: 对手使用地标「淤泥之池」发现随从（未打完就认负）")
