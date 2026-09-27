# hero_power_board.py — 英雄技能接入场攻/斩杀模拟

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .board_damage import hand_minion_cost
from .spell_board import BoardSpellDef, SpellApplyResult

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

BOARD_HERO_POWER: Dict[str, BoardSpellDef] = {}

_DH_CLAWS_PLUS_TWO = re.compile(r"^HERO_10\w*(?:hp2|bp2)$")
_DH_CLAWS_PLUS_ONE = re.compile(r"^HERO_10\w*(?:hp|bp)$")
_DH_CLAWS_EXTRA = frozenset({"VAN_HERO_10bp", "VAN_HERO_10bp2"})
_MAGE_FIREBLAST = re.compile(r"^HERO_08\w*(?:hp|bp)$")
_DRUID_SHAPESHIFT = re.compile(r"^HERO_06\w*(?:hp2?|bp2?)$")
_HUNTER_STEADY = re.compile(r"^HERO_05\w*(?:hp|bp)$")
_ROGUE_DAGGER_2 = re.compile(r"^HERO_03\w*(?:hp2|bp2)$")
_ROGUE_DAGGER_1 = re.compile(r"^HERO_03\w*(?:hp|bp)$")
_DK_GHOUL_CHARGE_1 = re.compile(r"^HERO_11\w*(?:hp|bp)$")
_DK_GHOUL_CHARGE_2 = re.compile(r"^HERO_11\w*(?:hp2|bp2)$")
_MAGE_EXTRA = frozenset({"VAN_HERO_08bp"})
_DRUID_EXTRA = frozenset({"VAN_HERO_06bp"})
_HUNTER_EXTRA = frozenset({"VAN_HERO_05bp"})
_ROGUE_EXTRA_1 = frozenset({"VAN_HERO_03bp"})
_ROGUE_EXTRA_2 = frozenset({"VAN_HERO_03bp2"})
_DK_GHOUL_EXTRA_1 = frozenset({"TUTR_HERO_11bp"})
DK_GHOUL_TOKEN_IDS = frozenset({"HERO_11bpt"})
# 英雄卡 → 技能卡：日志里旧技能已离场、新技能实体尚未 ZONE=PLAY 时的推断
_HERO_TO_POWER_CARD = {"CATA_190h": "CATA_190p"}
# SETASIDE：灌注切换后旧技能（如匕首精通）会留在此区，不可再当作可用技能
_DEAD_HP_ZONES = frozenset({"GRAVEYARD", "REMOVEDFROMGAME", "SETASIDE"})


def is_dk_ghoul_board_token(card_id: str) -> bool:
    """死亡骑士技能衍生物（脆弱的食尸鬼等）。"""
    return bool(card_id) and card_id in DK_GHOUL_TOKEN_IDS


def _register_hero_power(defn: BoardSpellDef) -> None:
    for cid in defn.card_ids:
        BOARD_HERO_POWER[cid] = defn


def hero_power_should_inline_in_sequence(defn: BoardSpellDef) -> bool:
    """点伤类英雄技能应插入法术序列（可先换血/解嘲再点），不要只在序列前结算。"""
    name = defn.name or ""
    if name in ("跃动的南瓜", "火焰冲击", "稳固射击", "虚空之刺"):
        return True
    cids = set(defn.card_ids or ())
    if cids & {"TOY_829hp", "TOY_829hp3"}:
        return True
    if any(str(c).startswith("__mage_fireblast") for c in cids):
        return True
    return False


def dk_ghoul_charge_stats(card_id: str) -> Optional[Tuple[int, int]]:
    """死亡骑士食尸鬼冲锋：召唤冲锋食尸鬼 (攻, 血)。"""
    if not card_id:
        return None
    if card_id in _DK_GHOUL_EXTRA_1 or _DK_GHOUL_CHARGE_1.match(card_id):
        return 1, 1
    if _DK_GHOUL_CHARGE_2.match(card_id):
        return 2, 1
    return None


