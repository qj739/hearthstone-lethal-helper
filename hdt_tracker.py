#!/usr/bin/env python3
# hdt_tracker.py - HDT风格的炉石传说辅助工具
# 仿照 Hearthstone Deck Tracker 的实现方式

"""
使用方法:
1. 确保炉石传说已启动
2. 运行: python hdt_tracker.py
3. 工具会自动监控游戏日志并检测斩杀机会
4. 浮层菜单栏「设置」可打开配置面板；右上角 × 可隐藏浮层

首次运行会自动安装 log.config 配置文件
"""

import os
import re
import sys
import time
from pathlib import Path


def _configure_stdio() -> None:
    """Windows 控制台默认常为 GBK，emoji/部分中文 print 会 UnicodeEncodeError 导致 EXE 闪退。"""
    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if stream is None:
            continue
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
            continue
        except Exception:
            pass
        try:
            import io

            buf = getattr(stream, "buffer", None)
            if buf is None:
                continue
            setattr(
                sys,
                name,
                io.TextIOWrapper(buf, encoding="utf-8", errors="replace", line_buffering=True),
            )
        except Exception:
            pass


_configure_stdio()

from hdt_python.app_paths import is_frozen, user_data_dir
from hdt_python.player_identity import format_identity_summary

if not is_frozen():
    sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.log_watcher import LogWatcherManager, find_power_log_path, install_log_config
from hdt_python.board_damage import board_active_turn_for_display, living_taunt_minions
from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker, MIN_LETHAL_PROMPT_PROB
from hdt_python.arena_season_bulk import register_arena_season_gap

register_arena_season_gap()
from hdt_python.spell_board import spell_script_damage
from hdt_python.state_snapshot import export_game_state
from hdt_python.hdt_compare import (
    find_hdt_state_file,
    load_hdt_state,
    compare_states,
    format_compare_report,
)
from hdt_python.overlay_settings import OverlaySettings, OverlaySettingsStore
from overlay_win import ComboOverlay, Overlay


def _has_combo_action_steps(lines: list[str]) -> bool:
    return any(re.match(r"^\d+\.\s", ln.strip()) for ln in lines)


