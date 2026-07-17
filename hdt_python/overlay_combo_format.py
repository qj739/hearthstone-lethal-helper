# overlay_combo_format.py — 斩杀步骤面板文案（法术/战吼/技能/手牌冲锋/场面攻击）

from __future__ import annotations

import re
from copy import deepcopy
from typing import List, Optional, Tuple, TYPE_CHECKING

from .board_damage import (
    collect_hand_charge_minions,
    format_hand_charge_label,
    living_taunt_minions,
    hero_has_divine_shield,
)
from .spell_board import (
    DRINK_NEXT,
    _is_battlecry_step,
    _step_card_id,
    _SyntheticSpellCard,
    drink_play_cost,
    pick_judge_unworthy_target,
)
from .weapon_board import get_weapon_def
from .location_board import get_location_def

if TYPE_CHECKING:
    from .lethal_checker import LethalChecker
    from .power_parser import Entity, GameState
    from .spell_board import BoardSpellDef


def _format_unit_label(unit: dict) -> str:
    if unit.get("kind") == "hero":
        return "敌方英雄"
    atk = int(unit.get("atk", 0) or 0)
    hp = max(0, int(unit.get("health", 0) or 0))
    tags: List[str] = []
    if unit.get("taunt"):
        tags.append("嘲讽")
    if unit.get("shield"):
        tags.append("圣盾")
    body = f"{atk}/{hp}"
    if tags:
        body += "·" + "".join(tags)
    return body


def _snapshot_enemy(units: List[dict]) -> dict:
    out = {}
    for u in units:
        if u.get("kind") == "hero":
            key = ("hero",)
            out[key] = (
                int(u.get("health", 0) or 0),
                bool(u.get("shield")),
                0,
                False,
            )
        else:
            key = ("minion", u.get("entity_id"))
            out[key] = (
                int(u.get("health", 0) or 0),
                bool(u.get("shield")),
                int(u.get("atk", 0) or 0),
                bool(u.get("taunt")),
            )
    return out


def _minions_affected(before: dict, after: List[dict]) -> bool:
    """施法前后敌方随从血量/圣盾/存活是否发生变化。"""
    for key, prev in before.items():
        if key[0] != "minion":
            continue
        prev_hp = prev[0]
        prev_sh = prev[1]
        if prev_hp <= 0:
            continue
        found_alive = False
        for unit in after:
            if ("minion", unit.get("entity_id")) != key:
                continue
            hp = int(unit.get("health", 0) or 0)
            if hp <= 0:
                return True
            found_alive = True
            if hp != prev_hp or bool(unit.get("shield")) != prev_sh:
                return True
        if not found_alive:
            return True
    return False


def _infer_target_label(
    before: dict,
    after: List[dict],
    *,
    uses_random: bool,
    direct_face: int,
) -> Optional[str]:
    if uses_random:
        return "随机"
    changed: List[dict] = []
    for u in after:
        if int(u.get("health", 0) or 0) <= 0:
            continue
        if u.get("kind") == "hero":
            key = ("hero",)
        else:
            key = ("minion", u.get("entity_id"))
        prev = before.get(key)
        if prev is None:
            continue
        prev_hp = prev[0]
        prev_sh = prev[1]
        if prev_hp != int(u.get("health", 0) or 0) or prev_sh != bool(u.get("shield")):
            changed.append(u)
    if len(changed) > 1:
        return "全体"
    if len(changed) == 1:
        return _format_unit_label(changed[0])
    for key, prev in before.items():
        if key[0] != "minion":
            continue
        prev_hp, prev_sh, prev_atk, prev_taunt = prev
        if prev_hp <= 0:
            continue
        still_alive = False
        for unit in after:
            if ("minion", unit.get("entity_id")) != key:
                continue
            if int(unit.get("health", 0) or 0) > 0:
                still_alive = True
                break
        if not still_alive:
            dead = {
                "kind": "minion",
                "atk": prev_atk,
                "health": prev_hp,
                "shield": prev_sh,
                "taunt": prev_taunt,
            }
            return _format_unit_label(dead)
    if direct_face > 0:
        if _minions_affected(before, after):
            return "全体敌人"
        return "敌方英雄"
    return None


