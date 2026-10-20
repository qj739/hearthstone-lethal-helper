# black_empire_p0.py — 黑帝国王朝（BE_）竞技场斩杀接入
#
# Patch 37.0 扩展 Reign of the Black Empire（套装 BE，135 可收藏）。
# 批量：法术/战吼/突袭/武器/地标；关键直伤与召唤线给精确覆盖。

from __future__ import annotations

import re
from typing import Dict, List

from .arena_season_bulk import (
    _SpellSpec,
    _load_cards,
    _card_text,
    _register_spells,
    _register_battlecries,
    _register_rush_cards,
    _register_weapons,
    _register_combos,
    _register_deathrattles,
    _register_end_turn,
    _BC_OVERRIDES,
    _SPELL_OVERRIDES,
    _log,
)
from .location_board import _register_location
from .spell_board import (
    BoardSpellDef,
    SpellApplyResult,
    _apply_all_enemies_damage,
    _apply_buff_to_spell_target,
    _apply_optimal_single_target_damage,
    _apply_random_enemy_hits,
    _apply_random_split_damage,
    _merge_spell_result,
    _register,
    _summon_friendly_fighter,
    hand_effect_active,
    scaled_spell_damage as _sd,
)
from .spell_p0_remove import _apply_optimal_destroy_enemy

_REGISTERED = False

# ── 精确覆盖（自动分类不准时）────────────────────────────────

_BE_SPELL_OVERRIDES: Dict[str, _SpellSpec] = {
    # 暗影之舞：对所有未受伤敌人 1 伤（v1 按全敌人）
    "BE_071": _SpellSpec("all_enemies", 1, note="未受伤敌人v1全敌"),
    # 星界坠雨：随机敌方随从 2 伤×5
    "BE_258": _SpellSpec("random_enemy_minion_hits", 2, amount2=5, uses_random=True),
    # 烈焰震击：两个不同敌人各 2
    "BE_302": _SpellSpec(
        "random_distinct_enemy_hits", 2, amount2=2, uses_random=True, note="两敌人各2",
    ),
    # 古言术：笞 — 随机敌人 3（下一暗影重复 v1 单次）
    "BE_223": _SpellSpec("random_enemy_hits", 3, amount2=1, uses_random=True),
    # 阳炎清算：敌方随从 AOE 1
    "BE_153": _SpellSpec("enemy_aoe", 1),
    # 起源大厅：吸血 8 点分摊
    "BE_183": _SpellSpec("random_split_enemies", 8, uses_random=True),
    # 冷暗虚空：随从 4 + 邻 2 → v1 仅主目标 4
    "BE_284": _SpellSpec("minion_direct", 4, note="邻接2伤v1仅主目标"),
    # 凶煞降临：消灭随从
    "BE_325": _SpellSpec("destroy_enemy"),
    # 力量展现：3 伤 / 有护甲则消灭 → v1 3 伤随从
    "BE_559": _SpellSpec("minion_direct", 3, note="护甲消灭v1仅3伤"),
    # 重塑之砧：英雄 +4 攻（耗护甲）
    "BE_042": _SpellSpec("hero_attack", 4, note="耗护甲v1仍+攻"),
    # 虚渺延火：3 直伤
    "BE_854": _SpellSpec("face_direct", 3),
    # 饥渴洞窟：吸血 2 直伤
    "BE_877": _SpellSpec("face_direct", 2),
    # 其余发现/过牌/拼装/延迟仪式
    "BE_005": _SpellSpec("noop", note="延迟仪式"),
    "BE_085": _SpellSpec("noop", note="延迟召唤"),
    "BE_087": _SpellSpec("noop", note="守卫+拼装"),
    "BE_094": _SpellSpec("noop", note="增益"),
    "BE_114": _SpellSpec("noop", note="拼装"),
    "BE_142": _SpellSpec("noop", note="数字=剩余法力"),
    "BE_146": _SpellSpec("noop", note="光环3回合"),
    "BE_154": _SpellSpec("noop", note="抽牌变形"),
    "BE_201": _SpellSpec("noop", note="冻结+召唤"),
    "BE_208": _SpellSpec("noop", note="抽牌增益"),
    "BE_220": _SpellSpec("noop", note="获取暗影"),
    "BE_221": _SpellSpec("noop", note="抽牌减费"),
    "BE_250": _SpellSpec("noop", note="牌库操控"),
    "BE_252": _SpellSpec("noop", note="召唤同费"),
    "BE_257": _SpellSpec("noop", note="拼装"),
    "BE_553": _SpellSpec("noop", note="拼装机械"),
    "BE_555": _SpellSpec("noop", note="发现减费"),
    "BE_571": _SpellSpec("noop", note="拼装亡语"),
    "BE_724": _SpellSpec("noop", note="幼虫"),
    "BE_726": _SpellSpec("noop", note="延迟克苏恩"),
    "BE_740": _SpellSpec("noop", note="拼装嘲讽"),
    "BE_801": _SpellSpec("noop", note="抽牌"),
    "BE_802": _SpellSpec("noop", note="植物亡语"),
    "BE_842": _SpellSpec("noop", note="冻结护甲抽牌"),
    "BE_873": _SpellSpec("noop", note="下回合召唤突袭"),
}

