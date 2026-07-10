#!/usr/bin/env python3
"""拆分用户 LOG 目录下的 Power.log，并检查获胜局斩杀识别情况。"""
from __future__ import annotations

import argparse
import contextlib
import io
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.lethal_checker import LethalChecker
from hdt_python.power_parser import GameState, PowerLogParser

CONCEDED_RE = re.compile(r"PLAYSTATE value=CONCEDED")
_CREATE_GAME_RE = re.compile(r"GameState\.DebugPrintPower\(\) - CREATE_GAME")
_WON_RE = re.compile(
    r"GameState\.DebugPrintPower\(\) - TAG_CHANGE Entity=([^ ]+) tag=PLAYSTATE value=WON"
)
_SEND_OPTION_RE = re.compile(r"GameState\.SendOption\(\)")
_MAIN_ACTION_RE = re.compile(
    r"GameState\.DebugPrintPower\(\) - TAG_CHANGE Entity=GameEntity tag=STEP value=MAIN_ACTION"
)
_LOCAL_TURN_RE = re.compile(
    r"GameState\.DebugPrintPower\(\) -\s+TAG_CHANGE Entity=([^ ]+) tag=CURRENT_PLAYER value=1\b"
)
_HERO_DAMAGE_RE = re.compile(
    r"GameState\.DebugPrintPower\(\) - .+Entity=\[entityName=[^\]]* id=(\d+) zone=PLAY zonePos=0 cardId=(HERO_[^\s]+) player=(\d+)\] tag=DAMAGE value=(\d+)"
)
_HERO_GRAVEYARD_RE = re.compile(
    r"GameState\.DebugPrintPower\(\) - .+Entity=\[entityName=[^\]]* id=(\d+) zone=PLAY zonePos=0 cardId=(HERO_[^\s]+) player=(\d+)\] tag=ZONE value=GRAVEYARD"
)


@dataclass
class LethalSnapshot:
    overlay: int = 0
    lethal: bool = False
    opp_hp: int = 0
    prob: float = 0.0
    note: str = ""


@dataclass
class GameReport:
    session: str
    game_index: int
    split_path: str = ""
    winner: str = ""
    local_name: str = ""
    local_won: bool = False
    parse_ok: bool = True
    error: str = ""
    pre_kill: Optional[LethalSnapshot] = None
    kill_turn_start: Optional[LethalSnapshot] = None
    verdict: str = ""
    note: str = ""
    end_type: str = ""
    final_judge: str = ""


def lethal_snapshot(gs: GameState) -> LethalSnapshot:
    lc = LethalChecker(gs)
    _, _, lethal = lc.calculate_lethal()
    overlay = lc.overlay_board_face_damage()
    prob = getattr(lc, "_overlay_lethal_prob", 0.0)
    note = lc.overlay_spell_note() or ""
    opp_hp = lc.get_opponent_effective_hp() if gs.opponent_player_id else 0
    return LethalSnapshot(
        overlay=overlay,
        lethal=lethal,
        opp_hp=opp_hp,
        prob=prob,
        note=note,
    )


