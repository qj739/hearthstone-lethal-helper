# end_turn_board.py — 回合结束触发（场攻/斩杀）

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING

from .board_damage import (
    apply_divine_shield_to_hits,
    entity_cardtype,
    entity_zone,
    is_dormant,
    is_silenced,
    is_players_turn,
)

if TYPE_CHECKING:
    from .power_parser import GameState


class EtKind(str, Enum):
    HERO_DAMAGE = "hero_damage"
    ALL_ENEMIES_DAMAGE = "all_enemies_damage"
    RANDOM_SPLIT_ENEMIES = "random_split_enemies"
    # 仅随机敌方随从：永不计入打脸（如窜逃的黑翼龙）
    RANDOM_ENEMY_MINION = "random_enemy_minion"
    SUMMON_ATTACK = "summon_attack"
    SUMMON_ATTACK_RANDOM = "summon_attack_random"
    SUMMON_ATTACK_MULTI = "summon_attack_multi"
    ATTACK_LOWEST_ENEMY = "attack_lowest_enemy"
    ATTACK_RANDOM_MINION_OVERFLOW = "attack_random_minion_overflow"


@dataclass(frozen=True)
class EndTurnDef:
    kind: EtKind
    amount: int = 0
    summon_atk: int = 0
    summon_health: int = 0
    summon_count: int = 1
    uses_self_atk: bool = False
    requires_dormant: bool = False
    requires_secret: bool = False
    uses_random: bool = False
    name: str = ""


END_TURN_BY_CARD: Dict[str, EndTurnDef] = {
    "TOY_647": EndTurnDef(  # 8费 12/12
        EtKind.ALL_ENEMIES_DAMAGE, amount=3,
        requires_dormant=True, name="玛瑟里顿",
    ),
    # 4费 4/4：回合结束若控制奥秘，对所有敌人（含英雄）造成 2 点伤害
    "REV_513": EndTurnDef(
        EtKind.ALL_ENEMIES_DAMAGE, amount=2,
        requires_secret=True, name="健谈的调酒师",
    ),
    "TOY_601": EndTurnDef(  # 10费 6/7；token TOY_601t2 6/7
        EtKind.SUMMON_ATTACK_RANDOM, summon_atk=6, summon_health=7,
        uses_random=True, name="工厂装配机",
    ),
    "TOY_601t": EndTurnDef(  # 微缩 1费 1/1；同样召唤 TOY_601t2 6/7 随机攻击
        EtKind.SUMMON_ATTACK_RANDOM, summon_atk=6, summon_health=7,
        uses_random=True, name="工厂装配机(微缩)",
    ),
    "RLK_720": EndTurnDef(  # 6费 5/6
        EtKind.ATTACK_LOWEST_ENEMY, uses_self_atk=True, name="侏儒嚼嚼怪",
    ),
    "RLK_706": EndTurnDef(  # 7费 7/7
        EtKind.HERO_DAMAGE, amount=3, name="莫格莱尼",
    ),
    "CORE_RLK_706": EndTurnDef(  # 7费 7/7
        EtKind.HERO_DAMAGE, amount=3, name="莫格莱尼",
    ),
    "SCH_337": EndTurnDef(  # 8费 6/8；召唤 2×3/3
        EtKind.SUMMON_ATTACK_MULTI, summon_atk=3, summon_health=3,
        summon_count=2, uses_random=True, name="问题学生",
    ),
    "EDR_453": EndTurnDef(  # 10费 12/7
        EtKind.ATTACK_RANDOM_MINION_OVERFLOW, uses_self_atk=True,
        uses_random=True, name="棘嗣幼龙",
    ),
    "CATA_475": EndTurnDef(  # 6费 3/6
        EtKind.ALL_ENEMIES_DAMAGE, amount=2, name="破鳞盾卫",
    ),
    "AV_340": EndTurnDef(  # 8费 9/7
        EtKind.ALL_ENEMIES_DAMAGE, amount=2, name="亮铜之翼",
    ),
    "CORE_BT_493": EndTurnDef(  # 7费 6/7
        EtKind.RANDOM_SPLIT_ENEMIES, amount=6, name="愤怒的女祭司",
    ),
    "BT_493": EndTurnDef(  # 7费 6/7
        EtKind.RANDOM_SPLIT_ENEMIES, amount=6, name="愤怒的女祭司",
    ),
    "CATA_999": EndTurnDef(  # 5费 4/4
        EtKind.HERO_DAMAGE, amount=4, name="土石幼龙",
    ),
    # 回合结束：随机对一个敌方随从造成 10 点伤害（不能打英雄）
    "YOP_034": EndTurnDef(
        EtKind.RANDOM_ENEMY_MINION, amount=10, uses_random=True, name="窜逃的黑翼龙",
    ),
    "CORE_YOP_034": EndTurnDef(
        EtKind.RANDOM_ENEMY_MINION, amount=10, uses_random=True, name="窜逃的黑翼龙",
    ),
}