_BE_BC_OVERRIDES: Dict[str, _SpellSpec] = {
    # 鲜血邪魔：残骸 AOE → v1 其他随从 1
    "BE_283": _SpellSpec("all_other_minions", 1, note="残骸叠伤v1×1"),
    # 石头穴居人：对随从 6 伤
    "BE_994": _SpellSpec("minion_direct", 6),
    # 祖拉玛特的仆从：沉默
    "BE_228": _SpellSpec("noop", note="沉默"),
}

# 自定义 apply（覆盖表 kind 表达不了的）
_CUSTOM_SPELL_IDS = frozenset({
    "BE_222",  # 古言术：现 — 召唤 5/5 吸血
    "BE_265",  # 合围 — 五只 3/1 突袭
    "BE_554",  # 轰炸 — 消灭随机 + 脸 3（机械复读 v1 一次）
    "BE_730",  # 发条群猪 — 两只 1/1 冲锋
    "BE_013t1",  # 克苏恩的愤怒
    "BE_013t2",  # 克苏恩的领域
    "BE_778",  # 凌空守望：两项克苏恩技能
    "BE_086",  # 污亵：全敌 2，手牌最高费再来一次
})
_CUSTOM_BC_IDS = frozenset({
    "BE_732",  # 穿刺者克洛恩 — 友方各对随机敌人造成自身攻击
    "BE_560",  # 指虎乱斗打手 — 冲锋（护甲+4/+4 v1 仅冲锋身材）
    "BE_303",  # 灼拳智者 — 亮边才全敌 4
    "BE_171",  # 威能恐魔 — 亮边才召唤复制
    "BE_151",  # 库区守卫 — 相邻随从 +2/+2
})


def _hand_play_cost(card, gs, player_id) -> int:
    """手牌当前法力值消耗（减费后的 COST）。"""
    from .spell_board import resolve_board_spell_def, spell_effective_cost

    if gs is not None and player_id is not None and resolve_board_spell_def(
        card, gs, player_id,
    ):
        return spell_effective_cost(card, gs, player_id)
    tags = getattr(card, "tags", None) or {}
    raw = tags.get("COST")
    if raw is not None:
        try:
            return max(0, int(raw))
        except (TypeError, ValueError):
            pass
    return max(0, int(getattr(card, "cost", 0) or 0))


