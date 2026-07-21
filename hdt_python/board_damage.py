# board_damage.py - 场攻计算（仿 HDT Utility/BoardDamage）
# 参考: HearthSim/Hearthstone-Deck-Tracker BoardCard.cs, BoardHero.cs, PlayerBoard.cs

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from hdt_python.app_paths import resource_path
from typing import TYPE_CHECKING, List, Optional, Tuple

if TYPE_CHECKING:
    from .power_parser import Entity, GameState

INFINITE_ATK = 2147483647

# 日志里常不写 tag=TAUNT 的已知嘲讽衍生物（如 TLC_234t 永生花芽 0/1）
_TAUNT_CARD_IDS = frozenset({
    "TLC_234t",
})


@lru_cache(maxsize=1)
def _card_db_taunt_ids() -> frozenset:
    """cards.json 中带 TAUNT 的 CardID（日志缺 tag=TAUNT 时兜底）。"""
    import json

    ids = set(_TAUNT_CARD_IDS)
    path = resource_path("json", "cards.json")
    if not path.is_file():
        return frozenset(ids)
    try:
        for card in json.loads(path.read_text(encoding="utf-8")):
            cid = card.get("id")
            if not cid:
                continue
            mech = card.get("mechanics") or []
            if "TAUNT" in mech:
                ids.add(cid)
    except (OSError, json.JSONDecodeError):
        pass
    return frozenset(ids)

_EXCLUDED_CARDTYPES = frozenset({
    "PLAYER", "ENCHANTMENT", "HERO_POWER", "SPELL", "HERO",
    "WEAPON", "GAME", "LOCATION",
})
_EXCLUDED_ZONES = frozenset({"GRAVEYARD", "SETASIDE", "REMOVEDFROMGAME"})
_ZONE_NAMES = ["", "PLAY", "DECK", "HAND", "GRAVEYARD", "REMOVEDFROMGAME", "SETASIDE", "SECRET"]
_CARDTYPE_NAMES = ["", "HERO", "MINION", "SPELL", "ENCHANTMENT", "WEAPON", "ITEM", "TOKEN", "HERO_POWER"]


def _tag(entity: "Entity", name: str) -> int:
    return entity.tags.get(name, 0)


def _clamp_attack(value: int) -> int:
    if value == INFINITE_ATK:
        return 0
    return max(0, int(value))


# 无法攻击英雄的武器（日志常写在英雄 CANNOT_ATTACK_HEROES，CardID 作兜底）
_WEAPONS_CANNOT_ATTACK_HEROES = frozenset({
    "END_012",  # 无穷之手
})


def hero_weapon_can_face(
    hero_entity: Optional["Entity"],
    weapon_entity: Optional["Entity"] = None,
) -> bool:
    """英雄持武是否可对敌方英雄打脸（无穷之手等除外）。"""
    if hero_entity is not None and (
        _tag(hero_entity, "CANNOT_ATTACK_HEROES")
        or _tag(hero_entity, "CANT_ATTACK_HEROES")
    ):
        return False
    if weapon_entity is None:
        return True
    if (
        _tag(weapon_entity, "CANNOT_ATTACK_HEROES")
        or _tag(weapon_entity, "CANT_ATTACK_HEROES")
    ):
        return False
    cid = weapon_entity.card_id or ""
    if cid in _WEAPONS_CANNOT_ATTACK_HEROES:
        return False
    if cid.startswith("CORE_") and cid[5:] in _WEAPONS_CANNOT_ATTACK_HEROES:
        return False
    return True


def effective_attack_from_tags(tags: dict) -> int:
    """
    从实体 tags 读取当前攻击力。
    ATK 与 479 可能不同步（BUFF 后常见 479 已更新、ATK 仍为牌面攻），取较大值。
    4472 可能滞后或为亡语脚本数据，仅作兜底。
    """
    v_atk = tags.get("ATK")
    v479 = tags.get("479")
    if v_atk is not None and v479 is not None:
        return _clamp_attack(max(int(v_atk), int(v479)))
    if v_atk is not None:
        return _clamp_attack(v_atk)
    if v479 is not None:
        return _clamp_attack(v479)

    v4472 = tags.get("4472")
    if v4472 is not None and v4472 > 0:
        return _clamp_attack(v4472)

    return 0


def entity_zone(entity: "Entity") -> str:
    """当前区域（entity.zone 与 tags[ZONE] 取一致结果）"""
    raw = entity.tags.get("ZONE")
    if raw is not None:
        if isinstance(raw, int) or (isinstance(raw, str) and str(raw).isdigit()):
            zi = int(raw)
            if 0 <= zi < len(_ZONE_NAMES):
                return _ZONE_NAMES[zi]
        return str(raw).upper()
    return (entity.zone or "").upper()


def entity_cardtype(entity: "Entity") -> Optional[str]:
    if entity.cardtype:
        return entity.cardtype
    raw = entity.tags.get("CARDTYPE")
    if raw is None:
        return None
    if isinstance(raw, int) or (isinstance(raw, str) and str(raw).isdigit()):
        ti = int(raw)
        if 0 <= ti < len(_CARDTYPE_NAMES):
            return _CARDTYPE_NAMES[ti]
    return str(raw).upper()


def _zone_name(entity: "Entity") -> str:
    return entity_zone(entity)


def hero_has_divine_shield(hero: Optional["Entity"]) -> bool:
    """英雄是否带圣盾"""
    return hero is not None and _tag(hero, "DIVINE_SHIELD") == 1


def apply_divine_shield_to_hits(hits: List[int], has_shield: bool) -> int:
    """英雄圣盾：攻击方可把最小一次攻击浪费在破盾上，其余伤害打脸"""
    if not hits:
        return 0
    total = sum(hits)
    if has_shield:
        return max(0, total - min(hits))
    return total


# 附魔 TAG_SCRIPT_DATA_NUM_1 存非攻数据（如发现费用），不可计入场攻
_ENCHANT_NON_ATTACK_SCRIPT_IDS = frozenset({
    "ULD_163e",  # 过期货物：记录发现牌费用，非 +攻
})
# 少数攻加成附魔只写 script、不写 323（如加尔手臂）
_ENCHANT_SCRIPT_ATTACK_IDS = frozenset({
    "CATA_726te",
    "EDR_810e",
    "EDR_810e2",
})


