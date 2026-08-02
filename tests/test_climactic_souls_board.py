#!/usr/bin/env python3
"""通灵最强音召唤的死忠歌迷不应被 PowerTaskList 的 SETASIDE 括号卡出场面。"""
import io
import contextlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from hdt_python.power_parser import GameState, PowerLogParser
from hdt_python.lethal_checker import LethalChecker

LOG = Path(
    r"C:\Program Files (x86)\Hearthstone\Logs"
    r"\Hearthstone_2026_07_31_22_51_53\Power.log"
)
# 打出 ETC_210 后下一回合 MAIN_ACTION
TARGET = 306920


def test_climactic_souls_stay_on_board_next_turn():
    lines = LOG.read_text(encoding="utf-8", errors="ignore").splitlines()
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    with contextlib.redirect_stdout(io.StringIO()):
        for i in range(TARGET):
            if lines[i].strip():
                p.process_line(lines[i].rstrip())

    fans = [
        m for m in gs.get_board(gs.local_player_id)
        if m.card_id == "ETC_522t"
    ]
    assert len(fans) >= 5, (
        f"expected >=5 Die-Hard Fans on board, got {len(fans)}; "
        f"board={[ (m.entity_id, m.card_id, m.zone) for m in gs.get_board(gs.local_player_id) ]}; "
        f"fans_zone={[(eid, gs.entities[eid].zone) for eid in range(222,227) if eid in gs.entities]}"
    )
    for f in fans:
        assert f.atk >= 5, (f.entity_id, f.atk)
        assert f.zone == "PLAY"

    lc = LethalChecker(gs)
    face = lc.overlay_board_face_damage()
    total, _, has = lc.calculate_lethal_potential()
    # 5×5 歌迷清 26 血嘲讽后仍有剩余打脸；对手 16 血时应亮斩
    assert face >= 10, (face, lc.overlay_board_breakdown(), lc.overlay_spell_note())
    assert has or total >= 16, (face, total, has, lc.overlay_spell_note())
    print("OK climactic souls on board", len(fans), "face", face, "lethal", has)


if __name__ == "__main__":
    test_climactic_souls_stay_on_board_next_turn()
