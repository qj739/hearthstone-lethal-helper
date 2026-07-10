# HDT_Integration.py - 与 Hearthstone Deck Tracker 集成
# 这是最实用的方案！

"""
方案说明：
Hearthstone Deck Tracker (HDT) 已经完成了所有内存读取工作。
我们可以通过以下方式获取它的数据：

1. 读取 HDT 的内存映射文件（如果启用）
2. 开发 HDT 插件（C#）然后通过IPC与Python通信
3. 使用 HDT 的 API 端点（某些插件提供）

推荐方案：开发简单的 HDT 插件，导出数据给 Python
"""

import json
import mmap
import struct
import time
from typing import Optional, Dict, List

class HDTMemoryReader:
    """
    读取 HDT 通过内存映射文件共享的游戏状态

    使用步骤：
    1. 安装 HDT: https://hsreplay.net/downloads/
    2. 创建 HDT 插件（见下方 C# 代码）
    3. 插件将游戏状态写入共享内存
    4. Python 从共享内存读取
    """

    def __init__(self, map_name: str = "HearthstoneGameState"):
        self.map_name = map_name
        self.mmf = None

    def connect(self) -> bool:
        """连接到共享内存"""
        try:
            # 尝试打开已存在的内存映射文件
            self.mmf = mmap.mmap(-1, 1024 * 1024, self.map_name)  # 1MB
            return True
        except Exception as e:
            print(f"无法连接到共享内存: {e}")
            print("请确保 HDT 插件正在运行")
            return False

    def read_game_state(self) -> Optional[Dict]:
        """从共享内存读取游戏状态（JSON格式）"""
        if not self.mmf:
            return None

        try:
            self.mmf.seek(0)
            # 读取数据长度（前4字节）
            length_bytes = self.mmf.read(4)
            if not length_bytes:
                return None

            length = struct.unpack('I', length_bytes)[0]
            if length == 0 or length > 1024 * 1024:
                return None

            # 读取JSON数据
            json_bytes = self.mmf.read(length)
            json_str = json_bytes.decode('utf-8')
            return json.loads(json_str)
        except Exception as e:
            print(f"读取失败: {e}")
            return None

    def close(self):
        """关闭连接"""
        if self.mmf:
            self.mmf.close()


class HDTFileReader:
    """
    读取 HDT 导出的状态文件

    这是最简单的方案！
    创建一个 HDT 插件，每次游戏状态更新时写入 JSON 文件
    Python 程序监控并读取这个文件
    """

    def __init__(self, state_file: str = "hdt_state.json"):
        self.state_file = state_file
        self.last_modified = 0

    def read_state(self) -> Optional[Dict]:
        """读取状态文件"""
        try:
            import os
            # 检查文件是否更新
            mtime = os.path.getmtime(self.state_file)
            if mtime <= self.last_modified:
                return None  # 没有更新

            self.last_modified = mtime

            with open(self.state_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"状态文件不存在: {self.state_file}")
            print("请启动 HDT 插件")
            return None
        except Exception as e:
            print(f"读取失败: {e}")
            return None


# --------------------------
# HDT 插件示例代码（C#）
# --------------------------