def _enchantment_attack_bonus(tags: dict, card_id: str = "") -> int:
    """附魔实体上的攻加成（tag 323 / ATK；script 仅在有 323 或白名单 card_id 时）。"""
    bonus = 0
    v323 = tags.get("323")
    if v323 is not None:
        bonus += max(0, int(v323))
    v_atk = tags.get("ATK")
    if v_atk is not None:
        bonus = max(bonus, max(0, int(v_atk)))
    cid = card_id or ""
    if cid in _ENCHANT_NON_ATTACK_SCRIPT_IDS:
        return bonus
    v_script = tags.get("TAG_SCRIPT_DATA_NUM_1")
    if v_script is not None and (v323 is not None or cid in _ENCHANT_SCRIPT_ATTACK_IDS):
        vs = int(v_script)
        if 0 < vs <= 30:
            bonus = max(bonus, vs)
    return bonus


def attached_enchantment_attack_bonus(gs: "GameState", entity: "Entity") -> int:
    """汇总挂在随从身上的附魔攻加成（CATA_153e 等）。"""
    if not entity.is_minion:
        return 0
    eid = entity.entity_id
    total = 0
    for e in list(gs.entities.values()):
        if entity_cardtype(e) != "ENCHANTMENT":
            continue
        if int(e.tags.get("ATTACHED", 0) or 0) != eid:
            continue
        if entity_zone(e) in ("GRAVEYARD", "REMOVEDFROMGAME"):
            continue
        total += _enchantment_attack_bonus(e.tags, e.card_id or "")
    return total


@lru_cache(maxsize=4096)
def card_display_name_zh(card_id: str, fallback: str = "") -> str:
    """cards_zhCN.json 中文名；缺失时回退 card_id 或 fallback。"""
    if not card_id:
        return fallback or "随从"
    path = resource_path("json", "cards_zhCN.json")
    if not path.is_file():
        return fallback or card_id
    try:
        import json
        with open(path, encoding="utf-8") as f:
            for card in json.load(f):
                if card.get("id") == card_id:
                    name = card.get("name") or ""
                    if name:
                        return name
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        pass
    return fallback or card_id


def format_hand_charge_label(
    gs: "GameState",
    player_id: int,
    entity: "Entity",
    atk: int,
    *,
    prefix: str = "打出",
) -> str:
    """手牌冲锋步骤/备注文案（含双面间谍复制）。"""
    name = card_display_name_zh(entity.card_id or "", entity.card_id or "随从")
    copies = 2 if double_agent_summons_copy(gs, player_id, entity) else 1
    body = f"{name}({atk}攻冲锋)"
    if copies > 1:
        body += f"×{copies}"
    return f"{prefix} {body}" if prefix else body


@lru_cache(maxsize=4096)
def _printed_minion_attack(card_id: str) -> int:
    """cards.json 牌面攻击力（HDT 以运行时 ATK 为准，附魔仅作 tag 未刷新时的兜底）。"""
    if not card_id:
        return 0
    cards_path = resource_path("json", "cards.json")
    if not cards_path.is_file():
        return 0
    try:
        import json
        with open(cards_path, encoding="utf-8") as f:
            for card in json.load(f):
                if card.get("id") == card_id:
                    return max(0, int(card.get("attack") or 0))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return 0
    return 0


@lru_cache(maxsize=1)
def _zero_attack_weapon_ids() -> frozenset[str]:
    """牌面 0 攻武器（卡德加智慧之球等），479 误同步耐久时不计场攻。"""
    path = resource_path("json", "cards.json")
    if not path.is_file():
        return frozenset({"TOY_373t"})
    try:
        import json
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return frozenset({"TOY_373t"})
    return frozenset(
        c["id"] for c in data
        if c.get("type") == "WEAPON" and int(c.get("attack") or 0) <= 0
    )


def _weapon_std_attack(entity: "Entity") -> int:
    """武器攻击力：不用 4472/耐久；0 攻武器恒为 0。无穷攻保留原值供清场，打脸另拦。"""
    cid = entity.card_id or ""
    if cid in _zero_attack_weapon_ids():
        return 0
    tags = entity.tags
    if "ATK" in tags:
        raw = int(tags["ATK"])
        if raw == INFINITE_ATK:
            return INFINITE_ATK
        return _clamp_attack(raw)
    v479 = tags.get("479")
    if v479 is not None:
        raw = int(v479)
        if raw == INFINITE_ATK:
            return INFINITE_ATK
        atk = _clamp_attack(raw)
        if _printed_minion_attack(cid) <= 0:
            return 0
        return atk
    if entity.atk:
        if entity.atk == INFINITE_ATK:
            return INFINITE_ATK
        atk = _clamp_attack(entity.atk)
        if _printed_minion_attack(cid) <= 0:
            return 0
        return atk
    return _printed_minion_attack(cid)


def _std_attack(entity: "Entity", game_state: Optional["GameState"] = None) -> int:
    """
    标准攻击力（含 BUFF；衍生物 HIDE_STATS 且无攻时返回 0）。

    对齐 HDT BoardCard：以实体 ATK tag 为准（effective_attack_from_tags 在 ATK/479
    不同步时取较大值）。附魔攻加成仅在「运行时攻仍低于牌面身材」时叠加
    （tag 尚未写入完整基础攻）。若 ATK 已达到牌面攻，视为已同步（含「变为 N」
    后再叠光环的情形），不再 printed+附魔，避免吸血蚊等被雷欧克/巴加斯特重复加攻。
    """
    if entity.is_weapon:
        return _weapon_std_attack(entity)
    atk = effective_attack_from_tags(entity.tags)
    if game_state is not None and entity.is_minion:
        ench = attached_enchantment_attack_bonus(game_state, entity)
        if ench > 0:
            printed = _printed_minion_attack(entity.card_id or "")
            runtime = atk
            # 严格 <：ATK 已到牌面时信任 tag（斗志有限→1 再 +光环后 ATK=3 等）
            if printed > 0 and runtime < printed:
                atk = max(runtime, printed + ench)
    if atk <= 0 and entity.atk > 0 and entity.atk != INFINITE_ATK:
        atk = entity.atk
    if _tag(entity, "HIDE_STATS") and atk <= 0:
        return 0
    return atk


