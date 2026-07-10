#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.board_damage import (
    is_exhausted, _num_turns_in_play, _minion_summoned_this_turn, attacks_this_turn,
)

log, target = sys.argv[1], int(sys.argv[2])
gs = GameState()
p = PowerLogParser(log, gs)
with open(log, encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()
starts = [i for i, l in enumerate(lines) if 'CREATE_GAME' in l and 'GameState.DebugPrintPower' in l]
start = starts[-1] if (target - 1) > starts[-1] else starts[0]
for i in range(start, target):
    p.process_line(lines[i])
pid = gs.local_player_id or 1
for m in gs.get_board(pid):
    print(
        m.card_id,
        'EXHAUSTED', m.tags.get('EXHAUSTED'),
        'NUM_TURNS', m.tags.get('NUM_TURNS_IN_PLAY'),
        'num_turns_fn', _num_turns_in_play(m),
        '1196', m.tags.get('1196'),
        'summoned', _minion_summoned_this_turn(m),
        'used', attacks_this_turn(m),
        'ex', is_exhausted(m),
    )
