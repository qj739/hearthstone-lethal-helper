#!/usr/bin/env python3
# test_overlay.py - 测试覆盖层窗口

"""
测试覆盖层显示效果（不需要炉石传说运行）
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from overlay_win import Overlay


def test_overlay_basic():
    """基础测试：白底模式"""
    print("=" * 60)
    print("测试 1: 基础覆盖层（白底黑字）")
    print("=" * 60)

    overlay = Overlay(title_hint="炉石传说", use_layered=False, opacity=220)
    overlay.start()

    print("覆盖层已启动")
    print("你应该看到一个白色窗口显示在屏幕左上角")
    print()

    # 模拟不同场景
    scenarios = [
        {
            "name": "等待数据",
            "text": "等待游戏数据...",
            "duration": 2
        },
        {
            "name": "正常对局",
            "text": "场攻: 7\n我方: 25+2血 | 对手: 18+0血\n总伤害: 13 / 18  (还差5)",
            "duration": 3
        },
        {
            "name": "接近斩杀",
            "text": "场攻: 8\n我方: 20+0血 | 对手: 10+2血\n总伤害: 11 / 12  (还差1)",
            "duration": 3
        },
        {
            "name": "有斩杀！",
            "text": "场攻: 8\n我方: 20+0血 | 对手: 10+0血\n⚔️ 斩杀！总伤 12 >= 10 ⚔️",
            "duration": 4
        },
        {
            "name": "对手有嘲讽",
            "text": "场攻: 8 [对手有2个嘲讽]\n我方: 22+0血 | 对手: 15+5血\n总伤害: 12 / 20  (还差8)",
            "duration": 3
        },
    ]

    for i, scenario in enumerate(scenarios, 1):
        print(f"[{i}/{len(scenarios)}] 场景: {scenario['name']}")
        overlay.set_text(scenario['text'])
        time.sleep(scenario['duration'])

    print("\n测试完成！")
    print("按 Ctrl+C 退出...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在关闭...")
        overlay.stop()
        print("已关闭")


def test_overlay_layered():
    """测试：半透明模式"""
    print("=" * 60)
    print("测试 2: 半透明覆盖层")
    print("=" * 60)

    overlay = Overlay(title_hint="炉石传说", use_layered=True, opacity=220)
    overlay.start()

    print("半透明覆盖层已启动")
    print("你应该看到一个透明背景、绿色文字的窗口")
    print()

    # 显示斩杀场景
    print("显示斩杀场景...")
    overlay.set_text("场攻: 10\n我方: 25+5血 | 对手: 8+0血\n⚔️ 斩杀！总伤 15 >= 8 ⚔️")

    print("\n测试将持续 10 秒...")
    print("按 Ctrl+C 可提前退出")

    try:
        for i in range(10, 0, -1):
            print(f"\r剩余 {i} 秒...", end="", flush=True)
            time.sleep(1)
        print("\r测试完成！     ")
    except KeyboardInterrupt:
        print("\n\n用户中断")

    overlay.stop()
    print("已关闭")


def test_overlay_with_game():
    """测试：检测炉石窗口"""
    print("=" * 60)
    print("测试 3: 炉石窗口检测")
    print("=" * 60)

    overlay = Overlay(title_hint="炉石传说", use_layered=False, opacity=220)

    # 测试窗口检测
    print("正在检测炉石传说窗口...")
    hs_hwnd = overlay._find_hs_window()

    if hs_hwnd:
        print(f"✅ 找到炉石窗口！句柄: {hs_hwnd}")
        rect = overlay._get_window_rect(hs_hwnd)
        print(f"   窗口位置: ({rect.left}, {rect.top})")
        print(f"   窗口大小: {rect.right - rect.left} x {rect.bottom - rect.top}")
        print("\n启动覆盖层...")
        overlay.start()
        overlay.set_text("场攻: 5\n我方: 30+0血 | 对手: 30+0血\n总伤害: 5 / 30  (还差25)")
        print("覆盖层应该显示在炉石窗口左上角")
        print("\n按 Ctrl+C 退出...")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        overlay.stop()
    else:
        print("❌ 未找到炉石传说窗口")
        print("\n可能原因：")
        print("  1. 炉石传说未启动")
        print("  2. 窗口标题不是'炉石传说'（可能是英文版）")
        print("\n解决方案：")
        print("  1. 启动炉石传说")
        print("  2. 如使用英文客户端，修改 title_hint 参数")


def main():
    """主菜单"""
    print("\n" + "🎮" * 30)
    print("覆盖层窗口测试工具")
    print("🎮" * 30 + "\n")

    print("选择测试模式：")
    print("  1. 基础测试（白底黑字，演示多个场景）")
    print("  2. 半透明测试（透明背景，绿色文字）")
    print("  3. 炉石窗口检测测试")
    print("  4. 运行所有测试")
    print()

    choice = input("请选择 (1-4): ").strip()

    if choice == "1":
        test_overlay_basic()
    elif choice == "2":
        test_overlay_layered()
    elif choice == "3":
        test_overlay_with_game()
    elif choice == "4":
        print("\n运行所有测试...\n")
        test_overlay_with_game()
        print("\n" + "=" * 60 + "\n")
        time.sleep(1)
        test_overlay_basic()
        print("\n" + "=" * 60 + "\n")
        time.sleep(1)
        test_overlay_layered()
    else:
        print("无效选择")
        return

    print("\n测试结束！")


if __name__ == "__main__":
    main()