def entity_has_taunt(
    entity: "Entity",
    game_state: Optional["GameState"] = None,
) -> bool:
    """是否带嘲讽（潜行/休眠不生效；日志 tag 缺失时用 CardID 兜底）。"""
    if _tag(entity, "STEALTH") == 1:
        return False
    if is_dormant(entity, game_state):
        return False
    if "TAUNT" in entity.tags:
        return _tag(entity, "TAUNT") == 1
    cid = entity.card_id or ""
    return cid in _card_db_taunt_ids()


def living_taunt_minions(
    board: List["Entity"],
    game_state: Optional["GameState"] = None,
) -> List["Entity"]:
    """存活且本回合生效的嘲讽随从（排除休眠、潜行）。"""
    return [
        m for m in board
        if m.current_health > 0
        and entity_has_taunt(m)
        and not is_dormant(m, game_state)
    ]


# 黑暗之赐等附魔：+2/+2 扰魔（日志有时只写在附魔实体上）
_SPELL_IMMUNE_ENCHANTMENT_IDS = frozenset({
    "EDR_100t1e",
})


def entity_spell_immune(
    entity: "Entity",
    gs: Optional["GameState"] = None,
) -> bool:
    """无法被法术/英雄技能指定（Elusive / CANNOT_BE_TARGETED_BY_SPELLS / 扰魔附魔）。"""
    if _tag(entity, "ELUSIVE") == 1:
        return True
    if _tag(entity, "CANNOT_BE_TARGETED_BY_SPELLS") == 1:
        return True
    if gs is None or not getattr(entity, "entity_id", None):
        return False
    eid = int(entity.entity_id)
    for e in list(gs.entities.values()):
        if entity_cardtype(e) != "ENCHANTMENT":
            continue
        if int(e.tags.get("ATTACHED", 0) or 0) != eid:
            continue
        if _tag(e, "ELUSIVE") == 1 or _tag(e, "CANNOT_BE_TARGETED_BY_SPELLS") == 1:
            return True
        if (e.card_id or "") in _SPELL_IMMUNE_ENCHANTMENT_IDS:
            return True
    return False


def _num_turns_in_play(entity: "Entity") -> int:
    """对齐 HDT：NUM_TURNS_IN_PLAY 缺失时 GetTag 视为 0（召唤疲劳）。"""
    if "NUM_TURNS_IN_PLAY" in entity.tags:
        return _tag(entity, "NUM_TURNS_IN_PLAY")
    return 0


def is_exhausted(entity: "Entity") -> bool:
    if entity.is_hero:
        return False

    used = effective_attacks_this_turn(entity, active_turn=True)
    per_turn = attacks_per_turn(entity, is_silenced(entity))
    if used >= per_turn:
        return True

    if _minion_summoned_this_turn(entity):
        if (has_charge(entity) or has_rush(entity)) and used == 0:
            return False
        return True

    # 日志常在回合开始后仍保留 EXHAUSTED=1，但 NUM_ATTACKS_THIS_TURN 已归零
    # 休眠刚苏醒也常带 EXHAUSTED=1 + NUM_TURNS>=1，不可当作“陈旧疲劳”清掉
    if (
        _tag(entity, "EXHAUSTED")
        and _num_turns_in_play(entity) >= 1
        and used == 0
        and not _tag(entity, "DORMANT_AWAKENED_THIS_TURN")
    ):
        return False

    if not _tag(entity, "EXHAUSTED"):
        return _num_turns_in_play(entity) == 0
    if has_charge(entity) or has_rush(entity):
        if used == 0:
            return False
    return True


def attacks_per_turn(entity: "Entity", silenced: bool = False) -> int:
    if silenced:
        return 1
    if _tag(entity, "MEGA_WINDFURY") or _tag(entity, "WINDFURY") == 3:
        return 4
    if _tag(entity, "WINDFURY"):
        return 2
    max_from_tag = _tag(entity, "MAX_NUM_ATTACKS")
    if max_from_tag > 0:
        return max_from_tag
    return 1


def attacks_this_turn(entity: "Entity") -> int:
    return _tag(entity, "NUM_ATTACKS_THIS_TURN")


def effective_attacks_this_turn(
    entity: "Entity", *, active_turn: bool = True,
) -> int:
    """
    本回合已攻击次数；回合刷新时 EXHAUSTED 已清零但 NUM_ATTACKS 仍残留上回合值时视为 0。
    """
    used = attacks_this_turn(entity)
    if not active_turn:
        return 0
    per_turn = attacks_per_turn(entity, is_silenced(entity))
    if (
        not _tag(entity, "EXHAUSTED")
        and _num_turns_in_play(entity) >= 1
        and used >= per_turn
    ):
        return 0
    return used


def has_charge(entity: "Entity") -> bool:
    """含疯狂药水等赋予的 NON_KEYWORD_CHARGE（日志 tag 887）。"""
    return (
        _tag(entity, "CHARGE") == 1
        or _tag(entity, "NON_KEYWORD_CHARGE") == 1
        or _tag(entity, "887") == 1
    )


def is_potion_madness_stolen(gs: "GameState", entity: "Entity") -> bool:
    """疯狂药水 CFM_603e：当回合偷来的随从。"""
    eid = entity.entity_id
    for e in list(gs.entities.values()):
        if (e.card_id or "") != "CFM_603e":
            continue
        if int(e.tags.get("ATTACHED", 0) or 0) == eid:
            return True
    return False


def has_rush(entity: "Entity") -> bool:
    """随从自带突袭（ATTACKABLE_BY_RUSH 是“可被突袭攻击”标记，不是突袭本身）。"""
    return _tag(entity, "RUSH") == 1


# 威拉罗克变形形态：手牌冲锋时日志常写 ZONE=PLAY 但未进入 board_slots
_VILEROK_CHARGE_IDS = frozenset({
    "WW_364t",
})