# 场面存在时，场攻搜索需额外评估「我方随从本回合不攻击」以保留敌方随从作溢出目标
HOLD_ATTACK_FOR_END_TURN_OVERFLOW_IDS = frozenset({"EDR_453"})

# 红牌：已唤醒时可优先考虑对其休眠以触发回合结束（玛瑟里顿等）
RED_CARD_FRIENDLY_WAKE_BENEFIT_IDS = frozenset({
    "TOY_647",  # 玛瑟里顿
})


class SimEndTurnMinion:
    """模拟当回合从手牌打出的回合结束随从（供 end_turn_face_damage 读取）。"""

    __slots__ = ("card_id", "atk", "current_health", "zone", "tags")

    def __init__(self, card_id: str, atk: int, health: int):
        self.card_id = card_id
        self.atk = atk
        self.current_health = health
        self.zone = "PLAY"
        self.tags = {"ATK": atk, "HEALTH": health, "ZONE": "PLAY"}


class SimFighterEndTurnEntity:
    """法术模拟中 fighters dict → 回合结束检测用伪实体。"""

    __slots__ = ("entity_id", "card_id", "atk", "current_health", "zone", "tags")

    def __init__(self, fighter: dict):
        self.entity_id = fighter.get("entity_id")
        self.card_id = fighter.get("card_id", "") or ""
        self.atk = int(fighter.get("atk", 0) or 0)
        self.current_health = int(fighter.get("health", 0) or 0)
        self.zone = "PLAY"
        self.tags = {
            "ATK": self.atk,
            "HEALTH": self.current_health,
            "ZONE": "PLAY",
            "DORMANT": 1 if fighter.get("dormant") else 0,
        }


def has_hold_attack_end_turn_on_board(friendly_board_entities: List) -> bool:
    """场上是否有需考虑「随从不攻击」的回合结束随从。"""
    for entity in friendly_board_entities:
        if not _entity_alive_on_board(entity):
            continue
        cid = getattr(entity, "card_id", "") or ""
        if cid in HOLD_ATTACK_FOR_END_TURN_OVERFLOW_IDS:
            return True
        if cid.startswith("CORE_") and cid[5:] in HOLD_ATTACK_FOR_END_TURN_OVERFLOW_IDS:
            return True
    return False


def has_hold_attack_end_turn_in_fighters(fighters: List[dict]) -> bool:
    """模拟场面（含本回合 sim_summon）是否含上述随从。"""
    for f in fighters:
        if f.get("health", 0) <= 0:
            continue
        cid = f.get("card_id", "") or ""
        if cid in HOLD_ATTACK_FOR_END_TURN_OVERFLOW_IDS:
            return True
        if cid.startswith("CORE_") and cid[5:] in HOLD_ATTACK_FOR_END_TURN_OVERFLOW_IDS:
            return True
    return False


