# eudora_loot.py — 尤朵拉神奇战利品（场攻优先子集）

from __future__ import annotations

import random
from typing import List, Optional, TYPE_CHECKING

from .spell_board import (
    BoardSpellDef,
    SpellApplyResult,
    _apply_all_enemies_damage,
    _apply_damage,
    _apply_damage_to_unit,
    _apply_direct_face,
    _apply_random_enemy_hits,
    _register,
    _remove_dead_taunts,
    _summon_friendly_fighter,
)

if TYPE_CHECKING:
    from .power_parser import GameState

MC_DEFAULT_SEED = 0

# 尤朵拉战利品 + 奥特兰克宝藏等同名 card_id
ICY_TOUCH_IDS = ("VAC_464t5", "ONY_005ta4", "PVPDR_SCH_Active61", "NAX14_04")
EMBERS_OF_RAGNAROS_IDS = ("VAC_464t23", "ONY_005tc1", "PVPDR_SCH_Active55", "LOOTA_827")
BOOK_OF_THE_DEAD_IDS = ("VAC_464t24", "ONY_005tc2", "PVPDR_SCH_Active54")
QUELDELAR_IDS = ("VAC_464t31", "ONY_005tc7", "PVPDR_SCH_Active25", "LOOTA_842")
SUPER_ENERGY_GUN_IDS = ("VAC_464t14", "ONY_005tb1", "PVPDR_SCH_Active51", "DALA_723")
BUBBA_IDS = ("VAC_464t6", "ONY_005ta5", "PVPDR_SCH_Active47", "GILA_410")
SERPENT_STAFF_IDS = ("VAC_464t17", "ONY_005tb5", "ULDA_008")
BOOMBOX_IDS = ("VAC_464t21", "ONY_005tb12", "LOOTA_838")
BEAUTY_BEAST_IDS = ("VAC_464t27", "ONY_005ta9", "PVPDR_SCH_Active29", "GILA_854")
MUTAGENIC_INJECTION_IDS = ("VAC_464t3", "ONY_005ta2", "NAX11_04")
GNOMISH_ARMY_KNIFE_IDS = ("VAC_464t15", "ONY_005tb2", "DALA_702")

EUDORA_LOOT_IDS = frozenset({
    "VAC_464t5", "VAC_464t23", "VAC_464t24", "VAC_464t31", "VAC_464t14",
    "VAC_464t6", "VAC_464t17", "VAC_464t21", "VAC_464t27", "VAC_464t3", "VAC_464t15",
})

TREASURE_LOOT_ALIAS_IDS = frozenset(
    ICY_TOUCH_IDS + EMBERS_OF_RAGNAROS_IDS + BOOK_OF_THE_DEAD_IDS
    + QUELDELAR_IDS + SUPER_ENERGY_GUN_IDS + BUBBA_IDS + SERPENT_STAFF_IDS
    + BOOMBOX_IDS + BEAUTY_BEAST_IDS + MUTAGENIC_INJECTION_IDS + GNOMISH_ARMY_KNIFE_IDS
)


def _rng(rng: Optional[random.Random]) -> random.Random:
    return rng if rng is not None else random.Random(MC_DEFAULT_SEED)


def game_minions_died(gs: Optional["GameState"]) -> int:
    """本局随从死亡数（亡者之书减费）。"""
    if gs is None:
        return 0
    eid = gs.game_entity_id
    if eid is not None:
        ent = gs.get_entity(eid)
        if ent:
            for key in ("NUM_MINIONS_KILLED_THIS_GAME", "825"):
                v = ent.tags.get(key)
                if v is not None:
                    return max(0, int(v))
    total = 0
    for pid in (gs.local_player_id, gs.opponent_player_id):
        if pid is None:
            continue
        hero = gs.get_hero(pid)
        if hero:
            v = hero.tags.get("NUM_MINIONS_PLAYER_KILLED_THIS_GAME")
            if v is not None:
                total += max(0, int(v))
    return total


def _book_of_the_dead_cost(gs: "GameState", player_id: int) -> int:
    return max(0, 14 - game_minions_died(gs))


def strip_weapon_fighters(fighters: List[dict]) -> int:
    """移除模拟中的武器攻击者，返回被替换武器剩余的英雄攻击次数。"""
    remaining = 0
    kept: List[dict] = []
    for f in fighters:
        if f.get("kind") == "weapon":
            remaining = max(remaining, int(f.get("attacks_left", 0) or 0))
        else:
            kept.append(f)
    fighters[:] = kept
    return remaining