def _is_vilerok_charge_card(card_id: str) -> bool:
    return card_id in _VILEROK_CHARGE_IDS


def _entity_on_board_slots(gs: "GameState", entity: "Entity") -> bool:
    pid = entity.controller
    if pid is None:
        return False
    eid = entity.entity_id
    return any(slot_eid == eid for slot_eid in gs.board_slots.get(pid, {}).values())


def vilerok_hand_attack_zone(gs: "GameState", entity: "Entity") -> bool:
    """狡诈巨龙威拉罗克：变形高亮后可从手牌冲锋，ZONE 可能已是 PLAY 却未上场。"""
    if not entity.is_minion or not _is_vilerok_charge_card(entity.card_id or ""):
        return False
    zone = entity_zone(entity)
    if zone == "HAND":
        return True
    return zone == "PLAY" and not _entity_on_board_slots(gs, entity)


# 黑暗之赐「活体梦魇」：手牌阶段常无 CHARGE 标签，靠附魔或 HAS_DARK_GIFT 指向的 gift 实体识别
_DARK_GIFT_CHARGE_IDS = frozenset({
    "EDR_100t5",
    "EDR_100t5e",
})


def _is_dark_gift_charge_card(card_id: str) -> bool:
    return card_id in _DARK_GIFT_CHARGE_IDS or card_id.startswith("EDR_100t5")


def has_dark_gift_charge(gs: "GameState", entity: "Entity") -> bool:
    """手牌/场面随从是否带有黑暗之赐的冲锋效果。"""
    eid = entity.entity_id
    for e in list(gs.entities.values()):
        if entity_cardtype(e) != "ENCHANTMENT":
            continue
        cid = e.card_id or ""
        if not _is_dark_gift_charge_card(cid):
            continue
        if _tag(e, "ATTACHED") == eid:
            return True

    gift_ref = entity.tags.get("HAS_DARK_GIFT")
    if gift_ref is not None and int(gift_ref) > 1:
        gift = gs.entities.get(int(gift_ref))
        if gift and _is_dark_gift_charge_card(gift.card_id or ""):
            return True
    return False


def hand_minion_has_charge(gs: "GameState", entity: "Entity") -> bool:
    """手牌随从本回合打出后能否立即攻击（冲锋标签、威拉罗克变形或黑暗之赐冲锋）。"""
    if not entity.is_minion:
        return False
    in_hand = entity_zone(entity) == "HAND"
    vilerok_hand = vilerok_hand_attack_zone(gs, entity)
    if not in_hand and not vilerok_hand:
        return False
    if has_charge(entity) or _is_vilerok_charge_card(entity.card_id or ""):
        return True
    return has_dark_gift_charge(gs, entity)


def hand_minion_cost(entity: "Entity") -> int:
    base_cost = int(entity.cost) if entity.cost and entity.cost > 0 else 0
    raw_tag = entity.tags.get("COST")
    tag_cost: Optional[int] = None
    if raw_tag is not None:
        try:
            tc = int(raw_tag)
            if tc >= 0:
                tag_cost = tc
                base_cost = max(base_cost, tc)
        except (TypeError, ValueError):
            pass
    prepared_raw = entity.tags.get("PREPARED")
    if prepared_raw is not None:
        try:
            prepared = int(prepared_raw)
            if prepared > 0 and base_cost > 0:
                prep_cost = max(0, base_cost - prepared)
                if tag_cost is None:
                    return prep_cost
                if tag_cost >= base_cost and prep_cost < base_cost:
                    return prep_cost
                return tag_cost
        except (TypeError, ValueError):
            pass
    if tag_cost is not None:
        return tag_cost
    if entity.cost > 0:
        return int(entity.cost)
    return 0


def hand_minion_attack(entity: "Entity") -> int:
    atk = effective_attack_from_tags(entity.tags)
    if atk > 0:
        return atk
    return max(0, int(entity.atk or 0))


def hand_minion_health(entity: "Entity") -> int:
    if entity.current_health > 0:
        return entity.current_health
    hp = int(entity.health or 0)
    if hp > 0:
        return hp
    return max(1, int(entity.tags.get("HEALTH", 0)))


def hand_minion_has_rush(entity: "Entity") -> bool:
    """手牌随从打出后带突袭（可解场、当回合不能打脸）。"""
    if not entity.is_minion or entity_zone(entity) != "HAND":
        return False
    return has_rush(entity)


def collect_hand_rush_minions(
    gs: "GameState", player_id: int, available_mana: int,
) -> List[Tuple["Entity", int, int]]:
    """可打出的手牌突袭随从：(实体, 费用, 攻击力)。"""
    from .rush_board import get_rush_def

    result: List[Tuple["Entity", int, int]] = []
    for card in gs.get_hand(player_id):
        if not hand_minion_has_rush(card):
            continue
        if get_rush_def(card.card_id or "") is None:
            continue
        cost = hand_minion_cost(card)
        if cost > available_mana:
            continue
        atk = hand_minion_attack(card)
        if atk <= 0:
            continue
        result.append((card, cost, atk))
    return result


DOUBLE_AGENT_IDS = frozenset({"AV_711"})


def player_hero_class(gs: "GameState", player_id: int) -> Optional[str]:
    hero = gs.get_hero(player_id)
    if hero is None:
        return None
    return hero.tags.get("CLASS")


def hand_has_other_class_card(
    gs: "GameState",
    player_id: int,
    *,
    exclude_entity_id: Optional[int] = None,
) -> bool:
    """手牌中是否存在非本职业、非中立的可打出卡牌（复仇 vendetta / 双面间谍战吼）。"""
    my_class = player_hero_class(gs, player_id)
    if not my_class:
        return False
    for card in gs.get_hand(player_id):
        if exclude_entity_id is not None and card.entity_id == exclude_entity_id:
            continue
        if not card.card_id or card.cardtype not in ("SPELL", "MINION", "WEAPON"):
            continue
        card_class = card.tags.get("CLASS")
        if not card_class or card_class in (my_class, "NEUTRAL"):
            continue
        return True
    return False