def _step_category(defn: "BoardSpellDef", card: Optional["Entity"]) -> str:
    cid = _step_card_id(defn, card)
    if get_weapon_def(cid):
        return "武器"
    if get_location_def(cid):
        return "地标"
    if _is_battlecry_step(defn, card):
        return "战吼"
    return "法术"


def _overlay_mana_left_after_plan(checker: "LethalChecker") -> Optional[int]:
    local = checker.game_state.local_player_id
    if local is None:
        return None
    mana = getattr(checker, "_overlay_mana_budget", None)
    if mana is None:
        mana = checker._overlay_mana_for_spells(local)
    seq = getattr(checker, "_overlay_best_seq", None) or []
    hp_name = getattr(checker, "_overlay_best_hp_name", None)
    if hp_name:
        from .hero_power_board import usable_hero_power
        row = usable_hero_power(
            checker.game_state, local, mana,
            next_turn=checker._hero_power_next_turn(),
        )
        if row is not None:
            _, _, hp_cost = row
            if hp_cost <= mana:
                mana -= hp_cost
    from .lethal_checker import LethalChecker
    return LethalChecker._mana_after_spell_sequence(seq, mana)


def playable_hand_charges_for_overlay(
    checker: "LethalChecker",
) -> List[Tuple["Entity", int, int]]:
    """最优打法下、剩余法力内可打出的手牌冲锋。"""
    local = checker.game_state.local_player_id
    if local is None:
        return []
    charges = collect_hand_charge_minions(checker.game_state, local)
    if not charges:
        return []
    mana_left = _overlay_mana_left_after_plan(checker)
    played: List[Tuple["Entity", int, int]] = []
    budget = mana_left
    for entity, cost, atk in sorted(charges, key=lambda x: -x[2]):
        if budget is not None and cost > budget:
            continue
        played.append((entity, cost, atk))
        if budget is not None:
            budget -= cost
    return played


def board_has_immediate_face_attackers(checker: "LethalChecker") -> bool:
    """场上随从/武器本回合是否还能对脸造成伤害（不含手牌冲锋）。"""
    local = checker.game_state.local_player_id
    if local is None:
        return False
    opp = checker.game_state.opponent_player_id
    opp_hero = checker.game_state.get_hero(opp) if opp is not None else None
    defender_shield = hero_has_divine_shield(opp_hero)
    opp_taunts: list = []
    if opp is not None:
        opp_board = checker.game_state.get_board(opp)
        opp_taunts = living_taunt_minions(opp_board, checker.game_state)
    board_view = checker.game_state.get_overlay_board(local)
    return checker._compute_immediate_board_face(
        board_view, local, opp_taunts, defender_shield,
    ) > 0


def hand_charge_step_labels(checker: "LethalChecker") -> List[str]:
    local = checker.game_state.local_player_id
    if local is None:
        return []
    return [
        format_hand_charge_label(checker.game_state, local, entity, atk)
        for entity, _cost, atk in playable_hand_charges_for_overlay(checker)
    ]


def _fighter_display_name(unit: dict, gs: Optional["GameState"] = None) -> str:
    cid = unit.get("card_id") or ""
    eid = unit.get("entity_id")
    if gs is not None and eid is not None:
        ent = gs.entities.get(eid)
        if ent and ent.card_id:
            cid = ent.card_id
    return cid or "随从"


def overlay_open_board_face(checker: "LethalChecker") -> int:
    """无嘲讽阻挡时，当前场面随从可打脸（未模拟法术 BUFF）。"""
    local = checker.game_state.local_player_id
    if local is None:
        return 0
    board_view = checker._board_view_for_fighters(local)
    opp = checker.game_state.opponent_player_id
    opp_hero = checker.game_state.get_hero(opp) if opp is not None else None
    shield = hero_has_divine_shield(opp_hero)
    return checker._compute_immediate_board_face(board_view, local, [], shield)


def split_minion_face_bonus(
    pure: int, minion_face: int, open_face: int,
) -> Tuple[int, int]:
    """
    将「模拟法术后随从打脸 − 纯场面」拆成 (法术清场增量, BUFF增量)。
    清场 = 解开嘲讽后、不加攻时就能多打出的部分；其余视为真实 BUFF。
    """
    total = max(0, int(minion_face) - int(pure))
    if total <= 0:
        return 0, 0
    clear_cap = max(0, int(open_face) - int(pure))
    clear_bonus = min(total, clear_cap)
    buff_bonus = total - clear_bonus
    return clear_bonus, buff_bonus