def _add_temp_weapon(
    fighters: List[dict],
    atk: int,
    durability: int,
    *,
    poisonous: bool = False,
    hero_immune_on_attack: bool = False,
    hero_aoe_on_attack: int = 0,
    card_id: str = "",
    attacks_left: Optional[int] = None,
) -> None:
    fighters.append({
        "kind": "weapon",
        "card_id": card_id,
        "atk": max(atk, 0),
        "health": 10**9,
        "attacks_left": 1 if attacks_left is None else max(attacks_left, 0),
        "durability": max(durability, 1),
        "can_face": True,
        "poisonous": poisonous,
        "hero_immune_on_attack": hero_immune_on_attack,
        "hero_aoe_on_attack": hero_aoe_on_attack,
    })


def apply_hero_aoe_after_attack(
    enemy_board: List[dict],
    fighters: List[dict],
    damage: int,
    *,
    enemy_shield: bool = False,
) -> int:
    """奎尔德拉：英雄攻击后对所有敌人造成伤害（随从 + 英雄直伤）。"""
    if damage <= 0:
        return 0
    res = _apply_all_enemies_damage(
        enemy_board, fighters, damage, enemy_shield=enemy_shield,
    )
    return res.opponent_lifesteal_heal


def _best_friendly_minion_index(fighters: List[dict]) -> Optional[int]:
    best_i: Optional[int] = None
    best_score = -1
    for i, f in enumerate(fighters):
        if f.get("kind") != "minion" or f.get("health", 0) <= 0:
            continue
        score = f.get("atk", 0) * max(f.get("attacks_left", 0), 1)
        if score > best_score:
            best_score = score
            best_i = i
    return best_i


def _buff_friendly_minion(
    fighters: List[dict],
    *,
    atk_bonus: int = 0,
    hp_bonus: int = 0,
    taunt: bool = False,
    full_keywords: bool = False,
) -> None:
    idx = _best_friendly_minion_index(fighters)
    if idx is None:
        return
    f = fighters[idx]
    f["atk"] = f.get("atk", 0) + atk_bonus
    f["health"] = f.get("health", 0) + hp_bonus
    if taunt:
        f["taunt"] = True
    if full_keywords:
        f["rush"] = True
        f["windfury"] = True
        f["shield"] = True
        f["lifesteal"] = True
        f["poisonous"] = True
        f["taunt"] = True
        if f.get("attacks_left", 0) <= 0:
            f["attacks_left"] = 1
        if f.get("rush"):
            f["can_face"] = False