def dh_claws_attack_bonus(card_id: str) -> Optional[int]:
    """恶魔猎手恶魔之爪 / 恶魔之咬：本回合 +N 攻（仅英雄/嘲讽攻击由 temp hero fighter 承担）。"""
    if not card_id:
        return None
    if card_id in _DH_CLAWS_EXTRA:
        return 2 if card_id.endswith("2") else 1
    if _DH_CLAWS_PLUS_TWO.match(card_id):
        return 2
    if _DH_CLAWS_PLUS_ONE.match(card_id):
        return 1
    return None


def _hero_power_synthetic_key(card_id: str) -> Optional[str]:
    if not card_id:
        return None
    bonus = dh_claws_attack_bonus(card_id)
    if bonus is not None:
        return f"__dh_claws_{bonus}"
    if card_id in _MAGE_EXTRA or _MAGE_FIREBLAST.match(card_id):
        return "__mage_fireblast_1"
    if card_id in _DRUID_EXTRA or _DRUID_SHAPESHIFT.match(card_id):
        return "__druid_shapeshift_1"
    if card_id in _HUNTER_EXTRA or _HUNTER_STEADY.match(card_id):
        return "__hunter_steady_2"
    if card_id in _ROGUE_EXTRA_2 or _ROGUE_DAGGER_2.match(card_id):
        return "__rogue_dagger_2_2"
    if card_id in _ROGUE_EXTRA_1 or _ROGUE_DAGGER_1.match(card_id):
        return "__rogue_dagger_1_2"
    ghoul = dk_ghoul_charge_stats(card_id)
    if ghoul is not None:
        atk, hp = ghoul
        return f"__dk_ghoul_{atk}_{hp}"
    return None


def get_hero_power_def(card_id: str) -> Optional[BoardSpellDef]:
    if not card_id:
        return None
    if card_id in BOARD_HERO_POWER:
        return BOARD_HERO_POWER[card_id]
    key = _hero_power_synthetic_key(card_id)
    if key is None:
        return None
    return BOARD_HERO_POWER.get(key)


def hero_power_cost(
    entity: "Entity",
    gs: Optional["GameState"] = None,
    player_id: Optional[int] = None,
    *,
    corpses_budget: Optional[int] = None,
) -> int:
    """英雄技能法力费用。CORPSE_SPENDER 时不占法力（残骸不够返回 999）。"""
    raw = int(entity.cost) if entity.cost and entity.cost > 0 else int(entity.tags.get("COST", 0) or 0)
    if int(entity.tags.get("CORPSE_SPENDER", 0) or 0) == 1:
        need = raw if raw > 0 else int(entity.tags.get("COST", 0) or 0)
        if need > 0:
            if corpses_budget is not None:
                if corpses_budget < need:
                    return 999
            elif gs is not None and player_id is not None:
                from .spell_board import player_corpses
                if player_corpses(gs, player_id) < need:
                    return 999
        return 0
    return raw


def hero_power_corpse_cost(entity: "Entity") -> int:
    """残骸费用（非残骸技能为 0）。"""
    if int(entity.tags.get("CORPSE_SPENDER", 0) or 0) != 1:
        return 0
    raw = int(entity.cost) if entity.cost and entity.cost > 0 else int(entity.tags.get("COST", 0) or 0)
    return max(0, raw)


def hero_power_is_ready(entity: "Entity", *, next_turn: bool = False) -> bool:
    """技能是否可用；next_turn=True 时按「下回合开始」视为已刷新（Overlay 对方回合用）。"""
    if next_turn:
        return True
    return int(entity.tags.get("EXHAUSTED", 0) or 0) != 1


def _player_hero_power_entities(
    gs: "GameState", player_id: int,
) -> Tuple[List["Entity"], List["Entity"]]:
    """返回 (PLAY 区技能, 尚未进 PLAY 但已识别的技能实体)。"""
    in_play: List["Entity"] = []
    pending: List["Entity"] = []
    for e in list(gs.entities.values()):
        if e.cardtype != "HERO_POWER":
            continue
        if not gs.is_entity_controlled_by(e, player_id):
            continue
        zone = e.zone or ""
        if zone == "PLAY":
            in_play.append(e)
        elif zone not in _DEAD_HP_ZONES and get_hero_power_def(e.card_id or ""):
            pending.append(e)
    return in_play, pending