def format_minion_face_bonus_paren(clear_bonus: int, buff_bonus: int) -> str:
    """浮层/步骤括号后缀，如 (法术清场+2,含BUFF+3)。"""
    parts: List[str] = []
    if clear_bonus > 0:
        parts.append(f"法术清场+{clear_bonus}")
    if buff_bonus > 0:
        parts.append(f"含BUFF+{buff_bonus}")
    if not parts:
        return ""
    return "(" + ",".join(parts) + ")"


def overlay_minion_face_bonus_paren(checker: "LethalChecker") -> str:
    """按当前 Overlay 分项生成场面打脸增量标注。"""
    pure, minion_bd, _, _, _ = checker.overlay_board_breakdown()
    hand_charge = checker.overlay_hand_charge_face()
    # 场面分项已含手牌冲锋；标 BUFF/清场前先扣掉，冲锋由独立步骤列出
    display_minion = max(0, minion_bd - hand_charge)
    clear_bonus, buff_bonus = split_minion_face_bonus(
        pure, display_minion, overlay_open_board_face(checker),
    )
    return format_minion_face_bonus_paren(clear_bonus, buff_bonus)


def _board_face_step_label(checker: "LethalChecker", minion_face: int) -> str:
    """场面随从打脸：清场增量标「法术清场」，真 BUFF 标「含BUFF」（不含手牌冲锋）。"""
    if minion_face <= 0:
        return "场面随从打脸"
    suffix = overlay_minion_face_bonus_paren(checker)
    if suffix:
        return f"场面随从打脸{suffix}"
    return "场面随从打脸"


def _board_attack_step_labels(checker: "LethalChecker") -> List[str]:
    """区分随从打脸与英雄武器（避免仅剩武器可攻时误标为场面随从）。"""
    local = checker.game_state.local_player_id
    if local is None or not board_has_immediate_face_attackers(checker):
        return []
    from .board_damage import build_player_board

    bv = build_player_board(checker.game_state, local, active_turn=True)
    minion_face = bv.minion_damage
    hero_face = bv.hero_damage
    steps: List[str] = []
    if minion_face > 0:
        steps.append(_board_face_step_label(checker, minion_face))
    if hero_face > 0:
        steps.append("英雄武器打脸")
    return steps


def overlay_combo_mana_affordable(checker: "LethalChecker") -> bool:
    """斩杀步骤里列出的法术/技能/饮品连喝/冲锋在当前法力下是否都能支付。"""
    local = checker.game_state.local_player_id
    if local is None:
        return True
    mana = checker._available_mana(local)
    hp_name = getattr(checker, "_overlay_best_hp_name", None)
    if hp_name:
        from .hero_power_board import usable_hero_power

        row = usable_hero_power(
            checker.game_state, local, mana,
            next_turn=checker._hero_power_next_turn(),
        )
        if row is None:
            return False
        _, _, hp_cost = row
        if hp_cost > mana:
            return False
        mana -= hp_cost
    from .spell_board import spell_sequence_mana_left

    seq = getattr(checker, "_overlay_best_seq", None) or []
    mana_left = spell_sequence_mana_left(seq, mana)
    if mana_left is None:
        return True
    for _entity, cost, _atk in playable_hand_charges_for_overlay(checker):
        if cost > mana_left:
            return False
        mana_left -= cost
    return True


def attack_phase_step_labels(
    checker: "LethalChecker",
    *,
    include_board: bool = True,
    include_hand_charges: bool = True,
) -> List[str]:
    """合并手牌冲锋与场面攻击步骤（手牌冲锋在前）。"""
    steps: List[str] = []
    if include_hand_charges:
        steps.extend(hand_charge_step_labels(checker))
    if include_board:
        steps.extend(_board_attack_step_labels(checker))
    return steps


def _has_numbered_steps(lines: List[str]) -> bool:
    return any(re.match(r"^\d+\.\s", ln.strip()) for ln in lines)


