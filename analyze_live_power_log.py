#!/usr/bin/env python3
"""分析注册表定位到的最新 Power.log（与 hdt_tracker 相同逻辑）"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.log_watcher import find_power_log_path, _registry_install_dirs, _power_log_candidates
from hdt_python.player_identity import format_identity_summary
from hdt_python.power_parser import PowerLogParser, GameState, find_last_game_replay_start
from hdt_python.lethal_checker import LethalChecker


def list_log_sessions():
    install_dirs = _registry_install_dirs()
    print("=== 注册表安装目录 ===")
    for d in install_dirs:
        print(f"  {d}")
    sessions = _power_log_candidates(install_dirs)
    sessions.sort(key=os.path.getmtime, reverse=True)
    print("\n=== Power.log 会话（新→旧）===")
    for power in sessions:
        from datetime import datetime
        mtime = os.path.getmtime(power)
        size = os.path.getsize(power)
        ts = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {power}  ({size // 1024} KB, 修改: {ts})")
    return sessions


def parse_last_game(power_log: str):
    gs = GameState()
    parser = PowerLogParser(power_log, gs)

    with open(power_log, "r", encoding="utf-8", errors="ignore") as f:
        all_lines = f.readlines()

    start = find_last_game_replay_start(all_lines)
    if start < 0:
        start = 0

    print(f"\n=== 解析: {power_log} ===")
    print(f"总行数: {len(all_lines)}, 最后一局从第 {start + 1} 行开始（含 DebugPrintGame 前缀）")

    for line in all_lines[start:]:
        line = line.rstrip("\n\r")
        if line:
            parser.process_line(line)

    hero_ids = {}
    for pid in (gs.local_player_id, gs.opponent_player_id):
        if pid:
            h = gs.get_hero(pid)
            if h and h.card_id:
                hero_ids[pid] = h.card_id

    print(format_identity_summary(
        gs.local_player_id,
        gs.opponent_player_id,
        gs.player_names,
        hero_ids,
        gs.local_player_identity_source or "",
    ))

    if not gs.local_player_id:
        print("未能识别我方玩家")
        return

    board = gs.get_board(gs.local_player_id)
    print(f"\n我方场面 ({len(board)} 个随从):")
    total = 0
    for m in board:
        dmg = m.board_attack_damage
        total += dmg
        print(
            f"  [{('攻' if m.can_attack else 'x')}] "
            f"{m.card_id or '未知'} {m.atk}/{m.current_health} "
            f"EXHAUSTED={m.tags.get('EXHAUSTED')} tag1196={m.tags.get('1196')} "
            f"剩余攻击={m.remaining_attacks}/{m.max_attacks} 场攻贡献={dmg}"
        )
    print(f"\n场攻合计: {total}")

    lc = LethalChecker(gs)
    t, sources, lethal = lc.calculate_lethal()
    board_from_lethal = sum(s.damage for s in sources if s.source_type == "board")
    print(f"斩杀器场面伤害: {board_from_lethal}, 总伤害: {t}, 有斩杀: {lethal}")


def main():
    list_log_sessions()

    power_log = find_power_log_path()
    print(f"\nfind_power_log_path() 选中: {power_log}")

    if power_log:
        parse_last_game(power_log)


if __name__ == "__main__":
    main()