def _blasphemy_repeats(card, gs, player_id, spent) -> bool:
    """本牌是剩余手牌里法力值消耗最高的（并列也算）。"""
    if card is None:
        return False
    if gs is None or player_id is None or not hasattr(gs, "get_hand"):
        return hand_effect_active(card)
    mine = _hand_play_cost(card, gs, player_id)
    my_id = getattr(card, "entity_id", None)
    spent_ids = spent or set()
    for other in gs.get_hand(player_id):
        oid = getattr(other, "entity_id", None)
        if oid is not None and (oid == my_id or oid in spent_ids):
            continue
        if _hand_play_cost(other, gs, player_id) > mine:
            return False
    return True


def _apply_blasphemy(
    t, f, *, mult=1, enemy_shield=False, spell_power=0,
    card=None, gs=None, player_id=None, spent_hand_ids=None, **_kw,
) -> SpellApplyResult:
    """污亵：所有敌人 2 点；若为本牌是手牌中法力最高的，再来一次。"""
    dmg = _sd(2, mult=mult, spell_power=spell_power)
    res = _apply_all_enemies_damage(t, f, dmg, enemy_shield=enemy_shield)
    if not _blasphemy_repeats(card, gs, player_id, spent_hand_ids):
        return res
    shield = False if res.broke_enemy_hero_shield else enemy_shield
    _merge_spell_result(res, _apply_all_enemies_damage(
        t, f, dmg, enemy_shield=shield,
    ))
    return res


def _apply_elder_manifest(t, f, *, mult=1, **_kw) -> SpellApplyResult:
    for _ in range(max(int(mult), 1)):
        _summon_friendly_fighter(f, 5, 5, card_id="BE_222t", lifesteal=True)
    return SpellApplyResult()


def _apply_encircle(t, f, *, mult=1, **_kw) -> SpellApplyResult:
    n = 5 * max(int(mult), 1)
    for _ in range(n):
        _summon_friendly_fighter(f, 3, 1, card_id="BE_265t", rush=True)
    return SpellApplyResult()


def _apply_clockwork_boars(t, f, *, mult=1, **_kw) -> SpellApplyResult:
    for _ in range(2 * max(int(mult), 1)):
        _summon_friendly_fighter(f, 1, 1, card_id="BE_730t", charge=True)
    return SpellApplyResult()


def _apply_cthun_wrath(
    t, f, *, mult=1, enemy_shield=False, rng=None, **_kw,
) -> SpellApplyResult:
    """克苏恩的愤怒：7 点伤害随机分到所有敌人（含英雄）。"""
    return _apply_random_split_damage(
        t, f, 7 * max(int(mult), 1),
        enemy_shield=enemy_shield, rng=rng, include_enemy_hero=True,
    )


def _apply_cthun_domain(t, f, *, mult=1, **_kw) -> SpellApplyResult:
    """克苏恩的领域：最多两个友方随从 +2/+3（斩杀取本回合能打脸的）。"""
    bonus_atk = 2 * max(int(mult), 1)
    bonus_hp = 3 * max(int(mult), 1)
    ranked = sorted(
        (
            (i, u) for i, u in enumerate(f)
            if u.get("kind") == "minion" and int(u.get("health", 0) or 0) > 0
        ),
        key=lambda item: (
            1 if int(item[1].get("attacks_left", 0) or 0) > 0 and item[1].get("can_face", True) else 0,
            int(item[1].get("atk", 0) or 0),
        ),
        reverse=True,
    )
    for i, _u in ranked[:2]:
        _apply_buff_to_spell_target(
            f, ("fighter", i, f[i]),
            bonus_atk=bonus_atk, bonus_health=bonus_hp,
        )
    return SpellApplyResult()


def _apply_watch_over(
    t, f, *, mult=1, enemy_shield=False, rng=None, **_kw,
) -> SpellApplyResult:
    """凌空守望：斩杀线取愤怒（随机 7）+ 领域（两随从 +2/+3）。"""
    total = SpellApplyResult()
    _merge_spell_result(total, _apply_cthun_wrath(
        t, f, mult=mult, enemy_shield=enemy_shield, rng=rng,
    ))
    _merge_spell_result(total, _apply_cthun_domain(t, f, mult=mult))
    return total


