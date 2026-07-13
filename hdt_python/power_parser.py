# power_parser.py - Power.log 解析器（仿照 HDT 的 PowerHandler）

import os
import re
from typing import Optional, Dict, Callable
from dataclasses import dataclass
from .log_watcher import LogWatcher
from .player_identity import (
    is_real_battle_tag,
    name_matches_env_override,
    optional_env_player_names,
)
from .board_damage import (
    is_board_entity,
    entity_zone,
    entity_cardtype,
    collect_board_minions,
    build_player_board,
    build_board_card,
    is_players_turn,
    board_active_turn_for_display,
    attacks_per_turn,
    attacks_this_turn,
)


# ========================================
# 预编译的正则表达式（性能优化，仿照HDT）
# ========================================

# 英雄卡 ID（HERO_11、HERO_03a）；排除 HERO_11bp / HERO_11bpt 等技能与衍生物
_HERO_CARD_ID = re.compile(r"^HERO_\d{2}[a-z]?$")


class PowerRegex:
    """预编译的正则表达式模式"""

    # 方括号实体（名称里可能含 [cardType=INVALID] 等嵌套方括号）
    _BRACKET_ENTITY = r"\[(?:[^\[\]]|\[[^\]]*\])*?\]"

    # 实体创建
    FULL_ENTITY = re.compile(
        r"FULL_ENTITY\s+-\s+(?:Creating|Updating)\s+(?:ID=(?P<id>\d+)|(?P<bracket>"
        + _BRACKET_ENTITY
        + r"))"
        r"(?:\s+CardID=(?P<card_id>[\w_]*))?"
    )

    # 实体显示（CardID 常在 ] 之后，与 ENTITY_BRACKET 配合解析）
    SHOW_ENTITY = re.compile(
        r"SHOW_ENTITY\s+-\s+Updating\s+Entity=(?P<entity>(?:"
        + _BRACKET_ENTITY
        + r"|\d+))"
        r"(?:\s+CardID=(?P<card_id>[\w_]*))?"
    )

    # 实体变形（妖术、变形术等）
    CHANGE_ENTITY = re.compile(
        r"CHANGE_ENTITY\s+-\s+Updating\s+Entity=(?P<entity>(?:"
        + _BRACKET_ENTITY
        + r"|\d+))"
        r"(?:\s+CardID=(?P<card_id>[\w_]*))?"
    )

    # 标签变化
    TAG_CHANGE = re.compile(
        r"TAG_CHANGE\s+Entity=(?P<entity>.+?)\s+tag=(?P<tag>\w+)\s+value=(?P<value>[\-\w]+)"
    )

    # 行内标签
    TAG = re.compile(r"tag=(?P<tag>\w+)\s+value=(?P<value>[\-\w]+)")

    # 实体隐藏
    HIDE_ENTITY = re.compile(r"HIDE_ENTITY\s+-\s+(?:Entity=)?(?P<entity>.+?)\s+tag")

    # 方块开始/结束
    BLOCK_START = re.compile(r"BLOCK_START\s+BlockType=(?P<type>\w+)")
    BLOCK_END = re.compile(r"BLOCK_END")

    # 方括号实体描述
    ENTITY_BRACKET = re.compile(
        r"\[.*?id=(?P<id>\d+)"
        r"(?:\s+zone=(?P<zone>\w+))?"
        r"(?:\s+zonePos=(?P<zone_pos>\d+))?"
        r"(?:\s+cardId=(?P<card_id>[\w_]*))?"
        r"(?:\s+player=(?P<player>\d+))?"
    )

    # 游戏实体
    GAME_ENTITY = re.compile(r"GameEntity\s+EntityID=(?P<id>\d+)")

    # 玩家实体
    PLAYER_ENTITY = re.compile(r"Player\s+EntityID=(?P<id>\d+)\s+PlayerID=(?P<player_id>\d+)")


# ========================================
# 实体和游戏状态
# ========================================

@dataclass
class Entity:
    """游戏实体"""
    entity_id: int
    card_id: Optional[str] = None
    controller: Optional[int] = None
    controller_uses_entity_id: bool = False
    zone: Optional[str] = None
    zone_pos: Optional[int] = None
    cardtype: Optional[str] = None
    cost: int = 0
    atk: int = 0
    health: int = 0
    damage: int = 0
    durability: int = 0

    # 标签
    tags: Dict[str, int] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = {}

    @property
    def current_health(self) -> int:
        return max(0, self.health - self.damage)

    @property
    def current_durability(self) -> int:
        """武器耐久（日志里常用 HEALTH 表示耐久）。"""
        if self.is_weapon:
            base = self.durability if self.durability > 0 else self.health
            return max(0, base - self.damage)
        return max(0, self.durability - self.damage)

    @property
    def effective_controller(self) -> Optional[int]:
        """当前控制者（以 CONTROLLER 标签为准，对齐 HDT/hslog）"""
        if "CONTROLLER" in self.tags:
            return self.tags["CONTROLLER"]
        return self.controller

    def is_controlled_by(self, player_id: int, game_state: Optional["GameState"] = None) -> bool:
        if game_state is not None:
            return game_state.is_entity_controlled_by(self, player_id)
        ctrl = self.effective_controller
        return ctrl is not None and ctrl == player_id

    @property
    def is_minion(self) -> bool:
        if self.cardtype in ("MINION", "TOKEN"):
            return True
        if self.cardtype in ("HERO", "WEAPON", "SPELL", "ENCHANTMENT", "HERO_POWER", "LOCATION", "GAME", "PLAYER"):
            return False
        # 部分衍生物日志里 CARDTYPE 未及时写入，用场面过滤兜底
        return is_board_entity(self) and entity_zone(self) == "PLAY"

    @property
    def is_spell(self) -> bool:
        return self.cardtype == "SPELL"

    @property
    def is_weapon(self) -> bool:
        return self.cardtype == "WEAPON"

    @property
    def is_hero(self) -> bool:
        if self.cardtype == "HERO":
            return True
        if self.cardtype in ("MINION", "TOKEN", "HERO_POWER", "WEAPON", "SPELL", "ENCHANTMENT"):
            return False
        cid = (self.card_id or "")
        return bool(_HERO_CARD_ID.match(cid))

    @property
    def is_board_minion(self) -> bool:
        """是否在场面上的随从（对齐 HDT BoardDamage 过滤）。"""
        return is_board_entity(self)

    def board_card_view(
        self,
        active_turn: bool = True,
        game_state: Optional["GameState"] = None,
    ):
        return build_board_card(self, active_turn, game_state)

    @property
    def can_attack(self) -> bool:
        """能否攻击随从（默认按我方回合；清嘲讽/场面用）。"""
        return self.board_card_view(True).can_attack_minion

    @property
    def can_attack_hero(self) -> bool:
        """能否对英雄造成伤害（默认按我方回合）。"""
        return self.board_card_view(True).can_attack_hero

    @property
    def remaining_attacks(self) -> int:
        from .board_damage import attacks_per_turn, effective_attacks_this_turn, is_silenced

        silenced = self.tags.get("SILENCED", 0) == 1
        per_turn = attacks_per_turn(self, silenced)
        used = effective_attacks_this_turn(self, active_turn=True)
        return max(0, per_turn - used)

    @property
    def board_attack_damage(self) -> int:
        """本随从可对英雄造成的伤害（仿 HDT 场攻语义）"""
        return self.board_card_view(True).attack if self.can_attack_hero else 0

    def hero_can_attack_with_weapon(self) -> bool:
        """英雄本回合是否还能攻击（含武器，仿 BoardHero.Include）"""
        if not self.is_hero:
            return False
        from .board_damage import _is_able_to_attack
        return _is_able_to_attack(self, True, False, True)

    def sync_attack_from_tags(self):
        """从标签同步攻击力（ATK 与 479 取较大值，4472 作回退）。"""
        from .board_damage import effective_attack_from_tags

        self.atk = effective_attack_from_tags(self.tags)

    def reset_for_new_card(self, card_id: Optional[str] = None) -> None:
        """实体 ID 复用时丢弃上一张牌的标签（后续 FULL_ENTITY 行内 tag 会重写）。"""
        if card_id is not None:
            self.card_id = card_id
        self.controller = None
        self.controller_uses_entity_id = False
        self.zone = None
        self.zone_pos = None
        self.cardtype = None
        self.cost = 0
        self.atk = 0
        self.health = 0
        self.damage = 0
        self.durability = 0
        self.tags.clear()


