# lethal_miss_audit.py — 斩杀后对照「回合初是否该提示」；晚亮/漏算写报告
from __future__ import annotations

import json
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .power_parser import GameState, PowerLogParser

# (verdict, diagnosis, report_path, game_log_path) -> None
MissNotifyFn = Callable[[str, str, str, str], None]

_REPO_ROOT = Path(__file__).resolve().parent.parent
_MISS_DIR_NAME = "lethal_misses"


def miss_reports_dir() -> Path:
    try:
        from .app_paths import is_frozen, user_data_dir

        if is_frozen():
            root = Path(user_data_dir()) / _MISS_DIR_NAME
        else:
            root = _REPO_ROOT / _MISS_DIR_NAME
    except Exception:
        root = _REPO_ROOT / _MISS_DIR_NAME
    root.mkdir(parents=True, exist_ok=True)
    return root


@dataclass
class OverlaySample:
    ts: float
    prompt: bool
    show: bool
    has_lethal: bool
    face: int
    opp_hp: int
    note: str = ""
    turn: Optional[int] = None
    before_action: bool = True


@dataclass
class MissReport:
    status: str  # pending | diagnosed | fixed | skipped
    created_at: str
    log_path: str
    runtime_prompted: bool
    prompted_before_action: bool
    local_won: bool
    end_type: str
    verdict: str
    note: str = ""
    pre_kill: Dict[str, Any] = field(default_factory=dict)
    kill_turn_start: Dict[str, Any] = field(default_factory=dict)
    last_sample: Dict[str, Any] = field(default_factory=dict)
    diagnosis: str = ""
    report_path: str = ""
    game_log: str = ""