def _apply_bombardment(
    t, f, *, mult=1, enemy_shield=False, spell_power=0, rng=None, **_kw,
) -> SpellApplyResult:
    _apply_optimal_destroy_enemy(t, f, mult=mult, enemy_shield=enemy_shield, **_kw)
    dmg = _sd(3, mult=mult, spell_power=spell_power)
    return _apply_optimal_single_target_damage(
        t, f, dmg, enemy_shield=enemy_shield, spell_power=0,
    )


def _ordered_friendly_minions(fighters: list) -> list:
    mins = [
        u for u in fighters
        if u.get("kind") == "minion" and int(u.get("health", 0) or 0) > 0
    ]
    if any(int(u.get("zone_pos") or 0) for u in mins):
        mins.sort(key=lambda u: int(u.get("zone_pos") or 0))
    return mins


def _neighbor_face_gain(unit, bonus_atk: int) -> int:
    if unit is None:
        return 0
    swings = int(unit.get("attacks_left", 0) or 0)
    if swings <= 0 or not unit.get("can_face", True):
        return 0
    return bonus_atk * swings


def _apply_vaultkeeper(t, f, *, mult=1, card=None, **_kw) -> SpellApplyResult:
    """库区守卫：战吼给落点两侧相邻随从 +2/+2。落点取本回合打脸收益最高的缝。"""
    bonus_atk = 2 * max(int(mult), 1)
    bonus_hp = 2 * max(int(mult), 1)
    mins = _ordered_friendly_minions(f)
    best_slot = 0
    best_key = (-1, -1)
    for slot in range(len(mins) + 1):
        left = mins[slot - 1] if slot > 0 else None
        right = mins[slot] if slot < len(mins) else None
        face = _neighbor_face_gain(left, bonus_atk) + _neighbor_face_gain(right, bonus_atk)
        neigh = int(left is not None) + int(right is not None)
        key = (face, neigh)
        if key > best_key:
            best_key = key
            best_slot = slot
    left = mins[best_slot - 1] if best_slot > 0 else None
    right = mins[best_slot] if best_slot < len(mins) else None
    for unit in (left, right):
        if unit is None:
            continue
        unit["atk"] = int(unit.get("atk", 0) or 0) + bonus_atk
        unit["health"] = int(unit.get("health", 0) or 0) + bonus_hp
    if mins and best_slot < len(mins):
        z = int(mins[best_slot].get("zone_pos") or 0)
        if z <= 0:
            z = best_slot + 1
        for unit in mins:
            zp = int(unit.get("zone_pos") or 0)
            if zp >= z:
                unit["zone_pos"] = zp + 1
    elif mins:
        z = int(mins[-1].get("zone_pos") or len(mins)) + 1
    else:
        z = 1
    before = len(f)
    _summon_bc_body(f, card, mult=mult)
    if len(f) > before:
        f[-1]["zone_pos"] = z
    return SpellApplyResult()


def _summon_bc_body(f, card, *, mult: int = 1) -> None:
    from .board_damage import hand_minion_attack, hand_minion_health

    if card is None:
        return
    atk = hand_minion_attack(card) * mult
    hp = hand_minion_health(card) * mult
    cid = card.card_id or ""
    aura = int(card.tags.get("AURA", 0) or 0) == 1
    _summon_friendly_fighter(f, atk, hp, card_id=cid, aura=aura)