def build_quick_sources_combo_lines(sources) -> List[str]:
    """快速斩杀路径的伤害来源 → 步骤文案（overlay 模拟未完成时的回退）。"""
    if not sources:
        return []
    lines = ["⚔ 斩杀步骤"]
    for i, src in enumerate(sources, 1):
        desc = getattr(src, "description", None) or str(src)
        lines.append(f"{i}. {desc}")
    return lines


def _spell_step_play_cost(defn: "BoardSpellDef", card, step_cost: int) -> int:
    cid = _step_card_id(defn, card) or (defn.card_ids[0] if defn.card_ids else "")
    return drink_play_cost(cid, step_cost)


def _append_spell_steps_with_drinks(
    steps: List[str],
    defn: "BoardSpellDef",
    card,
    step_cost: int,
    *,
    enemy_work: List[dict],
    fs_work: List[dict],
    spell_mult: int,
    enemy_shield: bool,
    checker: "LethalChecker",
    local: int,
    mana_work: Optional[int],
) -> Optional[int]:
    """模拟并记录法术步骤（含饮品连喝），返回更新后的剩余法力。"""
    cat = _step_category(defn, card)
    current_card = card
    play_cost = _spell_step_play_cost(defn, current_card, step_cost)
    if mana_work is not None and play_cost > mana_work:
        return mana_work

    cid = _step_card_id(defn, current_card) or (defn.card_ids[0] if defn.card_ids else "")

    while True:
        before = _snapshot_enemy(enemy_work)
        judge_target_label = None
        if cid == "TTN_853":
            picked = pick_judge_unworthy_target(enemy_work)
            if picked is not None:
                key = ("minion", picked.get("entity_id"))
                prev = before.get(key)
                if prev:
                    judge_target_label = _format_unit_label({
                        "kind": "minion",
                        "entity_id": picked.get("entity_id"),
                        "atk": prev[2],
                        "health": prev[0],
                        "shield": prev[1],
                        "taunt": prev[3] if len(prev) > 3 else picked.get("taunt", False),
                    })
                else:
                    judge_target_label = _format_unit_label(picked)
        res = defn.apply(
            enemy_work, fs_work, mult=spell_mult, enemy_shield=enemy_shield,
            gs=checker.game_state, player_id=local, card=current_card,
        )
        cup_cost = drink_play_cost(
            _step_card_id(defn, current_card) or cid, step_cost,
        )
        target = judge_target_label or _infer_target_label(
            before, enemy_work,
            uses_random=bool(defn.uses_random),
            direct_face=int(res.direct_face_damage or 0),
        )
        if cat == "武器":
            step = f"武器 {defn.name}"
        elif cat == "地标":
            step = f"地标 {defn.name}"
        elif cat == "战吼":
            step = f"战吼 {defn.name}"
        elif target:
            step = f"{defn.name} → {target}"
        else:
            step = f"{defn.name}"
        steps.append(step)
        if mana_work is not None:
            mana_work -= cup_cost

        if res.drinks_after <= 0:
            break
        next_cid = DRINK_NEXT.get(_step_card_id(defn, current_card) or cid)
        if not next_cid:
            break
        next_cost = drink_play_cost(next_cid, step_cost)
        if mana_work is not None and next_cost > mana_work:
            break
        current_card = _SyntheticSpellCard(next_cid, next_cost)
        cid = next_cid
    return mana_work


def build_combo_lines_for_display(checker: "LethalChecker") -> List[str]:
    """优先 overlay 模拟步骤；无具体步骤时回退快速斩杀来源或法术备注。"""
    lines = build_lethal_combo_lines(checker)
    if _has_numbered_steps(lines):
        return lines
    quick = getattr(checker, "_last_quick_lethal_sources", None) or []
    if quick:
        quick_lines = build_quick_sources_combo_lines(quick)
        if _has_numbered_steps(quick_lines):
            return quick_lines
    note = (checker.overlay_spell_note() or "").strip()
    if note and note not in ("计算超时",):
        return ["⚔ 斩杀步骤", f"1. {note}"]
    return lines