class GameState:
    """游戏状态（仿照HDT的Game类）"""

    def __init__(self):
        self.entities: Dict[int, Entity] = {}
        self.game_entity_id: Optional[int] = None
        self.player_ids: Dict[int, int] = {}  # entity_id -> player_id
        self.local_player_id: Optional[int] = None  # 我方玩家ID
        self.opponent_player_id: Optional[int] = None
        self.local_player_id_locked: bool = False  # 战网名/FRIENDLY_PLAYER 已锁定，手牌推断不可覆盖
        self.local_player_identity_source: Optional[str] = None  # 识别来源（调试）
        self.first_player_id: Optional[int] = None  # 先手玩家 ID（FIRST_PLAYER 标签）

        # 控制器追踪（用于备用识别）
        self.seen_controllers: set = set()
        self.player_names: Dict[int, str] = {}  # player_id -> 战网名
        self.weapon_entity_ids: Dict[int, int] = {}  # player_id -> 武器实体 id（来自 MAIN_HAND_WEAPON_ENTITY）
        self.hero_entity_ids: Dict[int, int] = {}  # player_id -> 英雄实体 id（来自 Player.HERO_ENTITY）
        self.active_player_id: Optional[int] = None  # 当前回合玩家（来自 Player 实体的 CURRENT_PLAYER=1）
        self._first_hand_reveal_done: bool = False  # FriendlyPlayerExporter 首张手牌揭示

        # 块追踪
        self.current_block_type: Optional[str] = None
        self.current_entity_id: Optional[int] = None

        # 是否处于进行中的对局（结束后为 False，避免 Overlay 显示上一场数据）
        self.in_game: bool = False

        # 战场槽位：player_id -> {zone_position(1-7) -> entity_id}（对齐 HDT 实时场面）
        self.board_slots: Dict[int, Dict[int, int]] = {}

        # FRIENDLY_PLAYER 标签值为 Player 实体 ID（2/3），待映射为 PlayerID
        self.friendly_player_entity_id: Optional[int] = None
        # 各玩家手牌曾出现的最大「已揭示 card_id」张数（对手打牌时日志会短暂暴露 card_id）
        self.revealed_hand_peak: Dict[int, int] = {1: 0, 2: 0}
        # CREATE_GAME 前 DebugPrintGame 写入的玩家名（新局 begin 时应用，避免被 reset 清掉）
        self._pre_create_player_names: Dict[int, str] = {}

    def reset(self, *, preserve_player: bool = False):
        """重置游戏状态（新游戏开始时调用）"""
        saved_local = self.local_player_id
        saved_opp = self.opponent_player_id
        saved_names = dict(self.player_names)
        saved_first = self.first_player_id

        self.entities.clear()
        self.game_entity_id = None
        self.player_ids.clear()
        self.local_player_id = None
        self.opponent_player_id = None
        self.local_player_id_locked = False
        self.local_player_identity_source = None
        self.first_player_id = None
        self.seen_controllers.clear()
        self.player_names.clear()
        self.weapon_entity_ids.clear()
        self.hero_entity_ids.clear()
        self.active_player_id = None
        self._first_hand_reveal_done = False
        self.current_block_type = None
        self.current_entity_id = None
        self.in_game = False
        self.board_slots.clear()
        self.friendly_player_entity_id = None
        self.revealed_hand_peak = {1: 0, 2: 0}
        self._pre_create_player_names = {}

        if preserve_player:
            self.local_player_id = saved_local
            self.opponent_player_id = saved_opp
            self.player_names = saved_names
            self.first_player_id = saved_first

    def begin_new_game(self):
        """CREATE_GAME：清空场面；应用本局 CREATE_GAME 前已解析的 DebugPrintGame 玩家名。"""
        pending_names = dict(self._pre_create_player_names)
        self.reset(preserve_player=False)
        self.player_names = pending_names
        self._pre_create_player_names = {}
        self.friendly_player_entity_id = None
        self.local_player_id_locked = False
        self.in_game = True

    def end_current_game(self):
        """对局结束：清空场面数据，保留玩家身份便于下一场识别"""
        self.in_game = False
        self.entities.clear()
        self.game_entity_id = None
        self.player_ids.clear()
        self.weapon_entity_ids.clear()
        self.hero_entity_ids.clear()
        self.active_player_id = None
        self.first_player_id = None
        self._first_hand_reveal_done = False
        self.current_block_type = None
        self.current_entity_id = None
        self.board_slots.clear()
        self.friendly_player_entity_id = None

    def remove_entity_from_board_slots(self, entity_id: int):
        for slots in self.board_slots.values():
            for pos, eid in list(slots.items()):
                if eid == entity_id:
                    del slots[pos]

    def get_board(self, player_id: int):
        """获取场面随从（以战场槽位表为准，过滤残留实体）"""
        from .board_damage import is_board_entity, collect_board_minions

        slots = self.board_slots.get(player_id, {})
        result = []
        stale_positions = []
        seen_entity_ids = set()
        # 快照槽位，避免解析线程与 overlay 并发修改 board_slots 时 KeyError
        for pos, eid in sorted(list(slots.items())):
            if eid in seen_entity_ids:
                stale_positions.append(pos)
                continue
            entity = self.entities.get(eid)
            if (
                entity
                and is_board_entity(entity)
                and self.is_entity_controlled_by(entity, player_id)
            ):
                result.append(entity)
                seen_entity_ids.add(eid)
            else:
                stale_positions.append(pos)
        for pos in stale_positions:
            slots.pop(pos, None)
        if not result:
            return collect_board_minions(list(self.entities.values()), player_id, self)
        # 疯狂药水等夺取：暂态 ZONE_POSITION 可能把友方随从挤出槽位表
        for entity in collect_board_minions(
            list(self.entities.values()), player_id, self,
        ):
            eid = entity.entity_id
            if eid not in seen_entity_ids and is_board_entity(entity):
                result.append(entity)
                seen_entity_ids.add(eid)
        if len(result) > 1:
            result.sort(
                key=lambda e: (
                    int(e.tags.get("ZONE_POSITION", 0) or 0),
                    e.entity_id,
                ),
            )
        return result

    def resolve_controller_to_player_id(
        self, raw: Optional[int], *, prefer_entity_id: bool = False
    ) -> Optional[int]:
        """将 CONTROLLER 标签值解析为 PlayerID（1/2）。

        FULL_ENTITY 里 CONTROLLER 与 bracket player= 一致，为 PlayerID(1/2)。
        TAG_CHANGE 改 CONTROLLER 时（如夺取控制权）多为 Player 实体 ID(2/3)。
        仅 value=2 存在歧义，需 prefer_entity_id 区分。
        """
        if raw is None:
            return None
        if prefer_entity_id and raw in self.player_ids:
            return self.player_ids[raw]
        if raw in (1, 2):
            return raw
        if raw in self.player_ids:
            return self.player_ids[raw]
        return None

    def get_entity_player_id(self, entity: Entity) -> Optional[int]:
        """实体归属的 PlayerID（1/2）"""
        raw = entity.tags.get("CONTROLLER")
        if raw is None:
            raw = entity.controller
        if raw is None:
            return None
        prefer_entity = bool(getattr(entity, "controller_uses_entity_id", False))
        return self.resolve_controller_to_player_id(raw, prefer_entity_id=prefer_entity)

    def is_entity_controlled_by(self, entity: Entity, player_id: int) -> bool:
        pid = self.get_entity_player_id(entity)
        return pid is not None and pid == player_id

    def count_revealed_hand_by_player(self) -> Dict[int, int]:
        """统计各玩家手牌中已揭示（有 card_id）的张数——客户端日志里只有我方手牌可见"""
        from .board_damage import _tag, entity_zone

        counts: Dict[int, int] = {1: 0, 2: 0}
        for e in list(self.entities.values()):
            if entity_zone(e) != "HAND":
                continue
            if not (e.card_id and str(e.card_id).strip()):
                continue
            # 对手打出随从/法术时，日志会短暂把 card_id 记在 HAND 区，需排除
            if _tag(e, "JUST_PLAYED"):
                continue
            pid = self.get_entity_player_id(e)
            if pid in counts:
                counts[pid] += 1
        return counts

    def bump_revealed_hand_peaks(self):
        """更新各玩家历史峰值，用于区分「我方整局手牌」与「对手出牌瞬间」"""
        for pid, c in self.count_revealed_hand_by_player().items():
            self.revealed_hand_peak[pid] = max(self.revealed_hand_peak.get(pid, 0), c)

    def infer_local_from_revealed_hand(self) -> Optional[int]:
        p1 = self.revealed_hand_peak.get(1, 0)
        p2 = self.revealed_hand_peak.get(2, 0)
        # 历史峰值：整局手牌可见性（对手打牌瞬间的 1 张不算）
        if p1 >= 2 and p1 > p2:
            return 1
        if p2 >= 2 and p2 > p1:
            return 2
        if p1 >= 2 and p2 == 0:
            return 1
        if p2 >= 2 and p1 == 0:
            return 2
        counts = self.count_revealed_hand_by_player()
        c1, c2 = counts[1], counts[2]
        if c1 >= 2 and c1 > c2:
            return 1
        if c2 >= 2 and c2 > c1:
            return 2
        if c1 > 0 and c2 == 0 and p1 >= 2:
            return 1
        return None

    def hand_inference_confident(self) -> bool:
        counts = self.count_revealed_hand_by_player()
        c1, c2 = counts[1], counts[2]
        if (c1 > 0) != (c2 > 0):
            return max(c1, c2) >= 1
        return max(c1, c2) >= 3 and abs(c1 - c2) >= 2

    def get_entity(self, entity_id: int) -> Entity:
        """获取实体，不存在则创建"""
        if entity_id not in self.entities:
            self.entities[entity_id] = Entity(entity_id=entity_id)
        return self.entities[entity_id]

    def get_player_entities(self, player_id: int, zone: str = "HAND"):
        """获取玩家在指定区域的实体"""
        return [
            e for e in list(self.entities.values())
            if self.is_entity_controlled_by(e, player_id) and e.zone == zone
        ]

    def get_player_board(self, player_id: int, active_turn: Optional[bool] = None, *, for_overlay: bool = False):
        """获取 HDT 风格的场面场攻视图"""
        return build_player_board(self, player_id, active_turn, for_overlay=for_overlay)

    def get_overlay_board(self, player_id: int):
        """Overlay 场攻视图（对方回合显示下回合潜力，对齐 HDT BoardState）"""
        return self.get_player_board(player_id, for_overlay=True)

    def is_local_turn(self) -> bool:
        if self.local_player_id is None:
            return True
        return is_players_turn(self, self.local_player_id)

    def board_overlay_attack(self, player_id: int) -> int:
        """Overlay 场攻数值（仿 HDT 场面攻击计数器）"""
        return self.get_overlay_board(player_id).damage

    def board_total_attack(self, player_id: int) -> int:
        """场面随从攻击力总和（不论本回合能否攻击）"""
        return sum(m.atk for m in self.get_board(player_id))

    def board_ready_attack(self, player_id: int) -> int:
        """随从本回合可对英雄造成的攻击伤害"""
        board = self.get_player_board(player_id)
        return board.minion_damage

    def weapon_attack_damage(self, player_id: int) -> int:
        """英雄本回合剩余攻击伤害（含武器，与 Overlay 场攻一致）"""
        board = self.get_overlay_board(player_id)
        return board.hero_damage

    def board_remaining_attack(self, player_id: int) -> int:
        """本回合剩余场攻（斩杀计算用）"""
        return self.get_player_board(player_id).damage

    def get_hand(self, player_id: int):
        """获取手牌"""
        from .board_damage import entity_zone

        return [
            e for e in list(self.entities.values())
            if self.is_entity_controlled_by(e, player_id)
            and entity_zone(e) == "HAND"
            and e.card_id  # 只返回已知的牌
        ]

    def get_hero(self, player_id: int) -> Optional[Entity]:
        """获取英雄（优先 Player 实体的 HERO_ENTITY 映射，不依赖 CONTROLLER 歧义）"""
        hid = self.hero_entity_ids.get(player_id)
        if hid is not None:
            hero = self.entities.get(hid)
            if hero:
                return hero
        for e in list(self.entities.values()):
            if e.is_hero and self.is_entity_controlled_by(e, player_id):
                return e
        return None

    def get_weapon(self, player_id: int) -> Optional[Entity]:
        """获取当前装备的武器（优先 MAIN_HAND_WEAPON_ENTITY）"""
        wid = self.weapon_entity_ids.get(player_id)
        if wid:
            w = self.entities.get(wid)
            if (
                w
                and self.is_entity_controlled_by(w, player_id)
                and w.zone == "PLAY"
                and (w.is_weapon or w.cardtype == "WEAPON")
                and w.current_durability > 0
            ):
                return w
            # 武器已卸下/离场，清除陈旧映射
            self.weapon_entity_ids.pop(player_id, None)
        for e in list(self.entities.values()):
            if self.is_entity_controlled_by(e, player_id) and e.is_weapon and e.zone == "PLAY":
                if e.current_durability > 0:
                    return e
        return None