def _apply_kronn(t, f, *, mult=1, card=None, enemy_shield=False, rng=None, **_kw) -> SpellApplyResult:
    """克洛恩：友方各对随机敌人造成等同于自身攻击的伤害。"""
    _summon_bc_body(f, card, mult=mult)
    res = SpellApplyResult()
    mins = [u for u in f if u.get("kind") == "minion" and int(u.get("health", 0) or 0) > 0]
    for m in mins:
        atk = int(m.get("atk", 0) or 0) * max(int(mult), 1)
        if atk <= 0:
            continue
        hit = _apply_random_enemy_hits(
            t, f, hits=1, damage=atk, enemy_shield=enemy_shield, rng=rng,
        )
        res.face_damage += int(getattr(hit, "face_damage", 0) or 0)
    return res


def _apply_brassknuckle(t, f, *, mult=1, card=None, **_kw) -> SpellApplyResult:
    """指虎乱斗打手：冲锋；护甲≥10 时 +4/+4（v1 无护甲信息时仅冲锋身材）。"""
    from .board_damage import hand_minion_attack, hand_minion_health

    if card is None:
        atk, hp = 6, 6
    else:
        atk = hand_minion_attack(card)
        hp = hand_minion_health(card)
    _summon_friendly_fighter(
        f, atk * mult, hp * mult, card_id="BE_560", charge=True,
    )
    return SpellApplyResult()


def _apply_scorchfist_scholar(
    t, f, *, mult=1, card=None, enemy_shield=False, **_kw,
) -> SpellApplyResult:
    """灼拳智者：本体上场；手牌亮边（双派系法术）才对所有敌人造成 4 点伤害。"""
    _summon_bc_body(f, card, mult=mult)
    if not hand_effect_active(card):
        return SpellApplyResult()
    return _apply_all_enemies_damage(t, f, 4 * mult, enemy_shield=enemy_shield)


def _apply_primus_of_power(
    t, f, *, mult=1, card=None, **_kw,
) -> SpellApplyResult:
    """威能恐魔：嘲讽本体上场；亮边再召唤一个复制。"""
    from .board_damage import hand_minion_attack, hand_minion_health

    if card is None:
        atk, hp = 4, 5
    else:
        atk = hand_minion_attack(card)
        hp = hand_minion_health(card)
    _summon_friendly_fighter(
        f, atk * mult, hp * mult, taunt=True, card_id="BE_171",
    )
    if not hand_effect_active(card):
        return SpellApplyResult()
    _summon_friendly_fighter(
        f, atk * mult, hp * mult, taunt=True, card_id="BE_171",
    )
    return SpellApplyResult()


def _collect_be_ids(cards: dict) -> Dict[str, List[str]]:
    cats: Dict[str, List[str]] = {
        "spell": [],
        "battlecry": [],
        "rush": [],
        "weapon": [],
        "combo": [],
        "deathrattle": [],
        "end_turn": [],
        "location": [],
    }
    for cid, c in cards.items():
        if c.get("set") != "BE" or not c.get("collectible"):
            continue
        typ = c.get("type")
        mechs = set(c.get("mechanics") or [])
        text = _card_text(c)
        if typ == "SPELL":
            cats["spell"].append(cid)
        elif typ == "WEAPON":
            cats["weapon"].append(cid)
        elif typ == "LOCATION":
            cats["location"].append(cid)
        elif typ == "MINION":
            if "COMBO" in mechs or re.search(r"<b>Combo</b>|连击", text, re.I):
                cats["combo"].append(cid)
            if "RUSH" in mechs or "CHARGE" in mechs:
                cats["rush"].append(cid)
            if "BATTLECRY" in mechs:
                cats["battlecry"].append(cid)
            if "DEATHRATTLE" in mechs:
                cats["deathrattle"].append(cid)
            if re.search(r"At the end of your turn|在你的回合结束时", text, re.I):
                cats["end_turn"].append(cid)
    return cats