class HearthstoneTracker:
    """
    炉石传说追踪器主类
    整合所有功能
    """

    def __init__(
        self,
        use_overlay=True,
        use_layered=False,
        compare_hdt=False,
        attach_overlay=True,
        overlay_settings: OverlaySettings | None = None,
        settings_store: OverlaySettingsStore | None = None,
    ):
        self.game_state = GameState()
        self.log_manager: LogWatcherManager = None
        self.power_parser: PowerLogParser = None
        self.lethal_checker: LethalChecker = None
        self.last_lethal_check = False
        self._overlay_dirty = True
        self._console_dirty = True
        self._force_immediate_overlay = False
        self.compare_hdt = compare_hdt
        self._hdt_state_path = find_hdt_state_file() if compare_hdt else None
        self._last_hdt_issues: tuple = ()
        self._last_hdt_compare = 0.0
        self._replay_ready = False  # Power.log 历史回放完成前不显示场面/斩杀
        self.settings_store = settings_store or OverlaySettingsStore()
        self.overlay_settings = overlay_settings or self.settings_store.settings

        # 影响场面/攻击/斩杀的标签
        self._overlay_tags = {
            "ZONE", "ATK", "479", "4472", "HEALTH", "DAMAGE", "DURABILITY", "EXHAUSTED",
            "NUM_ATTACKS_THIS_TURN", "NUM_TURNS_IN_PLAY", "RESOURCES", "1196", "JUST_PLAYED",
            "TAG_SCRIPT_DATA_NUM_1", "CARDTYPE", "FROZEN", "CANT_ATTACK",
            "WINDFURY", "MEGA_WINDFURY", "MAX_NUM_ATTACKS", "CHARGE", "RUSH",
            "ATTACKABLE_BY_RUSH", "ARMOR", "MAIN_HAND_WEAPON_ENTITY", "TURN", "CURRENT_PLAYER",
            "FIRST_PLAYER", "DORMANT", "DORMANT_AWAKEN_CONDITION_ENCHANT",
            "DORMANT_AWAKENED_THIS_TURN", "UNTOUCHABLE",
            "SCORE_VALUE_1", "SCORE_VALUE_2", "ATTACHED",
            "AURA", "INFUSED",
            "TITAN", "SILENCED", "HIDE_STATS", "TAUNT",
            "LOCATION_ACTION_COOLDOWN", "POWERED_UP", "COMBO_ACTIVE",
        }

        self.attach_overlay = attach_overlay
        cfg = self.overlay_settings
        # 窗口覆盖层
        self.use_overlay = use_overlay
        self.overlay: Overlay = None
        self.combo_overlay: ComboOverlay = None
        if use_overlay:
            self.overlay = Overlay(
                title_hint="炉石传说",
                use_layered=cfg.use_layered,
                opacity=cfg.opacity,
                attach_to_game=cfg.attach_to_game,
            )
            self.overlay.apply_settings(cfg)
            self.combo_overlay = ComboOverlay(
                title_hint="炉石传说",
                use_layered=cfg.use_layered,
                opacity=min(255, cfg.opacity + 15),
                anchor_overlay=self.overlay,
                attach_to_game=cfg.attach_to_game,
            )
            self.combo_overlay.apply_settings(cfg)
            self.settings_store.on_change(self._on_overlay_settings_changed)
            self.overlay.set_action_callbacks(
                on_settings=self._open_overlay_settings,
                on_close=self._on_overlay_close,
            )

    def _open_overlay_settings(self) -> None:
        from overlay_settings_ui import open_settings_dialog_async
        open_settings_dialog_async(
            self.settings_store,
            on_apply=self._on_overlay_settings_changed,
        )

    def _on_overlay_close(self) -> None:
        if self.combo_overlay:
            self.combo_overlay.hide()

    def _on_overlay_settings_changed(self, settings: OverlaySettings) -> None:
        self.overlay_settings = settings
        if self.overlay:
            self.overlay.apply_settings(settings)
        if self.combo_overlay:
            self.combo_overlay.apply_settings(settings)
        self._force_immediate_overlay = True
        self._overlay_dirty = True

    def setup(self) -> bool:
        """设置追踪器"""
        print("=" * 60)
        print("HDT风格的炉石传说辅助工具")
        print("仿照 Hearthstone Deck Tracker 实现")
        if self.compare_hdt:
            if self._hdt_state_path:
                print(f"HDT 对比已启用: {self._hdt_state_path}")
            else:
                print("HDT 对比已启用，但未找到 hdt_state.json（请先安装 HS Compare Exporter 插件）")
        print("=" * 60)

        # 1. 安装 log.config
        print("\n[1/3] 检查 log.config...")
        install_log_config()

        # 2. 查找日志目录
        print("\n[2/3] 查找炉石传说日志...")
        power_log = find_power_log_path()
        if not power_log:
            print("\n❌ 错误: 找不到 Power.log")
            print("请确保:")
            print("  1. 炉石传说已通过 Battle.net 正常安装")
            print("  2. 至少启动过一次游戏（并启用 Power 日志）")
            return False

        log_dir = os.path.dirname(power_log)

        # 3. 设置日志监控
        print("\n[3/3] 设置日志监控器...")
        self.log_manager = LogWatcherManager(log_dir)
        self.power_parser = PowerLogParser(power_log, self.game_state)
        self.log_manager.register_watcher("Power", self.power_parser)

        # 斩杀检测器
        self.lethal_checker = LethalChecker(self.game_state)

        # 注册事件处理器
        self._setup_event_handlers()
        self.power_parser.add_callback(self._on_power_log_line)

        print("\n✅ 设置完成！（我方 PlayerID 由 DebugPrintGame / FRIENDLY_PLAYER 自动识别，无需配置）")
        return True

    def _setup_event_handlers(self):
        """设置事件处理器"""

        def on_tag_changed(entity, tag, value):
            if tag in self._overlay_tags:
                self._overlay_dirty = True
            if tag in (
                "ZONE", "NUM_ATTACKS_THIS_TURN", "RESOURCES", "EXHAUSTED",
                "ATK", "479", "HEALTH", "DAMAGE", "1196", "JUST_PLAYED",
                "TURN", "CURRENT_PLAYER",
            ):
                self._console_dirty = True
            if tag == "COMBO_ACTIVE":
                self._invalidate_lethal_overlay(immediate=True)
            elif tag == "DAMAGE":
                opp = self.game_state.opponent_player_id
                hero_ids = self.game_state.hero_entity_ids
                if opp and hero_ids.get(opp) == getattr(entity, "entity_id", None):
                    self._invalidate_lethal_overlay(immediate=True)
            immediate = tag in (
                "EXHAUSTED", "NUM_ATTACKS_THIS_TURN", "1196", "JUST_PLAYED",
                "TURN", "CURRENT_PLAYER", "POWERED_UP", "COMBO_ACTIVE", "DAMAGE",
            )
            if immediate and (
                tag in ("TURN", "CURRENT_PLAYER", "COMBO_ACTIVE", "DAMAGE")
                or self._entity_affects_local_board(entity)
            ):
                self._invalidate_lethal_overlay(immediate=True)

        self.power_parser.on("tag_changed", on_tag_changed)
        self.power_parser.on("entity_created", self._on_entity_created)
        self.power_parser.on("entity_updated", self._on_entity_updated)
        self.power_parser.on("change_entity", self._on_change_entity)
        self.power_parser.on("entity_transform_ready", self._on_entity_transform_ready)
        self.power_parser.on("game_start", self._on_game_start)
        self.power_parser.on("game_end", self._on_game_end)

    def _on_power_log_line(self, _line: str) -> None:
        """Power.log 有新行写入时才标脏，避免空闲时反复重算斩杀。"""
        self._overlay_dirty = True
        self._console_dirty = True

    def _entity_affects_local_board(self, entity) -> bool:
        if entity is None:
            return False
        if entity.zone != "PLAY":
            return False
        local = self.game_state.local_player_id
        if local is None:
            return True
        return self.game_state.is_entity_controlled_by(entity, local)

    def _on_entity_updated(self, entity):
        self._overlay_dirty = True
        if self._entity_affects_local_board(entity):
            self._invalidate_lethal_overlay(immediate=True)

    def _invalidate_lethal_overlay(self, *, immediate: bool = False) -> None:
        if self.lethal_checker:
            self.lethal_checker.clear_overlay_cache()
        self._overlay_dirty = True
        self._console_dirty = True
        if immediate:
            self._force_immediate_overlay = True

    def _on_entity_created(self, entity):
        """新实体（含未知手牌、英雄技能 token 落场）立即标脏。"""
        from hdt_python.board_damage import entity_zone

        if entity is None:
            return
        local = self.game_state.local_player_id
        if local is None:
            return
        zone = entity_zone(entity)
        if zone in ("HAND", "PLAY") and self.game_state.is_entity_controlled_by(entity, local):
            self._invalidate_lethal_overlay(immediate=True)

    def _on_change_entity(self, entity):
        """CHANGE_ENTITY：先清缓存；完整属性在 entity_transform_ready 后再刷新。"""
        if not self._entity_affects_local_board(entity):
            return
        self._invalidate_lethal_overlay(immediate=False)

    def _on_entity_transform_ready(self, entity):
        """变形属性就绪（含回合结束随从）：立即重算场攻/斩杀。"""
        if not self._entity_affects_local_board(entity):
            return
        self._invalidate_lethal_overlay(immediate=True)

    def _on_game_start(self):
        self.last_lethal_check = False
        if self.lethal_checker:
            self.lethal_checker.clear_overlay_cache()
        self._overlay_dirty = True
        self._console_dirty = True

    def _on_game_end(self):
        self.last_lethal_check = False
        if self.lethal_checker:
            self.lethal_checker.clear_overlay_cache()
        self._overlay_dirty = True
        self._console_dirty = False
        self._clear_overlay_idle()

    def _is_match_active(self) -> bool:
        """对局是否已进入可分析阶段（非菜单/回放旧 LOG）。"""
        if self.power_parser and not self.power_parser.live_match_active:
            return False
        gs = self.game_state
        if not gs.in_game:
            return False
        local = gs.local_player_id
        opp = gs.opponent_player_id
        if local is None or opp is None:
            return False
        return bool(gs.hero_entity_ids.get(local) and gs.hero_entity_ids.get(opp))

    def _clear_overlay_idle(self):
        self.last_lethal_check = False
        if self.lethal_checker:
            self.lethal_checker.clear_overlay_cache()
        if self.overlay:
            self.overlay.set_text("等待游戏开始", theme=Overlay.THEME_NORMAL)
        if self.combo_overlay:
            self.combo_overlay.set_text("")

    def _ensure_player_detected(self) -> bool:
        if self.power_parser:
            self.power_parser.reconcile_local_player()
        if self.game_state.local_player_id is not None:
            return True
        if self.game_state.local_player_id is None:
            debug_info = (
                f"等待游戏数据...\n实体数: {len(self.game_state.entities)}\n"
                f"控制器: {self.game_state.seen_controllers}\n"
                f"（换牌或 FRIENDLY_PLAYER 后将自动识别我方）"
            )
            if self.overlay:
                self.overlay.set_text(debug_info, theme=Overlay.THEME_NORMAL)
            return False
        return True

    def _refresh_overlay(self):
        """刷新浮层（约每秒一次，不节流）"""
        if not self.overlay:
            return
        if self.overlay.is_user_closed:
            return
        if not self._replay_ready:
            self.overlay.set_text("正在同步对局…", theme=Overlay.THEME_NORMAL)
            if self.combo_overlay:
                self.combo_overlay.set_text("")
            return
        if not self._is_match_active():
            self._clear_overlay_idle()
            return
        if not self._ensure_player_detected():
            return

        is_local_turn = self.lethal_checker.is_local_turn()
        is_opp_turn = (
            self.lethal_checker.is_opponent_turn()
            if not is_local_turn
            else False
        )
        my_health, my_armor, _ = self.lethal_checker.get_my_health()
        my_total = my_health + my_armor
        opp_threat = self.lethal_checker.opponent_overlay_face_damage()
        opp_lethal_now = is_opp_turn and opp_threat >= my_total

        # 先算场攻（独立预算），避免斩杀搜索超时污染场攻缓存
        self.lethal_checker.overlay_board_face_damage()
        total_damage, _, has_lethal = self.lethal_checker.calculate_lethal_potential()
        timed_out = self.lethal_checker.lethal_calc_timed_out()
        health, armor, _ = self.lethal_checker.get_opponent_health()

        # 玩家 ID 错位时会把敌方场面当成己方：敌方回合且敌场攻已够斩杀时，不提示「我能斩」
        if opp_lethal_now:
            has_lethal = False

        prompt_lethal = self.lethal_checker.overlay_lethal_prompt_ok(
            has_lethal, opp_lethal_now=opp_lethal_now,
        )
        show_lethal = self.lethal_checker.overlay_red_prompt_ok(
            opp_lethal_now=opp_lethal_now,
        )

        self._update_overlay(
            total_damage, health, armor, has_lethal,
            is_opp_turn=is_opp_turn,
            my_health=my_health,
            my_armor=my_armor,
            opp_threat=opp_threat,
            opp_lethal_now=opp_lethal_now,
        )

        if (prompt_lethal or show_lethal) and not self.last_lethal_check:
            print("\n" + "🎯" * 30)
            print("⚔️  斩杀提示！检测到斩杀机会！ ⚔️")
            print("🎯" * 30)
            self.lethal_checker.print_lethal_info()
        self.last_lethal_check = prompt_lethal or show_lethal

    def _refresh_console(self):
        """刷新控制台状态（约每 2 秒一次）"""
        if not self._replay_ready:
            return
        if self.power_parser and not self.power_parser.live_match_active:
            return
        if not self._is_match_active():
            return
        if not self._ensure_player_detected():
            return
        self._print_game_state()
        self._maybe_compare_hdt()

    def _maybe_compare_hdt(self):
        """与 HDT 导出 JSON 对比场面（仅在有差异时打印）。"""
        if not self.compare_hdt or not self._hdt_state_path:
            return
        now = time.time()
        if now - self._last_hdt_compare < 2.0:
            return
        self._last_hdt_compare = now

        hdt = load_hdt_state(self._hdt_state_path)
        if not hdt:
            return
        ours = export_game_state(self.game_state, self.lethal_checker)
        issues = compare_states(ours, hdt)
        key = tuple(issues)
        if key == self._last_hdt_issues:
            return
        self._last_hdt_issues = key
        if issues:
            print("\n[HDT 对比] " + format_compare_report(issues, ours, hdt).replace("\n", "\n[HDT 对比] "))

    def _update_overlay(
        self,
        total_damage: int,
        opp_health: int,
        opp_armor: int,
        has_lethal: bool,
        *,
        is_opp_turn: bool = False,
        my_health: int = 30,
        my_armor: int = 0,
        opp_threat: int = 0,
        opp_lethal_now: bool = False,
    ):
        """更新覆盖层显示"""
        if not self.overlay:
            return

        local_id = self.game_state.local_player_id
        opp_id = self.game_state.opponent_player_id
        opp_board = self.game_state.get_board(opp_id) if opp_id else []

        # 第一行：场攻 = 纯随从（无法术） vs 解场法术后（随从+月亮井等直伤）
        opp_taunts = living_taunt_minions(opp_board, self.game_state)
        board_atk = self.lethal_checker.overlay_display_face()
        lethal_face = self.lethal_checker.cached_overlay_face()
        mc_max, lethal_prob, uses_random, top_outcomes = self.lethal_checker.overlay_face_stats()
        pure_board, minion_board, weapon_board, spell_direct, hero_power_face = (
            self.lethal_checker.overlay_board_breakdown()
        )
        hero_buff_face = self.lethal_checker.overlay_hero_buff_face()
        spell_note = self.lethal_checker.overlay_spell_note()
        hand_charge_face = self.lethal_checker.overlay_hand_charge_face()
        board_minion = max(0, minion_board - hand_charge_face)

        cfg = self.overlay_settings
        opp_total = self.lethal_checker._lethal_threshold_hp()
        lines = []

        extras = []
        if cfg.show_breakdown:
            if board_minion > 0:
                from hdt_python.overlay_combo_format import (
                    overlay_minion_face_bonus_paren,
                )
                bonus = overlay_minion_face_bonus_paren(self.lethal_checker)
                if bonus:
                    extras.append(f"随{board_minion}{bonus}")
                else:
                    extras.append(f"随{board_minion}")
            if hero_buff_face > 0:
                extras.append(f"英{hero_buff_face}")
            if weapon_board > 0:
                extras.append(f"武{weapon_board}")
            if spell_direct > 0:
                extras.append(f"法{spell_direct}")
            battlecry_face = self.lethal_checker.overlay_battlecry_face()
            if battlecry_face > 0:
                extras.append(f"吼{battlecry_face}")
            if hero_power_face > 0:
                extras.append(f"技{hero_power_face}")
            if hand_charge_face > 0:
                extras.append(f"冲{hand_charge_face}")
            dormant_et = self.lethal_checker.overlay_end_turn_face_for_display()
            if dormant_et > 0:
                extras.append(f"回{dormant_et}")
            fatigue_face = self.lethal_checker.overlay_fatigue_face()
            if fatigue_face > 0:
                extras.append(f"疲{fatigue_face}")
        else:
            battlecry_face = self.lethal_checker.overlay_battlecry_face()
            dormant_et = 0
            fatigue_face = self.lethal_checker.overlay_fatigue_face()

        if uses_random and top_outcomes:
            parts = [f"{dmg}({prob * 100:.0f}%)" for dmg, prob in top_outcomes]
            atk_line = f"场攻 {' '.join(parts)}"
        elif uses_random:
            atk_line = f"场攻 {mc_max} ({lethal_prob * 100:.0f}%)"
        else:
            atk_line = f"场攻 {board_atk}"

        show_lethal = self.lethal_checker.overlay_red_prompt_ok(
            opp_lethal_now=opp_lethal_now,
        )
        if show_lethal:
            dmg_show = mc_max if uses_random else lethal_face
            if is_opp_turn:
                if uses_random and 0 < lethal_prob < 1.0:
                    atk_line = f"⚔️下回合斩 {dmg_show} ({lethal_prob * 100:.0f}%)"
                else:
                    atk_line = f"⚔️下回合斩 {dmg_show}"
            elif uses_random and 0 < lethal_prob < 1.0:
                atk_line = f"⚔️斩杀 {mc_max} ({lethal_prob * 100:.0f}%)"
            else:
                atk_line = f"⚔️斩杀 {dmg_show}"
        if extras:
            atk_line += f" ({'+'.join(extras)})"
        lines.append(atk_line)

        if cfg.show_spell_detail and not cfg.compact_mode:
            spell_detail_parts: list[str] = []
            if pure_board > 0 and pure_board != board_atk:
                spell_detail_parts.append(f"纯随{pure_board}")
            if spell_note and spell_note != "计算超时":
                spell_detail_parts.append(spell_note)
            elif spell_direct > 0:
                spell_detail_parts.append(f"法术打脸{spell_direct}")
            if spell_detail_parts:
                lines.append(" ".join(spell_detail_parts))

        if cfg.show_calc_time:
            calc_ms = self.lethal_checker.format_overlay_calc_ms(
                self.lethal_checker.overlay_calc_elapsed_ms(),
            )
            if calc_ms:
                lines.append(f"耗时 {calc_ms}")

        if cfg.show_taunt_line and opp_taunts:
            lines.append(f"嘲 {len(opp_taunts)}")

        status_parts = []
        if cfg.show_hp_line:
            status_parts.append(f"我 {my_health}+{my_armor}  敌 {opp_health}+{opp_armor}")
        if cfg.show_threat_line:
            my_total = my_health + my_armor
            if opp_lethal_now:
                status_parts.append(f"⚠️ 敌斩 {opp_threat}≥{my_total}")
            elif is_opp_turn and opp_threat >= my_total - 5 and opp_threat > 0:
                diff = my_total - opp_threat
                status_parts.append(f"敌威胁 {opp_threat}/{my_total} 差{diff}")
        if status_parts:
            if cfg.compact_mode:
                lines.append(" · ".join(status_parts))
            else:
                lines.extend(status_parts)

        lethal_parts = []
        prompt_lethal = self.lethal_checker.overlay_lethal_prompt_ok(
            has_lethal, opp_lethal_now=opp_lethal_now,
        )
        diff_damage = self.lethal_checker.overlay_diff_damage(
            total_damage, has_lethal or show_lethal,
        )
        diff_note = self.lethal_checker.overlay_lethal_diff_note(
            total_damage, opp_total, has_lethal=has_lethal, prompt_lethal=prompt_lethal,
        )
        if cfg.show_lethal_diff:
            if is_opp_turn:
                if show_lethal or prompt_lethal:
                    dmg_line = mc_max if uses_random else lethal_face
                    if uses_random and 0 < lethal_prob < 1.0:
                        lethal_parts.append(
                            f"⚔️ 下回合斩 {dmg_line}≥{opp_total} ({lethal_prob * 100:.0f}%)"
                        )
                    else:
                        lethal_parts.append(f"⚔️ 下回合斩 {dmg_line}≥{opp_total}")
                elif not opp_lethal_now:
                    diff = opp_total - diff_damage
                    lethal_parts.append(f"下回合 {diff_damage}/{opp_total} 差{diff}")
            elif show_lethal or prompt_lethal:
                dmg_line = mc_max if uses_random else lethal_face
                if uses_random and 0 < lethal_prob < 1.0:
                    lethal_parts.append(
                        f"⚔️ 概率斩杀 {dmg_line}≥{opp_total} ({lethal_prob * 100:.0f}%)"
                    )
                else:
                    lethal_parts.append(f"⚔️ 斩杀 {dmg_line}≥{opp_total}")
            elif self.lethal_checker.lethal_calc_timed_out():
                lethal_parts.append("⏱ 斩杀计算超时")
            else:
                diff = opp_total - diff_damage
                line = f"{diff_damage}/{opp_total} 差{diff}"
                if diff_note:
                    line += f" ({diff_note})"
                lethal_parts.append(line)
        if lethal_parts:
            lines.extend(lethal_parts if not cfg.compact_mode else [" · ".join(lethal_parts)])

        combo_lines: list[str] = []
        if cfg.show_combo_overlay and show_lethal:
            combo_lines = self.lethal_checker.overlay_combo_display_lines()

        overlay_text = "\n".join(lines)
        overlay_colors = None
        if opp_lethal_now and not show_lethal:
            theme = Overlay.THEME_OPP_LETHAL
            overlay_colors = None
        elif show_lethal:
            if not uses_random or lethal_prob >= 1.0:
                theme = Overlay.THEME_MY_LETHAL
                overlay_colors = None
            elif uses_random and lethal_prob >= MIN_LETHAL_PROMPT_PROB:
                overlay_colors = self.overlay.lethal_colors_for_prob_on_base(lethal_prob)
                theme = Overlay.THEME_NORMAL
            else:
                theme = Overlay.THEME_MY_LETHAL
                overlay_colors = None
        else:
            theme = Overlay.THEME_NORMAL
            overlay_colors = None
        self.overlay.set_text(overlay_text, theme=theme, colors=overlay_colors)

        if self.combo_overlay and cfg.show_combo_overlay:
            if show_lethal and combo_lines:
                self.combo_overlay.set_text(
                    "\n".join(combo_lines),
                    theme=ComboOverlay.THEME_COMBO_LETHAL,
                )
            else:
                self.combo_overlay.set_text("")
        elif self.combo_overlay:
            self.combo_overlay.set_text("")

    def _print_game_state(self):
        """打印游戏状态"""
        my_hero = self.game_state.get_hero(self.game_state.local_player_id)
        opp_hero = self.game_state.get_hero(self.game_state.opponent_player_id) if self.game_state.opponent_player_id else None

        my_board = self.game_state.get_board(self.game_state.local_player_id)
        my_hand = self.game_state.get_hand(self.game_state.local_player_id)

        opp_board = self.game_state.get_board(self.game_state.opponent_player_id) if self.game_state.opponent_player_id else []

        print("\n" + "-" * 60)
        hero_ids = {}
        if self.game_state.local_player_id:
            h = self.game_state.get_hero(self.game_state.local_player_id)
            if h and h.card_id:
                hero_ids[self.game_state.local_player_id] = h.card_id
        if self.game_state.opponent_player_id:
            h = self.game_state.get_hero(self.game_state.opponent_player_id)
            if h and h.card_id:
                hero_ids[self.game_state.opponent_player_id] = h.card_id
        print(format_identity_summary(
            self.game_state.local_player_id,
            self.game_state.opponent_player_id,
            self.game_state.player_names,
            hero_ids,
            self.game_state.local_player_identity_source or "",
        ))

        if my_hero:
            my_health = my_hero.current_health
            # 如果血量还没设置，使用默认值
            if my_health == 0 and my_hero.health == 0:
                my_health = 30
            my_armor = my_hero.tags.get("ARMOR", 0)
            my_mana = my_hero.tags.get("RESOURCES", 0)
            my_mana_used = my_hero.tags.get("RESOURCES_USED", 0)
            print(f"我方: {my_health}+{my_armor}血 | {my_mana - my_mana_used}/{my_mana}法力")
        else:
            print("我方: 等待数据...")

        if opp_hero:
            opp_health = opp_hero.current_health
            # 如果血量还没设置，使用默认值
            if opp_health == 0 and opp_hero.health == 0:
                opp_health = 30
            opp_armor = opp_hero.tags.get("ARMOR", 0)
            print(f"对手: {opp_health}+{opp_armor}血")
        else:
            print("对手: 等待数据...")

        pid = self.game_state.local_player_id
        my_weapon = self.game_state.get_weapon(pid)
        # 与浮层同步重算，避免控制台读到过期分项（如误显示「回」）
        self.lethal_checker.overlay_board_face_damage()
        remaining = self.lethal_checker.overlay_display_face()
        lethal_face = self.lethal_checker.cached_overlay_face()
        pure_board, minion_board, weapon_board, spell_direct, hero_power_face = (
            self.lethal_checker.overlay_board_breakdown()
        )
        hero_buff_face = self.lethal_checker.overlay_hero_buff_face()
        spell_note = self.lethal_checker.overlay_spell_note()
        hand_charge_face = self.lethal_checker.overlay_hand_charge_face()
        board_minion = max(0, minion_board - hand_charge_face)
        is_opp_turn = not self.game_state.is_local_turn()
        turn_hint = " [下回合预览]" if is_opp_turn else ""
        print(f"\n场攻(Overlay): {remaining}{turn_hint}  |  场面: 我方 {len(my_board)} 随从 | 对手 {len(opp_board)} 随从")
        breakdown_parts = []
        if board_minion > 0:
            breakdown_parts.append(f"随{board_minion}")
        if hero_buff_face > 0:
            breakdown_parts.append(f"英{hero_buff_face}")
        if weapon_board > 0:
            breakdown_parts.append(f"武{weapon_board}")
        if spell_direct > 0:
            breakdown_parts.append(f"法{spell_direct}")
        battlecry_face = self.lethal_checker.overlay_battlecry_face()
        if battlecry_face > 0:
            breakdown_parts.append(f"吼{battlecry_face}")
        if hero_power_face > 0:
            breakdown_parts.append(f"技{hero_power_face}")
        if hand_charge_face > 0:
            breakdown_parts.append(f"冲{hand_charge_face}")
        dormant_et = self.lethal_checker.overlay_end_turn_face_for_display()
        if dormant_et > 0:
            breakdown_parts.append(f"回{dormant_et}")
        fatigue_face = self.lethal_checker.overlay_fatigue_face()
        if fatigue_face > 0:
            breakdown_parts.append(f"疲{fatigue_face}")
        if breakdown_parts:
            print(f"  分项: {'+'.join(breakdown_parts)}", end="")
        spell_detail_parts = []
        if pure_board > 0 and pure_board != remaining:
            spell_detail_parts.append(f"纯随{pure_board}")
        if spell_note and spell_note != "计算超时":
            spell_detail_parts.append(spell_note)
        elif spell_direct > 0:
            spell_detail_parts.append(f"法术打脸{spell_direct}")
        if spell_detail_parts:
            if breakdown_parts:
                print()
            print(f"  {' '.join(spell_detail_parts)}")
        elif breakdown_parts:
            print()
        calc_label = self.lethal_checker.format_overlay_calc_ms(
            self.lethal_checker.overlay_calc_elapsed_ms(),
        )
        if calc_label:
            print(f"  场攻计算: {calc_label}")
        if my_weapon:
            from hdt_python.board_damage import _weapon_std_attack
            w_atk = self.game_state.weapon_attack_damage(pid)
            weapon_atk = _weapon_std_attack(my_weapon)
            print(
                f"武器: {my_weapon.card_id} 攻{weapon_atk}/耐{my_weapon.current_durability}"
                f"  本回合可攻:{w_atk}"
            )
        print(f"手牌: {len(my_hand)} 张")

        # 显示场面随从（对方回合用下回合潜力视角，与 Overlay 场攻一致）
        board_active = board_active_turn_for_display(self.game_state, pid)
        if my_board:
            print("\n我方场面:")
            for minion in my_board[:7]:  # 最多7个随从
                card_name = minion.card_id or "未知"
                view = minion.board_card_view(board_active, self.game_state)
                from hdt_python.board_damage import is_dormant
                dormant = is_dormant(minion, self.game_state)
                atk = 0 if dormant else view.std_attack
                stats = f"{atk}/{minion.current_health}"
                if dormant:
                    can_atk = "眠"
                else:
                    can_atk = "✓" if view.can_attack_hero else "✗"
                print(f"  [{can_atk}] {card_name} ({stats})")

        # 显示手牌
        if my_hand:
            print("\n手牌:")
            for card in my_hand[:10]:
                card_name = card.card_id or "未知"
                cost = card.cost
                script_dmg = spell_script_damage(
                    card, default=0,
                    gs=self.game_state, player_id=pid,
                )
                if script_dmg > 0 and card.is_spell:
                    print(f"  ({cost}) {card_name}  [{script_dmg}伤]")
                else:
                    print(f"  ({cost}) {card_name}")

        print("-" * 60)

    def run(self):
        """运行追踪器"""
        if not self.setup():
            if is_frozen():
                try:
                    input("\n按回车退出…")
                except Exception:
                    time.sleep(8)
            return

        print("\n" + "=" * 60)
        print("开始监控游戏...")
        print("提示: 按 Ctrl+C 停止")
        print("=" * 60)

        try:
            # 先启动覆盖层窗口，再同步 Power.log（回放可能耗时数秒）
            if self.use_overlay and self.overlay:
                if self.overlay.start(wait_ready=8.0):
                    self.overlay.set_text("正在同步对局…", theme=Overlay.THEME_NORMAL)
                    rect = self.overlay.window_rect()
                    if rect:
                        mode = (
                            "已挂到炉石窗口（Win+G 录游戏可录入）"
                            if rect.get("attached_to_game")
                            else "独立置顶窗（录屏请用整屏/OBS）"
                        )
                        print(
                            f"覆盖层已就绪：屏幕坐标 ({rect['left']}, {rect['top']})，{mode}"
                        )
                    else:
                        print("覆盖层窗口已就绪")
                    if self.combo_overlay:
                        self.combo_overlay.start(wait_ready=8.0)
                else:
                    err = getattr(self.overlay, "_last_error", "") or "未知错误"
                    print(f"⚠️ 覆盖层未能启动: {err}")
                    print("   控制台数据仍会更新；请关闭其他 tracker 实例后重试")
                    print("   若用 --no-overlay 请去掉；半透明异常可去掉 --layered 用白底模式")
                    self.overlay = None
                    self.combo_overlay = None
            elif self.use_overlay:
                print("⚠️ 覆盖层未能初始化")

            # 日志回放放到后台，避免阻塞时长时间只有控制台、浮层不刷新
            import threading
            replay_done = threading.Event()

            def _start_logs():
                try:
                    self.log_manager.start()
                finally:
                    replay_done.set()

            threading.Thread(target=_start_logs, name="HSLogReplay", daemon=True).start()
            while not replay_done.wait(timeout=0.2):
                self._refresh_overlay()
            self._replay_ready = True
            self._overlay_dirty = True
            self._console_dirty = True
            self._refresh_overlay()
            self._refresh_console()

            # 主循环：仅 Power.log 有更新时重算（见 _on_power_log_line / 事件标脏）
            while True:
                if self._force_immediate_overlay or self._overlay_dirty:
                    self._refresh_overlay()
                    self._overlay_dirty = False
                    self._force_immediate_overlay = False
                if self._console_dirty:
                    self._refresh_console()
                    self._console_dirty = False
                time.sleep(0.2)

        except KeyboardInterrupt:
            print("\n\n正在停止...")
            self.log_manager.stop()
            if self.overlay:
                self.overlay.stop()
            if self.combo_overlay:
                self.combo_overlay.stop()
            print("已停止。")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='炉石传说辅助工具 - 斩杀检测')
    parser.add_argument('--no-overlay', action='store_true', help='禁用窗口覆盖层（只显示控制台输出）')
    parser.add_argument('--layered', action='store_true', help='使用半透明覆盖层模式（默认白底）')
    parser.add_argument(
        '--float-overlay',
        action='store_true',
        help='独立置顶浮层（HDT 同款）；默认挂到炉石窗口内便于 Win+G 录屏',
    )
    parser.add_argument(
        '--compare-hdt',
        action='store_true',
        help='与 HDT 插件导出的场面 JSON 对比（需安装 hdt_plugin/CompareExporter）',
    )
    parser.add_argument(
        '--settings-path',
        type=str,
        default='',
        help='自定义设置文件路径（默认 overlay_settings.json）',
    )

    args = parser.parse_args()

    settings_path = Path(args.settings_path) if args.settings_path else None
    settings_store = OverlaySettingsStore(settings_path)
    settings_store.load()
    overlay_settings = settings_store.settings.merge_cli(
        layered=True if args.layered else None,
        float_overlay=True if args.float_overlay else None,
    )

    use_overlay = not args.no_overlay

    tracker = HearthstoneTracker(
        use_overlay=use_overlay,
        use_layered=overlay_settings.use_layered,
        compare_hdt=args.compare_hdt,
        attach_overlay=overlay_settings.attach_to_game,
        overlay_settings=overlay_settings,
        settings_store=settings_store,
    )
    tracker.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        import traceback

        traceback.print_exc()
        if is_frozen():
            try:
                input("\n程序异常退出，按回车关闭…")
            except Exception:
                time.sleep(15)
        raise