def parse_to_line(lines: List[str], log_label: str, end_line: int) -> GameState:
    gs = GameState()
    parser = PowerLogParser(log_label, gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(min(end_line, len(lines))):
            line = lines[i].rstrip("\n\r")
            if line:
                parser.process_line(line)
    return gs


def parse_with_snapshots(
    lines: List[str],
    log_label: str,
    checkpoints: Dict[str, int],
) -> Dict[str, LethalSnapshot]:
    if not checkpoints:
        return {}
    ordered = sorted(checkpoints.items(), key=lambda x: x[1])
    stop_at = ordered[-1][1]
    gs = GameState()
    parser = PowerLogParser(log_label, gs)
    results: Dict[str, LethalSnapshot] = {}
    ci = 0
    with contextlib.redirect_stdout(io.StringIO()):
        for i, raw in enumerate(lines):
            if i >= stop_at:
                break
            line = raw.rstrip("\n\r")
            if line:
                parser.process_line(line)
            while ci < len(ordered) and i + 1 >= ordered[ci][1]:
                results[ordered[ci][0]] = lethal_snapshot(gs)
                ci += 1
    return results


def local_battletag(gs: GameState) -> str:
    pid = gs.local_player_id
    if pid is None:
        return ""
    return gs.player_names.get(pid) or f"Player{pid}"


def is_local_winner(local_name: str, winner: str) -> bool:
    if not local_name or not winner:
        return False
    if local_name == winner:
        return True
    return local_name.split("#")[0] == winner.split("#")[0]


def opponent_conceded(lines: List[str], won_line: int, winner: str) -> bool:
    for i in range(max(0, won_line - 30), won_line + 1):
        if CONCEDED_RE.search(lines[i]) and winner not in lines[i]:
            return True
    return False


def scan_winner(lines: List[str]) -> tuple[Optional[int], str]:
    for i, ln in enumerate(lines):
        m = _WON_RE.search(ln)
        if m:
            return i, m.group(1)
    return None, ""


def find_kill_events(
    lines: List[str],
    local_pid: int,
    opp_pid: int,
    won_idx: int,
) -> tuple[Optional[int], Optional[int]]:
    kill_idx = None
    for i in range(won_idx, max(-1, won_idx - 800), -1):
        ln = lines[i]
        gm = _HERO_GRAVEYARD_RE.search(ln)
        if gm and int(gm.group(3)) == opp_pid:
            kill_idx = i
            break
        dm = _HERO_DAMAGE_RE.search(ln)
        if dm and int(dm.group(3)) == opp_pid and int(dm.group(4)) >= 25:
            kill_idx = i
            break
    if kill_idx is None:
        return None, None
    send_idx = None
    for i in range(kill_idx, max(-1, kill_idx - 150), -1):
        if _SEND_OPTION_RE.search(lines[i]):
            send_idx = i
            break
    return send_idx, kill_idx


def find_kill_turn_main_action(
    lines: List[str],
    local_tag: str,
    before_line: int,
) -> Optional[int]:
    last_local_turn = None
    for i in range(before_line):
        m = _LOCAL_TURN_RE.search(lines[i])
        if m and m.group(1) == local_tag:
            last_local_turn = i
    if last_local_turn is None:
        return None
    for i in range(last_local_turn, before_line):
        if _MAIN_ACTION_RE.search(lines[i]):
            return i + 1
    return None


def split_power_logs(logs_root: Path, split_root: Path) -> int:
    count = 0
    for pl in sorted(logs_root.glob("*/Power.log")):
        session = pl.parent.name
        lines = pl.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
        starts = [i for i, ln in enumerate(lines) if _CREATE_GAME_RE.search(ln)]
        out_dir = split_root / session
        out_dir.mkdir(parents=True, exist_ok=True)
        for idx, start in enumerate(starts):
            end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
            (out_dir / f"game_{idx + 1:02d}.log").write_text(
                "".join(lines[start:end]), encoding="utf-8",
            )
            count += 1
    return count


def analyze_split_file(path: Path) -> GameReport:
    session = path.parent.name
    m = re.search(r"game_(\d+)", path.name)
    game_index = int(m.group(1)) if m else 0
    rep = GameReport(session=session, game_index=game_index, split_path=str(path))
    label = f"{session}/{path.name}"
    try:
        lines = path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
        won_line, winner = scan_winner(lines)
        if won_line is None:
            rep.verdict = "未完"
            return rep

        rep.winner = winner
        gs_meta = parse_to_line(lines, label, won_line + 1)
        rep.local_name = local_battletag(gs_meta)
        rep.local_won = is_local_winner(rep.local_name, winner)
        if not rep.local_won:
            rep.verdict = "负"
            return rep

        local = gs_meta.local_player_id
        opp = gs_meta.opponent_player_id
        if local is None or opp is None:
            rep.verdict = "解析失败"
            return rep

        send_idx, kill_idx = find_kill_events(lines, local, opp, won_line)
        rep.end_type = (
            "对手投降" if opponent_conceded(lines, won_line, winner)
            else ("英雄击杀" if kill_idx is not None else "其他胜法")
        )
        before = send_idx or kill_idx or won_line
        turn_idx = find_kill_turn_main_action(lines, rep.local_name, before)

        checkpoints: Dict[str, int] = {}
        if turn_idx is not None:
            checkpoints["turn"] = turn_idx
        if send_idx is not None:
            checkpoints["pre_kill"] = send_idx

        snaps = parse_with_snapshots(lines, label, checkpoints)
        rep.kill_turn_start = snaps.get("turn")
        rep.pre_kill = snaps.get("pre_kill")

        pk = rep.pre_kill
        ts = rep.kill_turn_start
        if pk:
            rep.note = pk.note
            if pk.lethal:
                rep.final_judge = "✅ 斩杀前正确"
            elif rep.end_type == "英雄击杀":
                rep.final_judge = "❌ 漏算斩杀"
            elif rep.end_type == "对手投降":
                rep.final_judge = "— 投降局(未达斩)"
            else:
                rep.final_judge = "⚠️ 未识别"
        elif ts and ts.lethal:
            rep.note = ts.note
            rep.final_judge = "✅ 回合初正确"
        elif ts and not ts.lethal:
            if rep.end_type == "英雄击杀":
                rep.final_judge = "❌ 漏算斩杀"
            elif rep.end_type == "对手投降":
                rep.final_judge = "— 投降局(未达斩)"
            else:
                rep.final_judge = "⚠️ 非标准斩杀胜"
        else:
            rep.final_judge = "⚠️ 未定位检查点"
        rep.verdict = rep.final_judge
    except Exception as e:
        rep.parse_ok = False
        rep.error = str(e)
        rep.verdict = "错误"
    return rep


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--logs-root",
        default=r"C:\Users\hp\Desktop\LOGS(1)\LOGS",
        help="含 Hearthstone_* 子目录的 LOG 根目录",
    )
    args = ap.parse_args()

    logs_root = Path(args.logs_root)
    split_root = logs_root / "split_games"

    n = split_power_logs(logs_root, split_root)
    print(f"已拆分 {n} 场 -> {split_root}")

    files = sorted(split_root.glob("*/game_*.log"))
    reports = [analyze_split_file(p) for p in files]
    wins = [r for r in reports if r.local_won]

    print("\n| 会话 | 局 | 结束方式 | 回合初场攻 | 斩 | 斩杀前场攻 | 斩 | 对手血 | 判定 | 备注 |")
    print("|---|---:|---|---:|---:|---:|---:|---:|---|---|")
    for r in wins:
        ts = r.kill_turn_start
        pk = r.pre_kill
        note = (r.note or "")[:36].replace("|", "/")
        sess = r.session.replace("Hearthstone_", "")
        print(
            f"| {sess} | {r.game_index} | {r.end_type} | "
            f"{ts.overlay if ts else '-'} | "
            f"{'Y' if ts and ts.lethal else ('N' if ts else '-')} | "
            f"{pk.overlay if pk else '-'} | "
            f"{'Y' if pk and pk.lethal else ('N' if pk else '-')} | "
            f"{pk.opp_hp if pk else (ts.opp_hp if ts else '-')} | "
            f"{r.final_judge} | {note} |"
        )

    miss = [r for r in wins if r.final_judge.startswith("❌")]
    ok = [r for r in wins if r.final_judge.startswith("✅")]
    concede = [r for r in wins if r.end_type == "对手投降"]
    print(
        f"\n合计 {len(reports)} 场 | 我方胜 {len(wins)} 场 "
        f"(其中对手投降 {len(concede)} 场) | "
        f"斩杀识别正确 {len(ok)} | 真漏算 {len(miss)}"
    )
    if miss:
        print("\n漏算明细:")
        for r in miss:
            pk = r.pre_kill
            ts = r.kill_turn_start
            snap = pk or ts
            if snap:
                print(
                    f"  {r.session} game_{r.game_index:02d}: "
                    f"场攻={snap.overlay} 对手={snap.opp_hp} 概率={snap.prob:.0%} "
                    f"note={snap.note!r}"
                )
    return 0


if __name__ == "__main__":
    sys.exit(main())