def build_lethal_combo_lines(checker: "LethalChecker") -> List[str]:
    """生成斩杀步骤行（技能/法术/战吼/武器 + 手牌冲锋 + 场面攻击）。"""
    seq = getattr(checker, "_overlay_best_seq", None) or []
    hp_name = getattr(checker, "_overlay_best_hp_name", None)
    order = getattr(checker, "_overlay_best_order", "spell_first") or "spell_first"

    local = checker.game_state.local_player_id
    if local is None:
        return []

    if not seq and not hp_name:
        attack_steps = attack_phase_step_labels(checker)
        et_face = checker.overlay_end_turn_face_for_display()
        if et_face > 0:
            names = []
            local_board = checker.game_state.get_board(local)
            if local_board:
                from .end_turn_board import end_turn_names_on_board

                names = end_turn_names_on_board(local_board)
            et_label = names[0] if len(names) == 1 else "回合结束触发"
            attack_steps = list(attack_steps) + [f"{et_label}打脸+{et_face}"]
        if attack_steps:
            lines = ["⚔ 斩杀步骤"]
            for i, step in enumerate(attack_steps, 1):
                lines.append(f"{i}. {step}")
            return lines
        return ["⚔ 斩杀步骤", "1. 场面随从打脸"]

    opp = checker.game_state.opponent_player_id
    opp_hero = checker.game_state.get_hero(opp) if opp else None
    enemy_shield = bool(opp_hero and opp_hero.tags.get("DIVINE_SHIELD", 0) == 1)

    board_view = checker.game_state.get_overlay_board(local)
    fighters = checker._build_fighters(board_view, local)
    enemy = checker._build_enemy_minion_states(local)
    from .spell_board import spell_effect_multiplier
    spell_mult = spell_effect_multiplier(checker.game_state, local)
    mana_work: Optional[int] = checker._overlay_mana_for_spells(local)

    lines: List[str] = ["⚔ 斩杀步骤"]
    if order == "attack_interleaved":
        from .interleave_board import interleave_note_suffix
        suffix = interleave_note_suffix(seq, order).strip()
        lines.append(f"（{suffix or '战吼穿插'}）")
    elif order == "attack_first":
        lines.append("（先攻后法）")

    steps: List[str] = []
    if order == "attack_first" and seq and _board_attack_step_labels(checker):
        steps.extend(_board_attack_step_labels(checker))

    if hp_name:
        from .hero_power_board import apply_hero_power_to_fighters
        fs_hp = deepcopy(fighters)
        ok, mana_left, _hp_res = apply_hero_power_to_fighters(
            checker.game_state, local, fs_hp, mana_work,
            enemy_shield=enemy_shield,
            taunts=enemy,
        )
        if ok:
            fighters = fs_hp
            mana_work = mana_left
            steps.append(f"技能 {hp_name}")

    enemy_work = deepcopy(enemy)
    fs_work = deepcopy(fighters)

    for defn, cost, card in seq:
        play_cost = _spell_step_play_cost(defn, card, cost)
        if mana_work is not None and play_cost > mana_work:
            continue
        if "CATA_138" in (defn.card_ids or ()):
            from .spell_board import (
                _friendly_minion_count,
                _pick_best_spell_target_fighter,
            )

            gift_count = _friendly_minion_count(
                fs_work, gs=checker.game_state, player_id=local,
            )
            picked = _pick_best_spell_target_fighter(
                fs_work, gs=checker.game_state, player_id=local,
            )
            res = defn.apply(
                enemy_work, fs_work, mult=spell_mult, enemy_shield=enemy_shield,
                gs=checker.game_state, player_id=local, card=card,
            )
            if picked is None or gift_count <= 0:
                step = f"{defn.name}（无合法目标）"
            else:
                _, _, unit = picked
                name = _fighter_display_name(unit, checker.game_state)
                step = f"{defn.name} → {name}(+{gift_count}/+{gift_count})"
            steps.append(step)
            if mana_work is not None:
                mana_work -= play_cost
            continue
        mana_work = _append_spell_steps_with_drinks(
            steps, defn, card, cost,
            enemy_work=enemy_work,
            fs_work=fs_work,
            spell_mult=spell_mult,
            enemy_shield=enemy_shield,
            checker=checker,
            local=local,
            mana_work=mana_work,
        )

    if order == "attack_first":
        steps.extend(hand_charge_step_labels(checker))
    else:
        steps.extend(
            attack_phase_step_labels(
                checker,
                include_board=True,
                include_hand_charges=True,
            )
        )

    for i, step in enumerate(steps, 1):
        lines.append(f"{i}. {step}")

    return lines
