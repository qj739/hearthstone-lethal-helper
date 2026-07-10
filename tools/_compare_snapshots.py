#!/usr/bin/env python3
import contextlib
import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_06_24_12_01_30\Power.log"
)
lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()

SNAPSHOTS = [
    ("15:18:04 黑翼实验品刚上场", 406774),
    ("15:21:30 月亮井龙息可打", 415535),
    ("15:22:09 回合开始", 417869),
]


def replay(target: int) -> GameState:
    gs = GameState()
    parser = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for line in lines[: target + 1]:
            if line.strip():
                parser.process_line(line.rstrip())
    return gs


for label, target in SNAPSHOTS:
    gs = replay(target)
    lc = LethalChecker(gs)
    print(f"\n=== {label} (line {target}) ===")
    print("对手血量:", lc.get_opponent_health()[2])
    for pid, name in [(gs.local_player_id, "我方"), (gs.opponent_player_id, "对方")]:
        print(f"  {name}:")
        for m in gs.get_board(pid):
            print(
                f"    {m.card_id} 攻{m.atk} 血{m.current_health}/{m.health}"
                f" dmg={m.tags.get('DAMAGE', 0)}"
                f" 嘲={m.tags.get('TAUNT', 0)}"
                f" tag479={m.tags.get('479')} tagATK={m.tags.get('ATK')}"
            )
    hand = [c.card_id for c in gs.get_hand(gs.local_player_id)]
    print(
        "  手牌: 月亮井", "EDR_476" in hand,
        "龙息", "CATA_464t" in hand,
        "琥珀雏龙", "RLK_915" in hand,
    )
    try:
        face = lc.overlay_board_face_damage()
        _, _, has = lc.calculate_lethal_potential()
        pure, mn, _, sp, _ = lc.overlay_board_breakdown()
        print(f"  场攻={face} (随{mn}+法{sp}) 斩杀={has}")
    except Exception as exc:
        print(f"  场攻计算异常: {exc}")