def get_active_hero_power(gs: "GameState", player_id: int) -> Optional["Entity"]:
    """当前英雄技能实体（双职业 = PLAY 区副职业技能）。"""
    in_play, pending = _player_hero_power_entities(gs, player_id)
    for group in (in_play, pending):
        for e in group:
            if get_hero_power_def(e.card_id or ""):
                return e
        if group:
            return group[0]
    return None


def list_usable_hero_powers(
    gs: "GameState",
    player_id: int,
    available_mana: int,
    *,
    next_turn: bool = False,
    corpses_budget: Optional[int] = None,
) -> List[Tuple["Entity", BoardSpellDef, int, int]]:
    """所有可用英雄技能：(实体, 定义, 法力费, 残骸费)。残骸技能优先。"""
    from .spell_board import player_corpses

    corpses_left = (
        corpses_budget
        if corpses_budget is not None
        else player_corpses(gs, player_id)
    )
    rows: List[Tuple["Entity", BoardSpellDef, int, int]] = []
    in_play, pending = _player_hero_power_entities(gs, player_id)
    # PLAY 区已有技能时只用 PLAY：灌注后旧匕首等会留在 SETASIDE，勿回退使用
    pool = list(in_play) if in_play else list(pending)
    for e in pool:
        if not hero_power_is_ready(e, next_turn=next_turn):
            continue
        defn = get_hero_power_def(e.card_id or "")
        if defn is None:
            continue
        corpse_need = hero_power_corpse_cost(e)
        mana_need = hero_power_cost(
            e, gs, player_id, corpses_budget=corpses_left,
        )
        if mana_need >= 999:
            continue
        if mana_need > available_mana:
            continue
        if corpse_need > corpses_left:
            continue
        rows.append((e, defn, mana_need, corpse_need))
    rows.sort(key=lambda r: (0 if r[3] > 0 else 1, r[2], r[0].entity_id))
    return rows


def _inferred_hero_power_row(
    gs: "GameState", player_id: int, available_mana: int, *, next_turn: bool = False,
) -> Optional[Tuple[Optional["Entity"], BoardSpellDef, int]]:
    """
    灭世者死亡之翼等：旧技能已 SETASIDE、新技能实体尚未创建时，
    按英雄卡推断「无情」等技能是否仍可用。
    """
    hero = gs.get_hero(player_id)
    if hero is None:
        return None
    power_cid = _HERO_TO_POWER_CARD.get(hero.card_id or "")
    if not power_cid:
        return None
    defn = get_hero_power_def(power_cid)
    if defn is None:
        return None
    entity: Optional["Entity"] = None
    for e in list(gs.entities.values()):
        if (e.card_id or "") != power_cid:
            continue
        if not gs.is_entity_controlled_by(e, player_id):
            continue
        entity = e
        break
    if entity is not None and not hero_power_is_ready(entity, next_turn=next_turn):
        return None
    cost = defn.base_cost
    if entity is not None:
        cost = hero_power_cost(entity, gs, player_id)
    if cost > available_mana:
        return None
    return entity, defn, cost


def _hand_transform_hero_power_row(
    gs: "GameState", player_id: int, available_mana: int,
) -> Optional[Tuple[Optional["Entity"], BoardSpellDef, int]]:
    """
    手牌有可打出的替换英雄卡（如灭世者死亡之翼）时，推断打出后可用的新技能。
    返回的 cost = 打出英雄卡费用 + 技能费用（overlay 会从总法力中一并扣除）。
    """
    hero = gs.get_hero(player_id)
    if hero is None:
        return None
    hero_cid = hero.card_id or ""
    best: Optional[Tuple[Optional["Entity"], BoardSpellDef, int]] = None
    for card in gs.get_hand(player_id):
        cid = card.card_id or ""
        power_cid = _HERO_TO_POWER_CARD.get(cid)
        if not power_cid or cid == hero_cid:
            continue
        defn = get_hero_power_def(power_cid)
        if defn is None:
            continue
        play_cost = hand_minion_cost(card, gs, player_id)
        hp_cost = defn.base_cost
        for e in list(gs.entities.values()):
            if (e.card_id or "") != power_cid:
                continue
            if not gs.is_entity_controlled_by(e, player_id):
                continue
            hp_cost = hero_power_cost(e, gs, player_id)
            break
        total = play_cost + hp_cost
        if total > available_mana:
            continue
        if best is None or total < best[2]:
            best = (None, defn, total)
    return best


