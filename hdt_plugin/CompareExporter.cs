/*
 * HS Compare Exporter — HDT 插件
 * 将对局状态写入 JSON，供 Python compare_hdt.py 与 Power.log 解析结果对比。
 *
 * 编译：见 README.md
 * 输出：%LocalAppData%\HSCompare\hdt_state.json
 */

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Windows.Controls;
using Hearthstone_Deck_Tracker;
using Hearthstone_Deck_Tracker.Enums;
using Hearthstone_Deck_Tracker.Hearthstone;
using Hearthstone_Deck_Tracker.Plugins;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace HSCompareExporter
{
    public class CompareExporter : IPlugin
    {
        private bool _enabled = true;
        private DateTime _lastWrite = DateTime.MinValue;
        private static readonly string OutputDir = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "HSCompare");
        private static readonly string OutputFile = Path.Combine(OutputDir, "hdt_state.json");

        public string Name => "HS Compare Exporter";
        public string Description => "导出场面 JSON 供 Python 斩杀工具与 HDT 对比";
        public string ButtonText => "打开输出目录";
        public string Author => "HS Lethal Tool";
        public Version Version => new Version(1, 0, 0);
        public MenuItem MenuItem => null;

        public void OnLoad()
        {
            _enabled = true;
            GameEvents.OnGameStart.Add(OnGameEvent);
            GameEvents.OnTurnStart.Add(OnTurnStart);
            GameEvents.OnInMenu.Add(OnInMenu);
        }

        public void OnUnload()
        {
            _enabled = false;
            GameEvents.OnGameStart.Remove(OnGameEvent);
            GameEvents.OnTurnStart.Remove(OnTurnStart);
            GameEvents.OnInMenu.Remove(OnInMenu);
        }

        public void OnButtonPress()
        {
            try
            {
                Directory.CreateDirectory(OutputDir);
                System.Diagnostics.Process.Start(OutputDir);
            }
            catch
            {
                // ignore
            }
        }

        public void OnUpdate()
        {
            if (!_enabled)
                return;
            if ((DateTime.Now - _lastWrite).TotalMilliseconds < 400)
                return;
            WriteState();
        }

        private void OnGameEvent() => WriteState();
        private void OnTurnStart(ActivePlayer player) => WriteState();

        private void OnInMenu()
        {
            WriteState(inMenu: true);
        }

        private void WriteState(bool inMenu = false)
        {
            if (!_enabled)
                return;

            try
            {
                var game = Core.Game;
                var root = new JObject
                {
                    ["source"] = "hdt",
                    ["timestamp"] = DateTime.Now.ToString("o"),
                    ["inGame"] = !inMenu && game != null && game.IsInGame,
                };

                if (inMenu || game == null || !game.IsInGame)
                {
                    root["isMyTurn"] = false;
                    root["player"] = EmptyPlayer();
                    root["opponent"] = EmptyOpponent();
                }
                else
                {
                    root["isMyTurn"] = game.IsInProgress && game.IsPlayerTurn;
                    root["turn"] = game.TurnCount;
                    root["player"] = ExportPlayer(game.Player, game);
                    root["opponent"] = ExportOpponent(game.Opponent);
                }

                Directory.CreateDirectory(OutputDir);
                File.WriteAllText(OutputFile, root.ToString(Formatting.Indented));
                _lastWrite = DateTime.Now;
            }
            catch
            {
                // HDT 会在对局外抛异常，静默忽略
            }
        }

        private static JObject EmptyPlayer()
        {
            return new JObject
            {
                ["hero"] = new JObject { ["health"] = 30, ["armor"] = 0, ["total"] = 30 },
                ["mana"] = 0,
                ["handCount"] = 0,
                ["board"] = new JArray(),
                ["boardFaceDamage"] = 0,
                ["boardMinionAttack"] = 0,
                ["boardWeaponAttack"] = 0,
            };
        }

        private static JObject EmptyOpponent()
        {
            return new JObject
            {
                ["hero"] = new JObject { ["health"] = 30, ["armor"] = 0, ["total"] = 30 },
                ["handCount"] = 0,
                ["board"] = new JArray(),
            };
        }

        private static JObject ExportPlayer(Player player, Game game)
        {
            var hero = player.Board.FirstOrDefault(c => c.IsHero);
            var minions = player.Board.Where(c => c.IsMinion).OrderBy(c => c.ZonePosition).ToList();
            var oppHasTaunt = game.Opponent.Board.Any(c => c.IsMinion && c.HasTaunt);

            int minionFace = 0;
            var board = new JArray();
            foreach (var c in minions)
            {
                var bc = new Hearthstone_Deck_Tracker.Utility.BoardDamage.BoardCard(c, activeTurn: true);
                bool canAttackHero = bc.Include && (!oppHasTaunt || bc.Taunt);
                if (canAttackHero)
                    minionFace += bc.Attack;

                board.Add(new JObject
                {
                    ["entityId"] = c.Id,
                    ["cardId"] = c.CardId ?? "",
                    ["attack"] = c.Attack,
                    ["health"] = c.Health,
                    ["zonePos"] = c.ZonePosition,
                    ["canAttack"] = bc.Include,
                    ["canAttackHero"] = canAttackHero,
                    ["taunt"] = c.HasTaunt,
                    ["exhausted"] = bc.Exhausted,
                });
            }

            int weaponFace = 0;
            JObject weapon = null;
            if (player.HasWeapon)
            {
                var w = player.WeaponCard;
                if (w != null)
                {
                    var heroCard = player.Board.FirstOrDefault(c => c.IsHero);
                    var boardHero = heroCard != null
                        ? new Hearthstone_Deck_Tracker.Utility.BoardDamage.BoardHero(heroCard, w, activeTurn: true)
                        : null;
                    bool wCanHero = boardHero != null && boardHero.Include
                        && (!oppHasTaunt || minions.Any(m =>
                        {
                            var bm = new Hearthstone_Deck_Tracker.Utility.BoardDamage.BoardCard(m, activeTurn: true);
                            return bm.Include && bm.Taunt;
                        }));
                    if (wCanHero)
                        weaponFace = boardHero?.Attack ?? 0;
                    weapon = new JObject
                    {
                        ["cardId"] = w.CardId ?? "",
                        ["attack"] = w.Attack,
                        ["durability"] = w.Health,
                    };
                }
            }

            return new JObject
            {
                ["hero"] = HeroJson(hero),
                ["mana"] = player.Mana,
                ["manaUsed"] = player.ManaUsed,
                ["handCount"] = player.HandCount,
                ["weapon"] = weapon ?? JValue.CreateNull(),
                ["board"] = board,
                ["boardMinionAttack"] = minionFace,
                ["boardWeaponAttack"] = weaponFace,
                ["boardFaceDamage"] = minionFace + weaponFace,
            };
        }

        private static JObject ExportOpponent(Player opponent)
        {
            var hero = opponent.Board.FirstOrDefault(c => c.IsHero);
            var board = new JArray(
                opponent.Board
                    .Where(c => c.IsMinion)
                    .OrderBy(c => c.ZonePosition)
                    .Select(c => new JObject
                    {
                        ["entityId"] = c.Id,
                        ["cardId"] = c.CardId ?? "",
                        ["attack"] = c.Attack,
                        ["health"] = c.Health,
                        ["zonePos"] = c.ZonePosition,
                        ["canAttack"] = c.CanAttack,
                        ["canAttackHero"] = false,
                        ["taunt"] = c.HasTaunt,
                        ["exhausted"] = c.IsExhausted,
                    }));

            return new JObject
            {
                ["hero"] = HeroJson(hero),
                ["handCount"] = opponent.HandCount,
                ["board"] = board,
            };
        }

        private static JObject HeroJson(Card hero)
        {
            int health = hero?.Health ?? 30;
            int armor = hero?.Armor ?? 0;
            return new JObject
            {
                ["health"] = health,
                ["armor"] = armor,
                ["total"] = health + armor,
            };
        }
    }
}