def _register_custom_spells(zh: dict, cards: dict) -> None:
    specs = [
        (("BE_222",), 5, "古言术：现", _apply_elder_manifest, False),
        (("BE_265",), 6, "合围", _apply_encircle, False),
        (("BE_554",), 5, "轰炸", _apply_bombardment, True),
        (("BE_730",), 2, "发条群猪", _apply_clockwork_boars, False),
        (("BE_013t1",), 0, "克苏恩的愤怒", _apply_cthun_wrath, True),
        (("BE_013t2",), 2, "克苏恩的领域", _apply_cthun_domain, False),
        (("BE_778",), 6, "凌空守望", _apply_watch_over, True),
        (("BE_086",), 4, "污亵", _apply_blasphemy, False),
    ]
    for card_ids, cost, name, fn, uses_random in specs:
        cid = card_ids[0]
        cname = zh.get(cid) or cards.get(cid, {}).get("name") or name
        _register(BoardSpellDef(
            card_ids, cost, cname, fn, uses_random=uses_random,
        ))
        _log("法术", cid, cname, "custom")


def _register_custom_battlecries(zh: dict, cards: dict) -> None:
    from .battlecry_board import _register_bc

    specs = [
        ("BE_732", 10, "穿刺者克洛恩", _apply_kronn, True, "custom_kronn"),
        ("BE_560", 8, "指虎乱斗打手", _apply_brassknuckle, False, "charge_body"),
        ("BE_303", 5, "灼拳智者", _apply_scorchfist_scholar, False, "powered_all_enemies_4"),
        ("BE_171", 4, "威能恐魔", _apply_primus_of_power, False, "powered_summon_copy"),
        ("BE_151", 5, "库区守卫", _apply_vaultkeeper, False, "adjacent_+2/+2"),
    ]
    for cid, default_cost, default_name, fn, uses_random, impl in specs:
        cname = zh.get(cid) or cards.get(cid, {}).get("name") or default_name
        cost = int(cards.get(cid, {}).get("cost", default_cost) or default_cost)
        _register_bc(BoardSpellDef(
            (cid,), cost, cname, fn, uses_random=uses_random,
        ))
        _log("战吼", cid, cname, impl)


def _register_locations(ids: List[str], cards: dict, zh: dict) -> None:
    """地标：斩杀侧多为 noop；注册以便手牌地标可被枚举。"""

    def _noop(*_a, **_k):
        return SpellApplyResult()

    for cid in ids:
        card = cards.get(cid, {})
        cost = int(card.get("cost", 0) or 0)
        name = zh.get(cid) or card.get("name") or cid
        _register_location(BoardSpellDef((cid,), cost, name, _noop))
        _log("地标", cid, name, "noop")


def _inject_overrides() -> None:
    _SPELL_OVERRIDES.update(_BE_SPELL_OVERRIDES)
    _BC_OVERRIDES.update(_BE_BC_OVERRIDES)


def register_black_empire() -> None:
    """注册全部 BE 可收藏卡（幂等）。"""
    global _REGISTERED
    if _REGISTERED:
        return

    _inject_overrides()

    cards, zh = _load_cards()
    cats = _collect_be_ids(cards)

    # 自定义优先（避免被自动 noop/错类覆盖：_register_spells 跳过已注册）
    _register_custom_spells(zh, cards)
    _register_custom_battlecries(zh, cards)

    # 轰炸等自定义已注册；从自动列表去掉自定义 id，其余走 bulk
    spell_ids = [c for c in cats["spell"] if c not in _CUSTOM_SPELL_IDS]
    bc_ids = [c for c in cats["battlecry"] if c not in _CUSTOM_BC_IDS]

    _register_spells(spell_ids, cards, zh)
    _register_battlecries(bc_ids, cards, zh)
    _register_rush_cards(cats["rush"], cards, zh)
    _register_weapons(cats["weapon"], cards, zh)
    _register_combos(cats["combo"], cards, zh)
    _register_deathrattles(cats["deathrattle"], cards, zh)
    _register_end_turn(cats["end_turn"], cards, zh)
    _register_locations(cats["location"], cards, zh)

    _REGISTERED = True


# 模块导入即注册（须在 spell_board 初始化后）
register_black_empire()