def double_agent_summons_copy(
    gs: "GameState",
    player_id: int,
    entity: "Entity",
) -> bool:
    """双面间谍 AV_711：手牌有另一职业牌时战吼召唤复制。"""
    if (entity.card_id or "") not in DOUBLE_AGENT_IDS:
        return False
    return hand_has_other_class_card(
        gs, player_id, exclude_entity_id=entity.entity_id,
    )


def collect_hand_charge_minions(
    gs: "GameState", player_id: int,
) -> List[Tuple["Entity", int, int]]:
    """可打出的手牌冲锋随从：(实体, 费用, 攻击力)。"""
    result: List[Tuple["Entity", int, int]] = []
    seen: set = set()

    def _try_add(card: "Entity") -> None:
        eid = card.entity_id
        if eid in seen:
            return
        if not hand_minion_has_charge(gs, card):
            return
        cost = hand_minion_cost(card)
        atk = hand_minion_attack(card)
        if atk <= 0:
            return
        seen.add(eid)
        result.append((card, cost, atk))

    for card in gs.get_hand(player_id):
        _try_add(card)
    for card in list(gs.entities.values()):
        if not gs.is_entity_controlled_by(card, player_id):
            continue
        if entity_zone(card) == "HAND":
            continue
        if vilerok_hand_attack_zone(gs, card):
            _try_add(card)
    return result


def _minion_summoned_this_turn(entity: "Entity") -> bool:
    """是否本回合刚进入场面（对齐 HDT：NUM_TURNS_IN_PLAY 缺失视为 0）。"""
    if _tag(entity, "SUMMONING_SICKNESS") or _tag(entity, "1196"):
        return True
    if _tag(entity, "JUST_PLAYED"):
        return True
    # 休眠刚苏醒：本回合仍有召唤失调，不可攻击（玛瑟里顿等）
    if _tag(entity, "DORMANT_AWAKENED_THIS_TURN"):
        return True
    return _num_turns_in_play(entity) == 0


def _rush_blocks_hero_this_turn(entity: "Entity", active_turn: bool) -> bool:
    """突袭随从上场当回合不能打脸（可解嘲讽）。"""
    if not active_turn or not entity.is_minion:
        return False
    if not has_rush(entity) or has_charge(entity):
        return False
    # 1196/JUST_PLAYED 会在场面首次攻击后全局清空，不能再依赖它们。
    # 对齐 HDT：NUM_TURNS_IN_PLAY 缺失时视为 0（本回合刚上场）。
    return _num_turns_in_play(entity) == 0


def is_silenced(entity: "Entity") -> bool:
    return _tag(entity, "SILENCED") == 1


def is_dormant(entity: "Entity", game_state: Optional["GameState"] = None) -> bool:
    """休眠随从本回合不参与场攻/交换（含暮光主母等带唤醒附魔的休眠）。"""
    if "DORMANT" in entity.tags:
        return _tag(entity, "DORMANT") == 1
    if game_state is not None:
        eid = getattr(entity, "entity_id", None)
        if eid is not None:
            for e in list(game_state.entities.values()):
                if _tag(e, "ATTACHED") != eid:
                    continue
                if entity_zone(e) not in ("PLAY", "SETASIDE"):
                    continue
                if _tag(e, "DORMANT_AWAKEN_CONDITION_ENCHANT") == 1:
                    return True
    return False


def is_titan_blocked(entity: "Entity") -> bool:
    if not _tag(entity, "TITAN"):
        return False
    used = 0
    if _tag(entity, "TITAN_ABILITY_USED_1"):
        used += 1
    if _tag(entity, "TITAN_ABILITY_USED_2"):
        used += 1
    if _tag(entity, "TITAN_ABILITY_USED_3"):
        used += 1
    return used < 3


def is_board_entity(entity: "Entity") -> bool:
    """场面随从过滤（对齐 HDT PlayerBoard.Filter + 战场槽位 1-7）"""
    zone = entity_zone(entity)
    if zone in _EXCLUDED_ZONES:
        return False
    if zone != "PLAY":
        return False
    if entity.current_health <= 0 or _tag(entity, "DEAD"):
        return False
    if _tag(entity, "ATTACHED") > 0:
        return False

    ct = entity_cardtype(entity)
    if ct in _EXCLUDED_CARDTYPES:
        return False

    cid = entity.card_id or ""
    if cid.endswith("e") and ct != "MINION":
        return False

    zpos = _tag(entity, "ZONE_POSITION")
    if not (1 <= zpos <= 7):
        return False

    if ct in ("MINION", "TOKEN"):
        return True

    # 极少数 CARDTYPE 未及时写入的随从：必须有战场槽位且像随从
    if cid and not cid.endswith("e") and not cid.endswith("p") and "HERO" not in cid:
        return _tag(entity, "ATK") > 0 or _tag(entity, "HEALTH") > 0 or entity.health > 0
    return False


def collect_board_minions(entities, player_id: int, game_state: "GameState") -> List["Entity"]:
    """按 ZONE_POSITION 去重，每槽只保留最新实体（避免离场随从残留）"""
    snapshot = list(entities)
    candidates = [
        e for e in snapshot
        if game_state.is_entity_controlled_by(e, player_id) and is_board_entity(e)
    ]
    by_pos: dict = {}
    for e in candidates:
        zpos = _tag(e, "ZONE_POSITION")
        if 1 <= zpos <= 7:
            cur = by_pos.get(zpos)
            if cur is None or e.entity_id > cur.entity_id:
                by_pos[zpos] = e
    if by_pos:
        return sorted(by_pos.values(), key=lambda x: _tag(x, "ZONE_POSITION"))
    return candidates[:7]


def _get_game_entity(game_state: "GameState"):
    if game_state.game_entity_id is None:
        return None
    return game_state.entities.get(game_state.game_entity_id)


def _resolve_current_player_id(game_state: "GameState") -> Optional[int]:
    """当前回合的 PlayerID（1/2）。"""
    active = getattr(game_state, "active_player_id", None)
    if active:
        return active

    game_entity = _get_game_entity(game_state)
    if not game_entity:
        return None
    raw = _tag(game_entity, "CURRENT_PLAYER")
    if raw <= 0:
        return None
    mapped = game_state.player_ids.get(raw)
    if mapped is not None:
        return mapped
    if raw in (1, 2):
        return raw
    return None


