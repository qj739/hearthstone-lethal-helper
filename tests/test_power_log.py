#!/usr/bin/env python3
# test_power_log.py - 测试 Power.log 解析

"""
直接读取 Power.log 并测试解析
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from hdt_python.power_parser import PowerLogParser, GameState


def test_power_log():
    """测试解析 Power.log"""

    log_file = "Power.log"

    if not Path(log_file).exists():
        print(f"❌ 找不到文件: {log_file}")
        return

    print("=" * 60)
    print("测试 Power.log 解析")
    print("=" * 60)

    # 创建游戏状态和解析器
    game_state = GameState()
    parser = PowerLogParser(log_file, game_state)

    # 读取文件并逐行处理
    print(f"\n读取文件: {log_file}\n")

    with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
        lines = f.readlines()

    print(f"总行数: {len(lines)}")
    print("开始解析...\n")

    # 处理全部行
    for i, line in enumerate(lines):
        line = line.rstrip('\n\r')
        if line:
            parser.process_line(line)

    # 输出结果
    print("\n" + "=" * 60)
    print("解析结果")
    print("=" * 60)
    print(f"处理行数: {parser.lines_processed}")
    print(f"实体总数: {len(game_state.entities)}")
    print(f"我方玩家ID: {game_state.local_player_id}")
    print(f"对手玩家ID: {game_state.opponent_player_id}")
    print(f"控制器: {game_state.seen_controllers}")

    # 显示玩家信息
    if game_state.local_player_id:
        print(f"\n✅ 成功识别我方玩家: {game_state.local_player_id}")

        # 显示手牌
        my_hand = game_state.get_hand(game_state.local_player_id)
        print(f"\n我方手牌 ({len(my_hand)} 张):")
        for card in my_hand[:10]:
            print(f"  ID={card.entity_id} CardID={card.card_id or '未知'} Cost={card.cost}")

        # 显示场面
        my_board = game_state.get_board(game_state.local_player_id)
        print(f"\n我方场面 ({len(my_board)} 个随从):")
        for minion in my_board:
            print(f"  ID={minion.entity_id} CardID={minion.card_id or '未知'} {minion.atk}/{minion.current_health}")
    else:
        print("\n❌ 未能识别玩家")
        print("可能原因:")
        print("  1. 日志格式解析问题")
        print("  2. 需要更多行数据")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_power_log()