HDT_PLUGIN_CODE = """
/*
HDT 插件代码 (C#)
保存为: HearthstoneStateExporter.cs

编译步骤:
1. 创建 .NET Framework 4.5+ 类库项目
2. 添加 NuGet 包: HearthstoneDeckTracker
3. 将此代码放入项目
4. 编译生成 DLL
5. 将 DLL 放到 HDT 的 Plugins 目录

这个插件会将游戏状态导出为 JSON 文件
*/

using System;
using System.IO;
using System.Text;
using Hearthstone_Deck_Tracker.API;
using Hearthstone_Deck_Tracker.Enums;
using Hearthstone_Deck_Tracker.Hearthstone;
using Newtonsoft.Json;

namespace HearthstoneStateExporter
{
    public class StateExporter
    {
        private const string OUTPUT_FILE = "hdt_state.json";

        public StateExporter()
        {
            // 订阅游戏状态更新事件
            GameEvents.OnGameStart.Add(OnGameStart);
            GameEvents.OnTurnStart.Add(OnTurnStart);
            GameEvents.OnInMenu.Add(OnInMenu);
        }

        private void OnGameStart()
        {
            UpdateState();
        }

        private void OnTurnStart(ActivePlayer player)
        {
            UpdateState();
        }

        private void OnInMenu()
        {
            // 游戏结束，清空状态
        }

        private void UpdateState()
        {
            try
            {
                var game = Core.Game;
                if (game == null) return;

                var state = new
                {
                    Timestamp = DateTime.Now,

                    // 玩家信息
                    Player = new
                    {
                        Health = game.Player.Board.FirstOrDefault(c => c.IsHero)?.Health ?? 30,
                        Armor = game.Player.Board.FirstOrDefault(c => c.IsHero)?.Armor ?? 0,
                        Mana = game.Player.Mana,
                        Hand = game.Player.Hand.Select(c => new
                        {
                            CardId = c.CardId,
                            Cost = c.Cost,
                            Name = c.Name
                        }),
                        Board = game.Player.Board.Where(c => c.IsMinion).Select(c => new
                        {
                            CardId = c.CardId,
                            Attack = c.Attack,
                            Health = c.Health,
                            CanAttack = c.CanAttack,
                            HasCharge = c.HasCharge,
                            HasTaunt = c.HasTaunt
                        })
                    },

                    // 对手信息
                    Opponent = new
                    {
                        Health = game.Opponent.Board.FirstOrDefault(c => c.IsHero)?.Health ?? 30,
                        Armor = game.Opponent.Board.FirstOrDefault(c => c.IsHero)?.Armor ?? 0,
                        HandCount = game.Opponent.HandCount,
                        Board = game.Opponent.Board.Where(c => c.IsMinion).Select(c => new
                        {
                            CardId = c.CardId,
                            Attack = c.Attack,
                            Health = c.Health,
                            HasTaunt = c.HasTaunt
                        })
                    }
                };

                // 写入 JSON 文件
                string json = JsonConvert.SerializeObject(state, Formatting.Indented);
                File.WriteAllText(OUTPUT_FILE, json, Encoding.UTF8);
            }
            catch (Exception ex)
            {
                // Log error
                Console.WriteLine($"Error exporting state: {ex}");
            }
        }
    }
}
"""


def main():
    print("HDT 集成方案演示\n")
    print("=" * 60)
    print("方案1: 文件读取（推荐，最简单）")
    print("  - 创建 HDT 插件导出 JSON 文件")
    print("  - Python 读取文件获取游戏状态")
    print()
    print("方案2: 共享内存")
    print("  - 更快，但实现复杂")
    print("=" * 60)

    # 尝试文件读取方案
    reader = HDTFileReader("hdt_state.json")

    print("\n等待 HDT 状态文件...")
    print("(需要先安装 HDT 插件)\n")

    last_state = None
    while True:
        state = reader.read_state()
        if state and state != last_state:
            print("\n" + "=" * 60)
            print("游戏状态更新:")
            print(json.dumps(state, indent=2, ensure_ascii=False))
            print("=" * 60)

            # 斩杀检测示例
            if "Player" in state and "Opponent" in state:
                my_board_atk = sum(m.get("Attack", 0) for m in state["Player"].get("Board", []))
                opp_hp = state["Opponent"].get("Health", 30) + state["Opponent"].get("Armor", 0)

                print(f"\n我方场面攻击: {my_board_atk}")
                print(f"对手总血量: {opp_hp}")

                if my_board_atk >= opp_hp:
                    print("\n⚔️ 有斩杀！⚔️")

            last_state = state

        time.sleep(0.5)


if __name__ == "__main__":
    print("HDT 插件代码已保存在变量中")
    print("查看 HDT_PLUGIN_CODE 变量获取 C# 代码\n")

    # 保存 C# 代码到文件
    with open("HDT_Plugin_Code.cs", "w", encoding="utf-8") as f:
        f.write(HDT_PLUGIN_CODE)
    print("已保存 HDT 插件代码到: HDT_Plugin_Code.cs\n")

    # main()  # 取消注释以运行
    print("使用说明:")
    print("1. 编译 HDT_Plugin_Code.cs 为 DLL")
    print("2. 将 DLL 放到 HDT 的 Plugins 文件夹")
    print("3. 启动 HDT 和炉石传说")
    print("4. 运行此 Python 脚本: python tools/hdt_integration.py")