def _turn_parity_is_players_turn(game_state: "GameState", player_id: int) -> Optional[bool]:
    """仿 HDT EntityHelper.IsPlayersTurn 的 TURN 奇偶判定。"""
    game_entity = _get_game_entity(game_state)
    if not game_entity:
        return None
    turn = _tag(game_entity, "TURN")
    if turn <= 0:
        return None
    first_pid = game_state.first_player_id
    if first_pid is None:
        return None
    offset = 0 if first_pid == player_id else 1
    return (turn + offset) % 2 == 1


def is_players_turn(game_state: "GameState", player_id: int) -> bool:
    """当前是否为 player_id 的回合。"""
    from_current = _resolve_current_player_id(game_state)
    from_parity = _turn_parity_is_players_turn(game_state, player_id)

    if from_current is not None and from_parity is not None:
        current_says = from_current == player_id
        if current_says == from_parity:
            return current_says
        # CURRENT_PLAYER 可能是 EntityID，与 TURN 冲突时以 HDT 的 TURN 奇偶为准
        return from_parity

    if from_current is not None:
        return from_current == player_id
    if from_parity is not None:
        return from_parity
    return False


def board_active_turn_for_display(game_state: "GameState", player_id: int) -> bool:
    """仿 HDT BoardState.CreateBoard：我方面板在对方回合用 activeTurn=False 显示下回合场攻"""
    local_pid = game_state.local_player_id
    if local_pid is not None:
        local_turn = is_players_turn(game_state, local_pid)
        is_player_board = player_id == local_pid
        return local_turn if is_player_board else (not local_turn)
    return is_players_turn(game_state, player_id)


@dataclass
class BoardCardView:
    """单张牌的可攻击视图（仿 BoardCard）"""
    entity: "Entity"
    active_turn: bool
    exhausted: bool
    include: bool
    attack: int
    attacks_per_turn: int
    attacks_this_turn: int
    can_attack_minion: bool
    can_attack_hero: bool
    game_state: Optional["GameState"] = None

    @property
    def std_attack(self) -> int:
        return _std_attack(self.entity, self.game_state)


def _calculate_attack(
    entity: "Entity",
    active_turn: bool,
    is_weapon: bool,
    game_state: Optional["GameState"] = None,
) -> int:
    silenced = is_silenced(entity)
    per_turn = attacks_per_turn(entity, silenced)
    remaining = max(
        per_turn - (effective_attacks_this_turn(entity, active_turn=active_turn) if active_turn else 0),
        0,
    )
    std = _std_attack(entity, game_state)
    if is_weapon:
        health = _weapon_health(entity)
        remaining = min(remaining, health)
    return remaining * std


def _weapon_health(entity: "Entity") -> int:
    return entity.current_durability


def _is_able_to_attack(
    entity: "Entity",
    active_turn: bool,
    is_weapon: bool,
    is_hero: bool,
    game_state: Optional["GameState"] = None,
) -> bool:
    if _tag(entity, "CANT_ATTACK") or _tag(entity, "FROZEN"):
        return False
    if is_dormant(entity, game_state) or is_titan_blocked(entity):
        return False
    if is_weapon and active_turn:
        return False
    if not active_turn:
        return True
    exhausted = is_exhausted(entity)
    if exhausted:
        return has_charge(entity) and attacks_this_turn(entity) == 0
    if effective_attacks_this_turn(entity, active_turn=True) >= attacks_per_turn(
        entity, is_silenced(entity),
    ):
        return False
    zone = _zone_name(entity)
    if zone in ("DECK", "HAND"):
        silenced = is_silenced(entity)
        windfury = _tag(entity, "WINDFURY") and not silenced
        used = attacks_this_turn(entity)
        return (windfury and used < 2) or (not windfury and used < 1)
    return True


def _can_attack_minion(
    entity: "Entity",
    active_turn: bool,
    game_state: Optional["GameState"] = None,
) -> bool:
    """能否攻击随从（清嘲讽用）：突袭上场当回合可参与"""
    if not entity.is_minion:
        return False
    if entity.current_health <= 0 or _std_attack(entity, game_state) <= 0:
        return False
    if _tag(entity, "CANT_ATTACK") or _tag(entity, "FROZEN"):
        return False
    if is_dormant(entity, game_state) or is_titan_blocked(entity):
        return False
    if not active_turn:
        return True
    exhausted = is_exhausted(entity)
    if exhausted:
        used = attacks_this_turn(entity)
        if used == 0 and (has_charge(entity) or has_rush(entity)):
            return True
        return False
    per_turn = attacks_per_turn(entity, is_silenced(entity))
    if attacks_this_turn(entity) >= per_turn:
        return False
    return True


def _can_attack_hero(
    entity: "Entity",
    active_turn: bool,
    game_state: Optional["GameState"] = None,
) -> bool:
    """能否对英雄造成伤害（场攻/打脸斩杀用）：突袭上场当回合不计入"""
    if not entity.is_minion:
        return False
    if _rush_blocks_hero_this_turn(entity, active_turn):
        return False
    return _is_able_to_attack(
        entity, active_turn, is_weapon=False, is_hero=False, game_state=game_state,
    )


def build_board_card(
    entity: "Entity",
    active_turn: bool,
    game_state: Optional["GameState"] = None,
) -> BoardCardView:
    exhausted = is_exhausted(entity)
    is_weapon = entity.is_weapon
    silenced = is_silenced(entity)
    per_turn = attacks_per_turn(entity, silenced)
    used = effective_attacks_this_turn(entity, active_turn=active_turn)
    can_minion = (
        _can_attack_minion(entity, active_turn, game_state) if entity.is_minion else False
    )
    can_hero = (
        _can_attack_hero(entity, active_turn, game_state) if entity.is_minion else False
    )
    include = _is_able_to_attack(
        entity, active_turn, is_weapon=is_weapon, is_hero=entity.is_hero,
        game_state=game_state,
    )
    if entity.is_minion:
        attack = (
            _calculate_attack(entity, active_turn, False, game_state) if include else 0
        )
    else:
        attack = _calculate_attack(entity, active_turn, is_weapon) if include else 0
    return BoardCardView(
        entity=entity,
        active_turn=active_turn,
        exhausted=exhausted,
        include=include,
        attack=attack,
        attacks_per_turn=per_turn,
        attacks_this_turn=used,
        can_attack_minion=can_minion,
        can_attack_hero=can_hero,
        game_state=game_state,
    )