# 写在 Player 战网名实体上、需同步到 Hero 的标签
_PLAYER_MANA_TAGS = frozenset({
    "RESOURCES",
    "RESOURCES_USED",
    "TEMP_RESOURCES",
    "MAXRESOURCES",
    "CORPSES",
})
# 写在 Player 战网名实体上、需同步到 Player 实体（连击等）
_PLAYER_TURN_TAGS = frozenset({
    "NUM_OPTIONS_PLAYED_THIS_TURN",
    "NUM_CARDS_PLAYED_THIS_TURN",
    "COMBO_ACTIVE",
})

# CREATE_GAME 前通常有 DebugPrintGame（PlayerName）；回放须包含这段前缀
REPLAY_PREAMBLE_LINES = 80


def find_last_game_replay_start(all_lines: list) -> int:
    """返回最后一场 CREATE_GAME 回放起点（含其前的 DebugPrintGame 前缀行）。

    优先选用 PowerTaskList 的 CREATE_GAME（与 HDT 一致，且紧跟 DebugPrintGame 玩家名）。
    """
    best_create = -1
    best_start = -1
    for i in range(len(all_lines) - 1, -1, -1):
        line = all_lines[i]
        if "CREATE_GAME" not in line:
            continue
        is_ptl = "PowerTaskList" in line
        if best_create >= 0 and not is_ptl:
            break
        preamble_start = max(0, i - REPLAY_PREAMBLE_LINES)
        for j in range(i - 1, preamble_start - 1, -1):
            if "DebugPrintGame() - PlayerID=" in all_lines[j]:
                preamble_start = min(preamble_start, j)
                break
        best_create = i
        best_start = preamble_start
        if is_ptl:
            break
    return best_start