class LethalMissAuditor:
    """
    漏斩判定（贴合常见体验）：
    - 以「斩杀回合开始」能否识别为主，不是「斩完前一刻」。
    - 「打一半才亮」：回合初回放已能斩 / 场攻已够，但操作前从未提示。
    """

    def __init__(self, on_miss: Optional[MissNotifyFn] = None) -> None:
        self._lock = threading.Lock()
        self._had_prompt = False
        self._prompted_before_action = False
        self._local_acted_this_turn = False
        self._samples: List[OverlaySample] = []
        self._max_samples = 60
        self._busy = False
        self._on_miss = on_miss

    def set_on_miss(self, on_miss: Optional[MissNotifyFn]) -> None:
        self._on_miss = on_miss

    def reset_game(self) -> None:
        with self._lock:
            self._had_prompt = False
            self._prompted_before_action = False
            self._local_acted_this_turn = False
            self._samples.clear()

    def on_local_turn_start(self) -> None:
        """我方回合开始：清空「本回合是否已动手」。"""
        with self._lock:
            self._local_acted_this_turn = False

    def on_local_action(self) -> None:
        """我方打出牌 / 攻击等：之后的提示算「打一半才发现」。"""
        with self._lock:
            self._local_acted_this_turn = True

    def note_overlay(
        self,
        *,
        prompt_lethal: bool,
        show_lethal: bool,
        has_lethal: bool,
        face: int,
        opp_hp: int,
        note: str = "",
        turn: Optional[int] = None,
    ) -> None:
        with self._lock:
            before = not self._local_acted_this_turn
            if prompt_lethal or show_lethal:
                self._had_prompt = True
                if before:
                    self._prompted_before_action = True
            sample = OverlaySample(
                ts=time.time(),
                prompt=bool(prompt_lethal),
                show=bool(show_lethal),
                has_lethal=bool(has_lethal),
                face=int(face or 0),
                opp_hp=int(opp_hp or 0),
                note=note or "",
                turn=turn,
                before_action=before,
            )
            self._samples.append(sample)
            if len(self._samples) > self._max_samples:
                self._samples = self._samples[-self._max_samples :]

    def on_match_ending(
        self,
        gs: "GameState",
        power_parser: "PowerLogParser",
    ) -> None:
        """对局清空前：本地胜则异步回放，按回合初标准判漏/晚亮。"""
        if getattr(power_parser, "_live_mode", True) is False:
            return

        local = gs.local_player_id
        opp = gs.opponent_player_id
        if local is None or opp is None:
            return

        local_won = _entity_playstate_in(gs.get_hero(local), ("WON", 4))
        if not local_won:
            local_won = _any_player_entity_playstate(gs, local, ("WON", 4))
        if not local_won:
            return

        opp_conceded = _entity_playstate_in(gs.get_hero(opp), ("CONCEDED", 8))
        if not opp_conceded:
            opp_conceded = _any_player_entity_playstate(gs, opp, ("CONCEDED", 8))

        with self._lock:
            prompted = self._had_prompt
            early = self._prompted_before_action
            samples = list(self._samples)

        log_path = getattr(power_parser, "log_file", None) or ""
        if not log_path or not Path(log_path).is_file():
            return

        last = asdict(samples[-1]) if samples else {}
        with self._lock:
            if self._busy:
                return
            self._busy = True

        def _job() -> None:
            try:
                self._diagnose_and_write(
                    log_path=str(log_path),
                    opp_conceded=opp_conceded,
                    last_sample=last,
                    runtime_prompted=prompted,
                    prompted_before_action=early,
                )
            finally:
                with self._lock:
                    self._busy = False

        threading.Thread(target=_job, name="LethalMissAudit", daemon=True).start()

    def _diagnose_and_write(
        self,
        *,
        log_path: str,
        opp_conceded: bool,
        last_sample: Dict[str, Any],
        runtime_prompted: bool,
        prompted_before_action: bool,
    ) -> None:
        path = Path(log_path)
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines(
                keepends=True,
            )
        except OSError as e:
            print(f"[漏斩审计] 跳过: 读日志失败: {e}")
            return

        create_idxs = [
            i for i, ln in enumerate(lines)
            if "GameState.DebugPrintPower() - CREATE_GAME" in ln
        ]
        if not create_idxs:
            print("[漏斩审计] 跳过: 日志无 CREATE_GAME")
            return

        start = create_idxs[-1]
        out_dir = miss_reports_dir()
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        game_log = out_dir / f"game_{stamp}.log"
        game_log.write_text("".join(lines[start:]), encoding="utf-8")

        analyze_split_file = _load_analyze_split_file()
        if analyze_split_file is None:
            print("[漏斩审计] 跳过: 无法加载 analyze_user_logs_lethal")
            return
        rep = analyze_split_file(game_log)

        if opp_conceded or rep.end_type == "对手投降":
            self._write_report(
                stamp=stamp,
                log_path=log_path,
                game_log=game_log,
                rep=rep,
                last_sample=last_sample,
                runtime_prompted=runtime_prompted,
                prompted_before_action=prompted_before_action,
                status="skipped",
                verdict="对手投降，跳过漏斩审计",
                diagnosis="对手投降",
            )
            return
        if not rep.local_won or rep.end_type != "英雄击杀":
            return

        verdict, diagnosis = _judge_miss(
            rep,
            runtime_prompted=runtime_prompted,
            prompted_before_action=prompted_before_action,
        )
        if verdict is None:
            return

        report_path = self._write_report(
            stamp=stamp,
            log_path=log_path,
            game_log=game_log,
            rep=rep,
            last_sample=last_sample,
            runtime_prompted=runtime_prompted,
            prompted_before_action=prompted_before_action,
            status="pending",
            verdict=verdict,
            diagnosis=diagnosis,
        )
        _announce_miss(report_path, verdict, diagnosis)
        _write_pending_queue(out_dir, report_path, verdict, diagnosis)
        if self._on_miss is not None:
            try:
                self._on_miss(
                    verdict,
                    diagnosis,
                    str(report_path),
                    str(game_log),
                )
            except Exception as e:
                print(f"[漏斩审计] 提示回调失败: {e}")

    def _write_report(
        self,
        *,
        stamp: str,
        log_path: str,
        game_log: Optional[Path],
        rep,
        last_sample: Dict[str, Any],
        runtime_prompted: bool,
        prompted_before_action: bool,
        status: str,
        verdict: str,
        diagnosis: str,
    ) -> Path:
        out_dir = miss_reports_dir()
        path = out_dir / f"miss_{stamp}.json"

        def _snap(s) -> Dict[str, Any]:
            if s is None:
                return {}
            return {
                "overlay": s.overlay,
                "lethal": s.lethal,
                "opp_hp": s.opp_hp,
                "prob": s.prob,
                "note": s.note,
            }

        payload = MissReport(
            status=status,
            created_at=datetime.now().isoformat(timespec="seconds"),
            log_path=log_path,
            runtime_prompted=runtime_prompted,
            prompted_before_action=prompted_before_action,
            local_won=bool(rep.local_won),
            end_type=rep.end_type or "",
            verdict=verdict,
            note=rep.note or "",
            pre_kill=_snap(rep.pre_kill),
            kill_turn_start=_snap(rep.kill_turn_start),
            last_sample=last_sample,
            diagnosis=diagnosis,
            report_path=str(path),
            game_log=str(game_log) if game_log else "",
        )
        path.write_text(
            json.dumps(asdict(payload), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path


def _judge_miss(
    rep,
    *,
    runtime_prompted: bool,
    prompted_before_action: bool,
) -> tuple[Optional[str], str]:
    """
    返回 (verdict, diagnosis)；无需报告时 verdict=None。
    优先看斩杀回合初，避免「打一半才亮」被 pre_kill 判成正确。
    """
    ts = rep.kill_turn_start
    pk = rep.pre_kill
    base = _build_diagnosis(rep)
    runtime = (
        f"运行时提示={runtime_prompted} 动手前提示={prompted_before_action}"
    )

    if ts is not None:
        # 回合初已能判斩，但动手前没提示 → 典型「打一半才发现」
        if ts.lethal and not prompted_before_action:
            return (
                "❌ 回合初漏提示（打一半才亮）",
                f"{base} | {runtime}",
            )
        # 场攻已够血却 has_lethal=False（嘲讽抑制等）
        if (
            not ts.lethal
            and ts.opp_hp > 0
            and ts.overlay >= ts.opp_hp
            and not prompted_before_action
        ):
            return (
                "❌ 回合初场攻够但未判斩",
                f"{base} | {runtime}",
            )
        if ts.lethal and prompted_before_action:
            return None, ""
        # 回合初确实不够，中途才成立 → 不算漏斩
        if not ts.lethal and pk and pk.lethal:
            return None, ""
        if not ts.lethal and not (pk and pk.lethal):
            return (
                "❌ 漏算斩杀",
                f"{base} | {runtime}",
            )

    if pk is not None:
        if pk.lethal and not runtime_prompted:
            return (
                "⚠️ 回放能斩但运行时未提示",
                f"{base} | {runtime}",
            )
        if not pk.lethal:
            return (
                "❌ 漏算斩杀",
                f"{base} | {runtime}",
            )

    return None, ""


def _entity_playstate_in(entity, values) -> bool:
    if entity is None:
        return False
    ps = entity.tags.get("PLAYSTATE")
    if ps is None:
        return False
    strs = {v.upper() for v in values if isinstance(v, str)}
    ints = {v for v in values if isinstance(v, int)}
    if isinstance(ps, str) and ps.upper() in strs:
        return True
    try:
        return int(ps) in ints
    except (TypeError, ValueError):
        return False


def _any_player_entity_playstate(gs: "GameState", pid: int, values) -> bool:
    for eid in getattr(gs, "player_ids", []) or []:
        ent = gs.get_entity(eid)
        if ent is None:
            continue
        ctrl = getattr(ent, "controller", None)
        if ctrl is not None and ctrl != pid:
            continue
        if _entity_playstate_in(ent, values):
            return True
    return False


def _build_diagnosis(rep) -> str:
    snap = rep.kill_turn_start or rep.pre_kill
    parts = []
    if snap:
        parts.append(
            f"回合初/斩前 场攻={snap.overlay} 对手血={snap.opp_hp} "
            f"lethal={snap.lethal} P={snap.prob:.0%}"
        )
        if snap.note:
            parts.append(f"note={snap.note!r}")
    if rep.kill_turn_start and rep.pre_kill:
        parts.append(
            f"斩前lethal={rep.pre_kill.lethal} 场攻={rep.pre_kill.overlay}"
        )
    parts.append(f"结束={rep.end_type}")
    return " | ".join(parts)


def _announce_miss(report_path: Path, verdict: str, diagnosis: str) -> None:
    print("\n" + "!" * 56)
    print("⚠️  【漏斩】本局回合初未正确提示斩杀")
    print(f"   判定: {verdict}")
    if diagnosis:
        print(f"   线索: {diagnosis}")
    print(f"   报告: {report_path}")
    print("   >>> 请到 Cursor 对 Agent 说：「有漏斩，请回溯 lethal_misses」")
    print("!" * 56 + "\n")
    try:
        import winsound
        winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
    except Exception:
        pass


def _write_pending_queue(
    out_dir: Path, report_path: Path, verdict: str, diagnosis: str,
) -> None:
    queue = out_dir / "PENDING.md"
    queue.write_text(
        "# 待修复漏斩\n\n"
        f"- report: `{report_path.name}`\n"
        f"- verdict: {verdict}\n"
        f"- diagnosis: {diagnosis}\n"
        "\n"
        "用户提示语：有漏斩，请回溯 lethal_misses\n\n"
        "Agent: 以「斩杀回合开始」状态为准回放（不要只看斩杀前一刻），"
        "修代码 + 补测试，再把 json status 改为 fixed。\n",
        encoding="utf-8",
    )


def _load_analyze_split_file():
    root = str(_REPO_ROOT)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from tools.analyze_user_logs_lethal import analyze_split_file
        return analyze_split_file
    except Exception:
        return None