@dataclass
class BoardHeroView:
    """英雄 + 武器（仿 BoardHero）"""
    hero: BoardCardView
    weapon: Optional[BoardCardView]
    include: bool
    attack: int
    has_weapon: bool

    @property
    def entity(self) -> "Entity":
        return self.hero.entity


# 团队之灵：你的回合英雄 +2 攻（场上光环；日志有时英雄 ATK 未含此加成）
TEAM_SPIRIT_CARD_IDS = frozenset({"TOY_028"})
TEAM_SPIRIT_ATK_BONUS = 2


def count_board_team_spirit(
    game_state: Optional["GameState"], player_id: Optional[int],
) -> int:
    """场上存活、未沉默的团队之灵数量。"""
    if game_state is None or player_id is None:
        return 0
    n = 0
    for m in game_state.get_board(player_id):
        cid = m.card_id or ""
        if cid not in TEAM_SPIRIT_CARD_IDS and not cid.endswith("TOY_028"):
            continue
        if int(getattr(m, "current_health", 0) or 0) <= 0:
            continue
        if is_silenced(m):
            continue
        if is_dormant(m, game_state):
            continue
        n += 1
    return n


def hero_weapon_strike_damage(
    hero_entity: "Entity",
    weapon_entity: Optional["Entity"],
    *,
    team_spirit_count: int = 0,
) -> int:
    """英雄单次打脸伤害。

    有武器时以武器攻为底；若英雄 ATK 更高（团队之灵光环、恶魔之爪等已写入
    英雄 ATK），取较大值。埃提耶识等英雄 479 未同步时仍能靠武器攻兜底。

    team_spirit_count：场上团队之灵数。若英雄 ATK 相对武器的超额攻击
    尚未覆盖光环 +2×N，则补足缺失部分，避免漏算。
    """
    hero_atk = _std_attack(hero_entity)
    w_atk = (
        _std_attack(weapon_entity)
        if weapon_entity is not None and _std_attack(weapon_entity) > 0
        else 0
    )
    base = max(w_atk, hero_atk) if w_atk > 0 else hero_atk
    n = max(0, int(team_spirit_count or 0))
    if n <= 0:
        return base
    want = TEAM_SPIRIT_ATK_BONUS * n
    have_extra = max(0, hero_atk - w_atk)
    missing = max(0, want - have_extra)
    return base + missing


def hero_can_attack_with_weapon(
    hero_entity: "Entity",
    weapon_entity: Optional["Entity"],
    active_turn: bool,
    *,
    team_spirit_count: int = 0,
) -> bool:
    """英雄本回合是否还能持武攻击。"""
    if not _is_able_to_attack(hero_entity, active_turn, False, True):
        return False
    if weapon_entity is None:
        return hero_weapon_strike_damage(
            hero_entity, None, team_spirit_count=team_spirit_count,
        ) > 0
    if weapon_entity.current_durability <= 0:
        return False
    return _std_attack(weapon_entity) > 0 or hero_weapon_strike_damage(
        hero_entity, weapon_entity, team_spirit_count=team_spirit_count,
    ) > 0


def _attack_with_weapon(
    hero_entity: "Entity",
    weapon_entity: Optional["Entity"],
    active_turn: bool,
    *,
    team_spirit_count: int = 0,
) -> int:
    if not hero_can_attack_with_weapon(
        hero_entity, weapon_entity, active_turn,
        team_spirit_count=team_spirit_count,
    ):
        return 0
    if not hero_weapon_can_face(hero_entity, weapon_entity):
        return 0
    base = hero_weapon_strike_damage(
        hero_entity, weapon_entity, team_spirit_count=team_spirit_count,
    )
    used = attacks_this_turn(hero_entity) if active_turn else 0
    if weapon_entity is None:
        silenced = is_silenced(hero_entity)
        if _tag(hero_entity, "WINDFURY") and not silenced and used == 0:
            return base * 2
        return base
    w_atk = _std_attack(weapon_entity)
    w_health = _weapon_health(weapon_entity)
    hero_wf = _tag(hero_entity, "WINDFURY") and not is_silenced(hero_entity)
    weapon_wf = _tag(weapon_entity, "WINDFURY") and not is_silenced(weapon_entity)
    if (hero_wf or weapon_wf) and w_health >= 2 and used == 0:
        return base * 2
    if hero_wf and not weapon_wf and w_health == 1:
        return base * 2 - w_atk
    return base


def build_board_hero(
    hero: "Entity",
    weapon: Optional["Entity"],
    active_turn: bool,
    *,
    team_spirit_count: int = 0,
) -> BoardHeroView:
    hero_view = build_board_card(hero, active_turn)
    weapon_view = build_board_card(weapon, active_turn) if weapon else None
    include = hero_can_attack_with_weapon(
        hero, weapon, active_turn, team_spirit_count=team_spirit_count,
    )
    attack = (
        _attack_with_weapon(
            hero, weapon, active_turn, team_spirit_count=team_spirit_count,
        )
        if include else 0
    )
    return BoardHeroView(
        hero=hero_view,
        weapon=weapon_view,
        include=include,
        attack=attack,
        has_weapon=weapon is not None,
    )