def end_turn_face_from_fighters(
    fighters: List[dict],
    enemy_board: List[dict],
    defender_shield: bool,
    *,
    game_state: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> int:
    """法术/交换模拟后，从 fighters 估算回合结束追加打脸。"""
    entities: List = []
    seen_eids: set = set()
    for f in fighters:
        if f.get("health", 0) <= 0:
            continue
        if f.get("silenced"):
            continue
        cid = f.get("card_id", "") or ""
        if not _resolve_end_turn_def(cid):
            continue
        eid = f.get("entity_id")
        if eid is not None:
            if eid in seen_eids:
                continue
            seen_eids.add(eid)
        entities.append(SimFighterEndTurnEntity(f))
    if not entities:
        return 0
    face, _ = end_turn_face_damage(
        entities, enemy_board, defender_shield,
        game_state=game_state, player_id=player_id,
    )
    return face


def sim_end_turn_entities_from_fighters(fighters: Optional[List[dict]]) -> List:
    """
    本回合 fighters 中的回合结束源：
    - sim_summon：手牌打出尚未落场的 token
    - 其余（如红牌休眠玛瑟里顿）：用 SimFighterEndTurnEntity 覆盖场面休眠状态
    """
    if not fighters:
        return []
    out: List = []
    seen_eids: set = set()
    for f in fighters:
        if f.get("health", 0) <= 0:
            continue
        if f.get("silenced"):
            continue
        cid = f.get("card_id", "") or ""
        if not _resolve_end_turn_def(cid):
            continue
        eid = f.get("entity_id")
        if eid is not None:
            if eid in seen_eids:
                continue
            seen_eids.add(eid)
        if f.get("sim_summon"):
            out.append(SimEndTurnMinion(
                cid, int(f.get("atk", 0) or 0), int(f.get("health", 0) or 0),
            ))
        else:
            out.append(SimFighterEndTurnEntity(f))
    return out


def _fighter_end_turn_override_eids(extra_board_entities: Optional[List]) -> set:
    if not extra_board_entities:
        return set()
    return {
        ent.entity_id for ent in extra_board_entities
        if isinstance(ent, SimFighterEndTurnEntity) and ent.entity_id is not None
    }


def merge_board_entities_for_end_turn(
    friendly_board_entities: List,
    extra: Optional[List],
) -> List:
    if not extra:
        return list(friendly_board_entities)
    return list(friendly_board_entities) + list(extra)


# 战吼后永久附着英雄：RLK_706e3「Mograine's Migraine」
MOGRAINE_AURA_ENCHANT_IDS = frozenset({"RLK_706e3"})


def has_mograine_end_turn_aura(
    game_state: Optional["GameState"],
    player_id: Optional[int],
) -> bool:
    """战吼已触发：英雄附着 RLK_706e3，本体离场后仍每回合结束 +3。"""
    if game_state is None or player_id is None:
        return False
    hero = game_state.get_hero(player_id)
    if hero is None:
        return False
    hero_eid = hero.entity_id
    for entity in list(game_state.entities.values()):
        if entity_cardtype(entity) != "ENCHANTMENT":
            continue
        cid = entity.card_id or ""
        if cid not in MOGRAINE_AURA_ENCHANT_IDS:
            continue
        if int(entity.tags.get("ATTACHED", 0) or 0) == hero_eid:
            return True
    return False


def _mograine_on_board(friendly_board_entities: List) -> bool:
    for entity in friendly_board_entities:
        if not _entity_alive_on_board(entity):
            continue
        cid = getattr(entity, "card_id", "") or ""
        if cid in ("RLK_706", "CORE_RLK_706"):
            return True
    return False


def _resolve_end_turn_def(card_id: str) -> Optional[EndTurnDef]:
    if not card_id:
        return None
    defn = END_TURN_BY_CARD.get(card_id)
    if defn:
        return defn
    if card_id.startswith("CORE_"):
        return END_TURN_BY_CARD.get(card_id[5:])
    return END_TURN_BY_CARD.get("CORE_" + card_id)


def player_controls_secret(
    game_state: Optional["GameState"],
    player_id: Optional[int],
) -> bool:
    """己方 SECRET 区是否有奥秘（健谈的调酒师等条件）。"""
    if game_state is None or player_id is None:
        return False
    for e in game_state.get_player_entities(player_id, "SECRET"):
        if int(e.tags.get("SECRET", 0) or 0) == 1:
            return True
        # 部分日志未打 SECRET 标记：SECRET 区的法术仍视为奥秘
        ctype = (getattr(e, "cardtype", None) or e.tags.get("CARDTYPE") or "")
        if str(ctype).upper() == "SPELL":
            return True
    return False


def _skip_for_missing_secret(
    defn: EndTurnDef,
    game_state: Optional["GameState"],
    player_id: Optional[int],
) -> bool:
    """requires_secret 且当前未控制奥秘时跳过。"""
    if not defn.requires_secret:
        return False
    return not player_controls_secret(game_state, player_id)


def _living_enemy_minions(enemy_board: List[dict]) -> List[dict]:
    return [
        m for m in enemy_board
        if m.get("health", 0) > 0 and m.get("kind") not in ("hero", "sim_meta")
    ]


def _attackable_enemy_minions(enemy_board: List[dict]) -> List[dict]:
    """可被攻击的敌方随从（休眠随从不可被选为攻击目标）。"""
    from .combat_sim import unit_is_dormant

    return [
        m for m in _living_enemy_minions(enemy_board)
        if not unit_is_dormant(m)
    ]


def _living_enemy_taunts(enemy_board: List[dict]) -> List[dict]:
    return [
        m for m in _living_enemy_minions(enemy_board)
        if m.get("taunt")
    ]


def _entity_std_atk(entity) -> int:
    atk = getattr(entity, "atk", None)
    if atk is not None:
        return max(int(atk), 0)
    return max(int(entity.tags.get("ATK", 0) or 0), 0)


def _summon_attack_face(
    atk: int,
    enemy_board: List[dict],
    defender_shield: bool,
) -> int:
    """召唤物当回合攻击一次：无嘲讽打脸，有嘲讽则打第一个嘲讽。"""
    taunts = _living_enemy_taunts(enemy_board)
    if not taunts:
        return apply_divine_shield_to_hits([atk], defender_shield)
    target = taunts[0]
    if target.get("shield"):
        target["shield"] = False
        return 0
    target["health"] = target.get("health", 0) - atk
    return 0


def _summon_attack_random_face(
    atk: int,
    enemy_board: List[dict],
    defender_shield: bool,
    *,
    rng: Optional[random.Random] = None,
) -> int:
    """
    随机攻击一个敌人（英雄 + 所有存活随从，无视嘲讽）。
    无 rng 时取乐观上界（必打脸）。
    """
    if atk <= 0:
        return 0
    living = _living_enemy_minions(enemy_board)
    if rng is None:
        return apply_divine_shield_to_hits([atk], defender_shield)
    # None 表示英雄
    pool: List[Optional[dict]] = [None]
    pool.extend(living)
    target = rng.choice(pool)
    if target is None:
        return apply_divine_shield_to_hits([atk], defender_shield)
    if target.get("shield"):
        target["shield"] = False
        return 0
    target["health"] = target.get("health", 0) - atk
    return 0


def _opponent_hero_health(
    game_state: Optional["GameState"],
    player_id: Optional[int],
) -> Optional[int]:
    if game_state is None or player_id is None:
        return None
    opp = game_state.opponent_player_id
    if opp is None:
        return None
    hero = game_state.get_hero(opp)
    if hero is None:
        return None
    return max(0, hero.current_health + hero.tags.get("ARMOR", 0))


def _attack_lowest_enemy_face(
    atk: int,
    enemy_board: List[dict],
    defender_shield: bool,
    *,
    hero_health: Optional[int] = None,
) -> int:
    """攻击生命值最低的敌人（含英雄）；场上无随从且英雄更高血时仍可能打脸。"""
    living = _attackable_enemy_minions(enemy_board)
    hero_hp = hero_health
    if hero_hp is None:
        hero_hp = 10**9
    if not living:
        return apply_divine_shield_to_hits([atk], defender_shield)
    lowest_minion_hp = min(m.get("health", 0) for m in living)
    if hero_hp <= lowest_minion_hp:
        return apply_divine_shield_to_hits([atk], defender_shield)
    target = min(living, key=lambda m: m.get("health", 0))
    if target.get("shield"):
        target["shield"] = False
        return 0
    target["health"] = target.get("health", 0) - atk
    return 0


def _attack_random_minion_overflow_face(
    atk: int,
    enemy_board: List[dict],
    defender_shield: bool,
    *,
    rng: Optional[random.Random] = None,
) -> int:
    """
    随机攻击敌方随从，溢出打脸。
    休眠随从不可被选为目标；无 rng 时在可攻击随从中取溢出最大的目标（乐观上界）。
    圣盾：与 Explosive Runes / 棘嗣幼龙等一致，溢出按随从当前血量计算
    （3/3 圣盾 + 12 攻 → 9 打脸），而非整次攻击被圣盾吸收为 0。
    """
    living = _attackable_enemy_minions(enemy_board)
    if not living or atk <= 0:
        return 0
    if rng is not None:
        target = rng.choice(living)
        hp = target.get("health", 0)
        overflow = max(atk - hp, 0)
        if target.get("shield"):
            target["shield"] = False
        else:
            target["health"] = hp - atk
        if overflow <= 0:
            return 0
        return apply_divine_shield_to_hits([overflow], defender_shield)
    best_overflow = 0
    for target in living:
        hp = target.get("health", 0)
        overflow = max(atk - hp, 0)
        if overflow > best_overflow:
            best_overflow = overflow
    if best_overflow <= 0:
        return 0
    return apply_divine_shield_to_hits([best_overflow], defender_shield)


def _random_split_enemies_face(
    amount: int,
    enemy_board: List[dict],
    defender_shield: bool,
) -> int:
    """随机分配到所有敌人；斩杀模拟乐观上界 = 全部打脸。"""
    if amount <= 0:
        return 0
    return apply_divine_shield_to_hits([amount], defender_shield)


def _entity_alive_on_board(entity) -> bool:
    return (
        getattr(entity, "current_health", 0) > 0
        and getattr(entity, "zone", "") == "PLAY"
    )


def _dormant_awaken_enchant(game_state: "GameState", host_eid: int):
    """挂在休眠随从上的唤醒倒计时附魔（如玛瑟 TOY_647e2 清扫）。"""
    for e in list(game_state.entities.values()):
        if int(e.tags.get("ATTACHED", 0) or 0) != host_eid:
            continue
        if int(e.tags.get("DORMANT_AWAKEN_CONDITION_ENCHANT", 0) or 0) != 1:
            continue
        if entity_zone(e) not in ("PLAY", "SETASIDE"):
            continue
        return e
    return None


def dormant_awakens_at_next_turn_start(
    entity,
    game_state: Optional["GameState"],
) -> bool:
    """
    下一回合开始（MAIN_START_TRIGGERS）时是否会苏醒。

    休眠倒计时附魔：SCORE_VALUE_1=总回合，SCORE_VALUE_2=已过回合；
    每回合开始 +1，达到 SCORE_VALUE_1 时苏醒。玛瑟里顿在对手回合
    SCORE_VALUE_2 通常已为 1，轮到我方时开局即醒，不再触发休眠回合结束。
    """
    if game_state is None:
        return False
    eid = getattr(entity, "entity_id", None)
    if eid is None:
        return False
    enchant = _dormant_awaken_enchant(game_state, int(eid))
    if enchant is None:
        return False
    total = int(enchant.tags.get("SCORE_VALUE_1", 0) or 0)
    if total <= 0:
        return False
    progress = int(enchant.tags.get("SCORE_VALUE_2", 0) or 0)
    return progress + 1 >= total


def _skip_dormant_end_turn_next_turn_preview(
    entity,
    defn: EndTurnDef,
    game_state: Optional["GameState"],
    player_id: Optional[int],
) -> bool:
    """对方回合预览下回合时：若休眠随从会在开局苏醒，则不计其回合结束。"""
    if not defn.requires_dormant:
        return False
    if game_state is None or player_id is None:
        return False
    # 仅在「当前不是该玩家回合」时做下回合预览
    if is_players_turn(game_state, player_id):
        return False
    return dormant_awakens_at_next_turn_start(entity, game_state)


def _end_turn_def_uses_random(defn: Optional[EndTurnDef], *, dormant: bool = False) -> bool:
    return bool(
        defn
        and defn.uses_random
        and (not defn.requires_dormant or dormant)
    )


def end_turn_uses_random(friendly_board_entities: List) -> bool:
    """场上是否有带随机目标的回合结束效果。"""
    for entity in friendly_board_entities:
        if not _entity_alive_on_board(entity):
            continue
        if is_silenced(entity):
            continue
        defn = _resolve_end_turn_def(getattr(entity, "card_id", "") or "")
        if _end_turn_def_uses_random(
            defn, dormant=is_dormant(entity),
        ):
            return True
    return False


def end_turn_uses_random_fighters(fighters: Optional[List[dict]]) -> bool:
    """模拟场面（含本回合 sim_summon）是否含随机回合结束源。"""
    if not fighters:
        return False
    for f in fighters:
        if f.get("health", 0) <= 0:
            continue
        if f.get("silenced"):
            continue
        defn = _resolve_end_turn_def(f.get("card_id", "") or "")
        if _end_turn_def_uses_random(
            defn, dormant=bool(f.get("dormant")),
        ):
            return True
    return False


def _apply_end_turn_def(
    defn: EndTurnDef,
    entity,
    enemy_board: List[dict],
    defender_shield: bool,
    *,
    rng: Optional[random.Random] = None,
    hero_health: Optional[int] = None,
) -> int:
    if defn.kind == EtKind.HERO_DAMAGE:
        return apply_divine_shield_to_hits([defn.amount], defender_shield)
    if defn.kind == EtKind.ALL_ENEMIES_DAMAGE:
        return apply_divine_shield_to_hits([defn.amount], defender_shield)
    if defn.kind == EtKind.RANDOM_SPLIT_ENEMIES:
        return _random_split_enemies_face(defn.amount, enemy_board, defender_shield)
    if defn.kind == EtKind.RANDOM_ENEMY_MINION:
        # 文本为「敌方随从」：无溢出、不选英雄，场攻贡献恒为 0
        return 0
    if defn.kind == EtKind.SUMMON_ATTACK:
        return _summon_attack_face(defn.summon_atk, enemy_board, defender_shield)
    if defn.kind == EtKind.SUMMON_ATTACK_RANDOM:
        return _summon_attack_random_face(
            defn.summon_atk, enemy_board, defender_shield, rng=rng,
        )
    if defn.kind == EtKind.SUMMON_ATTACK_MULTI:
        total = 0
        for _ in range(max(defn.summon_count, 1)):
            if defn.uses_random:
                total += _summon_attack_random_face(
                    defn.summon_atk, enemy_board, defender_shield, rng=rng,
                )
            else:
                total += _summon_attack_face(
                    defn.summon_atk, enemy_board, defender_shield,
                )
        return total
    atk = _entity_std_atk(entity) if defn.uses_self_atk else defn.amount
    if defn.kind == EtKind.ATTACK_LOWEST_ENEMY:
        return _attack_lowest_enemy_face(
            atk, enemy_board, defender_shield, hero_health=hero_health,
        )
    if defn.kind == EtKind.ATTACK_RANDOM_MINION_OVERFLOW:
        return _attack_random_minion_overflow_face(
            atk, enemy_board, defender_shield, rng=rng,
        )
    return 0


def end_turn_face_damage(
    friendly_board_entities: List,
    enemy_board: List[dict],
    defender_shield: bool,
    *,
    game_state: Optional["GameState"] = None,
    player_id: Optional[int] = None,
    rng: Optional[random.Random] = None,
    extra_board_entities: Optional[List] = None,
    opponent_hero_hp: Optional[int] = None,
) -> Tuple[int, List[str]]:
    """
    回合结束追加打脸（在当回合攻击/法术模拟之后结算）。
    返回 (打脸伤害, 来源说明列表)。
    opponent_hero_hp：模拟线内已打脸后的英雄有效生命（侏儒嚼嚼怪等选目标用）。
    """
    override_eids = _fighter_end_turn_override_eids(extra_board_entities)
    board_entities = merge_board_entities_for_end_turn(
        friendly_board_entities, extra_board_entities,
    )
    if opponent_hero_hp is not None:
        hero_health = max(0, int(opponent_hero_hp))
    else:
        hero_health = _opponent_hero_health(game_state, player_id)
    total = 0
    notes: List[str] = []
    for entity in board_entities:
        if not _entity_alive_on_board(entity):
            continue
        if is_silenced(entity):
            continue
        eid = getattr(entity, "entity_id", None)
        if (
            eid is not None
            and eid in override_eids
            and not isinstance(entity, SimFighterEndTurnEntity)
        ):
            continue
        defn = _resolve_end_turn_def(getattr(entity, "card_id", "") or "")
        if defn is None:
            continue
        if defn.requires_dormant and not is_dormant(entity):
            continue
        if _skip_for_missing_secret(defn, game_state, player_id):
            continue
        if _skip_dormant_end_turn_next_turn_preview(
            entity, defn, game_state, player_id,
        ):
            continue

        face = _apply_end_turn_def(
            defn, entity, enemy_board, defender_shield, rng=rng,
            hero_health=hero_health,
        )
        total += face
        if face > 0:
            notes.append(f"回合结束:{defn.name or entity.card_id}+{face}")

    if (
        not _mograine_on_board(friendly_board_entities)
        and has_mograine_end_turn_aura(game_state, player_id)
    ):
        face = apply_divine_shield_to_hits([3], defender_shield)
        total += face
        if face > 0:
            notes.append(f"回合结束:莫格莱尼光环+{face}")

    return total, notes


def board_end_turn_face_now(
    friendly_board_entities: List,
    enemy_board: List[dict],
    defender_shield: bool,
    *,
    game_state: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> int:
    """
    当前场面下、本回合结束可预估的打脸伤害。
    随从刚变形/召唤上场（当回合不能攻击）时也应立即计入。
    """
    face, _ = end_turn_face_damage(
        friendly_board_entities,
        enemy_board,
        defender_shield,
        game_state=game_state,
        player_id=player_id,
    )
    return face


def board_dormant_end_turn_face_now(
    friendly_board_entities: List,
    enemy_board: List[dict],
    defender_shield: bool,
    *,
    game_state: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> int:
    """仅休眠随从触发的回合结束打脸（如玛瑟里顿 +3），不计入 Overlay 场攻展示。"""
    hero_health = _opponent_hero_health(game_state, player_id)
    total = 0
    for entity in friendly_board_entities:
        if not _entity_alive_on_board(entity):
            continue
        if is_silenced(entity):
            continue
        defn = _resolve_end_turn_def(getattr(entity, "card_id", "") or "")
        if defn is None or not defn.requires_dormant or not is_dormant(entity):
            continue
        if _skip_dormant_end_turn_next_turn_preview(
            entity, defn, game_state, player_id,
        ):
            continue
        total += _apply_end_turn_def(
            defn, entity, enemy_board, defender_shield,
            hero_health=hero_health,
        )
    return total


def end_turn_names_on_board(
    friendly_board_entities: List,
    *,
    game_state: Optional["GameState"] = None,
    player_id: Optional[int] = None,
) -> List[str]:
    """场上已注册回合结束源的显示名。"""
    names: List[str] = []
    for entity in friendly_board_entities:
        if not _entity_alive_on_board(entity):
            continue
        defn = _resolve_end_turn_def(getattr(entity, "card_id", "") or "")
        if not defn:
            continue
        if defn.requires_dormant and not is_dormant(entity):
            continue
        if _skip_for_missing_secret(defn, game_state, player_id):
            continue
        if _skip_dormant_end_turn_next_turn_preview(
            entity, defn, game_state, player_id,
        ):
            continue
        names.append(defn.name or entity.card_id or "回合结束")
    return names
