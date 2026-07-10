import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from analyze_user_logs_lethal import parse_to_line, lethal_snapshot
from hdt_python.lethal_checker import LethalChecker

LOG = Path(
    r"C:\Users\hp\Desktop\LOGS(1)\LOGS\split_games"
    r"\Hearthstone_2026_06_15_23_18_06\game_02.log"
)
lines = LOG.read_text(encoding="utf-8", errors="replace").splitlines()
label = str(LOG)

checkpoints = [
    (15438, "回合初"),
    (17200, "破嘲后"),
    (18577, "克洛诺戈尔打脸结算后"),
    (18623, "打脸后选项刷新"),
    (19034, "结束回合前"),
    (19151, "对手回合初"),
    (19764, "投降前"),
]
for ln, name in checkpoints:
    gs = parse_to_line(lines, label, ln + 1)
    opp = gs.opponent_player_id
    h = gs.get_hero(opp)
    lc = LethalChecker(gs)
    s = lethal_snapshot(gs)
    _, _, pot_lethal = lc.calculate_lethal_potential()
    hp, armor, total = lc.get_opponent_health()
    print(
        f"{name} L{ln+1}: turn={lc.is_local_turn()} "
        f"hero {h.card_id} cur={h.current_health} dmg_tag={h.tags.get('DAMAGE',0)} armor={armor} "
        f"eff_hp={s.opp_hp} overlay={s.overlay} lethal={s.lethal} pot_lethal={pot_lethal} note={s.note!r}"
    )
