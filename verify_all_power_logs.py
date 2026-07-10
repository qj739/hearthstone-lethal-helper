#!/usr/bin/env python3
"""用已拆分的单局 Power.log 验证斩杀判断（默认读 split_games）。"""
from __future__ import annotations

import argparse
import contextlib
import io
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker

LOGS_ROOT = Path(__file__).parent / "Logs"
SPLIT_ROOT = LOGS_ROOT / "split_games"

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
    local_player_id: Optional[int] = None
    parse_ok: bool = True
    error: str = ""
    pre_kill: Optional[LethalSnapshot] = None
    kill_turn_start: Optional[LethalSnapshot] = None
    kill_line: Optional[int] = None
    details: List[str] = field(default_factory=list)


def _progress(done: int, total: int, msg: str = "") -> None:
    if total <= 0:
        return
    pct = 100.0 * done / total
    bar_len = 30
    filled = int(bar_len * done / total)
    bar = "#" * filled + "-" * (bar_len - filled)
    line = f"\r[{bar}] {pct:5.1f}% ({done}/{total}) {msg}"
    print(line, end="", flush=True)


def _finish_progress() -> None:
    print(flush=True)


def lethal_snapshot(gs: GameState) -> LethalSnapshot:
    lc = LethalChecker(gs)
    _, _, lethal = lc.calculate_lethal()
    overlay = lc.overlay_board_face_damage()
    prob = getattr(lc, "_overlay_lethal_prob", 0.0)
    note = lc.overlay_spell_note()
    opp_hp = lc.get_opponent_effective_hp() if gs.opponent_player_id else 0
    return LethalSnapshot(
        overlay=overlay,
        lethal=lethal,
        opp_hp=opp_hp,
        prob=prob,
        note=note or "",
    )


def parse_to_line(lines: List[str], log_label: str, end_line: int) -> GameState:
    gs = GameState()
    parser = PowerLogParser(log_label, gs)
    limit = min(end_line, len(lines))
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(limit):
            line = lines[i].rstrip("\n\r")
            if line:
                parser.process_line(line)
    return gs


def parse_with_snapshots(
    lines: List[str],
    log_label: str,
    checkpoints: Dict[str, int],
) -> Dict[str, LethalSnapshot]:
    """单次前向解析，在指定行号处截取斩杀快照。"""
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
    name = gs.player_names.get(pid)
    if name:
        return name
    return f"Player{pid}"


def is_local_winner(local_name: str, winner: str) -> bool:
    if not local_name or not winner:
        return False
    if local_name == winner:
        return True
    return local_name.split("#")[0] == winner.split("#")[0]


def scan_winner(lines: List[str]) -> Tuple[Optional[int], str]:
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
) -> Tuple[Optional[int], Optional[int]]:
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


def discover_split_games() -> List[Path]:
    if not SPLIT_ROOT.is_dir():
        return []
    files = sorted(SPLIT_ROOT.glob("*/game_*.log"))
    return files


def split_power_logs() -> int:
    """从完整 Power.log 拆分到 split_games（仅当缺失时手动调用）。"""
    power_logs = sorted(LOGS_ROOT.glob("*/Power.log"))
    count = 0
    for pl in power_logs:
        session = pl.parent.name
        lines = pl.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
        starts = [i for i, ln in enumerate(lines) if _CREATE_GAME_RE.search(ln)]
        out_dir = SPLIT_ROOT / session
        out_dir.mkdir(parents=True, exist_ok=True)
        for idx, start in enumerate(starts):
            end = starts[idx + 1] if idx + 1 < len(starts) else len(lines)
            out_path = out_dir / f"game_{idx + 1:02d}.log"
            out_path.write_text("".join(lines[start:end]), encoding="utf-8")
            count += 1
    return count