def _apply_icy_touch(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    """极寒之击：8 直伤（冻结 v1 不计入场攻）。"""
    return _apply_direct_face(8 * mult, enemy_shield)


def _apply_embers_of_ragnaros(
    taunts, fighters, *, mult, enemy_shield, rng=None, **_kw,
) -> SpellApplyResult:
    """拉格纳罗斯的余烬：随机 3 个火球各 8 伤。"""
    return _apply_random_enemy_hits(
        taunts, fighters, hits=3, damage=8 * mult,
        enemy_shield=enemy_shield, rng=_rng(rng),
    )


def _apply_book_of_the_dead(
    taunts, fighters, *, mult, enemy_shield, **_kw,
) -> SpellApplyResult:
    """亡者之书：对所有敌人 7 伤。"""
    return _apply_all_enemies_damage(
        taunts, fighters, 7 * mult, enemy_shield=enemy_shield,
    )


def _apply_queldelar(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    _add_temp_weapon(
        fighters, 6, 3, hero_aoe_on_attack=4 * mult, card_id="VAC_464t31",
    )
    return SpellApplyResult()


def _apply_super_energy_gun(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    _add_temp_weapon(
        fighters, 1, 4, poisonous=True, hero_immune_on_attack=True, card_id="VAC_464t14",
    )
    return SpellApplyResult()


def _hound_attack_enemy_minions(
    taunts: List[dict],
    fighters: List[dict],
    *,
    count: int,
    enemy_shield: bool,
) -> SpellApplyResult:
    """布巴猎犬：每条 1 伤攻击一个敌方随从（优先嘲讽）。"""
    res = SpellApplyResult()
    for _ in range(count):
        targets = [
            t for t in taunts
            if t.get("health", 0) > 0 and t.get("kind") != "hero"
        ]
        if not targets:
            break
        taunt_targets = [t for t in targets if t.get("taunt")]
        target = taunt_targets[0] if taunt_targets else targets[0]
        heal, face, _ = _apply_damage_to_unit(
            target, 1, taunts=taunts, fighters=fighters, enemy_shield=enemy_shield,
        )
        res.opponent_lifesteal_heal += heal
        res.direct_face_damage += face
    _remove_dead_taunts(taunts)
    return res


def _apply_bubba(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    """布巴：6 条 1/1 突袭猎犬攻击敌方随从。"""
    res = _hound_attack_enemy_minions(
        taunts, fighters, count=6 * mult, enemy_shield=enemy_shield,
    )
    for _ in range(6 * mult):
        _summon_friendly_fighter(
            fighters, 1, 1, rush=True, card_id="VAC_464t6",
        )
        fighters[-1]["attacks_left"] = 0
    return res


def _apply_serpent_staff(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    """异鳞之杖：三条 1/1 突袭剧毒复生蛇。"""
    for _ in range(3 * mult):
        _summon_friendly_fighter(
            fighters, 1, 1, rush=True, poisonous=True, card_id="VAC_464t17",
        )
    return SpellApplyResult()


def _apply_boombox(
    taunts, fighters, *, mult, enemy_shield, rng=None, **_kw,
) -> SpellApplyResult:
    """砰砰箱：7 次随机 1–4 伤。"""
    res = SpellApplyResult()
    roll = _rng(rng)
    for _ in range(7 * mult):
        dmg = roll.randint(1, 4)
        part = _apply_random_enemy_hits(
            taunts, fighters, hits=1, damage=dmg,
            enemy_shield=enemy_shield, rng=roll,
        )
        res.opponent_lifesteal_heal += part.opponent_lifesteal_heal
        res.direct_face_damage += part.direct_face_damage
    return res


def _apply_beauty_beast(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    """野兽美女：0/3 突袭；攻击随从并存活后变 8/8。"""
    res = SpellApplyResult()
    for _ in range(mult):
        _summon_friendly_fighter(
            fighters, 0, 3, rush=True, card_id="VAC_464t27",
        )
        f = fighters[-1]
        best_i: Optional[int] = None
        best_atk = 10**9
        for i, t in enumerate(taunts):
            if t.get("health", 0) <= 0 or t.get("kind") == "hero":
                continue
            atk = t.get("atk", 0)
            if atk < f.get("health", 0) and atk < best_atk:
                best_atk = atk
                best_i = i
        if best_i is None:
            continue
        t = taunts[best_i]
        taken = t.get("atk", 0)
        f["health"] -= taken
        if f.get("health", 0) > 0:
            f["atk"] = 8
            f["health"] = 8
            f["card_id"] = "VAC_464t27t"
            f["attacks_left"] = 0
    return res


def _apply_mutagenic_injection(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    for _ in range(mult):
        _buff_friendly_minion(fighters, atk_bonus=4, hp_bonus=4, taunt=True)
    return SpellApplyResult()


def _apply_gnomish_army_knife(taunts, fighters, *, mult, enemy_shield, **_kw) -> SpellApplyResult:
    for _ in range(mult):
        _buff_friendly_minion(fighters, full_keywords=True)
    return SpellApplyResult()


def _register_eudora_loot() -> None:
    specs = [
        (ICY_TOUCH_IDS, 5, "极寒之击", _apply_icy_touch, False, None),
        (EMBERS_OF_RAGNAROS_IDS, 10, "拉格纳罗斯的余烬", _apply_embers_of_ragnaros, True, None),
        (BOOK_OF_THE_DEAD_IDS, 14, "亡者之书", _apply_book_of_the_dead, False, _book_of_the_dead_cost),
        (QUELDELAR_IDS, 6, "奎尔德拉", _apply_queldelar, False, None),
        (SUPER_ENERGY_GUN_IDS, 3, "超级能量枪", _apply_super_energy_gun, False, None),
        (BUBBA_IDS, 5, "布巴", _apply_bubba, False, None),
        (SERPENT_STAFF_IDS, 5, "异鳞之杖", _apply_serpent_staff, False, None),
        (BOOMBOX_IDS, 4, "砰砰博士的砰砰箱", _apply_boombox, True, None),
        (BEAUTY_BEAST_IDS, 3, "野兽美女", _apply_beauty_beast, False, None),
        (MUTAGENIC_INJECTION_IDS, 2, "变异注射", _apply_mutagenic_injection, False, None),
        (GNOMISH_ARMY_KNIFE_IDS, 5, "侏儒军刀", _apply_gnomish_army_knife, False, None),
    ]
    for card_ids, cost, name, fn, uses_random, cost_fn in specs:
        _register(BoardSpellDef(
            card_ids=card_ids,
            base_cost=cost,
            name=name,
            apply=fn,
            cost_fn=cost_fn,
            uses_random=uses_random,
        ))


_register_eudora_loot()