def usable_hero_power(
    gs: "GameState", player_id: int, available_mana: int, *, next_turn: bool = False,
) -> Optional[Tuple[Optional["Entity"], BoardSpellDef, int]]:
    rows = list_usable_hero_powers(
        gs, player_id, available_mana, next_turn=next_turn,
    )
    if rows:
        e, defn, mana_need, _corpse = rows[0]
        return e, defn, mana_need
    row = _inferred_hero_power_row(gs, player_id, available_mana, next_turn=next_turn)
    if row is not None:
        return row
    return _hand_transform_hero_power_row(gs, player_id, available_mana)


def has_usable_hero_power(
    gs: "GameState", player_id: int, available_mana: int, *, next_turn: bool = False,
) -> bool:
    return usable_hero_power(
        gs, player_id, available_mana, next_turn=next_turn,
    ) is not None


def apply_all_usable_hero_powers(
    gs: "GameState",
    player_id: int,
    fighters: List[dict],
    mana_budget: Optional[int],
    *,
    enemy_shield: bool = False,
    next_turn: bool = False,
    taunts: Optional[List[dict]] = None,
    corpses_budget: Optional[int] = None,
) -> Tuple[bool, Optional[int], List[str], SpellApplyResult, int]:
    """
    依次使用所有当前可用英雄技能（残骸 buff 优先，再法力技能）。
    返回 (是否用过, 剩余法力, 技能名列表, 合并结果, 剩余残骸预算)。
    """
    from .spell_board import player_corpses

    mana_left = mana_budget
    corpses_left = (
        corpses_budget
        if corpses_budget is not None
        else player_corpses(gs, player_id)
    )
    names: List[str] = []
    total = SpellApplyResult()
    used = False
    # 同一实体只点一次；用过的 eid 跳过
    used_eids: set = set()
    while True:
        budget = 10**9 if mana_left is None else mana_left
        rows = [
            r for r in list_usable_hero_powers(
                gs, player_id, budget, next_turn=next_turn,
                corpses_budget=corpses_left,
            )
            if r[0].entity_id not in used_eids
        ]
        if not rows:
            break
        entity, defn, mana_need, corpse_need = rows[0]
        hp_res = defn.apply(
            list(taunts or []),
            fighters,
            mult=1,
            enemy_shield=enemy_shield,
            gs=gs,
            player_id=player_id,
            next_turn_preview=next_turn,
        )
        total.direct_face_damage += int(hp_res.direct_face_damage or 0)
        total.battlecry_face_damage += int(hp_res.battlecry_face_damage or 0)
        total.self_hero_heal += int(hp_res.self_hero_heal or 0)
        if hp_res.broke_enemy_hero_shield:
            total.broke_enemy_hero_shield = True
        if mana_left is not None:
            mana_left -= mana_need
        corpses_left = max(0, corpses_left - corpse_need)
        used_eids.add(entity.entity_id)
        names.append(defn.name)
        used = True
    return used, mana_left, names, total, corpses_left


def apply_hero_power_to_fighters(
    gs: "GameState",
    player_id: int,
    fighters: List[dict],
    mana_budget: Optional[int],
    *,
    enemy_shield: bool = False,
    next_turn: bool = False,
    taunts: Optional[List[dict]] = None,
) -> Tuple[bool, Optional[int], SpellApplyResult]:
    """对 fighters 施加英雄技能效果；返回 (是否成功, 剩余法力, 技能结果)。"""
    used, mana_left, _names, hp_res, _corpses = apply_all_usable_hero_powers(
        gs, player_id, fighters, mana_budget,
        enemy_shield=enemy_shield, next_turn=next_turn, taunts=taunts,
    )
    return used, mana_left, hp_res


from . import hero_power_p0  # noqa: E402, F401