@dataclass
class PlayerBoardView:
    """玩家场面场攻（仿 PlayerBoard）"""
    hero: Optional[BoardHeroView]
    cards: List[BoardCardView]
    active_turn: bool
    player_id: Optional[int] = None
    game_state: Optional["GameState"] = None

    @property
    def minion_damage(self) -> int:
        return sum(
            c.attack for c in self.cards
            if is_board_entity(c.entity) and c.can_attack_hero
        )

    @property
    def hero_damage(self) -> int:
        if self.hero and self.hero.include:
            return self.hero.attack
        return 0

    @property
    def damage(self) -> int:
        """仿 HDT PlayerBoard.Damage：可打脸单位攻击力之和（突袭当回合不计入）"""
        total = self.hero_damage
        for card in self.cards:
            if not is_board_entity(card.entity) or not card.entity.is_minion:
                continue
            if card.can_attack_hero:
                total += card.attack
        return total

    def minion_attackers_for_taunts(self) -> List[Tuple["Entity", int]]:
        """清嘲讽搜索用：可攻击随从的每次攻击（含突袭当回合）"""
        result = []
        for card in self.cards:
            if not card.entity.is_minion or not card.can_attack_minion:
                continue
            std = card.std_attack
            if std <= 0:
                continue
            per_turn = card.attacks_per_turn
            used = (
                effective_attacks_this_turn(card.entity, active_turn=self.active_turn)
                if self.active_turn else 0
            )
            remaining = max(per_turn - used, 0)
            for _ in range(remaining):
                result.append((card.entity, std))
        return result

    def face_hit_damages(self) -> List[int]:
        """无嘲讽时每次打脸攻击的伤害列表（用于圣盾模拟）"""
        from .secret_attack_board import player_has_crusader_aura, stamp_crusader_aura_on_fighter
        from .rush_combat import stamp_fighter_attack_effects, simulate_minion_face_hits
        from .spell_board import entity_is_beast

        hits: List[int] = []
        secret_active = False
        if self.game_state is not None and self.player_id is not None:
            secret_active = player_has_crusader_aura(self.game_state, self.player_id)
        if self.hero and self.hero.include:
            hero_entity = self.hero.entity
            weapon_entity = self.hero.weapon.entity if self.hero.weapon else None
            spirit_n = count_board_team_spirit(self.game_state, self.player_id)
            if hero_weapon_can_face(hero_entity, weapon_entity):
                if weapon_entity and _std_attack(weapon_entity) > 0:
                    w_atk = hero_weapon_strike_damage(
                        hero_entity, weapon_entity, team_spirit_count=spirit_n,
                    )
                    if w_atk != INFINITE_ATK:
                        silenced = is_silenced(hero_entity)
                        per_turn = attacks_per_turn(hero_entity, silenced)
                        used = (
                            effective_attacks_this_turn(
                                hero_entity, active_turn=self.active_turn,
                            )
                            if self.active_turn else 0
                        )
                        remaining = max(per_turn - used, 0)
                        dur = _weapon_health(weapon_entity)
                        for _ in range(min(remaining, dur)):
                            hits.append(w_atk)
                elif self.hero.attack > 0:
                    hits.append(self.hero.attack)
        minion_fighters: List[dict] = []
        for card in self.cards:
            if not card.entity.is_minion:
                continue
            if not card.can_attack_minion and not card.can_attack_hero:
                continue
            std = card.std_attack
            if std <= 0:
                continue
            per_turn = card.attacks_per_turn
            used = (
                effective_attacks_this_turn(card.entity, active_turn=self.active_turn)
                if self.active_turn else 0
            )
            remaining = max(per_turn - used, 0)
            if remaining <= 0:
                continue
            cid = card.entity.card_id or ""
            fighter = {
                "kind": "minion",
                "entity_id": card.entity.entity_id,
                "card_id": cid,
                "atk": std,
                "health": max(card.entity.current_health, 1),
                "attacks_left": remaining,
                "can_face": card.can_attack_hero,
                "beast": entity_is_beast(card.entity),
            }
            stamp_fighter_attack_effects(fighter, cid)
            if self.game_state is not None and self.player_id is not None:
                stamp_crusader_aura_on_fighter(fighter, self.game_state, self.player_id)
            minion_fighters.append(fighter)
        hits.extend(simulate_minion_face_hits(minion_fighters, secret_active=secret_active))
        return hits

    def face_attack_damage_no_taunt(self, defender_has_divine_shield: bool = False) -> int:
        """无嘲讽时场面可打脸伤害（可选计入防守方英雄圣盾）"""
        return apply_divine_shield_to_hits(
            self.face_hit_damages(), defender_has_divine_shield
        )


def _pick_weapon(entities: List["Entity"]) -> Optional["Entity"]:
    weapons = [
        e for e in entities
        if e.is_weapon and entity_zone(e) == "PLAY" and e.current_durability > 0
    ]
    if not weapons:
        return None
    if len(weapons) == 1:
        return weapons[0]
    for w in weapons:
        if _tag(w, "JUST_PLAYED"):
            return w
    return weapons[0]


def build_player_board(
    game_state: "GameState",
    player_id: int,
    active_turn: Optional[bool] = None,
    *,
    for_overlay: bool = False,
) -> PlayerBoardView:
    if active_turn is None:
        active_turn = (
            board_active_turn_for_display(game_state, player_id)
            if for_overlay
            else is_players_turn(game_state, player_id)
        )

    raw = [
        e for e in list(game_state.entities.values())
        if game_state.is_entity_controlled_by(e, player_id) and entity_zone(e) == "PLAY"
    ]
    filtered = [
        e for e in raw
        if entity_cardtype(e) not in ("PLAYER", "ENCHANTMENT", "HERO_POWER")
        and entity_zone(e) not in _EXCLUDED_ZONES
    ]

    hero_entity = game_state.get_hero(player_id)
    weapon_entity = game_state.get_weapon(player_id)
    if weapon_entity is None:
        weapon_entity = _pick_weapon(filtered)

    cards: List[BoardCardView] = []
    hero_view: Optional[BoardHeroView] = None

    if hero_entity:
        spirit_n = count_board_team_spirit(game_state, player_id)
        hero_view = build_board_hero(
            hero_entity, weapon_entity, active_turn, team_spirit_count=spirit_n,
        )
        cards.append(hero_view.hero)

    for e in game_state.get_board(player_id):
        cards.append(build_board_card(e, active_turn, game_state))

    return PlayerBoardView(
        hero=hero_view,
        cards=cards,
        active_turn=active_turn,
        player_id=player_id,
        game_state=game_state,
    )
