# lethal_checker.py - 斩杀检测器

import random
import time
from itertools import combinations
from typing import List, Tuple, Optional, Set
from .power_parser import GameState
from .board_damage import (
    build_player_board,
    attacks_per_turn,
    attacks_this_turn,
    effective_attacks_this_turn,
    is_silenced,
    is_players_turn,
    hero_can_attack_with_weapon,
    hero_weapon_can_face,
    hero_has_divine_shield,
    hero_weapon_strike_damage,
    apply_divine_shield_to_hits,
    entity_has_taunt,
    entity_zone,
    living_taunt_minions,
    _std_attack,
    collect_hand_charge_minions,
    hand_minion_has_charge,
    hand_minion_cost,
    hand_minion_attack,
    double_agent_summons_copy,
    format_hand_charge_label,
)
from .battlecry_board import hand_all_board_plays
from .interleave_board import interleave_note_suffix, sequence_needs_attack_interleave, sequence_has_interleave_spell
from .hero_power_board import has_usable_hero_power, usable_hero_power, apply_hero_power_to_fighters
from .spell_board import (
    enumerate_spell_sequences,
    apply_spell_sequence,
    apply_spell_sequence_with_meta,
    spell_effect_multiplier,
    total_spell_power,
    entity_is_dragon,
    entity_is_beast,
    SpellApplyResult,
    spell_sequence_transposition_key,
    get_board_spell_def,
    spell_effective_cost,
    sequence_uses_random,
    split_deterministic_random_sequence,
    sequence_random_spells_all_last,
    merge_spell_apply_results,
    MC_TRIALS,
)
from .deathrattle import on_minion_died, remove_dead_taunts, resolve_minion_death, sim_armor_gain
from .end_turn_board import (
    board_end_turn_face_now,
    end_turn_face_damage,
    end_turn_names_on_board,
    end_turn_uses_random,
    end_turn_uses_random_fighters,
    has_hold_attack_end_turn_in_fighters,
    has_hold_attack_end_turn_on_board,
    sim_end_turn_entities_from_fighters,
)

# Overlay 随机线路：搜索与展示 MC 共用试验次数；每次试验独立种子
OVERLAY_MC_TRIALS = 50
# 随机斩杀提示/高亮最低概率（低于此值不提示斩杀）
MIN_LETHAL_PROMPT_PROB = 0.2


def _mc_rng(trial_index: int) -> random.Random:
    return random.Random(trial_index * 9973 + 101)


def _clone_combat_state(d: dict) -> dict:
    """复制战斗模拟 dict（仅标量字段，不拷贝 Entity 引用）。"""
    out = dict(d)
    out.pop("original", None)
    return out


def _clone_combat_states(states: List[dict]) -> List[dict]:
    return [_clone_combat_state(s) for s in states]


class DamageSource:
    """伤害来源"""

    def __init__(self, source_type: str, damage: int, description: str, mana_cost: int = 0):
        self.source_type = source_type  # "board", "spell", "weapon", "hero_power", "charge"
        self.damage = damage
        self.description = description
        self.mana_cost = mana_cost

    def __repr__(self):
        if self.mana_cost > 0:
            return f"{self.description}: {self.damage}伤害 ({self.mana_cost}费)"
        return f"{self.description}: {self.damage}伤害"


# 法术伤害数据库（简化版）
# 格式: "CardID": (费用, 基础伤害, 可打脸)
#   can_hit_face=True  — 可对敌方英雄造成直伤（含随机/可选目标）
#   can_hit_face=False — 只能打随从或仅为加攻等，不计入直伤斩杀
SPELL_DAMAGE_DB = {
    # === 法师 ===
    "CS2_029": (4, 6, True),       # 火球术 Fireball
    "EX1_279": (10, 10, True),     # 炎爆术 Pyroblast
    "CS2_024": (2, 3, True),       # 寒冰箭 Frostbolt
    "EX1_173": (6, 5, True),       # 星火术 Starfire
    "VAN_EX1_173": (6, 5, True),   # 星火术（怀旧）
    "CS2_025": (1, 3, True),       # 奥术飞弹 Arcane Missiles（随机，可打脸）
    "RLK_843": (1, 2, True),       # 奥术箭（法力渴求8→3伤，快速估算用基底2）
    "EX1_275": (3, 3, True),       # 寒冰枪 Ice Lance

    # === 术士 ===
    "CS2_057": (3, 4, False),      # 暗影箭 Shadow Bolt（只能打随从）
    "EX1_308": (1, 4, True),       # 灵魂之火 Soulfire
    "CORE_EX1_308": (1, 4, True),  # 灵魂之火 Soulfire（核心）

    # === 猎人 ===
    "DS1_185": (1, 2, True),       # 奥术射击 Arcane Shot
    "EX1_539": (3, 5, True),       # 杀戮命令 Kill Command
    "CORE_EX1_539": (3, 5, True),  # 杀戮命令 Kill Command（核心）

    # === 德鲁伊 ===
    "CS2_012": (3, 4, True),       # 横扫 Swipe（主目标4，无嘲讽打脸4）
    "CORE_CS2_012": (3, 4, True),  # 横扫 Swipe（核心）
    "EX1_154": (2, 3, True),       # 愤怒 Wrath

    # === 盗贼 ===
    "CS2_072": (0, 2, False),      # 背刺 Backstab（只能打未受伤随从）
    "CORE_CS2_072": (0, 2, False), # 背刺 Backstab（核心）
    "EX1_278": (2, 1, True),       # 刺骨 Shiv

    # === 萨满 ===
    "EX1_238": (1, 3, True),       # 闪电箭 Lightning Bolt
    "CORE_EX1_238": (1, 3, True),  # 闪电箭 Lightning Bolt（核心）
    "EX1_241": (3, 5, True),       # 熔岩爆裂 Lava Burst
    "CORE_EX1_241": (3, 5, True),  # 熔岩爆裂 Lava Burst（核心）
    "CS2_037": (1, 1, True),       # 冰霜震击 Frost Shock

    # === 牧师 ===
    "CS2_236": (1, 2, False),     # 神圣惩击 Holy Smite（只能打随从）
    "CORE_CS2_236": (1, 2, False), # 神圣惩击 Holy Smite（核心）

    # === 战士 ===
    "EX1_400": (2, 2, True),       # 猛击 Slam
    "CORE_EX1_400": (2, 2, True),  # 猛击 Slam（核心）

    # === 圣骑士 ===
    "CS2_094": (4, 3, True),       # 愤怒之锤 Hammer of Wrath
    "CORE_CS2_094": (4, 3, True),  # 愤怒之锤 Hammer of Wrath（核心）

    # === 恶魔猎手 ===
    "BT_175": (1, 2, False),       # 混乱打击 Chaos Strike（+2攻，非直伤）
    "BT_801": (4, 3, False),       # 眼棱 Eye Beam（默认只能打随从）
}

# 冲锋随从
# 格式: "CardID": (费用, 打脸伤害)
CHARGE_MINIONS_DB = {
    # === 中立 ===
    "CS2_124": (3, 3),   # 狼骑兵 Wolfrider 3/1冲锋
    "CS2_150": (1, 1),   # 石牙野猪 Stonetusk Boar 1/1冲锋
    "EX1_116": (6, 6),   # 雷矛特种兵 Reckless Rocketeer 6/3冲锋
    "WW_364t": (3, 3),   # 狡诈巨龙威拉罗克（威拉罗克变形）

    # === 战士 ===
    "NEW1_011": (5, 5),  # 科拉隆精英 Kor'kron Elite 5/5冲锋
}


# 斩杀 / Overlay 场攻搜索超时（秒）
LETHAL_CALC_TIMEOUT_SEC = 30.0
OVERLAY_FACE_TIMEOUT_SEC = 8.0
# 进入法术序列搜索的手牌上限；超过则按 spell_estimate_trim_damage 裁剪
MAX_HAND_SPELLS_FOR_SEARCH = 7