def analyze_split_file(path: Path) -> GameReport:
    session = path.parent.name
    m = re.search(r"game_(\d+)", path.name)
    game_index = int(m.group(1)) if m else 0
    rep = GameReport(session=session, game_index=game_index, split_path=str(path))
    label = f"{session}/{path.name}"

    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines(keepends=True)

        won_line, winner = scan_winner(lines)
        if won_line is None:
            rep.details.append("对局未结束或无 WON 记录")
            return rep

        rep.winner = winner
        gs_meta = parse_to_line(lines, label, won_line + 1)
        rep.local_player_id = gs_meta.local_player_id
        rep.local_name = local_battletag(gs_meta)
        rep.local_won = is_local_winner(rep.local_name, winner)

        if not rep.local_won:
            opp_name = gs_meta.player_names.get(gs_meta.opponent_player_id or 0, winner)
            rep.details.append(f"负 (对手 {opp_name or winner})")
            return rep

        local = gs_meta.local_player_id
        opp = gs_meta.opponent_player_id
        if local is None or opp is None:
            rep.details.append("未识别双方 PlayerID")
            return rep

        send_idx, kill_idx = find_kill_events(lines, local, opp, won_line)
        rep.kill_line = (kill_idx + 1) if kill_idx is not None else None
        before = send_idx or kill_idx or won_line
        turn_idx = find_kill_turn_main_action(lines, rep.local_name, before)

        checkpoints: Dict[str, int] = {}
        if turn_idx is not None:
            checkpoints["turn"] = turn_idx
        if send_idx is not None:
            checkpoints["pre_kill"] = send_idx

        snaps = parse_with_snapshots(lines, label, checkpoints)
        if "turn" in snaps:
            rep.kill_turn_start = snaps["turn"]
            s = rep.kill_turn_start
            rep.details.append(
                f"斩杀回合初: overlay={s.overlay} lethal={s.lethal} "
                f"opp_hp={s.opp_hp} prob={s.prob:.0%}"
            )
        if "pre_kill" in snaps:
            rep.pre_kill = snaps["pre_kill"]
            s = rep.pre_kill
            rep.details.append(
                f"斩杀前: overlay={s.overlay} lethal={s.lethal} "
                f"opp_hp={s.opp_hp} prob={s.prob:.0%}"
            )
            if s.note:
                rep.details.append(f"  打法: {s.note}")

        if rep.pre_kill:
            if rep.pre_kill.lethal:
                rep.details.append("✓ 斩杀前已识别")
            else:
                rep.details.append(
                    f"✗ 斩杀前未识别 (场攻{rep.pre_kill.overlay} < 对手{rep.pre_kill.opp_hp})"
                )
        elif rep.kill_turn_start and rep.kill_turn_start.lethal:
            rep.details.append("✓ 仅回合初识别")
        else:
            rep.details.append("? 胜但未定位斩杀检查点")

    except Exception as e:
        rep.parse_ok = False
        rep.error = str(e)

    return rep


def print_summary(reports: List[GameReport]) -> None:
    print("\n" + "=" * 88)
    print(
        f"{'会话':<32} {'局':>3} {'结果':<6} {'回合初场攻':>8} {'回合初斩':>6} "
        f"{'斩杀前场攻':>8} {'斩杀前斩':>6} {'对手血':>6}"
    )
    print("-" * 88)
    for r in reports:
        result = "胜" if r.local_won else ("负" if r.winner else "未完")
        ts = r.kill_turn_start
        pk = r.pre_kill
        print(
            f"{r.session:<32} {r.game_index:>3} {result:<6} "
            f"{ts.overlay if ts else '-':>8} "
            f"{'Y' if ts and ts.lethal else ('N' if ts else '-'):>6} "
            f"{pk.overlay if pk else '-':>8} "
            f"{'Y' if pk and pk.lethal else ('N' if pk else '-'):>6} "
            f"{pk.opp_hp if pk else '-':>6}"
        )
        for d in r.details:
            print(f"    {d}")
        if r.error:
            print(f"    ERROR: {r.error}")
    print("=" * 88)

    wins = [r for r in reports if r.local_won]
    pre_ok = sum(1 for r in wins if r.pre_kill and r.pre_kill.lethal)
    turn_ok = sum(1 for r in wins if r.kill_turn_start and r.kill_turn_start.lethal)
    print(
        f"\n合计 {len(reports)} 场 | 我方胜 {len(wins)} 场 | "
        f"斩杀前识别 {pre_ok}/{len(wins)} | 斩杀回合初识别 {turn_ok}/{len(wins)}"
    )
    print(f"数据来源: {SPLIT_ROOT}")


def main() -> int:
    ap = argparse.ArgumentParser(description="验证 split_games 下各场对局的斩杀判断")
    ap.add_argument(
        "--split",
        action="store_true",
        help="先从 Logs/*/Power.log 重新拆分到 split_games",
    )
    args = ap.parse_args()

    if args.split:
        n = split_power_logs()
        print(f"已拆分 {n} 场 -> {SPLIT_ROOT}")

    game_files = discover_split_games()
    if not game_files:
        print(f"未找到拆分对局: {SPLIT_ROOT}")
        print("请先运行: python verify_all_power_logs.py --split")
        return 1

    total = len(game_files)
    print(f"共 {total} 场拆分对局，开始验证...", flush=True)
    t0 = time.perf_counter()
    reports: List[GameReport] = []

    for i, path in enumerate(game_files, start=1):
        short = f"{path.parent.name}/game_{path.stem.split('_')[-1]}"
        _progress(i - 1, total, f"解析 {short}")
        reports.append(analyze_split_file(path))
        _progress(i, total, f"完成 {short}")

    _finish_progress()
    elapsed = time.perf_counter() - t0
    print(f"耗时 {elapsed:.1f}s", flush=True)
    print_summary(reports)
    return 0


if __name__ == "__main__":
    sys.exit(main())
