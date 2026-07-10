#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import (
    board_active_turn_for_display, is_exhausted, is_players_turn, build_board_card,
)

log = sys.argv[1]
target = int(sys.argv[2])
gs = GameState()
p = PowerLogParser(log, gs)
with open(log, encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
starts = [i for i,l in enumerate(lines) if 'CREATE_GAME' in l and 'GameState.DebugPrintPower' in l]
start = max((s for s in starts if s < target), default=starts[0])
for i in range(start, target):
    p.process_line(lines[i])
pid = gs.local_player_id or 1
active = board_active_turn_for_display(gs, pid)
print('line', target, 'my_turn', is_players_turn(gs, pid), 'active_pid', gs.active_player_id, 'board_active', active)
lc = LethalChecker(gs)
print('overlay', lc.overlay_board_face_damage(), lc.overlay_board_breakdown())
for m in gs.get_board(pid):
    v = build_board_card(m, active, gs)
    print(
        m.card_id, 'atk', v.std_attack, 'ex', is_exhausted(m),
        'EXHAUSTED tag', m.tags.get('EXHAUSTED'),
        'can_hero', v.can_attack_hero, 'attack dmg', v.attack,
        'pure_board', gs.get_overlay_board(pid).damage,
    )
opp_taunts = [x for x in gs.get_board(2) if x.tags.get('TAUNT')]
print('opp taunts', len(opp_taunts))