class PowerLogParser(LogWatcher):
    """
    Power.log 解析器
    仿照 HDT 的 PowerHandler
    """

    def __init__(self, log_file: str, game_state: GameState):
        super().__init__(log_file, "Power")
        self.game_state = game_state
        self.event_handlers: Dict[str, list] = {
            "game_start": [],
            "game_end": [],
            "turn_start": [],
            "entity_created": [],
            "entity_updated": [],
            "change_entity": [],
            "entity_transform_ready": [],
            "tag_changed": [],
        }
        self._pending_transform_eids: set = set()
        # CHANGE_ENTITY 后日志常写 NUM_TURNS_IN_PLAY=0；已在场且本回合未攻击的随从应保留原值
        self._transform_preserve_ntp: Dict[int, int] = {}
        self.lines_processed = 0
        self._last_create_game_line = -100000
        self._game_end_emitted = False
        self._live_mode = True  # False=回放历史，不触发对局结束
        self._live_match_active = False  # 仅实时对局时为 True（用于 Overlay）
        self._awaiting_live_signal = False  # 回放保留场面，等实时日志再激活
        self.debug_mode = False  # 调试模式

    @property
    def live_match_active(self) -> bool:
        """当前是否应展示场面/斩杀（排除仅回放旧 LOG、已结束对局）。"""
        return self._live_match_active

    def start(self, read_last_lines: int = 0):
        """启动监控；历史回放阶段不触发对局结束。"""
        self._live_mode = False
        ok = super().start(read_last_lines=read_last_lines)
        self._live_mode = True
        self._finalize_replay_state()
        return ok

    def on(self, event: str, handler: Callable):
        """注册事件处理器"""
        if event in self.event_handlers:
            self.event_handlers[event].append(handler)

    def emit(self, event: str, *args, **kwargs):
        """触发事件"""
        if event in self.event_handlers:
            for handler in self.event_handlers[event]:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    print(f"[Power] 事件处理器错误 ({event}): {e}")

    def process_line(self, line: str):
        """处理日志行"""
        # 跳过空行
        if not line:
            return

        # 提取日志内容（跳过时间戳部分）
        # 格式: D 11:51:58.2141702 GameState.DebugPrintPower() - ...
        # 或: D 11:51:58.2141702 PowerTaskList.DebugPrintPower() - ...
        if line.startswith("D ") and "DebugPrintPower()" in line:
            # 找到 " - " 之后的内容
            idx = line.find(" - ")
            if idx != -1:
                line = line[idx + 3:]  # 提取实际内容
            else:
                return  # 没有实际内容，跳过
        elif line.startswith("D ") and "DebugPrintGame()" in line:
            idx = line.find(" - ")
            if idx != -1:
                self._handle_debug_print_game(line[idx + 3:])
            return
        elif line.startswith("D ") and "DebugPrintEntityChoices()" in line:
            idx = line.find(" - ")
            if idx != -1:
                self._handle_entity_choices(line[idx + 3:])
            return
        elif line.startswith("D "):
            return  # 其他 D 开头的非 Power.log 行，跳过

        if self._live_mode:
            self._maybe_confirm_live_match(line)

        # 检测新游戏开始（PowerTaskList 会重复打印 CREATE_GAME，勿二次重置）
        if line.strip() == "CREATE_GAME":
            if (
                self.game_state.game_entity_id is not None
                and (self.lines_processed - self._last_create_game_line) < 3000
            ):
                return
            print("[Power] 🎮 检测到新游戏开始，重置状态")
            self._last_create_game_line = self.lines_processed
            self._game_end_emitted = False
            self.game_state.begin_new_game()
            self._pending_transform_eids.clear()
            self._transform_preserve_ntp.clear()
            if self._live_mode:
                self._awaiting_live_signal = False
                self._live_match_active = True
            self.reconcile_local_player()
            self._apply_friendly_player()
            self.emit("game_start")
            self.lines_processed = 0
            return

        # 实时阶段：对局已结束后忽略日志，直到下一场 CREATE_GAME
        if self._live_mode and not self.game_state.in_game:
            return

        self.lines_processed += 1
        # 每处理100行输出一次调试信息
        if self.lines_processed % 100 == 0:
            print(f"[Power] 已处理 {self.lines_processed} 行，玩家ID: {self.game_state.local_player_id}, 实体数: {len(self.game_state.entities)}")

        # TAG_CHANGE（必须在 GameEntity 定义行判断之前，否则 TURN 等标签会被吞掉）
        if "CACHED_TAG_FOR_DORMANT_CHANGE" in line:
            self._handle_cached_dormant_change(line)
            return

        m = PowerRegex.TAG_CHANGE.search(line)
        if m:
            self._handle_tag_change(m)
            return

        # GameEntity 定义行
        if PowerRegex.GAME_ENTITY.search(line):
            self._handle_game_entity(line)
            return

        # Player 定义行
        if "Player EntityID=" in line:
            self._handle_player_entity(line)
            return

        # FULL_ENTITY
        m = PowerRegex.FULL_ENTITY.search(line)
        if m:
            self._handle_full_entity(m)
            return

        # SHOW_ENTITY
        m = PowerRegex.SHOW_ENTITY.search(line)
        if m:
            self._handle_show_entity(m)
            return

        # HIDE_ENTITY
        m = PowerRegex.HIDE_ENTITY.search(line)
        if m:
            self._handle_hide_entity(m)
            return

        if "CHANGE_ENTITY" in line:
            m = PowerRegex.CHANGE_ENTITY.search(line)
            if m:
                self._handle_change_entity(m)
            return

        # 行内TAG（在FULL_ENTITY或SHOW_ENTITY之后）
        if self.game_state.current_entity_id and "tag=" in line:
            m = PowerRegex.TAG.search(line)
            if m:
                self._apply_tag(
                    self.game_state.current_entity_id,
                    m.group("tag"),
                    m.group("value")
                )
            return

        # BLOCK_START/END
        if "BLOCK_START" in line:
            m = PowerRegex.BLOCK_START.search(line)
            if m:
                self.game_state.current_block_type = m.group("type")
                if m.group("type") == "FINAL_GAMEOVER":
                    self._maybe_end_game()
            return

        if "BLOCK_END" in line:
            self._flush_pending_transforms()
            self.game_state.current_block_type = None
            self.game_state.current_entity_id = None
            return

    def _handle_debug_print_game(self, content: str):
        """客户端 DebugPrintGame：带真实 # 战网名的 PlayerID 即本地玩家（对手为 UNKNOWN HUMAN PLAYER）。"""
        m = re.search(r"PlayerID=(\d+),\s*PlayerName=(.+)$", content.strip())
        if not m:
            return
        pid = int(m.group(1))
        name = m.group(2).strip()
        existing = self.game_state.player_names.get(pid)
        if self._is_unknown_player_name(name) and existing and not self._is_unknown_player_name(existing):
            return
        self.game_state.player_names[pid] = name
        if not self.game_state.in_game:
            self.game_state._pre_create_player_names[pid] = name
        if is_real_battle_tag(name):
            self._set_local_player(pid, f"DebugPrintGame={name}")
        else:
            self.reconcile_local_player()

    def _handle_entity_choices(self, content: str):
        """换牌 EntityChoices 仅登记战网名；双方都会出现，不能据此锁定我方。"""
        m = re.search(
            r"id=(\d+)\s+Player=(.+?)\s+TaskList=\d+\s+ChoiceType=(\w+)",
            content.strip(),
        )
        if not m:
            return
        if m.group(3) != "MULLIGAN":
            return
        pid = int(m.group(1))
        if pid not in (1, 2):
            return
        name = m.group(2).strip()
        if name and not self._is_unknown_player_name(name):
            self.game_state.player_names[pid] = name
            if name_matches_env_override(name):
                self._set_local_player(pid, f"HS_PLAYER_NAME(换牌)={name}")

    def _is_unknown_player_name(self, name: str) -> bool:
        n = (name or "").upper()
        return "UNKNOWN" in n and "PLAYER" in n

    def _set_local_player(self, player_id: int, source: str):
        gs = self.game_state
        name_locked = (
            "FRIENDLY_PLAYER" in source
            or "DebugPrintGame" in source
            or "HS_PLAYER_NAME" in source
        )
        if name_locked:
            gs.local_player_id_locked = True
        if gs.local_player_id == player_id:
            gs.local_player_identity_source = source
            return
        if gs.local_player_id is not None and gs.local_player_id != player_id:
            print(
                f"[Power] 纠正我方玩家: PlayerID {gs.local_player_id} -> {player_id} ({source})"
            )
        else:
            print(f"[Power] 识别我方玩家: PlayerID={player_id} ({source})")
        gs.local_player_id = player_id
        gs.local_player_identity_source = source
        gs.opponent_player_id = None
        gs.board_slots.clear()
        self._resync_all_board_slots()
        self._determine_opponent()

    def _resync_all_board_slots(self):
        """玩家归属纠正后，按当前 CONTROLLER 重建场面槽位"""
        from .board_damage import entity_zone, is_board_entity

        for eid in list(self.game_state.entities.keys()):
            entity = self.game_state.get_entity(eid)
            if entity_zone(entity) == "PLAY" and is_board_entity(entity):
                self._sync_board_slot(eid)

    def _known_player_names(self) -> Dict[int, str]:
        names = dict(self.game_state._pre_create_player_names)
        names.update(self.game_state.player_names)
        return names

    def _try_infer_local_from_hand(self):
        """仿 hslog：我方手牌在日志里可见 card_id，对手手牌不可见"""
        gs = self.game_state
        gs.bump_revealed_hand_peaks()
        if gs.local_player_id_locked:
            return
        inferred = gs.infer_local_from_revealed_hand()
        if inferred is None:
            return
        if gs.local_player_id == inferred:
            return
        if gs.local_player_id is not None and not gs.hand_inference_confident():
            return
        if not gs.hand_inference_confident():
            return
        self._set_local_player(inferred, "手牌可见(card_id)")

    def reconcile_local_player(self):
        """FRIENDLY_PLAYER / 换牌战网名 / 手牌可见 / 可选环境变量 校正我方 PlayerID。"""
        self._try_resolve_local_player_from_env()
        self._try_infer_local_from_hand()

    def _try_resolve_local_player_from_env(self):
        """仅当显式设置 HS_PLAYER_NAME(S) 环境变量时生效（普通用户无需配置）。"""
        if not optional_env_player_names():
            return
        for pid, name in self._known_player_names().items():
            if self._is_unknown_player_name(name):
                continue
            if name_matches_env_override(name):
                self._set_local_player(pid, f"HS_PLAYER_NAME={name}")
                return

    def _handle_game_entity(self, line: str):
        """处理 GameEntity"""
        m = PowerRegex.GAME_ENTITY.search(line)
        if m:
            eid = int(m.group("id"))
            self.game_state.game_entity_id = eid
            self.game_state.get_entity(eid)
            self.game_state.current_entity_id = eid

    def _handle_player_entity(self, line: str):
        """处理 Player 实体"""
        m = PowerRegex.PLAYER_ENTITY.search(line)
        if m:
            eid = int(m.group("id"))
            pid = int(m.group("player_id"))
            self.game_state.player_ids[eid] = pid
            entity = self.game_state.get_entity(eid)
            entity.controller = pid
            self.game_state.current_entity_id = eid
            self._reconcile_entity_controllers()
            self._apply_friendly_player()

    def _apply_friendly_player(self):
        """将 FRIENDLY_PLAYER（Player 实体 ID）映射为我方 PlayerID（1/2）"""
        gs = self.game_state
        eid = gs.friendly_player_entity_id
        if eid is None:
            return
        pid = gs.player_ids.get(eid)
        if pid is None:
            return
        self._set_local_player(pid, f"FRIENDLY_PLAYER 实体ID={eid}")
        self._try_infer_local_from_hand()

    def _handle_full_entity(self, match: re.Match):
        """处理 FULL_ENTITY"""
        eid = None
        card_id = match.group("card_id")

        # ID=数字 形式
        if match.group("id"):
            eid = int(match.group("id"))

        # 方括号形式
        elif match.group("bracket"):
            bracket = match.group("bracket")
            bm = PowerRegex.ENTITY_BRACKET.search(bracket)
            if bm:
                eid = int(bm.group("id"))
                if not card_id and bm.group("card_id"):
                    card_id = bm.group("card_id")

        if eid:
            entity = self.game_state.get_entity(eid)
            if card_id:
                if entity.card_id != card_id:
                    entity.reset_for_new_card(card_id)
                else:
                    entity.card_id = card_id
            if match.group("bracket"):
                bm = PowerRegex.ENTITY_BRACKET.search(match.group("bracket"))
                # 归属与区域仅由后续 tag=CONTROLLER / tag=ZONE 行决定（对齐 HDT/hslog）
            self.game_state.current_entity_id = eid
            self.emit("entity_created", entity)

    def _handle_show_entity(self, match: re.Match):
        """处理 SHOW_ENTITY"""
        entity_str = match.group("entity")
        card_id = match.group("card_id")
        eid = None

        # 数字形式
        if entity_str.isdigit():
            eid = int(entity_str)

        # 方括号形式
        elif entity_str.startswith("["):
            bm = PowerRegex.ENTITY_BRACKET.search(entity_str)
            if bm:
                eid = int(bm.group("id"))
                if not card_id and bm.group("card_id"):
                    card_id = bm.group("card_id")

        if eid:
            entity = self.game_state.get_entity(eid)
            if card_id:
                if entity.card_id != card_id:
                    entity.reset_for_new_card(card_id)
                else:
                    entity.card_id = card_id
            if entity_str.startswith("["):
                bm = PowerRegex.ENTITY_BRACKET.search(entity_str)
                if bm:
                    if bm.group("card_id") and not entity.card_id:
                        entity.card_id = bm.group("card_id")
                # 归属与区域仅由后续 tag= 行决定（方括号 player/zone 常为旧快照）
            self.game_state.current_entity_id = eid
            self.emit("entity_updated", entity)
            if card_id:
                self._try_infer_local_from_hand()

    def _entity_on_play_board(self, entity) -> bool:
        from .board_damage import entity_zone, is_board_entity

        if entity is None or entity_zone(entity) != "PLAY":
            return False
        return is_board_entity(entity)

    def _queue_board_transform(self, entity_id: int) -> None:
        entity = self.game_state.get_entity(entity_id)
        if self._entity_on_play_board(entity):
            self._pending_transform_eids.add(entity_id)

    def _flush_pending_transforms(self) -> None:
        if not self._pending_transform_eids:
            return
        pending = list(self._pending_transform_eids)
        self._pending_transform_eids.clear()
        for eid in pending:
            entity = self.game_state.get_entity(eid)
            if not self._entity_on_play_board(entity):
                continue
            self.emit("entity_transform_ready", entity)

    def _handle_change_entity(self, match: re.Match):
        """处理 CHANGE_ENTITY（变形/妖术后 CardID 与属性会在后续缩进行更新）"""
        entity_str = match.group("entity")
        card_id = match.group("card_id")
        eid = None

        if entity_str.isdigit():
            eid = int(entity_str)
        elif entity_str.startswith("["):
            bm = PowerRegex.ENTITY_BRACKET.search(entity_str)
            if bm:
                eid = int(bm.group("id"))
                if not card_id and bm.group("card_id"):
                    card_id = bm.group("card_id")

        if not eid:
            return

        entity = self.game_state.get_entity(eid)
        if self._entity_on_play_board(entity):
            prior_ntp = int(entity.tags.get("NUM_TURNS_IN_PLAY") or 0)
            prior_attacks = int(entity.tags.get("NUM_ATTACKS_THIS_TURN") or 0)
            if prior_ntp >= 1 and prior_attacks == 0:
                self._transform_preserve_ntp[eid] = prior_ntp
        if card_id:
            entity.card_id = card_id
        entity.damage = 0
        entity.tags.pop("DAMAGE", None)
        self.game_state.current_entity_id = eid
        self.emit("entity_updated", entity)
        self._sync_board_slot(eid)
        self._queue_board_transform(eid)
        self.emit("change_entity", entity)

    def _handle_cached_dormant_change(self, line: str) -> None:
        """随从入睡/唤醒时的 CACHED_TAG；唤醒后勿误标休眠。"""
        bm = PowerRegex.ENTITY_BRACKET.search(line)
        if not bm:
            return
        eid = int(bm.group("id"))
        entity = self.game_state.get_entity(eid)
        if entity.tags.get("DORMANT") == 0:
            return
        entity.tags["DORMANT"] = 1
        self.emit("tag_changed", entity, "DORMANT", 1)

    def _mark_host_dormant_from_enchant(self, enchant_entity: Entity) -> None:
        """唤醒条件附魔挂上时，宿主随从视为休眠。"""
        attached = enchant_entity.tags.get("ATTACHED")
        if attached is None:
            return
        try:
            host_id = int(attached)
        except (TypeError, ValueError):
            return
        host = self.game_state.get_entity(host_id)
        if host is None or not host.is_minion:
            return
        host.tags["DORMANT"] = 1
        self.emit("tag_changed", host, "DORMANT", 1)

    def _handle_tag_change(self, match: re.Match):
        """处理 TAG_CHANGE"""
        entity_str = match.group("entity")
        tag = match.group("tag")
        value = match.group("value")

        # 特殊处理 FRIENDLY_PLAYER（值为 Player 实体 ID，非 PlayerID）
        if tag == "FRIENDLY_PLAYER":
            self.game_state.friendly_player_entity_id = int(value)
            self._apply_friendly_player()
            return

        eid = None

        # 数字形式
        if entity_str.isdigit():
            eid = int(entity_str)

        # 方括号形式
        elif entity_str.startswith("["):
            bm = PowerRegex.ENTITY_BRACKET.search(entity_str)
            if bm:
                eid = int(bm.group("id"))
                if bm.group("card_id"):
                    entity = self.game_state.get_entity(eid)
                    if not entity.card_id:
                        entity.card_id = bm.group("card_id")
                # 不要用方括号里的 player/zone：多为旧快照，会误改归属或场攻

        # GameEntity
        elif "GameEntity" in entity_str:
            eid = self.game_state.game_entity_id

        # 玩家名形式（Entity=战网名#1234）
        else:
            pid = self._resolve_player_id_from_battle_tag(entity_str)
            if pid is not None and tag == "MAIN_HAND_WEAPON_ENTITY":
                self._set_player_weapon(pid, value, entity_str)
                return
            if pid is not None and tag == "HERO_ENTITY":
                self._set_player_hero_entity(pid, value)
                return
            if pid is not None and tag in _PLAYER_MANA_TAGS:
                hero = self.game_state.get_hero(pid)
                if hero:
                    self._apply_tag(hero.entity_id, tag, value, controller_from_tag_change=False)
                return
            if pid is not None and tag in _PLAYER_TURN_TAGS:
                for peid, ppid in self.game_state.player_ids.items():
                    if ppid == pid:
                        self._apply_tag(peid, tag, value, controller_from_tag_change=False)
                        return
            if tag == "CURRENT_PLAYER":
                self._handle_player_current_player(entity_str, value)
                return

        if eid:
            self._apply_tag(eid, tag, value, controller_from_tag_change=True)

    def _battle_tag_matches_player(self, entity_str: str, player_id: int) -> bool:
        name = self.game_state.player_names.get(player_id)
        if not name:
            return False
        if entity_str == name:
            return True
        if "#" in name and entity_str.split("#")[0] == name.split("#")[0]:
            return True
        return False

    def _handle_player_current_player(self, entity_str: str, value: str):
        """Player 实体上的 CURRENT_PLAYER 是 0/1 标志，不是 PlayerID。"""
        try:
            flag = int(value)
        except ValueError:
            return

        pid = self._resolve_player_id_from_battle_tag(entity_str)
        if pid is None:
            local_pid = self.game_state.local_player_id
            if local_pid and self._battle_tag_matches_player(entity_str, local_pid):
                pid = local_pid
            else:
                opp = self.game_state.opponent_player_id
                if opp and self._battle_tag_matches_player(entity_str, opp):
                    pid = opp
        if pid is None:
            return

        gs = self.game_state
        if flag == 1:
            gs.active_player_id = pid
            return

        # 回合交接：对手 CURRENT_PLAYER 先变 0 时，立即切换 active，避免仍按对方回合显示
        if flag == 0 and gs.active_player_id == pid:
            other = None
            if gs.local_player_id and gs.opponent_player_id:
                other = (
                    gs.opponent_player_id
                    if pid == gs.local_player_id
                    else gs.local_player_id
                )
            if other:
                gs.active_player_id = other

    def _resolve_player_id_from_name(self, entity_str: str) -> Optional[int]:
        for pid, name in self.game_state.player_names.items():
            if entity_str == name:
                return pid
            if "#" in name and entity_str.split("#")[0] == name.split("#")[0]:
                return pid
        return None

    def _resolve_player_id_from_battle_tag(self, entity_str: str) -> Optional[int]:
        """战网名 TAG_CHANGE：DebugPrintGame 常给出 UNKNOWN HUMAN PLAYER，需用真实 tag 反查 PlayerID。"""
        pid = self._resolve_player_id_from_name(entity_str)
        if pid is not None:
            return pid

        if "#" not in entity_str:
            return None

        gs = self.game_state
        if gs.local_player_id and self._battle_tag_matches_player(entity_str, gs.local_player_id):
            return gs.local_player_id

        for pid, name in list(gs.player_names.items()):
            if pid not in (1, 2):
                continue
            if self._is_unknown_player_name(name):
                gs.player_names[pid] = entity_str
                return pid

        if gs.local_player_id in (1, 2):
            opp = gs.opponent_player_id or (3 - gs.local_player_id)
            gs.player_names[opp] = entity_str
            return opp

        return None

    def _set_player_weapon(self, player_id: int, value: str, entity_str: str = ""):
        try:
            wid = int(value)
        except ValueError:
            wid = 0

        def apply(pid: int):
            if wid > 0:
                self.game_state.weapon_entity_ids[pid] = wid
            else:
                self.game_state.weapon_entity_ids.pop(pid, None)

        apply(player_id)
        local = self.game_state.local_player_id
        # 仅当战网名明确是我方时，才写入 local（避免把对手武器同步到我方）
        if local is not None and entity_str and self._battle_tag_matches_player(entity_str, local):
            if player_id != local:
                apply(local)
        elif local is None and wid > 0:
            pname = self.game_state.player_names.get(player_id, entity_str)
            if pname and name_matches_env_override(pname):
                self._set_local_player(player_id, f"武器持有者={pname}")

    def _set_player_hero_entity(self, player_id: Optional[int], value: str):
        """Player 战网名上的 HERO_ENTITY 变更（英雄牌替换英雄时指向新实体）。"""
        try:
            hid = int(value)
        except ValueError:
            return
        if hid <= 0:
            return
        pid = player_id
        if pid is None:
            hero = self.game_state.get_entity(hid)
            if hero.controller:
                pid = hero.controller
        if pid is not None:
            self.game_state.hero_entity_ids[pid] = hid

    def _handle_hide_entity(self, match: re.Match):
        """处理 HIDE_ENTITY"""
        entity_str = match.group("entity")
        eid = None

        if entity_str.isdigit():
            eid = int(entity_str)
        elif entity_str.startswith("["):
            bm = PowerRegex.ENTITY_BRACKET.search(entity_str)
            if bm:
                eid = int(bm.group("id"))

        if eid and eid in self.game_state.entities:
            entity = self.game_state.entities[eid]
            entity.zone = "GRAVEYARD"
            entity.tags["ZONE"] = 4
            self.game_state.remove_entity_from_board_slots(eid)

    def _sync_board_slot(self, entity_id: int):
        """根据 ZONE + ZONE_POSITION 更新战场槽位表"""
        from .board_damage import entity_zone, is_board_entity

        entity = self.game_state.get_entity(entity_id)
        if entity_zone(entity) != "PLAY":
            self.game_state.remove_entity_from_board_slots(entity_id)
            return
        zpos = entity.tags.get("ZONE_POSITION", 0)
        # 打出动画：先 ZONE=PLAY 后 ZONE_POSITION，或 PowerTaskList 重放行暂写 0
        if not (1 <= int(zpos or 0) <= 7):
            return
        self.game_state.remove_entity_from_board_slots(entity_id)
        if not is_board_entity(entity):
            return
        pid = self.game_state.get_entity_player_id(entity)
        if pid:
            self.game_state.board_slots.setdefault(pid, {})[int(zpos)] = entity_id

    def _apply_tag(
        self,
        entity_id: int,
        tag: str,
        value: str,
        *,
        controller_from_tag_change: bool = False,
    ):
        """应用标签到实体"""
        entity = self.game_state.get_entity(entity_id)

        # 尝试转换为整数
        int_value = None
        try:
            int_value = int(value)
        except ValueError:
            pass

        if (
            tag == "ZONE_POSITION"
            and int_value == 0
            and entity_zone(entity) == "PLAY"
        ):
            for slots in self.game_state.board_slots.values():
                if entity_id in slots.values():
                    return

        if tag == "NUM_TURNS_IN_PLAY" and int_value == 0:
            preserve = self._transform_preserve_ntp.pop(entity_id, None)
            if preserve is not None and preserve >= 1:
                int_value = preserve

        if int_value is not None:
            entity.tags[tag] = int_value
        elif value:
            entity.tags[tag] = value

        # 应用特定标签
        if tag == "ZONE":
            zones = ["", "PLAY", "DECK", "HAND", "GRAVEYARD", "REMOVEDFROMGAME", "SETASIDE", "SECRET"]
            if value.isdigit():
                zone_int = int(value)
                if 0 <= zone_int < len(zones):
                    entity.zone = zones[zone_int]
                    entity.tags["ZONE"] = zone_int
            else:
                entity.zone = value
                entity.tags["ZONE"] = value
            if entity_zone(entity) != "PLAY":
                entity.tags.pop("ZONE_POSITION", None)
                self.game_state.remove_entity_from_board_slots(entity_id)
            else:
                self._sync_board_slot(entity_id)
            if entity_zone(entity) == "HAND":
                self._try_infer_local_from_hand()

        elif tag == "CONTROLLER":
            if int_value is not None:
                old_pid = self.game_state.get_entity_player_id(entity)
                entity.tags["CONTROLLER"] = int_value
                # 随从/武器 TAG_CHANGE 的 CONTROLLER 为 PlayerID(1/2)；仅 Player 实体用 Entity ID
                is_player_entity = entity_id in self.game_state.player_ids
                use_entity_id = controller_from_tag_change and is_player_entity
                entity.controller_uses_entity_id = use_entity_id
                resolved = self.game_state.resolve_controller_to_player_id(
                    int_value, prefer_entity_id=use_entity_id
                )
                entity.controller = resolved if resolved is not None else int_value
                self.game_state.seen_controllers.add(int_value)
                self._determine_opponent()
                new_pid = self.game_state.get_entity_player_id(entity)
                if (
                    entity_zone(entity) == "PLAY"
                    and old_pid is not None
                    and new_pid is not None
                    and old_pid != new_pid
                ):
                    # 疯狂药水等夺取：旧 ZONE_POSITION 可能暂占新方槽位，须全量重建
                    self._resync_all_board_slots()
                else:
                    self._sync_board_slot(entity_id)
                if entity_zone(entity) == "HAND":
                    self._try_infer_local_from_hand()

        elif tag == "CARDTYPE":
            if value.isdigit():
                # 数字形式
                types = ["", "HERO", "MINION", "SPELL", "ENCHANTMENT", "WEAPON", "ITEM", "TOKEN", "HERO_POWER"]
                type_int = int(value)
                if 0 <= type_int < len(types):
                    entity.cardtype = types[type_int]
            else:
                # 字符串形式（直接使用）
                entity.cardtype = value
            if entity.is_minion or entity.is_weapon:
                entity.sync_attack_from_tags()
            if entity.is_weapon and entity.health > 0 and entity.durability == 0:
                entity.durability = entity.health
            if entity_cardtype(entity) == "ENCHANTMENT":
                self.game_state.remove_entity_from_board_slots(entity_id)
            elif entity_zone(entity) == "PLAY":
                self._sync_board_slot(entity_id)

        elif tag == "COST" and int_value is not None:
            entity.cost = int_value
        elif tag in ("ATK", "479", "4472") and int_value is not None:
            entity.sync_attack_from_tags()
        elif tag == "TAG_SCRIPT_DATA_NUM_1" and int_value is not None:
            entity.sync_attack_from_tags()
        elif tag == "HEALTH" and int_value is not None:
            entity.health = int_value
            if entity.is_weapon and int_value > 0:
                entity.durability = int_value
        elif tag == "DAMAGE" and int_value is not None:
            entity.damage = int_value
            if entity.current_health <= 0 and entity.is_minion:
                entity.zone = "GRAVEYARD"
                entity.tags["ZONE"] = 4
                self.game_state.remove_entity_from_board_slots(entity_id)
        elif tag == "DEAD" and int_value == 1:
            entity.zone = "GRAVEYARD"
            entity.tags["ZONE"] = 4
            self.game_state.remove_entity_from_board_slots(entity_id)
        elif tag == "DURABILITY" and int_value is not None:
            entity.durability = int_value
        elif tag == "ZONE_POSITION" and int_value is not None:
            entity.zone_pos = int_value
            self._sync_board_slot(entity_id)
        elif tag == "HERO_ENTITY" and int_value is not None:
            if entity_id in self.game_state.player_ids:
                pid = self.game_state.player_ids[entity_id]
                self.game_state.hero_entity_ids[pid] = int_value
        elif tag == "FIRST_PLAYER" and int_value == 1:
            if entity.controller is not None:
                self.game_state.first_player_id = entity.controller
        elif tag == "TURN" and int_value is not None and entity_id == self.game_state.game_entity_id:
            pass  # 已写入 tags，供 is_players_turn 使用
        elif tag == "STATE" and entity_id == self.game_state.game_entity_id:
            if self._is_game_over_state(value):
                self._maybe_end_game()
        elif tag == "PLAYSTATE":
            if self._is_game_over_playstate(value) and self._is_player_entity(entity_id):
                self._maybe_end_game()
        elif tag == "DORMANT_AWAKEN_CONDITION_ENCHANT" and int_value == 1:
            self._mark_host_dormant_from_enchant(entity)
        elif tag == "DORMANT" and entity.is_minion:
            entity.tags["DORMANT"] = int_value or 0

        # 触发事件
        self.emit("tag_changed", entity, tag, int_value if int_value is not None else value)

    @staticmethod
    def _is_game_over_state(value) -> bool:
        if isinstance(value, str):
            return value.upper() in ("COMPLETE", "FINAL_GAMEOVER")
        try:
            return int(value) == 3
        except (TypeError, ValueError):
            return False

    @staticmethod
    def _is_game_over_playstate(value) -> bool:
        if isinstance(value, str):
            return value.upper() in ("WON", "LOST", "CONCEDED")
        try:
            # WON=4, LOST=5, CONCEDED=8；3=LOSING 仍在对局中
            return int(value) in (4, 5, 8)
        except (TypeError, ValueError):
            return False

    def _is_player_entity(self, entity_id: int) -> bool:
        """仅玩家/英雄实体的 PLAYSTATE 才触发对局结束（避免误解析其它实体）。"""
        if entity_id in self.game_state.player_ids:
            return True
        entity = self.game_state.get_entity(entity_id)
        if entity and entity.is_hero:
            return True
        ct = entity_cardtype(entity) if entity else None
        return ct == "PLAYER"

    def _replay_indicates_game_over(self) -> bool:
        """回放快照是否已终局（不依赖 _live_mode）。"""
        if not self.game_state.in_game:
            return True
        ge_id = self.game_state.game_entity_id
        if ge_id is not None:
            ge = self.game_state.get_entity(ge_id)
            if ge is not None:
                state = ge.tags.get("STATE")
                if self._is_game_over_state(state):
                    return True
        for hero_id in self.game_state.hero_entity_ids.values():
            hero = self.game_state.get_entity(hero_id)
            if hero is None:
                continue
            ps = hero.tags.get("PLAYSTATE")
            if ps is not None and self._is_game_over_playstate(ps):
                return True
        for player_entity_id in self.game_state.player_ids:
            player = self.game_state.get_entity(player_entity_id)
            if player is None:
                continue
            ps = player.tags.get("PLAYSTATE")
            if ps is not None and self._is_game_over_playstate(ps):
                return True
        return False

    def _end_current_match(self):
        """对局结束：清空场面；回放收尾与实时终局共用。"""
        self._awaiting_live_signal = False
        self._live_match_active = False
        if not self.game_state.in_game or self._game_end_emitted:
            return
        print("[Power] 🏁 对局结束，清零场面数据")
        self._game_end_emitted = True
        self.lines_processed = 0
        self.game_state.end_current_game()
        self.emit("game_end")

    def _maybe_end_game(self):
        if not self._live_mode:
            return
        self._end_current_match()

    def _finalize_replay_state(self):
        """历史回放结束后收尾：终局清空；进行中对局仅保留场面，等实时日志再展示。"""
        if self._replay_indicates_game_over():
            self._end_current_match()
        elif self.game_state.in_game:
            print("[Power] 历史回放结束，保留场面；等待实时操作")
            self._game_end_emitted = False
            self._live_match_active = False
            self._awaiting_live_signal = True
        else:
            self._awaiting_live_signal = False
            self._live_match_active = False

    @staticmethod
    def _is_live_match_signal_line(line: str) -> bool:
        """菜单/空闲时通常无此类行；用于区分回放快照与正在进行的对局。"""
        s = line.strip()
        if s == "CREATE_GAME":
            return True
        if PowerRegex.TAG_CHANGE.search(line):
            return True
        if "GameEntity EntityID=" in line or "Player EntityID=" in line:
            return True
        if "EntityID=" in line and "cardID=" in line:
            return True
        if PowerRegex.FULL_ENTITY.search(line) or PowerRegex.SHOW_ENTITY.search(line):
            return True
        return False

    def _maybe_confirm_live_match(self, line: str):
        if not self._awaiting_live_signal or not self._is_live_match_signal_line(line):
            return
        self._awaiting_live_signal = False
        self._live_match_active = True
        print("[Power] 检测到实时对局活动，开始跟踪")

    def _reset_for_replay(self):
        """切换/重置日志文件前清空解析状态，避免沿用上一局 PlayerID。"""
        self.game_state.reset(preserve_player=False)
        self._game_end_emitted = False
        self._awaiting_live_signal = False
        self._live_match_active = False
        self._last_create_game_line = -100000
        self.lines_processed = 0
        self._pending_transform_eids.clear()
        self._transform_preserve_ntp.clear()

    def _replay_last_game(self, all_lines: list) -> int:
        """从最后一场 CREATE_GAME 前缀回放；返回回放起点行号（0-based）。"""
        last_start = find_last_game_replay_start(all_lines)
        if last_start < 0:
            return -1
        for raw in all_lines[last_start:]:
            raw = raw.rstrip("\n\r")
            if raw:
                self.process_line(raw)
        self._notify_log_activity()
        return last_start

    def _notify_log_activity(self) -> None:
        for callback in self.callbacks:
            try:
                callback("")
            except Exception:
                pass

    def read_new_lines(self):
        """日志被炉石截断重写时，重新智能回放当前对局。"""
        if not self.file_handle:
            return []
        try:
            current_size = os.path.getsize(self.log_file)
            if current_size < self.last_position:
                print(f"[{self.name}] 日志文件已重置，重新回放当前对局")
                self.file_handle.close()
                self.file_handle = open(self.log_file, "r", encoding="utf-8", errors="ignore")
                self.last_position = 0
                self._live_mode = False
                self._reset_for_replay()
                all_lines = self.file_handle.readlines()
                self._replay_last_game(all_lines)
                self.last_position = self.file_handle.tell()
                self._live_mode = True
                self._finalize_replay_state()
                return []
        except OSError:
            pass
        return super().read_new_lines()

    def try_switch_log_file(self) -> bool:
        """炉石新开日志会话时切换到最新的 Power.log。"""
        from .log_watcher import find_power_log_path

        new_path = find_power_log_path()
        if not new_path:
            return False
        new_path = os.path.abspath(new_path)
        if new_path == os.path.abspath(self.log_file):
            return False
        print(f"[Power] 检测到新日志文件，切换: {new_path}")
        if self.file_handle:
            self.file_handle.close()
            self.file_handle = None
        self.log_file = new_path
        self.file_handle = open(self.log_file, "r", encoding="utf-8", errors="ignore")
        self._live_mode = False
        self._reset_for_replay()
        self.file_handle.seek(0)
        all_lines = self.file_handle.readlines()
        self._replay_last_game(all_lines)
        self.last_position = self.file_handle.tell()
        self._live_mode = True
        self._finalize_replay_state()
        return True

    def _reconcile_entity_controllers(self):
        """Player 实体注册后，将已记录实体的 CONTROLLER 映射为 PlayerID"""
        for entity in list(self.game_state.entities.values()):
            raw = entity.tags.get("CONTROLLER")
            if raw is None:
                continue
            prefer = bool(getattr(entity, "controller_uses_entity_id", False))
            resolved = self.game_state.resolve_controller_to_player_id(
                raw, prefer_entity_id=prefer
            )
            if resolved is not None:
                entity.controller = resolved

    def _determine_opponent(self):
        """确定对手玩家ID"""
        if self.game_state.local_player_id is not None and self.game_state.opponent_player_id is None:
            # 找出不是我方的玩家
            all_player_ids = set(self.game_state.player_ids.values())
            for pid in all_player_ids:
                if pid != self.game_state.local_player_id:
                    self.game_state.opponent_player_id = pid
                    print(f"[Power] 识别到对手玩家: {pid}")
                    break