class LethalChecker:
    """
    斩杀检测器
    计算总伤害并判断是否有斩杀
    """

    def __init__(self, game_state: GameState):
        self.game_state = game_state
        self._last_lifesteal_heal = 0
        self._last_deathrattle_armor = 0
        self._overlay_lifesteal_heal = 0
        self._overlay_deathrattle_armor = 0
        self._lethal_deadline: Optional[float] = None
        self._lethal_budget_depth: int = 0
        self._lethal_timed_out: bool = False

    def lethal_calc_timed_out(self) -> bool:
        """最近一次斩杀/场攻计算是否因超时而中止。"""
        return self._lethal_timed_out

    def _begin_lethal_budget(self) -> None:
        if self._lethal_budget_depth == 0:
            self._lethal_timed_out = False
            self._lethal_deadline = time.perf_counter() + LETHAL_CALC_TIMEOUT_SEC
        self._lethal_budget_depth += 1

    def _end_lethal_budget(self) -> None:
        self._lethal_budget_depth = max(0, self._lethal_budget_depth - 1)
        if self._lethal_budget_depth == 0:
            self._lethal_deadline = None

    def _lethal_budget_expired(self) -> bool:
        if self._lethal_timed_out:
            return True
        if self._lethal_deadline is None:
            return False
        if time.perf_counter() >= self._lethal_deadline:
            self._lethal_timed_out = True
            return True
        return False

    def is_local_turn(self) -> bool:
        pid = self.game_state.local_player_id
        if pid is None:
            return True
        return is_players_turn(self.game_state, pid)

    def is_opponent_turn(self) -> bool:
        pid = self.game_state.opponent_player_id
        if pid is None:
            return False
        return is_players_turn(self.game_state, pid)

    def _hero_power_next_turn(self) -> bool:
        """对方回合时 Overlay/斩杀按「下回合」估算，英雄技能视为已刷新。"""
        return self.is_opponent_turn()

    def get_my_health(self) -> Tuple[int, int, int]:
        """我方英雄血量（当前血, 护甲, 总计）"""
        if self.game_state.local_player_id is None:
            return 30, 0, 30
        hero = self.game_state.get_hero(self.game_state.local_player_id)
        if not hero:
            return 30, 0, 30
        health = hero.current_health
        if health == 0 and hero.health == 0:
            health = 30
        armor = hero.tags.get("ARMOR", 0)
        return health, armor, health + armor

    def opponent_overlay_face_damage(self) -> int:
        """敌方对我方的场攻威胁（交换视角后的 overlay 场攻）。"""
        local = self.game_state.local_player_id
        opp = self.game_state.opponent_player_id
        if local is None or opp is None:
            return 0
        gs = self.game_state
        saved = (gs.local_player_id, gs.opponent_player_id)
        try:
            gs.local_player_id, gs.opponent_player_id = opp, local
            self.clear_overlay_cache()
            return self.overlay_board_face_damage()
        finally:
            gs.local_player_id, gs.opponent_player_id = saved
            self.clear_overlay_cache()

    def calculate_lethal(self) -> Tuple[int, List[DamageSource], bool]:
        """计算我方本回合斩杀（仅在我方回合）"""
        if not self.is_local_turn():
            return 0, [], False
        return self.calculate_lethal_potential()

    def calculate_lethal_potential(self) -> Tuple[int, List[DamageSource], bool]:
        """我方斩杀潜力（对方回合按「下回合」场面+法力估算，供 Overlay 高亮）"""
        local = self.game_state.local_player_id
        opp = self.game_state.opponent_player_id
        if local is None or opp is None:
            return 0, [], False
        self._begin_lethal_budget()
        try:
            if self._lethal_budget_expired():
                return 0, [], False
            on_local_turn = self.is_local_turn()
            # 快速斩杀：场面清嘲 + SPELL_DAMAGE_DB 直伤/冲锋累加，不模拟 spell_board 解场顺序
            total_damage, sources, quick_lethal = self._calculate_quick_lethal_for_player(
                local,
                opp,
                include_hand=True,
                board_active_turn=on_local_turn,
                mana_for_hand=None if on_local_turn else self._next_turn_mana(local),
                use_overlay_board=True,
            )
            self._last_quick_lethal_sources = list(sources)
            if self._lethal_budget_expired():
                overlay_lethal, total_damage = self._apply_overlay_board_lethal(
                    total_damage, sources,
                )
                has_lethal = quick_lethal or overlay_lethal
                if has_lethal and not self._turn_lethal_mana_ok(
                    local, sources,
                    quick_lethal=quick_lethal, overlay_lethal=overlay_lethal,
                ):
                    has_lethal = False
                return total_damage, sources, has_lethal
            overlay_lethal, total_damage = self._apply_overlay_board_lethal(
                total_damage, sources,
            )
            has_lethal = quick_lethal or overlay_lethal
            if has_lethal and not self._turn_lethal_mana_ok(
                local, sources,
                quick_lethal=quick_lethal, overlay_lethal=overlay_lethal,
            ):
                has_lethal = False
            if self._lethal_budget_expired():
                return total_damage, sources, has_lethal
            return total_damage, sources, has_lethal
        finally:
            self._end_lethal_budget()

    def get_opponent_effective_hp(self) -> int:
        """对手有效血量（含护甲、清嘲吸血、清嘲/法术触发亡语加甲）"""
        _, _, opp_total = self.get_opponent_health()
        lifesteal_heal = getattr(self, "_last_lifesteal_heal", 0)
        deathrattle_armor = getattr(self, "_last_deathrattle_armor", 0)
        if getattr(self, "_overlay_face_computed", False):
            lifesteal_heal = max(
                lifesteal_heal,
                getattr(self, "_overlay_lifesteal_heal", 0),
            )
            deathrattle_armor = max(
                deathrattle_armor,
                getattr(self, "_overlay_deathrattle_armor", 0),
            )
        return opp_total + lifesteal_heal + deathrattle_armor

    def _opponent_hero_hp_after_face_damage(self, defender_shield: bool, face_damage: int) -> int:
        """先攻/打脸后对手英雄剩余有效生命，供邪能弹幕等「最低血敌人」法术模拟。"""
        del defender_shield  # 打脸分量已由 apply_divine_shield_to_hits 计入
        return max(0, self.get_opponent_effective_hp() - max(0, face_damage))

    def _opponent_deck_count(self, player_id: Optional[int] = None) -> int:
        """对手牌库剩余张数。"""
        opp = player_id if player_id is not None else self.game_state.opponent_player_id
        if opp is None:
            return 0
        gs = self.game_state
        entities = list(gs.entities.values())
        return sum(
            1
            for e in entities
            if gs.is_entity_controlled_by(e, opp) and entity_zone(e) == "DECK"
        )

    def _opponent_fatigue_counter(self, player_id: Optional[int] = None) -> int:
        """对手 Player 实体 FATIGUE / FATIGUEREFERENCE（下一次抽牌疲劳伤害）。"""
        opp = player_id if player_id is not None else self.game_state.opponent_player_id
        if opp is None:
            return 0
        gs = self.game_state
        for eid, pid in gs.player_ids.items():
            if pid != opp:
                continue
            ent = gs.entities.get(eid)
            if not ent:
                continue
            fatigue = int(ent.tags.get("FATIGUE", 0) or 0)
            if fatigue > 0:
                return fatigue
            ref = int(ent.tags.get("FATIGUEREFERENCE", 0) or 0)
            if ref > 0:
                return ref
        opp_name = gs.player_names.get(opp, "")
        if opp_name:
            short = opp_name.split("#")[0]
            for ent in list(gs.entities.values()):
                nm = getattr(ent, "name", "") or ""
                if opp_name in nm or (short and short in nm):
                    fatigue = int(ent.tags.get("FATIGUE", 0) or 0)
                    if fatigue > 0:
                        return fatigue
                    ref = int(ent.tags.get("FATIGUEREFERENCE", 0) or 0)
                    if ref > 0:
                        return ref
        return 0

    def _opponent_upcoming_fatigue_damage(self) -> int:
        """
        对手牌库空时，下回合斩杀预览中可计入的疲劳伤害。
        对方回合（Overlay 下回合斩）时：对手本回合开始抽牌会吃疲劳，日志 HP 可能滞后。
        我方回合：对手疲劳发生在我们回合结束之后，不计入本回合斩杀。
        """
        if not self.is_opponent_turn():
            return 0
        if self._opponent_deck_count() > 0:
            return 0
        fatigue = self._opponent_fatigue_counter()
        return max(1, fatigue)

    def _lethal_threshold_hp(self, *, subtract_overlay_lifesteal: bool = False) -> int:
        """
        斩杀判定用对手有效血量。
        subtract_overlay_lifesteal：本 combo 内法术/清场触发的吸血已在同一模拟里结算，
        不应再抬高有效血线（否则月亮井等 AOE 会双重计入吸血）。
        对方回合预览下回合斩时，另减去对手即将承受的抽牌疲劳（牌库已空）。
        """
        threshold = self.get_opponent_effective_hp()
        if subtract_overlay_lifesteal:
            threshold -= int(getattr(self, "_overlay_lifesteal_heal", 0) or 0)
        threshold -= self._opponent_upcoming_fatigue_damage()
        return max(0, threshold)

    def _apply_overlay_board_lethal(
        self, total_damage: int, sources: List[DamageSource]
    ) -> Tuple[bool, int]:
        """与 Overlay 场攻对齐的场面斩杀兜底（含回合结束随机伤害的 MC 概率斩杀）。"""
        if not getattr(self, "_overlay_face_computed", False) or getattr(
            self, "_overlay_incomplete", False
        ):
            if self._lethal_budget_expired():
                self._overlay_incomplete = True
            else:
                self.overlay_board_face_damage()
        face = getattr(self, "_overlay_total_face", 0)
        mc_max, lethal_prob, uses_random, _top = self.overlay_face_stats()
        display = mc_max if uses_random else face
        if display <= 0:
            return False, total_damage
        lethal_hp = self._lethal_threshold_hp(subtract_overlay_lifesteal=True)
        boosted_total = max(total_damage, display)
        if uses_random:
            has_lethal = face >= lethal_hp or (
                mc_max >= lethal_hp and lethal_prob >= MIN_LETHAL_PROMPT_PROB
            )
        else:
            has_lethal = face >= lethal_hp
        # 对手仍有嘲讽且纯场面（无模拟清嘲）不足以斩杀 → 抑制误报
        if has_lethal and not uses_random:
            opp = self.game_state.opponent_player_id
            if opp is not None:
                taunts_now = living_taunt_minions(
                    self.game_state.get_board(opp), self.game_state,
                )
                if taunts_now:
                    pure, minion_bd, _, spell_bd, _ = self.overlay_board_breakdown()
                    board_from_spells = max(0, minion_bd) + max(
                        0, getattr(self, "_overlay_weapon_face", 0),
                    )
                    if (
                        board_from_spells <= 0
                        and pure < lethal_hp
                        and spell_bd < lethal_hp
                    ):
                        has_lethal = False
        if has_lethal and not any(s.source_type == "board" for s in sources):
            label = "场面攻击(Overlay)"
            if uses_random and lethal_prob < 1.0:
                label += f" P≈{lethal_prob:.0%}"
            sources.append(DamageSource("board", display, label))
        if has_lethal and self.is_local_turn():
            from .overlay_combo_format import overlay_combo_mana_affordable

            spent = getattr(self, "_overlay_mana_spent", 0)
            local = self.game_state.local_player_id
            avail = self._available_mana(local) if local is not None else 0
            if spent > avail or not overlay_combo_mana_affordable(self):
                has_lethal = False
        if has_lethal:
            total_damage = boosted_total
        return has_lethal, total_damage

    def overlay_diff_damage(self, total_damage: int, has_lethal: bool) -> int:
        """Overlay「差N」用的伤害：未确认斩杀时不拿 MC 上限凑成差0。"""
        if has_lethal:
            return total_damage
        if getattr(self, "_overlay_face_computed", False):
            face = int(getattr(self, "_overlay_total_face", 0) or 0)
            if face > 0:
                return min(total_damage, face)
        return total_damage

    def _next_turn_mana(self, player_id: int) -> int:
        resources, _, temp = self._hero_mana_tags(player_id)
        if resources > 0:
            return min(10, resources + 1) + temp
        estimated = self._estimate_mana_from_turn(player_id)
        return min(10, estimated + 1) if estimated > 0 else estimated

    def _hero_mana_tags(self, player_id: int) -> Tuple[int, int, int]:
        hero = self.game_state.get_hero(player_id)
        if not hero:
            return 0, 0, 0
        return (
            hero.tags.get("RESOURCES", 0),
            hero.tags.get("RESOURCES_USED", 0),
            hero.tags.get("TEMP_RESOURCES", 0),
        )

    def _estimate_mana_from_turn(self, player_id: int) -> int:
        """RESOURCES 未解析时的回退：按回合数估算水晶上限。"""
        gs = self.game_state
        game = gs.entities.get(gs.game_entity_id) if gs.game_entity_id else None
        if not game:
            return 0
        turn = game.tags.get("TURN", 0)
        if turn <= 0:
            return 0
        first = gs.first_player_id
        if first is None:
            return min(10, (turn + 1) // 2)
        if player_id == first:
            return min(10, (turn + 1) // 2)
        return min(10, turn // 2)

    def _available_mana(self, player_id: int) -> int:
        resources, used, temp = self._hero_mana_tags(player_id)
        if resources > 0 or used > 0 or temp != 0:
            return max(0, resources - used + temp)
        if is_players_turn(self.game_state, player_id):
            return 0
        return self._estimate_mana_from_turn(player_id)

    def _estimate_line_mana_spent(
        self,
        player_id: int,
        available_mana: int,
        *,
        seq: Optional[List] = None,
        hero_power_name: Optional[str] = None,
        hand_charges: Optional[List] = None,
    ) -> int:
        """估算最优打法所需法力（直伤前缀+法术序列含饮品连喝+技能+冲锋）。"""
        from .spell_board import spell_sequence_mana_left

        mana_left = max(0, available_mana)
        spent = 0

        if hero_power_name:
            row = usable_hero_power(
                self.game_state, player_id, mana_left,
                next_turn=self._hero_power_next_turn(),
            )
            if row is not None:
                _, _, cost = row
                if cost <= mana_left:
                    spent += cost
                    mana_left -= cost

        if seq:
            before = mana_left
            mana_left = spell_sequence_mana_left(seq, mana_left)
            if mana_left is not None:
                spent += before - mana_left

        for entity, cost, _ in sorted(hand_charges or [], key=lambda x: -x[2]):
            if cost <= mana_left:
                spent += cost
                mana_left -= cost

        return spent

    def _overlay_line_mana_ok(
        self,
        player_id: int,
        available_mana: int,
        *,
        seq: Optional[List] = None,
        use_hp: bool = False,
        hero_power_name: Optional[str] = None,
        hand_charges: Optional[List] = None,
    ) -> bool:
        """
        场攻/斩杀展示线路法力校验：法术序列须按全额费用计入，
        不可与英雄技能「先扣费后只算部分法术」的估算混用。
        """
        spell_mana = self._estimate_line_mana_spent(
            player_id, available_mana,
            seq=seq,
            hero_power_name=None,
            hand_charges=hand_charges,
        )
        if use_hp and hero_power_name:
            row = usable_hero_power(
                self.game_state, player_id, available_mana,
                next_turn=self._hero_power_next_turn(),
            )
            hp_cost = row[2] if row else 0
            return spell_mana + hp_cost <= available_mana
        return spell_mana <= available_mana

    def _turn_lethal_mana_ok(
        self,
        player_id: int,
        sources: List[DamageSource],
        *,
        quick_lethal: bool,
        overlay_lethal: bool,
    ) -> bool:
        """我方回合：斩杀线路所需法力不得超过当前剩余水晶。"""
        if not self.is_local_turn():
            return True
        avail = self._available_mana(player_id)
        if overlay_lethal:
            spent = getattr(self, "_overlay_mana_spent", 0)
            if spent > avail:
                return False
        if quick_lethal:
            quick_spent = sum(s.mana_cost for s in sources if s.mana_cost > 0)
            if quick_spent > avail:
                return False
        return True

    def _overlay_mana_for_spells(self, player_id: int) -> int:
        """Overlay 用法力：我方回合用剩余法力，对方回合用下回合法力（与场面潜力一致）。"""
        if self.is_local_turn():
            return self._available_mana(player_id)
        return self._next_turn_mana(player_id)

    def _hero_power_mana_budget(
        self, available_mana: int, mana_for_spells: int,
    ) -> int:
        """英雄技能可用法力：对方回合按整池下回合水晶，我方回合按扣直伤前缀后的剩余。"""
        if self.is_opponent_turn():
            return available_mana
        return mana_for_spells

    def _my_hero_hp_for_spells(self) -> int:
        _, _, total = self.get_my_health()
        return total

    def _minimum_affordable_board_spell_face(
        self, player_id: int, available_mana: int, defender_shield: bool,
    ) -> int:
        """手牌里在法力允许下，确定性法术直伤的最大值（单张或两张顺序，避免全排列）。"""
        hand_spells = hand_all_board_plays(self.game_state, player_id, available_mana)
        if not hand_spells:
            return 0
        mult = spell_effect_multiplier(self.game_state, player_id)
        hero_hp = self._my_hero_hp_for_spells()
        enemy = self._build_enemy_minion_states(player_id)
        fighters = self._build_fighters(
            self._board_view_for_fighters(player_id), player_id,
        )
        best = 0

        def eval_seq(seq) -> int:
            if seq and min(c for _, c, _ in seq) > available_mana:
                return 0
            if sequence_uses_random(seq):
                return 0
            res, hp_end, _ = apply_spell_sequence_with_meta(
                list(enemy), list(fighters), seq, spell_mult=mult,
                enemy_shield=defender_shield,
                gs=self.game_state, player_id=player_id,
                hero_hp=hero_hp, mana_budget=available_mana,
                next_turn_preview=self._hero_power_next_turn(),
            )
            dmg = res.direct_face_damage
            if self._hero_dead_after_spells(hp_end) and dmg < self.get_opponent_effective_hp():
                return 0
            return dmg

        for i, (card1, d1, c1) in enumerate(hand_spells):
            best = max(best, eval_seq([(d1, c1, card1)]))
            for j, (card2, d2, c2) in enumerate(hand_spells):
                if j == i:
                    continue
                best = max(best, eval_seq([(d1, c1, card1), (d2, c2, card2)]))
                best = max(best, eval_seq([(d2, c2, card2), (d1, c1, card1)]))
        return best

    def _board_view_for_fighters(self, player_id: int):
        """棘嗣幼龙等 HOLD 随从在场时用本回合攻击资格，避免 overlay 下回合潜力误判。"""
        if self._should_consider_hold_attack():
            return self.game_state.get_player_board(player_id, active_turn=True)
        return self.game_state.get_overlay_board(player_id)

    def overlay_board_face_damage(self) -> int:
        """
        Overlay 场攻 = 解场法术后随从/武器打脸 + 解场法术直伤（如月亮井对英雄）。
        无嘲讽且无解场法术时与 get_overlay_board().face_attack_damage_no_taunt 一致。
        """
        local = self.game_state.local_player_id
        if local is None:
            self._reset_overlay_board_breakdown(0, 0, 0, 0)
            return 0

        if self._restore_overlay_prompt_snapshot_if_needed():
            return getattr(self, "_overlay_total_face", 0)

        own_budget = self._lethal_budget_depth == 0
        t0 = time.perf_counter() if own_budget else None
        if own_budget:
            self._begin_lethal_budget()
        elif self._lethal_budget_expired():
            # 斩杀搜索耗尽共享预算时，场攻单独续期，避免嵌套调用直接缓存 0
            self._lethal_timed_out = False
            self._lethal_deadline = time.perf_counter() + OVERLAY_FACE_TIMEOUT_SEC
        try:
            if self._lethal_budget_expired():
                self._overlay_incomplete = True
                self._overlay_spell_note = "计算超时"
                return 0

            board_view = self._board_view_for_fighters(local)
            opp = self.game_state.opponent_player_id
            opp_hero = self.game_state.get_hero(opp) if opp is not None else None
            opp_shield = hero_has_divine_shield(opp_hero)
            opp_taunts: list = []
            if opp is not None:
                opp_board = self.game_state.get_board(opp)
                opp_taunts = living_taunt_minions(opp_board, self.game_state)

            mana = self._overlay_mana_for_spells(local)
            self._overlay_mana_budget = mana
            self._overlay_mana_spent = 0
            hand_spells = hand_all_board_plays(self.game_state, local, mana)
            pure_immediate = self._compute_immediate_board_face(
                board_view, local, opp_taunts, opp_shield,
            )
            pure_et = self._board_end_turn_face(local, opp_shield)
            if self._lethal_budget_expired():
                self._reset_overlay_board_breakdown(
                    pure_immediate, pure_immediate, 0,
                    pure_immediate + pure_et,
                )
                self._overlay_spell_note = "计算超时"
                return pure_immediate + pure_et

            min_spell_face = self._minimum_affordable_board_spell_face(
                local, mana, opp_shield,
            )

            hand_charges = collect_hand_charge_minions(self.game_state, local)
            if (
                not opp_taunts
                and not hand_spells
                and min_spell_face <= 0
                and not hand_charges
                and not has_usable_hero_power(
                    self.game_state, local, mana,
                    next_turn=self._hero_power_next_turn(),
                )
            ):
                enemy_states = self._build_enemy_minion_states(local)
                our_board = self.game_state.get_board(local)
                if end_turn_uses_random(our_board):
                    eff = self._lethal_threshold_hp()
                    mc_max, prob, top_outcomes, board_part = (
                        self._monte_carlo_pure_board_end_turn(
                            pure_immediate, enemy_states, opp_shield, eff,
                        )
                    )
                    self._reset_overlay_board_breakdown(
                        pure_immediate, board_part, 0, mc_max,
                        mc_max=mc_max, lethal_prob=prob,
                        uses_random=True, top_outcomes=top_outcomes,
                    )
                    self._overlay_best_seq = []
                    self._overlay_best_hp_name = None
                    return mc_max
                pure_fighters = self._build_fighters(board_view, local)
                pure_minion, pure_weapon, _, pure_hp = self._split_fighter_face(
                    pure_fighters, opp_shield,
                )
                pure_stolen = self._stolen_minion_face(pure_fighters, opp_shield)
                pure_total, pure_minion_et, pure_weapon_et, _, pure_hp_et, _ = (
                    self._apply_end_turn_face(
                        enemy_states, opp_shield, pure_immediate,
                        pure_minion, pure_weapon, pure_stolen, pure_hp,
                        fighters=pure_fighters,
                    )
                )
                self._reset_overlay_board_breakdown(
                    pure_immediate, pure_minion_et, pure_stolen, pure_total,
                    weapon_board=pure_weapon_et,
                    hero_power_face=pure_hp_et,
                )
                self._overlay_best_seq = []
                self._overlay_best_hp_name = None
                return pure_total

            face, spell_note = self._best_face_with_board_spells(
                board_view, local, opp_taunts, opp_shield, hand_spells, mana,
                pure_immediate=pure_immediate,
                pure_et=pure_et,
                effective_hp=self._lethal_threshold_hp(),
                hand_charges=hand_charges,
            )
            if self._lethal_budget_expired():
                self._overlay_spell_note = "计算超时"
            elif (
                min_spell_face > face
                and not getattr(self, "_overlay_uses_random", False)
            ):
                face = min_spell_face
                self._reset_overlay_board_breakdown(pure_immediate, 0, min_spell_face, face)
                if not spell_note and min_spell_face > 0:
                    spell_note = "法术:月亮井"
            self._overlay_spell_note = spell_note if not self._lethal_timed_out else "计算超时"
            return face
        finally:
            if own_budget:
                if t0 is not None:
                    self._overlay_calc_ms = (time.perf_counter() - t0) * 1000.0
                self._end_lethal_budget()
            if not self.overlay_spell_resolving():
                self._save_overlay_prompt_snapshot_if_lethal()

    def overlay_face_stats(self) -> Tuple[int, float, bool, List[Tuple[int, float]]]:
        """Overlay 场攻：(MC最高打脸, 斩杀概率, 是否含随机法术, 按伤害降序的前两种结果及概率)。"""
        max_face = getattr(self, "_overlay_mc_max", getattr(self, "_overlay_total_face", 0))
        prob = getattr(self, "_overlay_lethal_prob", 0.0)
        uses_random = getattr(self, "_overlay_uses_random", False)
        top_outcomes = getattr(self, "_overlay_top_outcomes", [])
        return max_face, prob, uses_random, top_outcomes

    def overlay_board_breakdown(self) -> Tuple[int, int, int, int, int]:
        """
        (纯场面打脸, 解场后随从打脸, 解场后武器打脸, 法术直伤打脸, 英雄技能打脸)。
        战吼打脸见 overlay_battlecry_face()；法术英雄攻见 overlay_hero_buff_face()。
        展示场攻 = 随从 + 英 + 武器 + 法术 + 战吼 + 技能。
        """
        pure = getattr(self, "_overlay_pure_board_face", 0)
        minion = getattr(self, "_overlay_board_face", 0)
        weapon = getattr(self, "_overlay_weapon_face", 0)
        spell = getattr(self, "_overlay_spell_face", 0)
        hero_power = getattr(self, "_overlay_hero_power_face", 0)
        return pure, minion, weapon, spell, hero_power

    def overlay_battlecry_face(self) -> int:
        """战吼随从等造成的打脸分量（不计入法术分项）。"""
        return getattr(self, "_overlay_battlecry_face", 0)

    def overlay_hero_buff_face(self) -> int:
        """法术/战吼等赋予的当回合英雄攻击力打脸分量。"""
        return getattr(self, "_overlay_hero_buff_face", 0)

    def overlay_calc_elapsed_ms(self) -> Optional[float]:
        """最近一次顶层场攻(Overlay)计算耗时（毫秒）。"""
        ms = getattr(self, "_overlay_calc_ms", None)
        return ms if ms is not None else None

    @staticmethod
    def format_overlay_calc_ms(ms: Optional[float]) -> str:
        if ms is None:
            return ""
        if ms >= 1000:
            return f"{ms / 1000:.2f}s"
        if ms >= 100:
            return f"{ms:.0f}ms"
        if ms >= 10:
            return f"{ms:.0f}ms"
        return f"{ms:.1f}ms"

    _OVERLAY_PROMPT_SNAPSHOT_KEYS = (
        "_overlay_best_seq",
        "_overlay_best_hp_name",
        "_overlay_best_order",
        "_overlay_face_computed",
        "_overlay_incomplete",
        "_overlay_pure_board_face",
        "_overlay_board_face",
        "_overlay_weapon_face",
        "_overlay_spell_face",
        "_overlay_battlecry_face",
        "_overlay_hero_power_face",
        "_overlay_hero_buff_face",
        "_overlay_lifesteal_heal",
        "_overlay_deathrattle_armor",
        "_overlay_total_face",
        "_overlay_mc_max",
        "_overlay_lethal_prob",
        "_overlay_uses_random",
        "_overlay_top_outcomes",
        "_overlay_spell_note",
        "_overlay_mana_budget",
        "_overlay_mana_spent",
    )

    def overlay_spell_resolving(self) -> bool:
        """我方法术仍在 PLAY 区结算（手牌已扣、效果未入账）。"""
        local = self.game_state.local_player_id
        if local is None or not self.is_local_turn():
            return False
        from .spell_board import BOARD_CLEAR_SPELLS

        for entity in list(self.game_state.entities.values()):
            if entity.zone != "PLAY":
                continue
            if not self.game_state.is_entity_controlled_by(entity, local):
                continue
            cid = entity.card_id or ""
            if entity.cardtype == "SPELL" or cid in BOARD_CLEAR_SPELLS:
                return True
        return False

    def _save_overlay_prompt_snapshot_if_lethal(self) -> None:
        """本地回合斩杀可成立时缓存 Overlay，供法术结算动画期间恢复。"""
        if not self.is_local_turn():
            return
        if not getattr(self, "_overlay_face_computed", False):
            return
        if getattr(self, "_overlay_incomplete", False):
            return
        face = getattr(self, "_overlay_total_face", 0)
        eff = self._lethal_threshold_hp(subtract_overlay_lifesteal=True)
        if face < eff:
            return
        snap: dict = {}
        for key in self._OVERLAY_PROMPT_SNAPSHOT_KEYS:
            value = getattr(self, key, None)
            if key == "_overlay_best_seq":
                value = list(value) if value else []
            elif key == "_overlay_top_outcomes":
                value = list(value) if value else []
            snap[key] = value
        self._overlay_prompt_snapshot = snap

    def _restore_overlay_prompt_snapshot_if_needed(self) -> bool:
        """法术结算中且重算场攻为 0/骤降时，恢复打出前的斩杀 Overlay。"""
        if not self.overlay_spell_resolving():
            return False
        snap = getattr(self, "_overlay_prompt_snapshot", None)
        if not snap:
            return False
        for key, value in snap.items():
            if key == "_overlay_best_seq":
                value = list(value) if value else []
            elif key == "_overlay_top_outcomes":
                value = list(value) if value else []
            setattr(self, key, value)
        return True

    def clear_overlay_cache(self) -> None:
        """对局结束/空闲时清空斩杀步骤与场攻缓存，避免浮层残留上一场数据。"""
        self._overlay_prompt_snapshot = None
        self._overlay_best_seq = []
        self._overlay_best_hp_name = None
        self._overlay_best_order = "spell_first"
        self._overlay_face_computed = False
        self._overlay_incomplete = False
        self._overlay_pure_board_face = 0
        self._overlay_board_face = 0
        self._overlay_weapon_face = 0
        self._overlay_spell_face = 0
        self._overlay_battlecry_face = 0
        self._overlay_hero_power_face = 0
        self._overlay_hero_buff_face = 0
        self._overlay_lifesteal_heal = 0
        self._overlay_deathrattle_armor = 0
        self._overlay_total_face = 0
        self._overlay_mc_max = 0
        self._overlay_lethal_prob = 0.0
        self._overlay_uses_random = False
        self._overlay_top_outcomes = []
        self._overlay_spell_note = ""
        self._overlay_mana_budget = 0
        self._overlay_mana_spent = 0
        self._overlay_calc_ms = None

    def cached_overlay_face(self) -> int:
        """返回本轮已算好的场攻（含回合结束），用于斩杀判定。"""
        if (
            getattr(self, "_overlay_face_computed", False)
            and not getattr(self, "_overlay_incomplete", False)
        ):
            return getattr(self, "_overlay_total_face", 0)
        return self.overlay_board_face_damage()

    def overlay_hand_charge_face(self) -> int:
        """手牌冲锋等打出后计入斩杀、但不计入场攻主数字的分量。"""
        if not getattr(self, "_overlay_face_computed", False):
            return 0
        local = self.game_state.local_player_id
        if local is None:
            return 0
        # 无手牌冲锋时不走残差公式，避免武器/装备法术伤害误显示为「冲」
        if not collect_hand_charge_minions(self.game_state, local):
            return 0
        total = getattr(self, "_overlay_total_face", 0)
        dormant_et = 0
        if local is not None:
            opp = self.game_state.opponent_player_id
            opp_hero = self.game_state.get_hero(opp) if opp is not None else None
            from .board_damage import hero_has_divine_shield
            dormant_et = self._board_dormant_end_turn_face(
                local, hero_has_divine_shield(opp_hero),
            )
        board_only = (
            getattr(self, "_overlay_pure_board_face", 0)
            + getattr(self, "_overlay_board_face", 0)
            + getattr(self, "_overlay_weapon_face", 0)
            + getattr(self, "_overlay_spell_face", 0)
            + getattr(self, "_overlay_hero_power_face", 0)
            + getattr(self, "_overlay_hero_buff_face", 0)
            + getattr(self, "_overlay_battlecry_face", 0)
        )
        return max(0, total - dormant_et - board_only)

    def overlay_display_face(self) -> int:
        """Overlay 场攻主数字：法术后场面+法术/技能/战吼，不含手牌冲锋与休眠回合结束。"""
        if not getattr(self, "_overlay_face_computed", False):
            return self.cached_overlay_face()
        hand_charge = self.overlay_hand_charge_face()
        minion_board = max(
            0,
            getattr(self, "_overlay_board_face", 0) - hand_charge,
        )
        return (
            minion_board
            + getattr(self, "_overlay_weapon_face", 0)
            + getattr(self, "_overlay_spell_face", 0)
            + getattr(self, "_overlay_hero_power_face", 0)
            + getattr(self, "_overlay_hero_buff_face", 0)
            + getattr(self, "_overlay_battlecry_face", 0)
        )

    def overlay_dormant_end_turn_face(self) -> int:
        """休眠随从等回合结束打脸（计入斩杀总数，分项单独显示「回」）。"""
        return self.overlay_end_turn_face_for_display(dormant_only=True)

    def overlay_end_turn_face_for_display(self, *, dormant_only: bool = False) -> int:
        """场上已注册回合结束源的打脸（非残差估算）。"""
        if not getattr(self, "_overlay_face_computed", False):
            return 0
        local = self.game_state.local_player_id
        if local is None:
            return 0
        opp = self.game_state.opponent_player_id
        opp_hero = self.game_state.get_hero(opp) if opp is not None else None
        from .board_damage import hero_has_divine_shield

        shield = hero_has_divine_shield(opp_hero)
        enemy_board = self._build_enemy_minion_states(local)
        if dormant_only:
            return self._board_dormant_end_turn_face(
                local, shield, enemy_board=enemy_board,
            )
        return self._board_end_turn_face(
            local, shield, enemy_board=enemy_board,
        )

    def _reset_overlay_board_breakdown(
        self,
        pure: int,
        minion_board: int,
        spell_direct: int,
        total: int,
        *,
        weapon_board: int = 0,
        hero_power_face: int = 0,
        hero_buff_face: int = 0,
        battlecry_face: int = 0,
        mc_max: Optional[int] = None,
        lethal_prob: Optional[float] = None,
        uses_random: bool = False,
        top_outcomes: Optional[List[Tuple[int, float]]] = None,
    ) -> None:
        self._overlay_pure_board_face = pure
        self._overlay_board_face = minion_board
        self._overlay_weapon_face = weapon_board
        self._overlay_spell_face = spell_direct
        self._overlay_battlecry_face = battlecry_face
        self._overlay_hero_power_face = hero_power_face
        self._overlay_hero_buff_face = hero_buff_face
        self._overlay_total_face = total
        self._overlay_mc_max = mc_max if mc_max is not None else total
        if lethal_prob is not None:
            self._overlay_lethal_prob = lethal_prob
        else:
            eff = self._lethal_threshold_hp()
            self._overlay_lethal_prob = 1.0 if total >= eff else 0.0
        self._overlay_uses_random = uses_random
        self._overlay_top_outcomes = top_outcomes or []
        self._overlay_face_computed = True
        self._overlay_incomplete = False

    @staticmethod
    def _mana_after_spell_sequence(seq: List, available_mana: Optional[int]) -> Optional[int]:
        from .spell_board import spell_sequence_mana_left

        return spell_sequence_mana_left(seq, available_mana)

    @staticmethod
    def _hand_charge_fighter(entity, atk: int, *, entity_id: Optional[int] = None) -> dict:
        hp = entity.current_health if entity.current_health > 0 else entity.health
        return {
            "kind": "minion",
            "entity_id": entity.entity_id if entity_id is None else entity_id,
            "card_id": entity.card_id or "",
            "atk": atk,
            "health": max(hp, 1),
            "shield": entity.tags.get("DIVINE_SHIELD", 0) == 1,
            "poisonous": entity.tags.get("POISONOUS", 0) == 1,
            "attacks_left": 1,
            "can_face": True,
            "charge": True,
            "from_hand": True,
        }

    def _append_hand_charge_fighters(
        self,
        fighters: List[dict],
        entity,
        atk: int,
        player_id: Optional[int],
    ) -> None:
        fighters.append(self._hand_charge_fighter(entity, atk))
        if (
            player_id is not None
            and double_agent_summons_copy(self.game_state, player_id, entity)
        ):
            fighters.append(
                self._hand_charge_fighter(entity, atk, entity_id=-entity.entity_id),
            )

    def _add_playable_hand_charges(
        self,
        fighters: List[dict],
        hand_charges: List,
        mana_left: Optional[int],
        *,
        player_id: Optional[int] = None,
    ) -> List[Tuple]:
        """在剩余法力内把手牌冲锋加入攻击者列表。返回实际打出的 (entity, cost, atk)。"""
        if not hand_charges:
            return []
        pid = player_id if player_id is not None else self.game_state.local_player_id
        played: List[Tuple] = []
        budget = mana_left
        for entity, cost, atk in sorted(hand_charges, key=lambda x: -x[2]):
            if budget is not None and cost > budget:
                continue
            self._append_hand_charge_fighters(fighters, entity, atk, pid)
            played.append((entity, cost, atk))
            if budget is not None:
                budget -= cost
        return played

    def _prepare_line_with_hero_power(
        self,
        fighters: List[dict],
        player_id: int,
        mana: Optional[int],
        *,
        use_hp: bool,
        defender_shield: bool = False,
        enemy: Optional[List[dict]] = None,
        hp_mode: str = "face",
    ) -> Tuple[List[dict], Optional[int], Optional[str], SpellApplyResult]:
        """可选：先使用英雄技能，返回 (fighters, 剩余法力, 技能名, 技能结果)。"""
        if not use_hp:
            return _clone_combat_states(fighters), mana, None, SpellApplyResult()
        fs = _clone_combat_states(fighters)
        next_turn = self._hero_power_next_turn()
        row = usable_hero_power(
            self.game_state, player_id, mana or 0, next_turn=next_turn,
        )
        if row is None:
            return fs, mana, None, SpellApplyResult()
        _hp, defn, cost = row
        if hp_mode == "setup":
            from .damaged_spell_power import apply_mage_fireblast_setup
            if not apply_mage_fireblast_setup(fs):
                return _clone_combat_states(fighters), mana, None, SpellApplyResult()
            mana_left = None if mana is None else mana - cost
            return fs, mana_left, defn.name, SpellApplyResult()
        applied, mana_left, hp_res = apply_hero_power_to_fighters(
            self.game_state, player_id, fs, mana, enemy_shield=defender_shield,
            next_turn=next_turn, taunts=_clone_combat_states(enemy or []),
        )
        if not applied:
            return fs, mana, None, SpellApplyResult()
        return fs, mana_left, defn.name, hp_res

    @staticmethod
    def _stolen_minion_face(fighters: List[dict], defender_shield: bool = False) -> int:
        """疯狂药水等偷来的随从打脸：计入法术分项，不算场面随从。"""
        stolen_fs = [
            f for f in fighters
            if f.get("kind") == "minion" and f.get("stolen_turn")
        ]
        return LethalChecker._fighters_face_damage(stolen_fs, defender_shield)

    @staticmethod
    def _category_face_hits(fighters: List[dict]) -> List[int]:
        """单类攻击者的打脸命中列表（不含圣盾）。"""
        hits = list(LethalChecker._fighters_face_hits(fighters))
        for f in fighters:
            if f.get("kind") != "weapon" or f.get("health", 0) <= 0:
                continue
            if not f.get("can_face", True):
                continue
            aoe = int(f.get("hero_aoe_on_attack", 0) or 0)
            if aoe <= 0:
                continue
            n = min(f.get("attacks_left", 0), f.get("durability", 0))
            hits.extend([aoe] * n)
        return hits

    @staticmethod
    def _split_fighter_face(fighters: List[dict], defender_shield: bool = False) -> Tuple[int, int, int, int]:
        """将剩余可打脸伤害拆为 (随从, 武器, 法术英雄攻, 英雄技能)。

        对手英雄圣盾只破一次：必须合并所有命中后再扣最小一击，
        不可对随从/武器分项各自扣圣盾（否则会重复浪费破盾）。
        """
        minion_fs = [
            f for f in fighters
            if f.get("kind") == "minion"
            and not f.get("from_hero_power")
            and not f.get("stolen_turn")
        ]
        weapon_fs = [f for f in fighters if f.get("kind") == "weapon"]
        hero_buff_fs = [
            f for f in fighters
            if f.get("kind") == "hero" and not f.get("from_hero_power")
        ]
        hp_fs = [f for f in fighters if f.get("from_hero_power")]
        from .rush_combat import inquisitor_face_mirror_hits

        # 跟刀按全场英雄挥击次数计，并入随从分项
        minion_hits = (
            LethalChecker._category_face_hits(minion_fs)
            + inquisitor_face_mirror_hits(fighters, [])
        )
        weapon_hits = LethalChecker._category_face_hits(weapon_fs)
        hero_buff_hits = LethalChecker._category_face_hits(hero_buff_fs)
        hp_hits = LethalChecker._category_face_hits(hp_fs)

        buckets = [minion_hits, weapon_hits, hero_buff_hits, hp_hits]
        if not defender_shield:
            return (
                sum(minion_hits),
                sum(weapon_hits),
                sum(hero_buff_hits),
                sum(hp_hits),
            )

        all_hits: List[int] = []
        owners: List[int] = []
        for i, hits in enumerate(buckets):
            for h in hits:
                all_hits.append(h)
                owners.append(i)
        if not all_hits:
            return (0, 0, 0, 0)

        soak = min(all_hits)
        soak_at = all_hits.index(soak)
        soaked_bucket = owners[soak_at]
        out = [sum(b) for b in buckets]
        out[soaked_bucket] = max(0, out[soaked_bucket] - soak)
        return (out[0], out[1], out[2], out[3])

    @staticmethod
    def _spell_face_including_stolen(
        fs: List[dict],
        spell_face: int,
        defender_shield: bool,
    ) -> int:
        return spell_face + LethalChecker._stolen_minion_face(fs, defender_shield)

    @staticmethod
    def _face_parts_from_fighters(
        fs: List[dict],
        spell_face: int,
        hp_direct: int,
        defender_shield: bool,
    ) -> Tuple[int, int, int, int, int, int]:
        minion_f, weapon_f, hero_buff_f, hp_f = LethalChecker._split_fighter_face(
            fs, defender_shield,
        )
        spell_face = LethalChecker._spell_face_including_stolen(
            fs, spell_face, defender_shield,
        )
        hp_total = hp_direct + hp_f
        total = minion_f + weapon_f + hero_buff_f + spell_face + hp_total
        return total, minion_f, weapon_f, spell_face, hp_total, hero_buff_f

    def _should_consider_hold_attack(self, fighters: Optional[List[dict]] = None) -> bool:
        """棘嗣幼龙等 HOLD 随从在场/手牌可打出/本回合 sim 打出时，评估攻击子集。"""
        local = self.game_state.local_player_id
        if local is None:
            return False
        if has_hold_attack_end_turn_on_board(self.game_state.get_board(local)):
            return True
        if fighters and has_hold_attack_end_turn_in_fighters(fighters):
            return True
        mana = self._overlay_mana_for_spells(local)
        from .end_turn_hand_board import hand_hold_attack_minions
        if hand_hold_attack_minions(self.game_state, local, mana or 0):
            return True
        return False

    def _attack_subset_eids_list(self, fighters: List[dict]) -> List[Set[int]]:
        """可攻击随从的全部攻击子集（含空集=全不攻、全集=全攻）。"""
        eids: List[int] = []
        for f in fighters:
            if f.get("attacks_left", 0) <= 0 or f.get("health", 0) <= 0:
                continue
            eid = f.get("entity_id")
            if eid is not None:
                eids.append(eid)
        if not eids:
            return [set()]
        return [
            {eids[i] for i in range(len(eids)) if mask & (1 << i)}
            for mask in range(1 << len(eids))
        ]

    def _run_masked_attack_phase(
        self,
        fighters: List[dict],
        enemy: List[dict],
        allowed_eids: Set[int],
        defender_shield: bool,
        *,
        rng: Optional[random.Random] = None,
    ) -> Tuple[List[dict], List[dict], int]:
        """仅 allowed_eids 中的随从参与当回合攻击，返回 (敌方场面, 己方 fighters, 打脸)。"""
        fs = _clone_combat_states(fighters)
        enemy_board = _clone_combat_states(enemy)
        fs, _ = self._mask_fighter_attacks(fs, allowed_eids)
        taunts = self._living_taunt_states(enemy_board)
        if taunts:
            self._exhaust_attacks_on_taunts(
                fs, taunts, enemy_board=enemy_board, rng=rng,
            )
        face = 0
        if not self._living_taunt_states(enemy_board):
            face = self._fighters_face_damage(fs, defender_shield)
        return enemy_board, fs, face

    def _finish_hold_after_attacks(
        self,
        enemy: List[dict],
        fs: List[dict],
        spell_face: int,
        hp_direct: int,
        defender_shield: bool,
        *,
        rng: Optional[random.Random] = None,
        fighters_for_et: Optional[List[dict]] = None,
    ) -> Tuple[int, int, int, int, int, int]:
        """攻击阶段已结束（可部分随从未攻），结算剩余打脸 + 回合结束。"""
        if self._living_taunt_states(enemy):
            minion_board = 0
            weapon_board = 0
            hero_buff_board = 0
            hp_board = hp_direct
        else:
            minion_board, weapon_board, hero_buff_board, remain_hp = (
                self._split_fighter_face(fs, defender_shield)
            )
            hp_board = hp_direct + remain_hp
            spell_face = self._spell_face_including_stolen(fs, spell_face, defender_shield)
        total_before_et = (
            minion_board + weapon_board + hero_buff_board + spell_face + hp_board
        )
        return self._apply_end_turn_face(
            enemy, defender_shield, total_before_et,
            minion_board, weapon_board, spell_face, hp_board,
            hero_buff_board=hero_buff_board,
            rng=rng, fighters=fighters_for_et or fs,
        )

    def _peak_line_face_after_state(
        self,
        enemy: List[dict],
        fs: List[dict],
        spell_face: int,
        hp_direct: int,
        defender_shield: bool,
        *,
        rng: Optional[random.Random] = None,
    ) -> int:
        """当前场面下最优攻击/打脸 + 回合结束的上界总伤（供突袭换随从择优）。"""
        if self._should_consider_hold_attack(fs):
            outcomes = [
                self._finish_hold_attack_subset_line_inner(
                    enemy, fs, subset, spell_face, hp_direct, defender_shield, rng=rng,
                )
                for subset in self._attack_subset_eids_list(fs)
            ]
            return max(outcomes, key=lambda x: x[0])[0]
        living_taunts = self._living_taunt_states(enemy)
        if living_taunts:
            face, _, can_clear = self._simulate_taunt_clear_from_state(
                fs, living_taunts, defender_shield, enemy_board=enemy,
            )
            if not can_clear:
                total = spell_face + hp_direct
            else:
                minion_board, weapon_board, hero_buff_board, remain_hp = (
                    self._split_fighter_face(fs, defender_shield)
                )
                spell_face = self._spell_face_including_stolen(
                    fs, spell_face, defender_shield,
                )
                total = (
                    minion_board + weapon_board + hero_buff_board
                    + spell_face + hp_direct + remain_hp
                )
        else:
            total, _, _, _, _, _ = self._face_parts_from_fighters(
                fs, spell_face, hp_direct, defender_shield,
            )
        return self._apply_end_turn_face(
            enemy, defender_shield, total, 0, 0, spell_face, hp_direct,
            rng=rng, fighters=fs,
        )[0]

    def _exhaust_rush_on_enemies(
        self,
        fs: List[dict],
        enemy: List[dict],
        defender_shield: bool,
        *,
        spell_face: int = 0,
        hp_direct: int = 0,
        rng: Optional[random.Random] = None,
    ) -> Tuple[List[dict], List[dict]]:
        """法术/战吼后：突袭随从先换敌方随从，再进入常规攻击阶段。"""
        from .combat_sim import exhaust_rush_on_enemy_minions

        return exhaust_rush_on_enemy_minions(
            fs, enemy, defender_shield,
            score_after=lambda f, e: self._peak_line_face_after_state(
                e, f, spell_face, hp_direct, defender_shield, rng=rng,
            ),
        )

    def _finish_hold_attack_subset_line(
        self,
        enemy: List[dict],
        fs: List[dict],
        allowed_eids: Set[int],
        spell_face: int,
        hp_direct: int,
        defender_shield: bool,
        *,
        rng: Optional[random.Random] = None,
    ) -> Tuple[int, int, int, int, int, int]:
        """先法后攻：法术已打完，突袭换随从，再按子集攻击，最后回合结束。"""
        fs, enemy = self._exhaust_rush_on_enemies(
            fs, enemy, defender_shield,
            spell_face=spell_face, hp_direct=hp_direct, rng=rng,
        )
        return self._finish_hold_attack_subset_line_inner(
            enemy, fs, allowed_eids, spell_face, hp_direct, defender_shield, rng=rng,
        )

    def _finish_hold_attack_subset_line_inner(
        self,
        enemy: List[dict],
        fs: List[dict],
        allowed_eids: Set[int],
        spell_face: int,
        hp_direct: int,
        defender_shield: bool,
        *,
        rng: Optional[random.Random] = None,
    ) -> Tuple[int, int, int, int, int, int]:
        """先法后攻：法术已打完，再按子集攻击，最后回合结束。"""
        enemy_work, fs_work, _ = self._run_masked_attack_phase(
            fs, enemy, allowed_eids, defender_shield, rng=rng,
        )
        return self._finish_hold_after_attacks(
            enemy_work, fs_work, spell_face, hp_direct, defender_shield,
            rng=rng, fighters_for_et=fs,
        )

    def _apply_end_turn_face(
        self,
        enemy: List[dict],
        defender_shield: bool,
        total: int,
        minion_board: int,
        weapon_board: int,
        spell_face: int,
        hp_board: int,
        *,
        hero_buff_board: int = 0,
        rng: Optional[random.Random] = None,
        fighters: Optional[List[dict]] = None,
    ) -> Tuple[int, int, int, int, int, int]:
        """在当回合攻击/法术结算后追加回合结束打脸。"""
        local = self.game_state.local_player_id
        if local is None:
            return (
                total, minion_board, weapon_board, spell_face, hp_board, hero_buff_board,
            )
        our_board = self.game_state.get_board(local)
        # 随机回合结束：确定性模拟（rng=None）不在此乐观加脸，交给 MC
        if rng is None and (
            end_turn_uses_random(our_board)
            or end_turn_uses_random_fighters(fighters)
        ):
            return (
                total, minion_board, weapon_board, spell_face, hp_board, hero_buff_board,
            )
        extra = sim_end_turn_entities_from_fighters(fighters)
        eff_hp = self._lethal_threshold_hp()
        hero_hp_after = max(0, eff_hp - max(0, int(total)))
        et_face, _ = end_turn_face_damage(
            our_board, enemy, defender_shield,
            game_state=self.game_state, player_id=local, rng=rng,
            extra_board_entities=extra or None,
            opponent_hero_hp=hero_hp_after,
        )
        if et_face <= 0:
            return (
                total, minion_board, weapon_board, spell_face, hp_board, hero_buff_board,
            )
        # 回合结束打脸计入 total（斩杀），但不并入 minion_board（场攻分项只含可攻击随从）
        return (
            total + et_face,
            minion_board,
            weapon_board,
            spell_face,
            hp_board,
            hero_buff_board,
        )

    @staticmethod
    def _unpack_face_outcome(
        outcome: Tuple[int, ...],
    ) -> Tuple[int, int, int, int, int, int, int, int, int]:
        if len(outcome) >= 9:
            return (
                outcome[0], outcome[1], outcome[2], outcome[3],
                outcome[4], outcome[5], outcome[6], outcome[7], outcome[8],
            )
        if len(outcome) >= 8:
            return (
                outcome[0], outcome[1], outcome[2], outcome[3],
                outcome[4], outcome[5], outcome[6], outcome[7], 0,
            )
        if len(outcome) >= 7:
            return (
                outcome[0], outcome[1], outcome[2], outcome[3],
                outcome[4], outcome[5], outcome[6], 0, 0,
            )
        if len(outcome) >= 6:
            return (
                outcome[0], outcome[1], outcome[2], outcome[3],
                outcome[4], outcome[5], 0, 0, 0,
            )
        return outcome[0], outcome[1], outcome[2], outcome[3], outcome[4], outcome[5], 0, 0, 0

    def _attach_lifesteal(
        self,
        outcome: Tuple[int, ...],
        lifesteal_heal: int,
        *,
        enemy_board: Optional[List[dict]] = None,
        deathrattle_armor: Optional[int] = None,
        battlecry_face: Optional[int] = None,
    ) -> Tuple[int, int, int, int, int, int, int, int, int]:
        (
            total, minion_board, weapon_board, spell_face, hp_board,
            hero_buff_board, _, _, bc_unpacked,
        ) = self._unpack_face_outcome(outcome)
        bc = bc_unpacked if battlecry_face is None else battlecry_face
        if deathrattle_armor is None:
            deathrattle_armor = sim_armor_gain(enemy_board) if enemy_board else 0
        return (
            total, minion_board, weapon_board, spell_face, hp_board,
            hero_buff_board, lifesteal_heal, deathrattle_armor, bc,
        )

    @staticmethod
    def _hero_dead_after_spells(hero_hp_after: Optional[int]) -> bool:
        return hero_hp_after is not None and hero_hp_after <= 0

    def _face_outcome_hero_dead_after_spells(
        self,
        enemy: List[dict],
        spell_res: SpellApplyResult,
        defender_shield: bool,
        hp_direct: int = 0,
        *,
        board_face: int = 0,
        lifesteal_heal: int = 0,
        rng: Optional[random.Random] = None,
    ) -> Tuple[int, int, int, int, int, int, int, int, int]:
        """法术自伤致死后不再随从攻击；同回合先攻打脸仍计入。"""
        spell_face = spell_res.direct_face_damage
        battlecry_face = spell_res.battlecry_face_damage
        total = board_face + spell_face + battlecry_face + hp_direct
        return self._attach_lifesteal(
            self._apply_end_turn_face(
                enemy, defender_shield, total,
                board_face, 0, spell_face, hp_direct,
                rng=rng,
            ),
            lifesteal_heal,
            enemy_board=enemy,
            battlecry_face=battlecry_face,
        )

    def _spell_first_face_from_state(
        self,
        enemy: List[dict],
        fs: List[dict],
        spell_res: SpellApplyResult,
        mana_left: Optional[int],
        charges: List,
        defender_shield: bool,
        hp_direct: int = 0,
        *,
        rng: Optional[random.Random] = None,
        hero_hp_after_spells: Optional[int] = None,
    ) -> Tuple[int, int, int, int, int, int, int, int, int]:
        """法术已全部打完后的随从/武器打脸 + 法术直伤 + 技能直伤 + 清嘲吸血/亡语加甲。"""
        if self._hero_dead_after_spells(hero_hp_after_spells):
            return self._face_outcome_hero_dead_after_spells(
                enemy, spell_res, defender_shield, hp_direct,
                lifesteal_heal=int(spell_res.opponent_lifesteal_heal or 0),
                rng=rng,
            )
        self._add_playable_hand_charges(fs, charges, mana_left)
        spell_face = spell_res.direct_face_damage
        battlecry_face = spell_res.battlecry_face_damage
        spell_component = spell_face + battlecry_face
        spell_ls = int(spell_res.opponent_lifesteal_heal or 0)
        if self._should_consider_hold_attack(fs):
            outcomes = [
                self._finish_hold_attack_subset_line(
                    enemy, fs, subset, spell_component, hp_direct, defender_shield, rng=rng,
                )
                for subset in self._attack_subset_eids_list(fs)
            ]
            return max(
                (
                    self._attach_lifesteal(
                        o, spell_ls, enemy_board=enemy, battlecry_face=battlecry_face,
                    )
                    for o in outcomes
                ),
                key=lambda x: x[0],
            )

        fs, enemy = self._exhaust_rush_on_enemies(
            fs, enemy, defender_shield,
            spell_face=spell_component, hp_direct=hp_direct, rng=rng,
        )
        from .combat_sim import rush_enable_face_if_no_enemy_minions

        rush_enable_face_if_no_enemy_minions(fs, enemy)
        living_taunts = self._living_taunt_states(enemy)
        if living_taunts:
            _, clear_ls, can_clear = self._simulate_taunt_clear_from_state(
                fs, living_taunts, defender_shield,
                extra_lifesteal_heal=spell_ls,
                enemy_board=enemy,
            )
            line_ls = clear_ls
            if not can_clear:
                line_ls = max(spell_ls, clear_ls)
                if spell_component <= 0 and hp_direct <= 0:
                    return self._attach_lifesteal(
                        self._apply_end_turn_face(
                            enemy, defender_shield, 0, 0, 0, 0, 0, rng=rng, fighters=fs,
                        ),
                        line_ls,
                        enemy_board=enemy,
                        battlecry_face=battlecry_face,
                    )
                return self._attach_lifesteal(
                    self._apply_end_turn_face(
                        enemy, defender_shield,
                        spell_component + hp_direct, 0, 0, spell_face, hp_direct,
                        rng=rng, fighters=fs,
                    ),
                    line_ls,
                    enemy_board=enemy,
                    battlecry_face=battlecry_face,
                )
            minion_board, weapon_board, hero_buff_board, remain_hp = (
                self._split_fighter_face(fs, defender_shield)
            )
            hp_board = hp_direct + remain_hp
            spell_face = self._spell_face_including_stolen(fs, spell_face, defender_shield)
            total = (
                minion_board + weapon_board + hero_buff_board
                + spell_face + battlecry_face + hp_board
            )
            return self._attach_lifesteal(
                self._apply_end_turn_face(
                    enemy, defender_shield, total,
                    minion_board, weapon_board, spell_face, hp_board,
                    hero_buff_board=hero_buff_board,
                    rng=rng, fighters=fs,
                ),
                line_ls,
                enemy_board=enemy,
                battlecry_face=battlecry_face,
            )
        total, minion_board, weapon_board, spell_face, hp_board, hero_buff_board = (
            self._face_parts_from_fighters(
                fs, spell_component, hp_direct, defender_shield,
            )
        )
        spell_face -= battlecry_face
        return self._attach_lifesteal(
            self._apply_end_turn_face(
                enemy, defender_shield, total,
                minion_board, weapon_board, spell_face, hp_board,
                hero_buff_board=hero_buff_board,
                rng=rng, fighters=fs,
            ),
            spell_ls,
            enemy_board=enemy,
            battlecry_face=battlecry_face,
        )

    def _simulate_line_outcome(
        self,
        base_enemy_minions: List[dict],
        fighters: List[dict],
        seq: List,
        order: str,
        *,
        spell_mult: int,
        defender_shield: bool,
        rng: Optional[random.Random] = None,
        available_mana: Optional[int] = None,
        hand_charges: Optional[List] = None,
        hp_direct: int = 0,
        extra_spell_face: int = 0,
    ) -> Tuple[int, int, int, int, int, int, int, int, int]:
        """返回 (总打脸, 随从打脸, 武器打脸, 法术直伤, 英雄技能, 法术英雄攻, 清嘲吸血, 亡语加甲, 战吼打脸)。"""
        enemy = _clone_combat_states(base_enemy_minions)
        fs = _clone_combat_states(fighters)
        hero_hp = self._my_hero_hp_for_spells()
        charges = hand_charges or []

        def _add_extra(res: SpellApplyResult) -> SpellApplyResult:
            if extra_spell_face:
                res.direct_face_damage += extra_spell_face
            return res

        if order == "spell_first":
            spell_res, hp_end, mana_end = apply_spell_sequence_with_meta(
                enemy, fs, seq, spell_mult=spell_mult,
                enemy_shield=defender_shield, rng=rng,
                gs=self.game_state, player_id=self.game_state.local_player_id,
                hero_hp=hero_hp, mana_budget=available_mana,
                next_turn_preview=self._hero_power_next_turn(),
            )
            return self._spell_first_face_from_state(
                enemy, fs, _add_extra(spell_res), mana_end, charges, defender_shield, hp_direct,
                rng=rng, hero_hp_after_spells=hp_end,
            )
        else:
            outcomes: List[Tuple[int, int, int, int, int, int, int, int]] = []
            if self._should_consider_hold_attack(fs):
                for subset in self._attack_subset_eids_list(fighters):
                    enemy_hold = _clone_combat_states(base_enemy_minions)
                    fs_hold = _clone_combat_states(fighters)
                    enemy_hold, fs_hold, _ = self._run_masked_attack_phase(
                        fs_hold, enemy_hold, subset, defender_shield, rng=rng,
                    )
                    spell_res_hold, hp_end_hold, _ = apply_spell_sequence_with_meta(
                        enemy_hold, fs_hold, seq, spell_mult=spell_mult,
                        enemy_shield=defender_shield, rng=rng,
                        gs=self.game_state, player_id=self.game_state.local_player_id,
                        hero_hp=hero_hp, mana_budget=available_mana,
                        next_turn_preview=self._hero_power_next_turn(),
                    )
                    spell_res_hold.direct_face_damage += extra_spell_face
                    mana_end = self._mana_after_spell_sequence(seq, available_mana)
                    if self._hero_dead_after_spells(hp_end_hold):
                        outcomes.append(self._face_outcome_hero_dead_after_spells(
                            enemy_hold, spell_res_hold, defender_shield, hp_direct,
                            lifesteal_heal=int(spell_res_hold.opponent_lifesteal_heal or 0),
                            rng=rng,
                        ))
                        continue
                    self._add_playable_hand_charges(fs_hold, charges, mana_end)
                    outcomes.append(self._attach_lifesteal(
                        self._finish_hold_after_attacks(
                            enemy_hold, fs_hold, spell_res_hold.direct_face_damage, hp_direct,
                            defender_shield, rng=rng, fighters_for_et=fs_hold,
                        ),
                        int(spell_res_hold.opponent_lifesteal_heal or 0),
                        enemy_board=enemy_hold,
                    ))

            taunts = self._living_taunt_states(enemy)
            board_face, attack_heal, fs, taunts_after = self._run_attack_phase(
                fs, taunts, defender_shield, enemy_board=enemy, rng=rng,
            )
            self._sync_taunt_states_after_attack(enemy, taunts_after)
            opp_hp_for_spell = self._opponent_hero_hp_after_face_damage(
                defender_shield, board_face,
            )
            spell_res, hp_end, _ = apply_spell_sequence_with_meta(
                enemy, fs, seq, spell_mult=spell_mult,
                enemy_shield=defender_shield, rng=rng,
                gs=self.game_state, player_id=self.game_state.local_player_id,
                hero_hp=hero_hp, mana_budget=available_mana,
                opponent_hero_hp=opp_hp_for_spell,
                next_turn_preview=self._hero_power_next_turn(),
            )
            spell_res.direct_face_damage += extra_spell_face
            if self._hero_dead_after_spells(hp_end):
                return self._face_outcome_hero_dead_after_spells(
                    enemy, spell_res, defender_shield, hp_direct,
                    board_face=board_face,
                    lifesteal_heal=attack_heal + int(spell_res.opponent_lifesteal_heal or 0),
                    rng=rng,
                )
            mana_left = self._mana_after_spell_sequence(seq, available_mana)
            self._add_playable_hand_charges(fs, charges, mana_left)
            taunts2 = self._living_taunt_states(enemy)
            spell_face = spell_res.direct_face_damage
            spell_ls = int(spell_res.opponent_lifesteal_heal or 0)
            if taunts2:
                clear_face, clear_ls, can_clear = self._simulate_taunt_clear_from_state(
                    fs, taunts2, defender_shield,
                    extra_lifesteal_heal=spell_ls,
                    enemy_board=enemy, rng=rng,
                )
                line_ls = attack_heal + clear_ls
                spell_face = self._spell_face_including_stolen(
                    fs, spell_face, defender_shield,
                )
                clear_board_total = 0
                if can_clear:
                    minion_board, weapon_board, hero_buff_board, remain_hp = (
                        self._split_fighter_face(fs, defender_shield)
                    )
                    clear_board_total = (
                        minion_board + weapon_board + hero_buff_board
                        + spell_face + hp_direct + remain_hp
                    )
                elif spell_face > 0 or hp_direct > 0:
                    clear_board_total = spell_face + hp_direct
                board_path_total = board_face + spell_face + hp_direct
                if board_face > 0 and board_path_total >= clear_board_total:
                    outcomes.append(self._attach_lifesteal(
                        self._apply_end_turn_face(
                            enemy, defender_shield, board_path_total,
                            board_face, 0, spell_face, hp_direct,
                            rng=rng, fighters=fs,
                        ),
                        attack_heal + spell_ls,
                        enemy_board=enemy,
                    ))
                elif not can_clear:
                    line_ls = attack_heal + max(spell_ls, clear_ls)
                    if spell_face <= 0 and hp_direct <= 0:
                        outcomes.append(self._attach_lifesteal(
                            self._apply_end_turn_face(
                                enemy, defender_shield, 0, 0, 0, 0, 0, rng=rng, fighters=fs,
                            ),
                            line_ls,
                            enemy_board=enemy,
                        ))
                    else:
                        outcomes.append(self._attach_lifesteal(
                            self._apply_end_turn_face(
                                enemy, defender_shield,
                                spell_face + hp_direct, 0, 0, spell_face, hp_direct,
                                rng=rng, fighters=fs,
                            ),
                            line_ls,
                            enemy_board=enemy,
                        ))
                else:
                    minion_board, weapon_board, hero_buff_board, remain_hp = (
                        self._split_fighter_face(fs, defender_shield)
                    )
                    hp_board = hp_direct + remain_hp
                    spell_face = self._spell_face_including_stolen(
                        fs, spell_face, defender_shield,
                    )
                    total = (
                        minion_board + weapon_board + hero_buff_board
                        + spell_face + hp_board
                    )
                    outcomes.append(self._attach_lifesteal(
                        self._apply_end_turn_face(
                            enemy, defender_shield, total,
                            minion_board, weapon_board, spell_face, hp_board,
                            hero_buff_board=hero_buff_board,
                            rng=rng, fighters=fs,
                        ),
                        line_ls,
                        enemy_board=enemy,
                    ))
            else:
                minion_board, weapon_board, hero_buff_board, remain_hp = (
                    self._split_fighter_face(fs, defender_shield)
                )
                spell_face = self._spell_face_including_stolen(
                    fs, spell_face, defender_shield,
                )
                if minion_board + weapon_board + hero_buff_board + remain_hp > 0:
                    hp_board = hp_direct + remain_hp
                else:
                    minion_board, weapon_board, hero_buff_board, hp_board = (
                        board_face, 0, 0, hp_direct,
                    )
                total = (
                    minion_board + weapon_board + hero_buff_board
                    + spell_face + hp_board
                )
                outcomes.append(self._attach_lifesteal(
                    self._apply_end_turn_face(
                        enemy, defender_shield, total,
                        minion_board, weapon_board, spell_face, hp_board,
                        hero_buff_board=hero_buff_board,
                        rng=rng, fighters=fs,
                    ),
                    attack_heal + spell_ls,
                    enemy_board=enemy,
                ))
            return max(outcomes, key=lambda x: x[0])

    def _simulate_line_face_total(
        self,
        base_enemy_minions: List[dict],
        fighters: List[dict],
        seq: List,
        order: str,
        *,
        spell_mult: int,
        defender_shield: bool,
        rng: Optional[random.Random] = None,
        available_mana: Optional[int] = None,
        hand_charges: Optional[List] = None,
        extra_spell_face: int = 0,
    ) -> Tuple[int, int, int]:
        outcome = self._simulate_line_outcome(
            base_enemy_minions, fighters, seq, order,
            spell_mult=spell_mult, defender_shield=defender_shield, rng=rng,
            available_mana=available_mana, hand_charges=hand_charges,
            extra_spell_face=extra_spell_face,
        )
        total, _, _, _, _, _, ls, armor, _ = self._unpack_face_outcome(outcome)
        return total, ls, armor

    @staticmethod
    def _top_two_damage_outcomes(counts: dict, trials: int) -> List[Tuple[int, float]]:
        if not counts or trials <= 0:
            return []
        ranked = sorted(counts.keys(), reverse=True)
        return [(dmg, counts[dmg] / trials) for dmg in ranked[:2]]

    def _mc_mean_line_face_total(
        self,
        base_enemy_minions: List[dict],
        fighters: List[dict],
        seq: List,
        order: str,
        *,
        spell_mult: int,
        defender_shield: bool,
        trials: int = OVERLAY_MC_TRIALS,
        available_mana: Optional[int] = None,
        hand_charges: Optional[List] = None,
    ) -> float:
        total = 0.0
        for i in range(trials):
            face, _, _ = self._simulate_line_face_total(
                base_enemy_minions, fighters, seq, order,
                spell_mult=spell_mult, defender_shield=defender_shield,
                rng=_mc_rng(i),
                available_mana=available_mana, hand_charges=hand_charges,
            )
            total += face
        return total / trials

    def _sequence_sim_needs_mc(self, seq: List, fighters: List[dict]) -> bool:
        """仅序列/攻击随机性需要 MC；场面随机回合结束不影响确定法术线打分。"""
        from .end_turn_hand_board import sequence_has_random_end_turn_hand
        from .rush_combat import fighters_need_random_attacks, sequence_has_ogre

        return (
            sequence_uses_random(seq)
            or sequence_has_random_end_turn_hand(seq)
            or sequence_has_ogre(seq)
            or fighters_need_random_attacks(fighters)
        )

    def _line_needs_random(self, seq: List, fighters: List[dict]) -> bool:
        local = self.game_state.local_player_id
        if local is not None:
            if end_turn_uses_random(self.game_state.get_board(local)):
                return True
        if end_turn_uses_random_fighters(fighters):
            return True
        return self._sequence_sim_needs_mc(seq, fighters)

    def _prefer_spell_line(
        self,
        score: float,
        best_score: float,
        seq: List,
        best_seq: List,
        fighters: List[dict],
        order: str,
        best_order: str,
        *,
        effective_hp: int = 999,
        cand_total: int = 0,
        best_total_int: int = 0,
        cand_mana: int = 0,
        best_mana: int = 0,
        cand_lifesteal: int = 0,
        cand_armor: int = 0,
        best_lifesteal: int = 0,
        best_armor: int = 0,
    ) -> bool:
        """同分或均已斩杀时优先更短、更省、确定性的序列。"""
        cand_penalty = max(0, cand_lifesteal) + max(0, cand_armor)
        best_penalty = max(0, best_lifesteal) + max(0, best_armor)
        # 吸血/亡语加甲已在 cand_total 模拟流程中体现，勿再加到有效血线
        cand_lethal = cand_total >= effective_hp > 0
        best_lethal = best_total_int >= effective_hp > 0
        if cand_lethal and not best_lethal:
            return True
        if best_lethal and not cand_lethal:
            return False
        if cand_lethal and best_lethal:
            if len(seq) != len(best_seq):
                return len(seq) < len(best_seq)
            from .spell_board import sequence_damages_friendly_minions
            cand_self_aoe = sequence_damages_friendly_minions(seq)
            best_self_aoe = sequence_damages_friendly_minions(best_seq)
            if cand_self_aoe != best_self_aoe:
                return not cand_self_aoe
            if cand_penalty != best_penalty:
                return cand_penalty < best_penalty
            if cand_mana != best_mana:
                return cand_mana < best_mana
            cand_rand = self._line_needs_random(seq, fighters)
            best_rand = self._line_needs_random(best_seq, fighters) if best_seq else False
            if cand_rand != best_rand:
                return not cand_rand
            if cand_total != best_total_int:
                return cand_total < best_total_int

        if score > best_score:
            return True
        if score < best_score:
            return False
        if cand_penalty != best_penalty:
            return cand_penalty < best_penalty
        cand_rand = self._line_needs_random(seq, fighters)
        best_rand = self._line_needs_random(best_seq, fighters) if best_seq else False
        if cand_rand != best_rand:
            return not cand_rand
        return order == "attack_interleaved" and best_order != "attack_interleaved"

    def _simulate_random_line_mc_best(
        self,
        base_enemy_minions: List[dict],
        fighters: List[dict],
        seq: List,
        orders: List[str],
        *,
        spell_mult: int,
        defender_shield: bool,
        available_mana: Optional[int],
        hand_charges: List,
        hp_direct: int,
        trials: int = OVERLAY_MC_TRIALS,
        extra_spell_face: int = 0,
    ) -> Tuple[str, Tuple[int, int, int, int, int, int]]:
        """随机法术线路：确定性法术先打完，再对随机后缀做 MC。"""
        best_order = orders[0]
        best_outcome = (0, 0, 0, 0, 0, 0)
        det_seq, rand_seq = split_deterministic_random_sequence(seq)
        hero_hp = self._my_hero_hp_for_spells()
        local_id = self.game_state.local_player_id

        for order in orders:
            if (
                order == "spell_first"
                and rand_seq
                and sequence_random_spells_all_last(seq)
                and not end_turn_uses_random_fighters(fighters)
            ):
                for i in range(trials):
                    if self._lethal_budget_expired():
                        break
                    enemy = _clone_combat_states(base_enemy_minions)
                    fs = _clone_combat_states(fighters)
                    spell_parts: List[SpellApplyResult] = []
                    mana_end = available_mana
                    hero_end = hero_hp
                    if det_seq:
                        det_res, hero_end, mana_end = apply_spell_sequence_with_meta(
                            enemy, fs, det_seq, spell_mult=spell_mult,
                            enemy_shield=defender_shield, rng=None,
                            gs=self.game_state, player_id=local_id,
                            hero_hp=hero_end, mana_budget=mana_end,
                            next_turn_preview=self._hero_power_next_turn(),
                        )
                        spell_parts.append(det_res)
                    rand_res, hero_end, mana_end = apply_spell_sequence_with_meta(
                        enemy, fs, rand_seq, spell_mult=spell_mult,
                        enemy_shield=defender_shield, rng=_mc_rng(i),
                        gs=self.game_state, player_id=local_id,
                        hero_hp=hero_end, mana_budget=mana_end,
                        next_turn_preview=self._hero_power_next_turn(),
                    )
                    spell_parts.append(rand_res)
                    spell_res = merge_spell_apply_results(*spell_parts)
                    if extra_spell_face:
                        spell_res.direct_face_damage += extra_spell_face
                    outcome = self._spell_first_face_from_state(
                        enemy, fs, spell_res, mana_end, hand_charges,
                        defender_shield, hp_direct, rng=_mc_rng(i),
                        hero_hp_after_spells=hero_end,
                    )
                    if outcome[0] > best_outcome[0]:
                        best_outcome = outcome
                        best_order = order
                continue

            for i in range(trials):
                if self._lethal_budget_expired():
                    break
                outcome = self._simulate_line_outcome(
                    base_enemy_minions, fighters, seq, order,
                    spell_mult=spell_mult, defender_shield=defender_shield,
                    rng=_mc_rng(i), available_mana=available_mana,
                    hand_charges=hand_charges, hp_direct=hp_direct,
                    extra_spell_face=extra_spell_face,
                )
                if outcome[0] > best_outcome[0]:
                    best_outcome = outcome
                    best_order = order
        return best_order, best_outcome

    def _monte_carlo_line_stats(
        self,
        base_enemy_minions: List[dict],
        fighters: List[dict],
        seq: List,
        order: str,
        *,
        spell_mult: int,
        defender_shield: bool,
        effective_hp: int,
        trials: int = OVERLAY_MC_TRIALS,
        available_mana: Optional[int] = None,
        hand_charges: Optional[List] = None,
        ignore_budget: bool = False,
    ) -> Tuple[int, float, List[Tuple[int, float]]]:
        """返回 (样本最高总打脸, P(总打脸 >= 有效血量), 按伤害降序前两种结果及概率)。"""
        extra_spell_face = int(getattr(self, "_overlay_direct_face", 0) or 0)
        _, _, static_hp = self.get_opponent_health()
        needs_random = self._line_needs_random(seq, fighters)
        if not needs_random:
            total, line_ls, line_armor = self._simulate_line_face_total(
                base_enemy_minions, fighters, seq, order,
                spell_mult=spell_mult, defender_shield=defender_shield,
                available_mana=available_mana, hand_charges=hand_charges,
                extra_spell_face=extra_spell_face,
            )
            line_eff = static_hp + line_ls + line_armor
            prob = 1.0 if total >= line_eff else 0.0
            top = [(total, 1.0)] if total > 0 else []
            return total, prob, top

        counts: dict = {}
        lethal_hits = 0
        det_seq, rand_seq = split_deterministic_random_sequence(seq)
        hero_hp = self._my_hero_hp_for_spells()
        local_id = self.game_state.local_player_id
        use_det_rand_mc = (
            order == "spell_first"
            and rand_seq
            and sequence_random_spells_all_last(seq)
            and not end_turn_uses_random_fighters(fighters)
            and (
                local_id is None
                or not end_turn_uses_random(self.game_state.get_board(local_id))
            )
        )
        for i in range(trials):
            if not ignore_budget and self._lethal_budget_expired():
                break
            if use_det_rand_mc:
                enemy = _clone_combat_states(base_enemy_minions)
                fs = _clone_combat_states(fighters)
                spell_parts: List[SpellApplyResult] = []
                mana_end = available_mana
                hero_end = hero_hp
                if det_seq:
                    det_res, hero_end, mana_end = apply_spell_sequence_with_meta(
                        enemy, fs, det_seq, spell_mult=spell_mult,
                        enemy_shield=defender_shield, rng=None,
                        gs=self.game_state, player_id=local_id,
                        hero_hp=hero_end, mana_budget=mana_end,
                        next_turn_preview=self._hero_power_next_turn(),
                    )
                    spell_parts.append(det_res)
                rand_res, hero_end, mana_end = apply_spell_sequence_with_meta(
                    enemy, fs, rand_seq, spell_mult=spell_mult,
                    enemy_shield=defender_shield, rng=_mc_rng(i),
                    gs=self.game_state, player_id=local_id,
                    hero_hp=hero_end, mana_budget=mana_end,
                    next_turn_preview=self._hero_power_next_turn(),
                )
                spell_parts.append(rand_res)
                spell_res = merge_spell_apply_results(*spell_parts)
                if extra_spell_face:
                    spell_res.direct_face_damage += extra_spell_face
                outcome = self._spell_first_face_from_state(
                    enemy, fs, spell_res, mana_end, hand_charges or [],
                    defender_shield, 0, rng=_mc_rng(i),
                    hero_hp_after_spells=hero_end,
                )
                total, _, _, _, _, _, line_ls, line_armor, _ = (
                    self._unpack_face_outcome(outcome)
                )
            else:
                total, line_ls, line_armor = self._simulate_line_face_total(
                    base_enemy_minions, fighters, seq, order,
                    spell_mult=spell_mult, defender_shield=defender_shield,
                    rng=_mc_rng(i),
                    available_mana=available_mana, hand_charges=hand_charges,
                    extra_spell_face=extra_spell_face,
                )
            counts[total] = counts.get(total, 0) + 1
            if total >= static_hp + line_ls + line_armor:
                lethal_hits += 1
        if not counts:
            return 0, 0.0, []
        actual_trials = sum(counts.values())
        peak = max(counts.keys())
        top = self._top_two_damage_outcomes(counts, actual_trials)
        return peak, lethal_hits / actual_trials, top

    def _enemy_board_after_exhaust_taunts(
        self,
        board_view,
        player_id: int,
        opp_taunts: list,
        defender_shield: bool,
    ) -> Tuple[int, List[dict], bool]:
        """
        用完随从攻击解嘲（可部分清嘲），返回 (可打脸伤害, 解嘲后敌方场面, 是否清完嘲讽)。
        """
        fighters = self._build_fighters(board_view, player_id)
        enemy_board = self._build_enemy_minion_states(player_id)
        taunts = self._living_taunt_states(enemy_board)
        if not taunts:
            fb = board_view.face_attack_damage_no_taunt(defender_shield)
            return fb, enemy_board, True

        board = _clone_combat_states(enemy_board)
        self._exhaust_attacks_on_taunts(
            fighters, taunts, enemy_board=board,
        )
        can_clear = not self._living_taunt_states(board)
        face, _, can_clear2 = self._calculate_board_damage_with_taunts(
            board_view, player_id, opp_taunts, defender_shield=defender_shield,
        )
        fb = face if (can_clear and can_clear2) else 0
        return fb, board, can_clear and can_clear2

    def _best_fallback_board_line(
        self,
        board_view,
        player_id: int,
        opp_taunts: list,
        defender_shield: bool,
    ) -> Tuple[int, List[dict], int]:
        """纯场面回退：棘嗣幼龙在场时枚举攻击子集。返回 (fb, enemy_after, board_part)。"""
        enemy_base = self._build_enemy_minion_states(player_id)
        fighters = self._build_fighters(board_view, player_id)
        minion_fb, weapon_fb, _, _ = self._split_fighter_face(fighters, defender_shield)

        if self._should_consider_hold_attack(fighters):
            candidates: List[Tuple[int, List[dict], int, int]] = []
            for subset in self._attack_subset_eids_list(fighters):
                outcome = self._finish_hold_attack_subset_line(
                    enemy_base, fighters, subset, 0, 0, defender_shield,
                )
                total, minion_part, weapon_part, _, _, _ = outcome
                enemy_work, _, _ = self._run_masked_attack_phase(
                    fighters, enemy_base, subset, defender_shield,
                )
                candidates.append((total, enemy_work, minion_part + weapon_part, 0))
            _, best_enemy, best_board, best_fb = max(candidates, key=lambda x: x[0])
            return best_fb, best_enemy, best_board

        candidates: List[Tuple[int, List[dict], int, int]] = []
        if opp_taunts:
            fb, enemy_after, _ = self._enemy_board_after_exhaust_taunts(
                board_view, player_id, opp_taunts, defender_shield,
            )
            total, board_part, _, _, _, _ = self._apply_end_turn_face(
                _clone_combat_states(enemy_after), defender_shield,
                fb, minion_fb, weapon_fb, 0, 0,
            )
            candidates.append((total, enemy_after, board_part, fb))
        else:
            fb = board_view.face_attack_damage_no_taunt(defender_shield)
            total, board_part, _, _, _, _ = self._apply_end_turn_face(
                _clone_combat_states(enemy_base), defender_shield,
                fb, minion_fb, weapon_fb, 0, 0,
            )
            candidates.append((total, enemy_base, board_part, fb))

        _, best_enemy, best_board, best_fb = max(candidates, key=lambda x: x[0])
        return best_fb, best_enemy, best_board

    def _monte_carlo_pure_board_end_turn(
        self,
        fb: int,
        enemy_after: List[dict],
        defender_shield: bool,
        effective_hp: int,
        *,
        trials: int = OVERLAY_MC_TRIALS,
    ) -> Tuple[int, float, List[Tuple[int, float]], int]:
        """
        纯场面 + 回合结束随机攻击的 MC。
        返回 (峰值总打脸, 斩杀概率, top_outcomes, 解场后随从+回合结束打脸分量)。
        """
        local = self.game_state.local_player_id
        our_board = self.game_state.get_board(local) if local is not None else []
        if not end_turn_uses_random(our_board):
            total, board_part, _, _, _, _ = self._apply_end_turn_face(
                _clone_combat_states(enemy_after), defender_shield, fb, fb, 0, 0, 0,
                fighters=None,
            )
            prob = 1.0 if total >= effective_hp else 0.0
            top = [(total, 1.0)] if total > 0 else []
            return total, prob, top, board_part

        counts: dict = {}
        lethal_hits = 0
        for i in range(trials):
            if self._lethal_budget_expired():
                break
            eb = _clone_combat_states(enemy_after)
            et, _ = end_turn_face_damage(
                our_board, eb, defender_shield,
                game_state=self.game_state, player_id=local,
                rng=random.Random(i + 401),
                opponent_hero_hp=max(0, effective_hp - fb),
            )
            total = fb + et
            counts[total] = counts.get(total, 0) + 1
            if total >= effective_hp:
                lethal_hits += 1
        if not counts:
            return fb, 0.0, [], fb
        actual_trials = sum(counts.values())
        peak = max(counts.keys())
        top = self._top_two_damage_outcomes(counts, actual_trials)
        return peak, lethal_hits / actual_trials, top, peak

    def _board_end_turn_face(
        self,
        player_id: int,
        defender_shield: bool,
        enemy_board: Optional[List[dict]] = None,
    ) -> int:
        """当前场面回合结束可预估打脸（变形/召唤后立即计入）。"""
        if enemy_board is None:
            enemy_board = self._build_enemy_minion_states(player_id)
        return board_end_turn_face_now(
            self.game_state.get_board(player_id),
            enemy_board,
            defender_shield,
            game_state=self.game_state,
            player_id=player_id,
        )

    def _board_dormant_end_turn_face(
        self,
        player_id: int,
        defender_shield: bool,
        enemy_board: Optional[List[dict]] = None,
    ) -> int:
        """休眠随从回合结束打脸（如玛瑟里顿），不计入 Overlay 场攻展示。"""
        from .end_turn_board import board_dormant_end_turn_face_now

        if enemy_board is None:
            enemy_board = self._build_enemy_minion_states(player_id)
        return board_dormant_end_turn_face_now(
            self.game_state.get_board(player_id),
            enemy_board,
            defender_shield,
            game_state=self.game_state,
            player_id=player_id,
        )

    def _overlay_board_floor_outcome(
        self,
        *,
        pure_immediate: int,
        player_id: int,
        defender_shield: bool,
        fighters: List[dict],
        base_enemy_minions: List[dict],
        available_mana: Optional[int] = None,
    ) -> Tuple[int, int, int, int]:
        """
        下回合保底场攻（随从/武器 + 回合结束 + 可用英雄技能），不含手牌法术。
        对方回合 overlay 与法术搜索分离时，避免漏计嚼嚼怪/敲狼锤等场面潜力。
        """
        fs = _clone_combat_states(fighters)
        if available_mana is not None and has_usable_hero_power(
            self.game_state,
            player_id,
            self._hero_power_mana_budget(available_mana, available_mana),
            next_turn=self._hero_power_next_turn(),
        ):
            fs, _, hp_name, _ = self._prepare_line_with_hero_power(
                fs,
                player_id,
                self._hero_power_mana_budget(available_mana, available_mana),
                use_hp=True,
                defender_shield=defender_shield,
                enemy=base_enemy_minions,
            )
            if not hp_name:
                fs = _clone_combat_states(fighters)
        minion, weapon, _, hp = self._split_fighter_face(fs, defender_shield)
        stolen = self._stolen_minion_face(fighters, defender_shield)
        total, minion_bd, weapon_bd, _, hp_bd, _ = self._apply_end_turn_face(
            _clone_combat_states(base_enemy_minions),
            defender_shield,
            pure_immediate,
            minion,
            weapon,
            stolen,
            hp,
            fighters=fighters,
        )
        if (
            total <= pure_immediate
            and has_hold_attack_end_turn_on_board(
                self.game_state.get_board(player_id),
            )
        ):
            et_now = self._board_end_turn_face(
                player_id, defender_shield, base_enemy_minions,
            )
            if et_now > 0:
                total = pure_immediate + et_now
                minion_bd = minion
        return total, minion_bd, weapon_bd, hp_bd

    def _compute_immediate_board_face(
        self,
        board_view,
        player_id: int,
        opp_taunts: list,
        defender_shield: bool,
    ) -> int:
        """不用手牌：仅随从/武器当回合可执行的打脸（不含回合结束）。"""
        if opp_taunts:
            face, _, can_clear = self._calculate_board_damage_with_taunts(
                board_view, player_id, opp_taunts, defender_shield=defender_shield,
            )
            return face if can_clear else 0
        return board_view.face_attack_damage_no_taunt(defender_shield)

    def _compute_pure_board_face(
        self,
        board_view,
        player_id: int,
        opp_taunts: list,
        defender_shield: bool,
    ) -> int:
        """场面打脸 = 当回合攻击 + 回合结束可预估伤害。"""
        immediate = self._compute_immediate_board_face(
            board_view, player_id, opp_taunts, defender_shield,
        )
        et_face = self._board_end_turn_face(player_id, defender_shield)
        return immediate + et_face

    def overlay_spell_note(self) -> str:
        """最近一次场攻计算使用的法术说明（供 Overlay 显示）。"""
        return getattr(self, "_overlay_spell_note", "")

    def _trim_hand_spells_for_search(
        self,
        hand_spells,
        available_mana: int,
        player_id: Optional[int],
    ):
        """满手牌时只保留高价值法术，避免组合爆炸（同名牌保留多张实体）。"""
        affordable = [
            item for item in hand_spells
            if item[2] <= available_mana
        ]
        if len(affordable) <= MAX_HAND_SPELLS_FOR_SEARCH:
            return affordable

        from .spell_board import spell_estimate_trim_damage

        def priority(item) -> tuple:
            card, defn, cost = item
            dmg = spell_estimate_trim_damage(
                card, defn, gs=self.game_state, player_id=player_id,
            )
            return (dmg / max(cost, 1), dmg, -cost)

        affordable.sort(key=priority, reverse=True)
        return affordable[:MAX_HAND_SPELLS_FOR_SEARCH]

    def _no_taunt_direct_face_setup(
        self,
        hand_spells,
        available_mana: int,
        *,
        spell_mult: int,
        defender_shield: bool,
        player_id: int,
        opp_taunts: list,
    ) -> Tuple[List, List, int, int, int]:
        """
        无嘲讽时拆出直伤固定前缀。
        返回 (combo手牌, direct前缀步骤, direct打脸, combo可用法力, direct已耗法力)。
        """
        from .spell_board import partition_hand_spells_by_tier, pack_no_taunt_direct_face_spells

        if opp_taunts:
            return hand_spells, [], 0, available_mana, 0
        combo_hand, direct_hand = partition_hand_spells_by_tier(hand_spells)
        direct_prefix, direct_face, direct_mana = pack_no_taunt_direct_face_spells(
            direct_hand, available_mana,
            spell_mult=spell_mult, enemy_shield=defender_shield,
            gs=self.game_state, player_id=player_id,
        )
        combo_mana = max(0, available_mana - direct_mana)
        return combo_hand, direct_prefix, direct_face, combo_mana, direct_mana

    def _combo_seq_for_simulation(self, best_seq: List) -> List:
        """展示序列含直伤前缀时，模拟/MC 只跑 combo 部分（直伤已用 extra_spell_face 计入）。"""
        prefix = getattr(self, "_overlay_direct_prefix", None) or []
        n = len(prefix)
        if n and len(best_seq) >= n:
            tail = best_seq[-n:]
            if tail == prefix:
                return best_seq[:-n]
        return best_seq

    def _enumerate_spells_for_search(
        self,
        hand_spells,
        available_mana: int,
        *,
        enemy_minions: Optional[List[dict]] = None,
        fighters: Optional[List[dict]] = None,
        spell_mult: int = 1,
        defender_shield: bool = False,
        player_id: Optional[int] = None,
    ):
        """
        枚举手牌法术打出序列。
        组合规模由 max_combo_len(7) + 法力剪枝 + 分层枚举 + 场面置换剪枝控制。
        """
        hand_spells = self._trim_hand_spells_for_search(
            hand_spells, available_mana, player_id,
        )
        return enumerate_spell_sequences(
            hand_spells,
            mana_budget=available_mana,
            max_combo_len=7,
            enemy_minions=enemy_minions,
            fighters=fighters,
            spell_mult=spell_mult,
            enemy_shield=defender_shield,
            gs=self.game_state,
            player_id=player_id,
            next_turn_preview=self._hero_power_next_turn(),
        )

    def overlay_red_prompt_ok(self, *, opp_lethal_now: bool = False) -> bool:
        """
        Overlay 是否应变红：仅看场攻模拟总伤 vs 对手有效血，不受法力校验影响。
        我方回合=本回合斩；对方回合=下回合斩预览（与 calculate_lethal_potential 一致）。
        """
        if opp_lethal_now:
            return False
        if not self.is_local_turn() and not self.is_opponent_turn():
            return False
        if not getattr(self, "_overlay_face_computed", False):
            return False
        if getattr(self, "_overlay_incomplete", False):
            return False
        face = int(getattr(self, "_overlay_total_face", 0) or 0)
        mc_max, lethal_prob, uses_random, _top = self.overlay_face_stats()
        threshold = self._lethal_threshold_hp(subtract_overlay_lifesteal=True)
        if threshold <= 0:
            return False
        if uses_random:
            return face >= threshold or (
                mc_max >= threshold and lethal_prob >= MIN_LETHAL_PROMPT_PROB
            )
        return face >= threshold

    def overlay_lethal_prompt_ok(
        self,
        has_lethal: bool,
        *,
        opp_lethal_now: bool = False,
    ) -> bool:
        """是否向用户展示斩杀提示（含随机线概率阈值）。"""
        if opp_lethal_now:
            return False
        if self.overlay_red_prompt_ok(opp_lethal_now=False):
            return True
        if not has_lethal:
            return False
        _mc_max, lethal_prob, uses_random, _top = self.overlay_face_stats()
        if not uses_random:
            return True
        return lethal_prob >= MIN_LETHAL_PROMPT_PROB

    def overlay_lethal_diff_note(
        self,
        total_damage: int,
        opp_total: int,
        *,
        has_lethal: bool,
        prompt_lethal: bool,
    ) -> Optional[str]:
        """未亮红但伤害数字贴脸时的补充说明（如随机斩杀低于阈值）。"""
        if prompt_lethal or has_lethal:
            return None
        _mc_max, lethal_prob, uses_random, _top = self.overlay_face_stats()
        if uses_random and _mc_max >= opp_total and lethal_prob < MIN_LETHAL_PROMPT_PROB:
            return f"随机最高{_mc_max} 概率{lethal_prob * 100:.0f}%<20%不提斩"
        diff_damage = self.overlay_diff_damage(total_damage, has_lethal=False)
        if diff_damage < opp_total:
            return None
        if total_damage >= opp_total:
            return "伤害够但未确认斩杀"
        return None

    def overlay_combo_display_lines(self) -> List[str]:
        """斩杀步骤面板文案（法术/战吼/技能/场面攻击；含快速斩杀回退）。"""
        from .overlay_combo_format import build_combo_lines_for_display
        return build_combo_lines_for_display(self)

    def _apply_overlay_stats_from_best_line(
        self,
        *,
        pure_immediate: int,
        pure_et: int = 0,
        best_board: int,
        best_weapon_board: int = 0,
        best_spell_face: int,
        best_total: int,
        best_hero_power_face: int,
        best_hero_buff_face: int = 0,
        best_battlecry_face: int = 0,
        best_seq: List,
        best_order: str,
        base_enemy_minions: List[dict],
        fighters: List[dict],
        spell_mult: int,
        defender_shield: bool,
        effective_hp: int,
        available_mana: int,
        charges: List,
        board_view=None,
        player_id: Optional[int] = None,
        opp_taunts: Optional[list] = None,
        ignore_budget: bool = False,
    ) -> int:
        """将当前最优打法写入 Overlay 统计；含随机/回合结束时跑 MC。"""
        pure_board = pure_immediate
        if not best_seq and best_total <= 0:
            return best_total
        sim_seq = self._combo_seq_for_simulation(best_seq)
        sim_mana = available_mana - int(getattr(self, "_overlay_direct_mana", 0) or 0)
        needs_random = self._line_needs_random(sim_seq, fighters)
        if needs_random:
            if sim_seq:
                mc_max, prob, top_outcomes = self._monte_carlo_line_stats(
                    base_enemy_minions, fighters, sim_seq, best_order,
                    spell_mult=spell_mult,
                    defender_shield=defender_shield,
                    effective_hp=effective_hp,
                    available_mana=sim_mana,
                    hand_charges=charges,
                    ignore_budget=ignore_budget,
                )
            elif board_view is not None and player_id is not None:
                fb, enemy_after, board_part = self._best_fallback_board_line(
                    board_view, player_id, opp_taunts or [], defender_shield,
                )
                mc_max, prob, top_outcomes, board_part = (
                    self._monte_carlo_pure_board_end_turn(
                        fb, enemy_after, defender_shield, effective_hp,
                    )
                )
                best_board = board_part
            else:
                mc_max, prob, top_outcomes = best_total, 0.0, []
            display_total = max(mc_max, best_total)
            if mc_max > best_total:
                non_board = (
                    best_spell_face + best_battlecry_face + best_weapon_board
                    + best_hero_power_face + best_hero_buff_face
                )
                best_board = max(best_board, max(0, mc_max - non_board))
            self._reset_overlay_board_breakdown(
                pure_board, best_board, best_spell_face, display_total,
                weapon_board=best_weapon_board,
                hero_power_face=best_hero_power_face,
                hero_buff_face=best_hero_buff_face,
                battlecry_face=best_battlecry_face,
                mc_max=mc_max, lethal_prob=prob,
                uses_random=True, top_outcomes=top_outcomes,
            )
            return display_total
        self._reset_overlay_board_breakdown(
            pure_board, best_board, best_spell_face, best_total,
            weapon_board=best_weapon_board,
            hero_power_face=best_hero_power_face,
            hero_buff_face=best_hero_buff_face,
            battlecry_face=best_battlecry_face,
        )
        return best_total

    def _best_face_with_board_spells(
        self,
        board_view,
        player_id: int,
        opp_taunts: list,
        defender_shield: bool,
        hand_spells,
        available_mana: int,
        *,
        pure_immediate: int = 0,
        pure_et: int = 0,
        effective_hp: int = 30,
        hand_charges: Optional[List] = None,
    ) -> Tuple[int, str]:
        fighters = self._build_fighters(board_view, player_id)
        spell_mult = spell_effect_multiplier(self.game_state, player_id)
        base_enemy_minions = self._build_enemy_minion_states(player_id)
        combo_hand, direct_prefix, direct_face, combo_mana, direct_mana = (
            self._no_taunt_direct_face_setup(
                hand_spells, available_mana,
                spell_mult=spell_mult, defender_shield=defender_shield,
                player_id=player_id, opp_taunts=opp_taunts,
            )
        )
        sequences = self._enumerate_spells_for_search(
            combo_hand, combo_mana,
            enemy_minions=base_enemy_minions,
            fighters=fighters,
            spell_mult=spell_mult,
            defender_shield=defender_shield,
            player_id=player_id,
        )
        sequences = sorted(
            sequences,
            key=lambda seq: (
                1 if self._line_needs_random(seq, fighters) else 0,
                len(seq),
            ),
        )
        charges = hand_charges or []
        fighter_atk = sum(
            f.get("atk", 0) * f.get("attacks_left", 0)
            for f in fighters
            if f.get("health", 0) > 0
        )
        # 有嘲讽且需穷举交换时保留 attack_first；无嘲讽但有法术时也在循环内按序列决定
        search_orders = ("spell_first", "attack_first")

        best_total = 0
        best_board = 0
        best_weapon_board = 0
        best_spell_face = 0
        best_battlecry_face = 0
        best_hero_power_face = 0
        best_hero_buff_face = 0
        best_lifesteal_heal = 0
        best_deathrattle_armor = 0
        best_note = ""
        best_seq: List = []
        best_order = "spell_first"
        best_hp_name: Optional[str] = None
        best_mana_spent = 0
        best_score = -1.0
        # Overlay 场攻分项：取最高总伤（含法术），与连招择优（已斩杀时更短更省）分离
        display_total = 0
        display_board = 0
        display_weapon_board = 0
        display_spell_face = 0
        display_battlecry_face = 0
        display_hero_power_face = 0
        display_hero_buff_face = 0
        display_note = ""
        display_score = -1.0
        display_seq: List = []
        display_order = "spell_first"
        display_hp_name: Optional[str] = None
        display_mana_spent = 0
        seen_fp: set = set()
        hero_hp = self._my_hero_hp_for_spells()
        local_id = self.game_state.local_player_id
        mana_for_spells = max(0, available_mana - direct_mana)
        hp_budget = self._hero_power_mana_budget(available_mana, mana_for_spells)
        from .damaged_spell_power import (
            hand_has_damaged_spellpower_card,
            has_undamaged_spellpower_on_fighters,
        )
        hp_modes: List[Tuple[bool, str]] = [(False, "face")]
        if has_usable_hero_power(
            self.game_state, player_id, hp_budget,
            next_turn=self._hero_power_next_turn(),
        ):
            hp_modes.append((True, "face"))
            if (
                has_undamaged_spellpower_on_fighters(fighters)
                or hand_has_damaged_spellpower_card(self.game_state, player_id)
            ):
                hp_modes.append((True, "setup"))

        for seq in sequences:
            if self._lethal_budget_expired():
                break
            if seq and min(c for _, c, _ in seq) > combo_mana:
                continue

            full_seq = seq + direct_prefix
            # 无对手嘲讽时，若仍有解场/直伤法术，须比较先攻后法（地狱烈焰等会先伤己方随从）
            if not opp_taunts and not full_seq:
                search_orders = ("spell_first",)
            elif not opp_taunts:
                search_orders = ("spell_first", "attack_first")
            elif opp_taunts and hand_spells and (
                (pure_immediate <= 0 and fighter_atk <= 2) or len(hand_spells) >= 5
            ):
                search_orders = ("spell_first",)
            else:
                search_orders = ("spell_first", "attack_first")

            for use_hp, hp_mode in hp_modes:
                line_fighters, line_mana, hp_name, hp_res = self._prepare_line_with_hero_power(
                    fighters, player_id, hp_budget, use_hp=use_hp,
                    defender_shield=defender_shield,
                    enemy=base_enemy_minions,
                    hp_mode=hp_mode,
                )
                if use_hp and not hp_name:
                    continue
                if use_hp and hp_name:
                    if self.is_opponent_turn():
                        row = usable_hero_power(
                            self.game_state, player_id, hp_budget,
                            next_turn=self._hero_power_next_turn(),
                        )
                        hp_cost = row[2] if row else 0
                        line_mana = max(0, available_mana - direct_mana - hp_cost)
                else:
                    line_mana = mana_for_spells
                hp_direct = hp_res.direct_face_damage

                def sim_attack_first(
                    _lf=line_fighters, _lm=line_mana, _hd=hp_direct,
                ) -> Tuple[int, int, int, int, int, int, int]:
                    return self._simulate_line_outcome(
                        base_enemy_minions, _lf, seq, "attack_first",
                        spell_mult=spell_mult, defender_shield=defender_shield,
                        rng=None,
                        available_mana=_lm, hand_charges=charges, hp_direct=_hd,
                        extra_spell_face=direct_face,
                    )

                if not seq:
                    candidates = [
                        (order, self._simulate_line_outcome(
                            base_enemy_minions, line_fighters, seq, order,
                            spell_mult=spell_mult, defender_shield=defender_shield,
                            available_mana=line_mana, hand_charges=charges,
                            hp_direct=hp_direct, extra_spell_face=direct_face,
                        ))
                        for order in search_orders
                    ]
                elif self._sequence_sim_needs_mc(seq, line_fighters):
                    mc_orders = list(search_orders)
                    best_order, sf = self._simulate_random_line_mc_best(
                        base_enemy_minions, line_fighters, seq, mc_orders,
                        spell_mult=spell_mult, defender_shield=defender_shield,
                        available_mana=line_mana, hand_charges=charges,
                        hp_direct=hp_direct, extra_spell_face=direct_face,
                    )
                    candidates = [(best_order, sf)]
                else:
                    enemy = _clone_combat_states(base_enemy_minions)
                    fs = _clone_combat_states(line_fighters)
                    spell_res, hp_end, mana_end = apply_spell_sequence_with_meta(
                        enemy, fs, seq, spell_mult=spell_mult,
                        enemy_shield=defender_shield,
                        gs=self.game_state, player_id=local_id,
                        hero_hp=hero_hp, mana_budget=line_mana,
                        next_turn_preview=self._hero_power_next_turn(),
                        inline_hero_power_used=use_hp,
                    )
                    if direct_face:
                        spell_res.direct_face_damage += direct_face
                    fp = (
                        use_hp,
                        spell_sequence_transposition_key(
                            enemy, fs, spell_res, hero_hp=hp_end, mana_left=mana_end,
                        ),
                    )
                    if fp in seen_fp:
                        continue
                    seen_fp.add(fp)
                    sf = self._spell_first_face_from_state(
                        enemy, fs, spell_res, mana_end, charges, defender_shield,
                        hp_direct,
                        hero_hp_after_spells=hp_end,
                    )
                    candidates = [("spell_first", sf)]
                    if "attack_first" in search_orders:
                        af = sim_attack_first()
                        total_af, _, _, _, _, _, _, _, _ = self._unpack_face_outcome(af)
                        total_sf, _, _, _, _, _, _, _, _ = self._unpack_face_outcome(sf)
                        if total_af > total_sf:
                            candidates = [("attack_first", af)]
                    if sequence_needs_attack_interleave(seq):
                        fi = self._simulate_attack_interleaved_outcome(
                            base_enemy_minions, line_fighters, seq,
                            spell_mult=spell_mult, defender_shield=defender_shield,
                            available_mana=line_mana, hand_charges=charges,
                            hp_direct=hp_direct,
                        )
                        candidates.append(("attack_interleaved", fi))

                line_random = self._sequence_sim_needs_mc(seq, line_fighters)
                for order, outcome in candidates:
                    (
                        total, minion_face, weapon_face, spell_face,
                        hero_power_face, hero_buff_face, line_ls, line_armor,
                        battlecry_face,
                    ) = self._unpack_face_outcome(outcome)
                    if total <= 0 and opp_taunts and not line_random:
                        continue
                    if line_random:
                        score = self._mc_mean_line_face_total(
                            base_enemy_minions, line_fighters, seq, order,
                            spell_mult=spell_mult, defender_shield=defender_shield,
                            available_mana=line_mana, hand_charges=charges,
                            trials=OVERLAY_MC_TRIALS,
                        )
                    else:
                        score = float(
                            total - max(0, line_ls) - max(0, line_armor),
                        )

                    cand_mana = self._estimate_line_mana_spent(
                        player_id, available_mana,
                        seq=full_seq,
                        hero_power_name=hp_name if use_hp else None,
                        hand_charges=charges,
                    )
                    if not self._overlay_line_mana_ok(
                        player_id, available_mana,
                        seq=full_seq,
                        use_hp=use_hp,
                        hero_power_name=hp_name if use_hp else None,
                        hand_charges=charges,
                    ):
                        continue
                    if self._prefer_spell_line(
                        score, best_score, full_seq, best_seq, fighters, order, best_order,
                        effective_hp=effective_hp,
                        cand_total=total,
                        best_total_int=best_total,
                        cand_mana=cand_mana,
                        best_mana=best_mana_spent,
                        cand_lifesteal=line_ls,
                        cand_armor=line_armor,
                        best_lifesteal=best_lifesteal_heal,
                        best_armor=best_deathrattle_armor,
                    ):
                        best_score = score
                        best_total = total
                        best_board = minion_face
                        best_weapon_board = weapon_face
                        best_spell_face = spell_face
                        best_battlecry_face = battlecry_face
                        best_hero_power_face = hero_power_face
                        best_hero_buff_face = hero_buff_face
                        best_lifesteal_heal = line_ls
                        best_deathrattle_armor = line_armor
                        best_note = self._format_spell_note(
                            full_seq, spell_mult, order, hand_charges=charges,
                            available_mana=available_mana,
                            hero_power_name=hp_name,
                        )
                        best_seq = full_seq
                        best_order = order
                        best_hp_name = hp_name
                        best_mana_spent = self._estimate_line_mana_spent(
                            player_id, available_mana,
                            seq=full_seq,
                            hero_power_name=hp_name,
                            hand_charges=charges,
                        )

                    if line_random:
                        if score > display_score:
                            display_score = score
                        # 随机线 MC 分数更高时，勿用较低的确定性 total 覆盖动情狂想曲等已算清的更高伤
                        if total > display_total:
                            display_total = total
                            display_board = minion_face
                            display_weapon_board = weapon_face
                            display_spell_face = spell_face
                            display_battlecry_face = battlecry_face
                            display_hero_power_face = hero_power_face
                            display_hero_buff_face = hero_buff_face
                            display_seq = full_seq
                            display_order = order
                            display_hp_name = hp_name
                            display_mana_spent = cand_mana
                            display_note = self._format_spell_note(
                                full_seq, spell_mult, order, hand_charges=charges,
                                available_mana=available_mana,
                                hero_power_name=hp_name,
                            )
                    elif (
                        total > display_total
                        or (
                            total == display_total
                            and (
                                spell_face > display_spell_face
                                or hero_buff_face > display_hero_buff_face
                            )
                        )
                    ):
                        display_total = total
                        display_board = minion_face
                        display_weapon_board = weapon_face
                        display_spell_face = spell_face
                        display_battlecry_face = battlecry_face
                        display_hero_power_face = hero_power_face
                        display_hero_buff_face = hero_buff_face
                        display_seq = full_seq
                        display_order = order
                        display_hp_name = hp_name
                        display_mana_spent = cand_mana
                        display_note = self._format_spell_note(
                            full_seq, spell_mult, order, hand_charges=charges,
                            available_mana=available_mana,
                            hero_power_name=hp_name,
                        )

        floor_total, floor_board, floor_weapon, floor_hp = (
            self._overlay_board_floor_outcome(
                pure_immediate=pure_immediate,
                player_id=player_id,
                defender_shield=defender_shield,
                fighters=fighters,
                base_enemy_minions=base_enemy_minions,
                available_mana=available_mana,
            )
        )
        if floor_total > display_total:
            display_total = floor_total + floor_hp
            display_board = floor_board
            display_weapon_board = floor_weapon
            display_hero_power_face = floor_hp
            display_score = float(floor_total)
            if not display_note and self.is_opponent_turn():
                names = end_turn_names_on_board(self.game_state.get_board(player_id))
                if names:
                    display_note = f"下回合+{'+'.join(names)}"

        if (
            display_total > 0
            and display_hero_power_face > 0
            and display_hp_name
        ):
            spell_mana = self._estimate_line_mana_spent(
                player_id, available_mana,
                seq=display_seq,
                hero_power_name=None,
                hand_charges=charges,
            )
            row = usable_hero_power(
                self.game_state, player_id, available_mana,
                next_turn=self._hero_power_next_turn(),
            )
            hp_cost = row[2] if row else 0
            if spell_mana + hp_cost > available_mana:
                display_total -= display_hero_power_face
                display_hero_power_face = 0
                display_hp_name = None
                display_mana_spent = spell_mana

        timed_out = self._lethal_budget_expired()

        if best_total > 0 or best_score > 0:
            self._overlay_lifesteal_heal = best_lifesteal_heal
            self._overlay_deathrattle_armor = best_deathrattle_armor
            self._overlay_direct_face = direct_face
            self._overlay_direct_prefix = direct_prefix
            self._overlay_direct_mana = direct_mana
            use_display = display_total > 0
            show_total = display_total if use_display else best_total
            show_board = display_board if use_display else best_board
            show_weapon = display_weapon_board if use_display else best_weapon_board
            show_spell = display_spell_face if use_display else best_spell_face
            show_battlecry = display_battlecry_face if use_display else best_battlecry_face
            show_hp = display_hero_power_face if use_display else best_hero_power_face
            show_buff = display_hero_buff_face if use_display else best_hero_buff_face
            show_seq = display_seq if use_display else best_seq
            show_order = display_order if use_display else best_order
            show_hp_name = display_hp_name if use_display else best_hp_name
            show_mana_spent = display_mana_spent if use_display else best_mana_spent
            overlay_face = self._apply_overlay_stats_from_best_line(
                pure_immediate=pure_immediate,
                pure_et=pure_et,
                best_board=show_board,
                best_weapon_board=show_weapon,
                best_spell_face=show_spell,
                best_battlecry_face=show_battlecry,
                best_total=show_total,
                best_hero_power_face=show_hp,
                best_hero_buff_face=show_buff,
                best_seq=show_seq,
                best_order=show_order,
                base_enemy_minions=base_enemy_minions,
                fighters=fighters,
                spell_mult=spell_mult,
                defender_shield=defender_shield,
                effective_hp=effective_hp,
                available_mana=available_mana,
                charges=charges,
                board_view=board_view,
                player_id=player_id,
                opp_taunts=opp_taunts,
                ignore_budget=timed_out,
            )
            self._overlay_best_seq = show_seq
            self._overlay_best_order = show_order
            self._overlay_best_hp_name = show_hp_name
            self._overlay_mana_spent = show_mana_spent
            if timed_out:
                return overlay_face if overlay_face > 0 else 0, "计算超时"
            return overlay_face, best_note

        # 回退：纯随从交换 / 无法术场攻
        fb, enemy_after, board_part_hint = self._best_fallback_board_line(
            board_view, player_id, opp_taunts, defender_shield,
        )

        mc_max, prob, top_outcomes, board_part = self._monte_carlo_pure_board_end_turn(
            fb, enemy_after, defender_shield, effective_hp,
        )
        floor_total, floor_board, floor_weapon, floor_hp = (
            self._overlay_board_floor_outcome(
                pure_immediate=pure_immediate,
                player_id=player_id,
                defender_shield=defender_shield,
                fighters=fighters,
                base_enemy_minions=base_enemy_minions,
                available_mana=available_mana,
            )
        )
        if floor_total > mc_max:
            mc_max = floor_total
            board_part = floor_board
            weapon_part = floor_weapon
            hp_part = floor_hp
        else:
            weapon_part = 0
            hp_part = 0
        uses_random = end_turn_uses_random(
            self.game_state.get_board(player_id),
        )
        self._reset_overlay_board_breakdown(
            pure_immediate, board_part, 0, mc_max,
            weapon_board=weapon_part,
            hero_power_face=hp_part,
            mc_max=mc_max, lethal_prob=prob,
            uses_random=uses_random, top_outcomes=top_outcomes,
        )
        self._overlay_best_seq = []
        self._overlay_best_hp_name = None
        return mc_max, ""

    def _format_spell_note(
        self,
        seq,
        spell_mult: int = 1,
        order: str = "spell_first",
        *,
        hand_charges: Optional[List] = None,
        available_mana: Optional[int] = None,
        hero_power_name: Optional[str] = None,
    ) -> str:
        parts: List[str] = []
        if hero_power_name:
            parts.append(f"技能:{hero_power_name}")
        if seq:
            names = "+".join(d.name for d, _, _ in seq)
            parts.append(f"法术:{names}")
        if hand_charges and available_mana is not None:
            mana_left = LethalChecker._mana_after_spell_sequence(seq, available_mana)
            playable = []
            budget = mana_left
            local = self.game_state.local_player_id
            for entity, cost, atk in sorted(hand_charges, key=lambda x: -x[2]):
                if cost <= budget:
                    if local is not None:
                        playable.append(
                            format_hand_charge_label(
                                self.game_state, local, entity, atk, prefix="",
                            )
                        )
                    else:
                        playable.append(f"{atk}攻冲锋")
                    budget -= cost
            if playable:
                parts.append("手牌冲锋:" + "+".join(playable))
        if not parts:
            return ""
        note = " ".join(parts)
        if spell_mult > 1:
            note += " x2埃提耶识"
        note += interleave_note_suffix(seq, order)
        if order not in ("attack_interleaved", "faceless_interleaved"):
            if order == "attack_first":
                note += " 先攻后法"
            else:
                note += " 先法后攻"
        return note

    def _simulate_taunt_clear_from_state(
        self,
        fighters: List[dict],
        taunts: List[dict],
        defender_shield: bool,
        *,
        extra_lifesteal_heal: int = 0,
        enemy_board: Optional[List[dict]] = None,
        rng: Optional[random.Random] = None,
    ) -> Tuple[int, int, bool]:
        """从已施法后的模拟状态继续清嘲（写回最优解后的 fighters / 敌方场面）。"""
        if not taunts:
            return self._fighters_face_damage(fighters, defender_shield), extra_lifesteal_heal, True
        if not any(f["attacks_left"] > 0 and f["health"] > 0 for f in fighters):
            return 0, extra_lifesteal_heal, False

        total_face, lifesteal_heal, best_fs, best_board = self._find_best_taunt_clear_state(
            fighters, taunts, defender_shield,
            enemy_board=enemy_board, rng=rng,
        )
        if total_face is None:
            return 0, extra_lifesteal_heal, False
        if best_fs is not None:
            fighters[:] = best_fs
        if enemy_board is not None and best_board is not None:
            self._apply_sim_board_to_enemy(enemy_board, best_board)
        return total_face, lifesteal_heal + extra_lifesteal_heal, True

    @staticmethod
    def _consume_attacks(fighters: List[dict]) -> None:
        for f in fighters:
            if f["kind"] == "weapon":
                f["attacks_left"] = 0
                f["durability"] = 0
            else:
                f["attacks_left"] = 0

    def _run_attack_phase(
        self,
        fighters: List[dict],
        taunts: List[dict],
        defender_shield: bool,
        *,
        enemy_board: Optional[List[dict]] = None,
        rng: Optional[random.Random] = None,
    ) -> Tuple[int, int, List[dict], List[dict]]:
        """
        完整攻击阶段：先消耗所有随从/武器攻击（不在攻击中间插法术）。
        Returns: (打脸伤害, 吸血回血, 攻击后 fighters, 剩余 taunts)
        """
        fs = _clone_combat_states(fighters)
        ts = _clone_combat_states(taunts)

        if not ts:
            face = self._fighters_face_damage(fs, defender_shield)
            self._consume_attacks(fs)
            return face, 0, fs, []

        board = _clone_combat_states(enemy_board if enemy_board is not None else ts)
        face, heal, best_fs, best_board = self._find_best_taunt_clear_state(
            fs, ts, defender_shield, enemy_board=board, rng=rng,
        )
        if face is not None:
            if enemy_board is not None:
                self._apply_sim_board_to_enemy(enemy_board, best_board or board)
            return face, heal, best_fs or [], self._living_taunt_states(best_board or board)

        fs2, _, heal2 = self._exhaust_attacks_on_taunts(
            fs, ts, enemy_board=board, rng=rng,
        )
        if enemy_board is not None:
            self._apply_sim_board_to_enemy(enemy_board, board)
        return 0, heal2, fs2, self._living_taunt_states(board)

    def _mask_fighter_attacks(
        self, fighters: List[dict], allowed_eids: Set[int],
    ) -> Tuple[List[dict], dict]:
        """仅 allowed_eids 保留 attacks_left，其余暂存为 0。返回 (fighters, 还原表)。"""
        saved: dict = {}
        for f in fighters:
            eid = f.get("entity_id")
            if eid is None:
                continue
            saved[eid] = f.get("attacks_left", 0)
            if eid not in allowed_eids:
                f["attacks_left"] = 0
        return fighters, saved

    @staticmethod
    def _restore_fighter_attacks(fighters: List[dict], saved: dict) -> None:
        for f in fighters:
            eid = f.get("entity_id")
            if eid is not None and eid in saved:
                f["attacks_left"] = saved[eid]

    @staticmethod
    def _restore_fighter_attacks_except(
        fighters: List[dict], saved: dict, skip_eids: Set[int],
    ) -> None:
        """仅恢复 skip_eids 以外随从的攻击次数（先攻者已消耗攻击）。"""
        for f in fighters:
            eid = f.get("entity_id")
            if eid is not None and eid in saved and eid not in skip_eids:
                f["attacks_left"] = saved[eid]

    def _run_partial_attack_phase(
        self,
        fighters: List[dict],
        taunts: List[dict],
        defender_shield: bool,
        *,
        allowed_eids: Set[int],
        consume_allowed_attacks: bool = False,
        enemy_board: Optional[List[dict]] = None,
    ) -> Tuple[int, int, List[dict], List[dict]]:
        """
        仅指定场面随从参与攻击。
        consume_allowed_attacks=False（默认）：先攻后还原攻击次数（无面穿插模拟换怪）。
        consume_allowed_attacks=True：先攻真实消耗攻击次数（法术穿插）。
        enemy_board：完整敌方场面，用于亡语召唤等写回。
        """
        fs = _clone_combat_states(fighters)
        ts = _clone_combat_states(taunts)
        if not allowed_eids:
            return 0, 0, fs, ts
        fs, saved = self._mask_fighter_attacks(fs, allowed_eids)
        board = _clone_combat_states(enemy_board if enemy_board is not None else taunts)
        face, heal, fs_out, ts_out = self._run_attack_phase(
            fs, ts, defender_shield, enemy_board=board,
        )
        if enemy_board is not None:
            self._apply_sim_board_to_enemy(enemy_board, board)
        if consume_allowed_attacks:
            self._restore_fighter_attacks_except(fs_out, saved, allowed_eids)
        else:
            self._restore_fighter_attacks(fs_out, saved)
        return face, heal, fs_out, ts_out

    def _optimal_partial_state_before_battlecry(
        self,
        enemy: List[dict],
        fighters: List[dict],
        allowed_eids: Set[int],
        seq: List,
        *,
        spell_mult: int,
        defender_shield: bool,
        available_mana: Optional[int] = None,
        hand_charges: Optional[List] = None,
    ) -> Tuple[List[dict], List[dict]]:
        """
        战吼 AOE 穿插（入侵者 / 碉堡中士等）：枚举允许先攻随从的所有解嘲分配，
        按「先攻 → 打出序列（含战吼）→ 再解嘲/打脸」选最优场面。
        """
        hero_hp = self._my_hero_hp_for_spells()
        charges = hand_charges or []
        best_enemy = _clone_combat_states(enemy)
        best_fs = _clone_combat_states(fighters)
        best_total = -1

        def _board_face_after_sequence(enemy_state: List[dict], fs_state: List[dict]) -> Tuple[int, int]:
            spell_res = apply_spell_sequence(
                enemy_state, fs_state, seq, spell_mult=spell_mult,
                enemy_shield=defender_shield,
                gs=self.game_state, player_id=self.game_state.local_player_id,
                hero_hp=hero_hp, mana_budget=available_mana,
                next_turn_preview=self._hero_power_next_turn(),
            )
            mana_left = self._mana_after_spell_sequence(seq, available_mana)
            fs_eval = _clone_combat_states(fs_state)
            self._add_playable_hand_charges(fs_eval, charges, mana_left)
            taunts2 = self._living_taunt_states(enemy_state)
            if taunts2:
                board_face, _, can_clear = self._simulate_taunt_clear_from_state(
                    fs_eval, taunts2, defender_shield,
                    extra_lifesteal_heal=spell_res.opponent_lifesteal_heal,
                    enemy_board=enemy_state,
                )
                if not can_clear:
                    board_face = 0
            else:
                board_face = self._fighters_face_damage(fs_eval, defender_shield)
            return board_face + spell_res.direct_face_damage, board_face

        def _evaluate(enemy_state: List[dict], fs_state: List[dict]) -> None:
            nonlocal best_total, best_enemy, best_fs
            total, _ = _board_face_after_sequence(
                _clone_combat_states(enemy_state),
                _clone_combat_states(fs_state),
            )
            if total > best_total:
                best_total = total
                best_enemy = _clone_combat_states(enemy_state)
                best_fs = _clone_combat_states(fs_state)

        def _dfs(enemy_state: List[dict], fs_state: List[dict], taunts: List[dict]) -> None:
            if self._lethal_budget_expired():
                _evaluate(enemy_state, fs_state)
                return
            has_action = False
            for f in fs_state:
                eid = f.get("entity_id")
                if eid not in allowed_eids:
                    continue
                if f.get("attacks_left", 0) <= 0 or f.get("health", 0) <= 0:
                    continue
                if not taunts:
                    break
                for t in taunts:
                    if t.get("health", 0) <= 0:
                        continue
                    fs2 = _clone_combat_states(fs_state)
                    ts2 = _clone_combat_states(taunts)
                    enemy2 = _clone_combat_states(enemy_state)
                    f2 = next(x for x in fs2 if x.get("entity_id") == eid)
                    t2 = next(x for x in ts2 if x.get("entity_id") == t.get("entity_id"))
                    self._apply_single_attack(
                        f2, t2, enemy_board=enemy2, fighters=fs2,
                    )
                    if self._taunt_is_dead(t2):
                        resolve_minion_death(t2, enemy2, fs2)
                        remove_dead_taunts(ts2)
                        remove_dead_taunts(enemy2)
                    self._sync_taunt_states_after_attack(enemy2, ts2)
                    has_action = True
                    _dfs(enemy2, fs2, self._living_taunt_states(enemy2))
            if not has_action:
                _evaluate(enemy_state, fs_state)

        _dfs(
            _clone_combat_states(enemy),
            _clone_combat_states(fighters),
            self._living_taunt_states(enemy),
        )
        return best_enemy, best_fs

    _optimal_partial_state_before_hostile = _optimal_partial_state_before_battlecry

    def _exhaust_rush_on_taunts(
        self, fighters: List[dict], taunts: List[dict],
    ) -> Tuple[List[dict], List[dict], int]:
        """仅突袭随从解嘲讽（当回合不能打脸）。"""
        fs = _clone_combat_states(fighters)
        saved: dict = {}
        for f in fs:
            eid = f.get("entity_id")
            if eid is None:
                continue
            saved[eid] = f.get("attacks_left", 0)
            if not f.get("rush"):
                f["attacks_left"] = 0
        fs_out, ts_out, heal = self._exhaust_attacks_on_taunts(fs, taunts)
        self._restore_fighter_attacks(fs_out, saved)
        return fs_out, ts_out, heal

    def _board_minion_attack_eids(self, fighters: List[dict]) -> List[int]:
        out: List[int] = []
        for f in fighters:
            if f.get("kind") != "minion":
                continue
            if f.get("health", 0) <= 0 or f.get("attacks_left", 0) <= 0:
                continue
            eid = f.get("entity_id")
            if eid is not None:
                out.append(eid)
        return out

    def _attack_interleave_subsets(self, fighters: List[dict]) -> List[Set[int]]:
        eids = self._board_minion_attack_eids(fighters)
        subsets: List[Set[int]] = []
        for r in range(len(eids) + 1):
            for combo in combinations(eids, r):
                subsets.append(set(combo))
        return subsets or [set()]

    def _simulate_attack_interleaved_outcome(
        self,
        base_enemy_minions: List[dict],
        fighters: List[dict],
        seq: List,
        *,
        spell_mult: int,
        defender_shield: bool,
        available_mana: Optional[int] = None,
        hand_charges: Optional[List] = None,
        hp_direct: int = 0,
    ) -> Tuple[int, int, int, int, int, int]:
        """
        无面 / 战吼 AOE / 法术穿插：枚举「哪些场面随从先攻」→ 打出序列 → 再解嘲/打脸。
        无面：突袭解嘲后非突袭打脸；入侵者/碉堡中士等：战吼后剩余随从解嘲并打脸；
        穿插法术：部分先攻改变场面后再施法（如疯狂药水偷亡语随从）。
        """
        from .interleave_board import (
            sequence_has_interleave_spell,
            sequence_has_pre_play_battlecry,
            sequence_is_faceless_only,
        )

        faceless_only = sequence_is_faceless_only(seq)
        has_pre_play = sequence_has_pre_play_battlecry(seq)
        hero_hp = self._my_hero_hp_for_spells()
        charges = hand_charges or []
        best_total = 0
        best_minion = 0
        best_weapon = 0
        best_spell = 0
        best_hp = 0
        best_hero_buff = 0

        for pre_attack_eids in self._attack_interleave_subsets(fighters):
            enemy = _clone_combat_states(base_enemy_minions)
            fs = _clone_combat_states(fighters)
            taunts = self._living_taunt_states(enemy)
            pre_board_face = 0
            opp_hp_for_spell = None

            if pre_attack_eids and taunts:
                if faceless_only:
                    _, _, fs, taunts_after = self._run_partial_attack_phase(
                        fs, taunts, defender_shield, allowed_eids=pre_attack_eids,
                        enemy_board=enemy,
                    )
                    self._sync_taunt_states_after_attack(enemy, taunts_after)
                elif has_pre_play:
                    enemy, fs = self._optimal_partial_state_before_battlecry(
                        enemy, fs, pre_attack_eids, seq,
                        spell_mult=spell_mult,
                        defender_shield=defender_shield,
                        available_mana=available_mana,
                        hand_charges=charges,
                    )
                else:
                    _, _, fs, taunts_after = self._run_partial_attack_phase(
                        fs, taunts, defender_shield, allowed_eids=pre_attack_eids,
                        consume_allowed_attacks=True, enemy_board=enemy,
                    )
                    self._sync_taunt_states_after_attack(enemy, taunts_after)
            elif not taunts and sequence_has_interleave_spell(seq):
                if pre_attack_eids:
                    _, _, fs, _ = self._run_partial_attack_phase(
                        fs, [], defender_shield, allowed_eids=pre_attack_eids,
                        consume_allowed_attacks=not faceless_only and not has_pre_play,
                    )
                pre_board_face, _, fs, _ = self._run_attack_phase(
                    fs, [], defender_shield,
                )
                opp_hp_for_spell = self._opponent_hero_hp_after_face_damage(
                    defender_shield, pre_board_face,
                )
            elif pre_attack_eids and not taunts:
                _, _, fs, _ = self._run_partial_attack_phase(
                    fs, [], defender_shield, allowed_eids=pre_attack_eids,
                    consume_allowed_attacks=not faceless_only and not has_pre_play,
                )

            spell_res = apply_spell_sequence(
                enemy, fs, seq, spell_mult=spell_mult,
                enemy_shield=defender_shield,
                gs=self.game_state, player_id=self.game_state.local_player_id,
                hero_hp=hero_hp, mana_budget=available_mana,
                opponent_hero_hp=opp_hp_for_spell,
                next_turn_preview=self._hero_power_next_turn(),
            )
            mana_left = self._mana_after_spell_sequence(seq, available_mana)
            self._add_playable_hand_charges(fs, charges, mana_left)

            spell_face = spell_res.direct_face_damage
            taunts2 = self._living_taunt_states(enemy)
            if faceless_only:
                if taunts2:
                    fs, taunts_after, _ = self._exhaust_rush_on_taunts(fs, taunts2)
                    self._sync_taunt_states_after_attack(enemy, taunts_after)
                    if self._living_taunt_states(enemy):
                        if spell_face <= 0 and hp_direct <= 0:
                            total, minion_board, weapon_board, spell_face, hp_face, hero_buff_board = (
                                0, 0, 0, 0, 0, 0,
                            )
                        else:
                            total, minion_board, weapon_board, spell_face, hp_face, hero_buff_board = (
                                spell_face + hp_direct, 0, 0, spell_face, hp_direct, 0,
                            )
                    else:
                        total, minion_board, weapon_board, spell_face, hp_face, hero_buff_board = (
                            self._face_parts_from_fighters(
                                fs, spell_face, hp_direct, defender_shield,
                            )
                        )
                else:
                    total, minion_board, weapon_board, spell_face, hp_face, hero_buff_board = (
                        self._face_parts_from_fighters(
                            fs, spell_face, hp_direct, defender_shield,
                        )
                    )
            elif taunts2:
                board_face, _, can_clear = self._simulate_taunt_clear_from_state(
                    fs, taunts2, defender_shield,
                    extra_lifesteal_heal=spell_res.opponent_lifesteal_heal,
                    enemy_board=enemy,
                )
                if not can_clear:
                    if spell_face <= 0 and hp_direct <= 0:
                        total, minion_board, weapon_board, spell_face, hp_face, hero_buff_board = (
                            0, 0, 0, 0, 0, 0,
                        )
                    else:
                        total, minion_board, weapon_board, spell_face, hp_face, hero_buff_board = (
                            spell_face + hp_direct, 0, 0, spell_face, hp_direct, 0,
                        )
                else:
                    minion_board, weapon_board, hero_buff_board, remain_hp = (
                        self._split_fighter_face(fs, defender_shield)
                    )
                    spell_face = self._spell_face_including_stolen(
                        fs, spell_face, defender_shield,
                    )
                    total = (
                        minion_board + weapon_board + hero_buff_board
                        + spell_face + hp_direct + remain_hp
                    )
                    hp_face = hp_direct + remain_hp
            else:
                total, minion_board, weapon_board, spell_face, hp_face, hero_buff_board = (
                    self._face_parts_from_fighters(
                        fs, spell_face, hp_direct, defender_shield,
                    )
                )

            if pre_board_face > 0:
                total += pre_board_face
                hero_buff_board += pre_board_face

            total, minion_board, weapon_board, spell_face, hp_face, hero_buff_board = (
                self._apply_end_turn_face(
                    enemy, defender_shield, total,
                    minion_board, weapon_board, spell_face, hp_face,
                    hero_buff_board=hero_buff_board,
                )
            )
            if total > best_total:
                best_total = total
                best_minion = minion_board
                best_weapon = weapon_board
                best_spell = spell_face
                best_hp = hp_face
                best_hero_buff = hero_buff_board

        return best_total, best_minion, best_weapon, best_spell, best_hp, best_hero_buff

    _simulate_faceless_interleaved_outcome = _simulate_attack_interleaved_outcome
    _faceless_interleave_subsets = _attack_interleave_subsets

    def _exhaust_attacks_on_taunts(
        self,
        fighters: List[dict],
        taunts: List[dict],
        *,
        enemy_board: Optional[List[dict]] = None,
        rng: Optional[random.Random] = None,
    ) -> Tuple[List[dict], List[dict], int]:
        """无法清完嘲讽时，仍模拟用完所有攻击（用于先攻后法）。"""
        from .deathrattle import remove_dead_taunts

        fs = _clone_combat_states(fighters)
        board = _clone_combat_states(enemy_board if enemy_board is not None else taunts)
        heal = 0
        made_progress = True
        while made_progress:
            made_progress = False
            living = self._living_taunt_states(board)
            if not living:
                break
            for f in fs:
                if f["attacks_left"] <= 0 or f["health"] <= 0:
                    continue
                target = living[0]
                h = self._apply_single_attack(
                    f, target, enemy_board=board, fighters=fs, rng=rng,
                )
                heal += h
                remove_dead_taunts(board)
                made_progress = True
                break
        if enemy_board is not None:
            self._apply_sim_board_to_enemy(enemy_board, board)
        return fs, self._living_taunt_states(board), heal

    def _calculate_quick_lethal_for_player(
        self,
        attacker_id: int,
        defender_id: int,
        *,
        include_hand: bool,
        board_active_turn: bool = True,
        mana_for_hand: Optional[int] = None,
        use_overlay_board: bool = False,
    ) -> Tuple[int, List[DamageSource], bool]:
        """
        快速斩杀估算：场面交换清嘲 + 手牌直伤/冲锋静态累加。
        不搜索 spell_board 解场顺序，非最优解；完整斩杀见 overlay_board_face_damage。
        """
        if defender_id is None:
            return 0, [], False

        damage_sources = []
        total_damage = 0

        atk_hero = self.game_state.get_hero(attacker_id)
        atk_board = self.game_state.get_board(attacker_id)
        atk_hand = self.game_state.get_hand(attacker_id) if include_hand else []

        opp_hero = self.game_state.get_hero(defender_id)
        if opp_hero:
            opp_health = opp_hero.current_health
            if opp_health == 0 and opp_hero.health == 0:
                opp_health = 30
            opp_armor = opp_hero.tags.get("ARMOR", 0)
            opp_total_hp = opp_health + opp_armor
            opp_shield = hero_has_divine_shield(opp_hero)
        else:
            opp_health, opp_armor, opp_total_hp = self._defender_health_tuple(defender_id)
            opp_shield = False

        spell_damage = total_spell_power(self.game_state, attacker_id)

        if atk_hero:
            if mana_for_hand is not None:
                available_mana = mana_for_hand
            else:
                available_mana = self._available_mana(attacker_id)
        else:
            available_mana = mana_for_hand if mana_for_hand is not None else 10

        def_board = self.game_state.get_board(defender_id)
        if use_overlay_board and attacker_id == self.game_state.local_player_id:
            atk_board_view = self.game_state.get_overlay_board(attacker_id)
        else:
            atk_board_view = build_player_board(
                self.game_state, attacker_id, active_turn=board_active_turn
            )

        opp_taunts = living_taunt_minions(def_board, self.game_state)

        board_damage = 0
        attackers = []

        if opp_taunts:
            total_face, lifesteal_heal, can_bypass = self._calculate_board_damage_with_taunts(
                atk_board_view, attacker_id, opp_taunts, defender_shield=opp_shield
            )
            self._last_lifesteal_heal = lifesteal_heal
            if can_bypass and total_face > 0:
                board_damage = total_face
                desc = "场面攻击（清嘲讽后剩余，含模拟交换）"
                if lifesteal_heal > 0:
                    desc += f" [对手吸血+{lifesteal_heal}]"
                damage_sources.append(DamageSource("board", board_damage, desc))
                total_damage += board_damage
        else:
            self._last_lifesteal_heal = 0
            self._last_deathrattle_armor = 0
            board_damage = atk_board_view.face_attack_damage_no_taunt(opp_shield)
            for card in atk_board_view.cards:
                if not card.entity.is_minion or not card.can_attack_hero:
                    continue
                remaining = max(card.attacks_per_turn - card.attacks_this_turn, 0)
                suffix = f"x{remaining}" if remaining > 1 else ""
                attackers.append(f"{card.entity.card_id or '随从'}({card.std_attack}{suffix})")

            if board_damage > 0:
                desc = f"场面攻击 [{', '.join(attackers)}]"
                if atk_board_view.hero_damage > 0:
                    desc += f" +英雄{atk_board_view.hero_damage}"
                damage_sources.append(DamageSource("board", board_damage, desc))
                total_damage += board_damage

        enemy_board = self._build_enemy_minion_states(attacker_id)
        et_face = board_end_turn_face_now(
            self.game_state.get_board(attacker_id),
            enemy_board,
            opp_shield,
            game_state=self.game_state,
            player_id=attacker_id,
        )
        if et_face > 0:
            names = end_turn_names_on_board(self.game_state.get_board(attacker_id))
            label = names[0] if len(names) == 1 else "回合结束"
            damage_sources.append(
                DamageSource("board", et_face, f"回合结束:{label}+{et_face}"),
            )
            total_damage += et_face

        for card in atk_hand:
            if card.card_id in SPELL_DAMAGE_DB:
                cost, base_damage, can_hit_face = SPELL_DAMAGE_DB[card.card_id]
                if not can_hit_face:
                    continue
                actual_cost = card.cost if card.cost > 0 else cost

                if actual_cost <= available_mana:
                    from .spell_board import manathirst_spell_face_damage
                    mt_dmg = manathirst_spell_face_damage(
                        card.card_id, self.game_state, attacker_id, card=card,
                    )
                    actual_damage = (
                        mt_dmg if mt_dmg is not None else base_damage
                    ) + spell_damage
                    desc = f"法术 {card.card_id}"
                    damage_sources.append(DamageSource("spell", actual_damage, desc, actual_cost))
                    total_damage += actual_damage
                    available_mana -= actual_cost

        # 手牌冲锋随从（静态表 + CHARGE 标签 / 黑暗之赐冲锋）
        for card in atk_hand:
            if not card.is_minion:
                continue
            charge_damage = None
            base_cost = 0
            if card.card_id in CHARGE_MINIONS_DB:
                base_cost, charge_damage = CHARGE_MINIONS_DB[card.card_id]
            elif hand_minion_has_charge(self.game_state, card):
                base_cost = hand_minion_cost(card)
                charge_damage = hand_minion_attack(card)
            else:
                continue
            actual_cost = card.cost if card.cost > 0 else base_cost
            if actual_cost <= available_mana and charge_damage > 0:
                copies = 1
                if double_agent_summons_copy(self.game_state, attacker_id, card):
                    copies = 2
                desc = f"冲锋 {card.card_id}"
                for _ in range(copies):
                    damage_sources.append(
                        DamageSource("charge", charge_damage, desc, actual_cost),
                    )
                    total_damage += charge_damage
                available_mana -= actual_cost

        # 判断是否有斩杀（吸血嘲讽、亡语加甲抬高有效血量；英雄圣盾在场面伤害里已计）
        opp_effective_hp = self._lethal_threshold_hp()
        board_only = sum(s.damage for s in damage_sources if s.source_type == "board")
        other_hits = [s.damage for s in damage_sources if s.source_type != "board"]
        if opp_shield and board_only <= 0 and other_hits:
            effective_damage = apply_divine_shield_to_hits(other_hits, True)
        else:
            effective_damage = total_damage
        has_lethal = effective_damage >= opp_effective_hp

        return total_damage, damage_sources, has_lethal

    def _defender_health_tuple(self, defender_id: int) -> Tuple[int, int, int]:
        """对手英雄未解析时的血量回退（与 get_opponent_health 一致）"""
        if defender_id == self.game_state.opponent_player_id:
            return self.get_opponent_health()
        return 30, 0, 30

    @staticmethod
    def _has_lifesteal(entity) -> bool:
        return entity.tags.get("LIFESTEAL", 0) == 1

    @staticmethod
    def _has_poisonous(entity) -> bool:
        return entity.tags.get("POISONOUS", 0) == 1

    def _build_fighters(self, board_view, player_id: int) -> List[dict]:
        """构建可参与交换的攻击者（随从 + 英雄武器），含血量与剩余攻击次数。"""
        by_id: dict = {}

        for card in board_view.cards:
            if not card.entity.is_minion or not card.can_attack_minion:
                continue
            eid = card.entity.entity_id
            if eid not in by_id:
                from .rush_combat import stamp_fighter_attack_effects

                from .board_damage import (
                    entity_spell_immune,
                    is_dormant,
                    _minion_summoned_this_turn,
                    is_potion_madness_stolen,
                )
                from .hero_power_board import is_dk_ghoul_board_token

                cid = card.entity.card_id or ""
                from_hp = (
                    is_dk_ghoul_board_token(cid)
                    and _minion_summoned_this_turn(card.entity)
                )
                stolen_turn = is_potion_madness_stolen(self.game_state, card.entity)
                fighter = {
                    "kind": "minion",
                    "entity_id": eid,
                    "card_id": cid,
                    "atk": card.std_attack,
                    "health": card.entity.current_health,
                    "shield": card.entity.tags.get("DIVINE_SHIELD", 0) == 1,
                    "poisonous": self._has_poisonous(card.entity),
                    "lifesteal": self._has_lifesteal(card.entity),
                    "spell_immune": entity_spell_immune(
                        card.entity, self.game_state,
                    ),
                    "attacks_left": 0,
                    "can_face": card.can_attack_hero,
                    "rush": card.entity.tags.get("RUSH", 0) == 1,
                    "dormant": is_dormant(card.entity, self.game_state),
                    "silenced": is_silenced(card.entity),
                    "from_hero_power": from_hp,
                    "stolen_turn": stolen_turn,
                }
                fighter["dragon"] = entity_is_dragon(card.entity)
                fighter["beast"] = entity_is_beast(card.entity)
                from .damaged_spell_power import fighter_spell_power_from_entity

                fighter["damage"] = int(card.entity.damage or 0)
                fighter["max_health"] = int(card.entity.health or card.entity.current_health or 0)
                fighter["spellpower"] = fighter_spell_power_from_entity(card.entity)
                stamp_fighter_attack_effects(
                    fighter, cid,
                    infused_cleave=False,
                )
                from .secret_attack_board import stamp_crusader_aura_on_fighter

                stamp_crusader_aura_on_fighter(fighter, self.game_state, player_id)
                by_id[eid] = fighter
            used = (
                effective_attacks_this_turn(card.entity, active_turn=card.active_turn)
                if card.active_turn else 0
            )
            by_id[eid]["attacks_left"] += max(card.attacks_per_turn - used, 0)

        fighters = [f for f in by_id.values() if f["attacks_left"] > 0 and f["atk"] > 0]

        hero = self.game_state.get_hero(player_id)
        weapon = self.game_state.get_weapon(player_id)
        active = board_view.active_turn
        if hero and weapon and hero_can_attack_with_weapon(hero, weapon, active):
            silenced = is_silenced(hero)
            max_a = attacks_per_turn(hero, silenced)
            used = attacks_this_turn(hero) if active else 0
            hero_attacks = max(max_a - used, 0)
            hero_attacks = min(hero_attacks, weapon.current_durability)
            w_atk = _std_attack(weapon)
            if hero_attacks > 0 and w_atk > 0:
                w_fighter = {
                    "kind": "weapon",
                    "card_id": weapon.card_id or "",
                    "atk": w_atk,
                    "health": hero.current_health + hero.tags.get("ARMOR", 0),
                    "shield": hero.tags.get("DIVINE_SHIELD", 0) == 1,
                    "attacks_left": hero_attacks,
                    "durability": weapon.current_durability,
                    "can_face": hero_weapon_can_face(hero, weapon),
                }
                from .weapon_p0 import stamp_equipped_weapon_effects
                stamp_equipped_weapon_effects(w_fighter, weapon.card_id or "")
                fighters.append(w_fighter)
        elif hero and hero_can_attack_with_weapon(hero, None, active):
            silenced = is_silenced(hero)
            max_a = attacks_per_turn(hero, silenced)
            used = attacks_this_turn(hero) if active else 0
            hero_attacks = max(max_a - used, 0)
            h_atk = hero_weapon_strike_damage(hero, None)
            if hero_attacks > 0 and h_atk > 0:
                fighters.append({
                    "kind": "hero",
                    "atk": h_atk,
                    "health": hero.current_health + hero.tags.get("ARMOR", 0),
                    "shield": hero.tags.get("DIVINE_SHIELD", 0) == 1,
                    "attacks_left": hero_attacks,
                    "can_face": hero_weapon_can_face(hero, None),
                })

        return fighters

    @staticmethod
    def _fighters_face_hits(fighters: List[dict]) -> List[int]:
        from .combat_sim import _friendly_taunt_blocks_face, _normalize_fighters
        from .rush_combat import simulate_minion_face_hits

        normed = _normalize_fighters(fighters)
        if _friendly_taunt_blocks_face(normed):
            return []
        hits: List[int] = []
        minion_fs: List[dict] = []
        for f in normed:
            if f.get("kind") == "minion":
                if f.get("health", 0) <= 0 or f.get("attacks_left", 0) <= 0:
                    continue
                if not f.get("can_face", True):
                    continue
                minion_fs.append(f)
                continue
            if not f.get("can_face", True):
                continue
            attacks_left = f.get("attacks_left", 0)
            if f.get("health", 0) <= 0 or attacks_left <= 0:
                continue
            if f.get("kind") == "weapon":
                n = min(attacks_left, f.get("durability", 0))
            else:
                n = attacks_left
            for _ in range(n):
                hits.append(f["atk"])
        hits.extend(simulate_minion_face_hits(minion_fs))
        return hits

    @staticmethod
    def _fighters_face_damage(
        fighters: List[dict],
        defender_shield: bool = False,
        *,
        include_inquisitor_mirror: bool = True,
    ) -> int:
        """存活攻击者剩余可打脸伤害（含未用于清嘲的武器；可选防守方英雄圣盾）"""
        from .rush_combat import inquisitor_face_mirror_hits

        base_hits = LethalChecker._fighters_face_hits(fighters)
        if include_inquisitor_mirror:
            hits = list(inquisitor_face_mirror_hits(fighters, base_hits))
        else:
            hits = list(base_hits)
        for f in fighters:
            if f.get("kind") != "weapon" or f.get("health", 0) <= 0:
                continue
            if not f.get("can_face", True):
                continue
            aoe = int(f.get("hero_aoe_on_attack", 0) or 0)
            if aoe <= 0:
                continue
            n = min(f.get("attacks_left", 0), f.get("durability", 0))
            hits.extend([aoe] * n)
        return apply_divine_shield_to_hits(hits, defender_shield)

    @staticmethod
    def _taunt_combat_state(entity, gs: Optional["GameState"] = None) -> dict:
        from .board_damage import entity_spell_immune, is_dormant

        state = {
            "entity_id": entity.entity_id,
            "health": entity.current_health,
            "atk": _std_attack(entity),
            "damage": getattr(entity, "damage", 0) or entity.tags.get("DAMAGE", 0),
            "zone_pos": entity.tags.get("ZONE_POSITION", 0) or getattr(entity, "zone_pos", 0),
            "shield": entity.tags.get("DIVINE_SHIELD", 0) == 1,
            "poisonous": LethalChecker._has_poisonous(entity),
            "lifesteal": LethalChecker._has_lifesteal(entity),
            "spell_immune": entity_spell_immune(entity, gs),
            "taunt": entity_has_taunt(entity, gs),
            "card_id": entity.card_id or "",
            "cost": int(getattr(entity, "cost", 0) or entity.tags.get("COST", 0) or 0),
            "script_data_num_1": int(entity.tags.get("TAG_SCRIPT_DATA_NUM_1", 0) or 0),
            "charge": entity.tags.get("CHARGE", 0) == 1,
            "rush": entity.tags.get("RUSH", 0) == 1,
            "legendary": entity.tags.get("RARITY") in ("LEGENDARY", 5),
            "frozen": entity.tags.get("FROZEN", 0) == 1,
            "dormant": is_dormant(entity, gs),
        }
        state["dragon"] = entity_is_dragon(entity)
        if gs is not None:
            from .reborn import entity_reborn_flags

            reborn, full_hp, max_hp = entity_reborn_flags(gs, entity)
            state["reborn"] = reborn
            state["reborn_full_health"] = full_hp
            state["reborn_used"] = not reborn and entity.tags.get("HAS_BEEN_REBORN", 0) == 1
            state["max_health"] = max_hp
        return state

    @staticmethod
    def _normalize_taunt_combat_state(taunt: dict) -> dict:
        """补全模拟嘲讽 dict 的缺省字段（手测/法术解场后的精简 dict 也可安全清嘲）。"""
        t = dict(taunt)
        t.setdefault("health", 0)
        t.setdefault("atk", 0)
        t.setdefault("damage", 0)
        t.setdefault("shield", False)
        t.setdefault("poisonous", False)
        t.setdefault("lifesteal", False)
        t.setdefault("spell_immune", False)
        t.setdefault("taunt", True)
        t.setdefault("card_id", "")
        t.setdefault("cost", 0)
        t.setdefault("charge", False)
        t.setdefault("rush", False)
        t.setdefault("frozen", False)
        t.setdefault("dormant", False)
        t.setdefault("dragon", False)
        t.setdefault("reborn", False)
        t.setdefault("reborn_full_health", False)
        t.setdefault("reborn_used", False)
        t.setdefault("max_health", max(int(t.get("health", 0) or 0), 1))
        return t

    @staticmethod
    def _living_taunt_states(enemy_minions: List[dict]) -> List[dict]:
        from .combat_sim import unit_is_dormant

        return [
            t for t in enemy_minions
            if t.get("health", 0) > 0 and t.get("taunt")
            and t.get("kind") not in ("hero", "sim_meta")
            and not unit_is_dormant(t)
        ]

    @staticmethod
    def _apply_sim_board_to_enemy(enemy_minions: List[dict], sim_board: List[dict]) -> None:
        """将模拟后的敌方场面写回列表（含亡语召唤的新随从）。"""
        enemy_minions[:] = _clone_combat_states(sim_board)

    @staticmethod
    def _sync_taunt_states_after_attack(
        enemy_minions: List[dict], taunts_after: List[dict],
    ) -> None:
        """攻击阶段后把嘲讽随从血量写回完整敌方场面列表。"""
        if not taunts_after:
            return
        by_id = {t["entity_id"]: t for t in taunts_after if t.get("entity_id") is not None}
        alive_ids = set(by_id.keys())
        for m in enemy_minions:
            if not m.get("taunt"):
                continue
            eid = m.get("entity_id")
            if eid in by_id:
                m["health"] = by_id[eid]["health"]
                m["shield"] = by_id[eid].get("shield", False)
            elif eid is not None and eid not in alive_ids and m.get("health", 0) > 0:
                m["health"] = 0

    def _build_enemy_minion_states(self, player_id: int) -> List[dict]:
        opp = self.game_state.opponent_player_id
        if opp is None:
            return []
        board = self.game_state.get_board(opp)
        return [
            self._taunt_combat_state(m, self.game_state)
            for m in board
            if m.current_health > 0
        ]

    @staticmethod
    def _apply_single_attack_core(fighter: dict, taunt: dict) -> int:
        """
        模拟一次攻击。更新 fighter / taunt 状态。
        Returns: 本次对目标造成的血量伤害（用于吸血回血）。
        """
        if fighter["attacks_left"] <= 0 or fighter["health"] <= 0:
            return 0

        from .secret_attack_board import crusader_strike_attack, apply_crusader_buff_after_strike

        strike_atk = crusader_strike_attack(fighter)
        if taunt.get("shield"):
            taunt["shield"] = False
            damage_dealt = 0
        else:
            damage_dealt = min(strike_atk, max(taunt.get("health", 0), 0))
            taunt["health"] = taunt.get("health", 0) - strike_atk
            if damage_dealt > 0 and fighter.get("poisonous"):
                taunt["health"] = 0

        if damage_dealt > 0 and taunt.get("poisonous"):
            fighter["health"] = 0
        elif taunt.get("atk", 0) > 0 and damage_dealt > 0:
            if fighter.get("shield"):
                fighter["shield"] = False
            elif not fighter.get("hero_immune_on_attack"):
                fighter["health"] -= taunt["atk"]

        fighter["attacks_left"] -= 1
        if fighter.get("kind") == "weapon":
            fighter["durability"] = max(0, fighter.get("durability", 0) - 1)
        elif damage_dealt > 0 or not taunt.get("shield"):
            apply_crusader_buff_after_strike(fighter)

        return damage_dealt if taunt.get("lifesteal") else 0

    @staticmethod
    def _apply_mirror_attack_core(fighter: dict, target: dict) -> int:
        """审判官跟刀：造成伤害但不消耗 attacks_left / 武器耐久。"""
        if fighter.get("health", 0) <= 0 or target.get("health", 0) <= 0:
            return 0

        from .secret_attack_board import crusader_strike_attack

        strike_atk = crusader_strike_attack(fighter)
        if target.get("shield"):
            target["shield"] = False
            damage_dealt = 0
        else:
            damage_dealt = min(strike_atk, max(target.get("health", 0), 0))
            target["health"] = target.get("health", 0) - strike_atk
            if damage_dealt > 0 and fighter.get("poisonous"):
                target["health"] = 0

        if damage_dealt > 0 and target.get("poisonous"):
            fighter["health"] = 0
        elif target.get("atk", 0) > 0 and target.get("health", 0) > 0:
            if fighter.get("shield"):
                fighter["shield"] = False
            else:
                fighter["health"] -= target["atk"]

        return damage_dealt if target.get("lifesteal") else 0

    def _apply_single_attack(
        self,
        fighter: dict,
        target: dict,
        *,
        enemy_board: Optional[List[dict]] = None,
        fighters: Optional[List[dict]] = None,
        rng: Optional[random.Random] = None,
    ) -> int:
        from .deathrattle import resolve_minion_death, remove_dead_taunts
        from .rush_combat import after_hero_attack, after_minion_attack

        was_alive = target.get("health", 0) > 0
        heal = self._apply_single_attack_core(fighter, target)

        if fighter.get("kind") == "weapon" and enemy_board is not None and fighters is not None:
            if self._taunt_is_dead(target):
                resolve_minion_death(target, enemy_board, fighters)
                remove_dead_taunts(enemy_board)
            heal += after_hero_attack(
                self, target, enemy_board=enemy_board, fighters=fighters,
                defender_shield=False,
            )
            from .weapon_p0 import after_hero_weapon_attack
            heal += after_hero_weapon_attack(
                fighter, target, enemy_board, fighters, enemy_shield=False,
            )
            aoe = int(fighter.get("hero_aoe_on_attack", 0) or 0)
            if aoe > 0:
                from .eudora_loot import apply_hero_aoe_after_attack
                heal += apply_hero_aoe_after_attack(
                    enemy_board, fighters, aoe,
                )
            return heal

        if enemy_board is not None and fighters is not None and fighter.get("kind") == "minion":
            heal += after_minion_attack(
                self, fighter, target,
                enemy_board=enemy_board, fighters=fighters,
                was_alive_before=was_alive,
            )
            if self._taunt_is_dead(target):
                resolve_minion_death(target, enemy_board, fighters)
                remove_dead_taunts(enemy_board)
            if fighter.get("health", 0) <= 0:
                resolve_minion_death(fighter, enemy_board, fighters)

        return heal

    @staticmethod
    def _taunt_is_dead(taunt: dict) -> bool:
        return taunt.get("health", 0) <= 0

    def _kill_taunt_outcomes(
        self,
        fighters: List[dict],
        taunt: dict,
        other_taunts: List[dict],
        *,
        enemy_board: Optional[List[dict]] = None,
        rng: Optional[random.Random] = None,
    ) -> List[Tuple[List[dict], List[dict], int]]:
        """枚举清掉单个嘲讽后的 (攻击者, 敌方场面, 吸血回血)。场面含亡语召唤。"""
        from .deathrattle import remove_dead_taunts
        from .rush_combat import ogre_pick_target

        outcomes: List[Tuple[List[dict], List[dict], int]] = []
        all_taunts = [taunt] + list(other_taunts)
        board = enemy_board if enemy_board is not None else all_taunts
        t_eid = taunt.get("entity_id")

        def _pick_on_board(board2: List[dict]) -> Optional[dict]:
            if t_eid is not None:
                for m in board2:
                    if m.get("entity_id") == t_eid and m.get("health", 0) > 0:
                        return m
            return None

        def dfs(fs: List[dict], board2: List[dict], heal: int):
            if self._lethal_budget_expired():
                return
            pick = _pick_on_board(board2)
            if pick is None or self._taunt_is_dead(pick):
                remove_dead_taunts(board2)
                outcomes.append((_clone_combat_states(fs), _clone_combat_states(board2), heal))
                return
            if not any(f["attacks_left"] > 0 and f["health"] > 0 for f in fs):
                return
            for i in range(len(fs)):
                if fs[i]["attacks_left"] <= 0 or fs[i]["health"] <= 0:
                    continue
                fs2 = _clone_combat_states(fs)
                board3 = _clone_combat_states(board2)
                target = _pick_on_board(board3)
                if target is None:
                    continue
                if fs2[i].get("ogre_misdirect"):
                    living = self._living_taunt_states(board3)
                    wrong = ogre_pick_target(target, living, rng)
                    wrong2 = next(
                        (x for x in board3 if x.get("entity_id") == wrong.get("entity_id")),
                        None,
                    )
                    if wrong2 is not None:
                        target = wrong2
                h = self._apply_single_attack(
                    fs2[i], target, enemy_board=board3, fighters=fs2, rng=rng,
                )
                remove_dead_taunts(board3)
                dfs(fs2, board3, heal + h)

        dfs(_clone_combat_states(fighters), _clone_combat_states(board), 0)
        return outcomes

    def _calculate_board_damage_with_taunts(
        self, board_view, player_id: int, opp_taunts: list, *, defender_shield: bool = False
    ) -> Tuple[int, int, bool]:
        """
        模拟交换清嘲讽，计算剩余打脸伤害（含武器参与清嘲）。

        Returns:
            (打脸伤害, 吸血回血, 是否清得掉所有嘲讽)
        """
        fighters = self._build_fighters(board_view, player_id)
        if not fighters:
            return 0, 0, False

        taunts = [self._taunt_combat_state(t, self.game_state) for t in opp_taunts]
        opp = self.game_state.opponent_player_id
        def_board = self.game_state.get_board(opp) if opp is not None else []
        enemy_board = [
            self._taunt_combat_state(m, self.game_state)
            for m in def_board
            if m.current_health > 0
        ]
        total_face, lifesteal_heal, best_fs, best_board = self._find_best_taunt_clear_state(
            fighters, taunts, defender_shield, enemy_board=enemy_board,
        )

        if total_face is None:
            return 0, 0, False

        self._last_deathrattle_armor = sim_armor_gain(best_board or [])
        can_clear = not self._living_taunt_states(best_board)
        return total_face, lifesteal_heal, can_clear

    def _find_best_taunt_clear(
        self,
        fighters: List[dict],
        taunts: List[dict],
        defender_shield: bool = False,
        *,
        enemy_board: Optional[List[dict]] = None,
        rng: Optional[random.Random] = None,
    ) -> Tuple[Optional[int], int]:
        face, heal, _, _ = self._find_best_taunt_clear_state(
            fighters, taunts, defender_shield,
            enemy_board=enemy_board, rng=rng,
        )
        if face is None:
            return None, 0
        return face, heal

    def _find_best_taunt_clear_state(
        self,
        fighters: List[dict],
        taunts: List[dict],
        defender_shield: bool = False,
        *,
        enemy_board: Optional[List[dict]] = None,
        rng: Optional[random.Random] = None,
    ) -> Tuple[Optional[int], int, Optional[List[dict]], List[dict]]:
        taunts = [self._normalize_taunt_combat_state(t) for t in taunts]
        board = _clone_combat_states(enemy_board if enemy_board is not None else taunts)
        if not taunts:
            fs = _clone_combat_states(fighters)
            return self._fighters_face_damage(fs, defender_shield), 0, fs, board

        if not any(f["attacks_left"] > 0 and f["health"] > 0 for f in fighters):
            return None, 0, None, board

        best_face: Optional[int] = None
        best_heal = 0
        best_armor = 0
        best_fighters: Optional[List[dict]] = None
        best_board: List[dict] = board

        for fs_after, board_after, heal_here in self._kill_taunt_outcomes(
            fighters, taunts[0], taunts[1:],
            enemy_board=board, rng=rng,
        ):
            if self._lethal_budget_expired():
                break
            remaining = self._living_taunt_states(board_after)
            sub_face, sub_heal, sub_fighters, sub_board = self._find_best_taunt_clear_state(
                fs_after, remaining, defender_shield,
                enemy_board=board_after, rng=rng,
            )
            if sub_face is None:
                continue
            total_heal = heal_here + sub_heal
            sub_armor = sim_armor_gain(sub_board)
            if best_face is None or sub_face > best_face or (
                sub_face == best_face and (
                    total_heal < best_heal
                    or (total_heal == best_heal and sub_armor < best_armor)
                )
            ):
                best_face = sub_face
                best_heal = total_heal
                best_armor = sub_armor
                best_fighters = sub_fighters
                best_board = sub_board

        if best_face is None:
            return None, 0, None, board
        return best_face, best_heal, best_fighters, best_board

    def get_opponent_health(self) -> Tuple[int, int, int]:
        """
        获取对手血量信息

        Returns:
            (当前血量, 护甲, 总血量)
        """
        if self.game_state.opponent_player_id is None:
            return 30, 0, 30

        opp_hero = self.game_state.get_hero(self.game_state.opponent_player_id)
        if not opp_hero:
            return 30, 0, 30

        # 获取当前血量（如果还没设置，使用默认值30）
        health = opp_hero.current_health
        if health == 0 and opp_hero.health == 0:
            # HEALTH 标签还没有被应用，使用默认值
            health = 30

        armor = opp_hero.tags.get("ARMOR", 0)
        total = health + armor

        return health, armor, total

    def print_lethal_info(self):
        """打印斩杀信息"""
        total_damage, sources, has_lethal = self.calculate_lethal()
        health, armor, total_hp = self.get_opponent_health()
        lifesteal_heal = getattr(self, "_last_lifesteal_heal", 0)
        deathrattle_armor = getattr(self, "_last_deathrattle_armor", 0)
        effective_hp = self.get_opponent_effective_hp()

        # 检查对手嘲讽
        opp_board = self.game_state.get_board(self.game_state.opponent_player_id) if self.game_state.opponent_player_id else []
        opp_taunts = living_taunt_minions(opp_board, self.game_state)

        print("\n" + "=" * 60)
        if has_lethal:
            print("⚔️  斩杀！有斩杀机会！ ⚔️")
        else:
            if lifesteal_heal > 0 or deathrattle_armor > 0:
                extra = []
                if lifesteal_heal > 0:
                    extra.append(f"吸血+{lifesteal_heal}")
                if deathrattle_armor > 0:
                    extra.append(f"亡语甲+{deathrattle_armor}")
                print(
                    f"总伤害: {total_damage} / 对手有效血量: {effective_hp} "
                    f"(含{', '.join(extra)}, 还差 {effective_hp - total_damage})"
                )
            else:
                print(f"总伤害: {total_damage} / 对手血量: {total_hp} (还差 {total_hp - total_damage})")

        print("=" * 60)
        if lifesteal_heal > 0 or deathrattle_armor > 0:
            parts = [f"对手血量: {health} + 护甲: {armor}"]
            if lifesteal_heal > 0:
                parts.append(f"清嘲吸血: {lifesteal_heal}")
            if deathrattle_armor > 0:
                parts.append(f"亡语加甲: {deathrattle_armor}")
            print(f"{' + '.join(parts)} = 有效: {effective_hp}")
        else:
            print(f"对手血量: {health} + 护甲: {armor} = 总计: {total_hp}")

        # 显示嘲讽信息
        if opp_taunts:
            print(f"⚠️  对手嘲讽: {len(opp_taunts)} 个")
            for taunt in opp_taunts:
                shield = "🛡️" if taunt.tags.get("DIVINE_SHIELD", 0) else ""
                ls = "💚吸血" if self._has_lifesteal(taunt) else ""
                ps = "☠️剧毒" if self._has_poisonous(taunt) else ""
                print(
                    f"     {shield}{ls}{ps} {taunt.card_id or '随从'} "
                    f"({taunt.atk}/{taunt.current_health})"
                )

        print(f"我方总伤害: {total_damage}")
        print("\n伤害来源:")

        if sources:
            for source in sources:
                print(f"  • {source}")
        else:
            print("  无可用伤害来源")

        print("=" * 60)
