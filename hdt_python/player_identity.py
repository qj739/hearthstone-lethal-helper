"""我方 PlayerID 识别辅助（零配置，对齐 HDT）。

正常对局无需任何配置文件。解析器按以下顺序自动识别「哪边是我」：
1. FRIENDLY_PLAYER — 客户端写入 Power.log，与 HDT 相同
2. DebugPrintGame — 客户端只打印己方真实战网名（对手为 UNKNOWN HUMAN PLAYER）
3. 手牌 card_id 长期可见 — 仅作临时推断，可被 1/2 覆盖

可选高级覆盖：环境变量 HS_PLAYER_NAME / HS_PLAYER_NAMES（测试或特殊场景）。
"""

from __future__ import annotations

import os
import re
from typing import Optional

_NAME_SPLIT = re.compile(r"[,;\n]+")


def is_real_battle_tag(name: str) -> bool:
    """日志里带 # 的真实战网名（非 UNKNOWN HUMAN PLAYER）。"""
    n = (name or "").strip()
    if not n or "#" not in n:
        return False
    upper = n.upper()
    return not ("UNKNOWN" in upper and "PLAYER" in upper)


def optional_env_player_names() -> list[str]:
    """仅环境变量（不读任何 txt 文件）。"""
    names: list[str] = []
    seen: set[str] = set()
    for raw in (
        os.environ.get("HS_PLAYER_NAMES", ""),
        os.environ.get("HS_PLAYER_NAME", ""),
    ):
        for part in _NAME_SPLIT.split(raw.replace("\r\n", "\n")):
            n = part.strip()
            if n and n not in seen:
                seen.add(n)
                names.append(n)
    return names


def battle_tag_matches(log_name: str, known: str) -> bool:
    log_name = (log_name or "").strip()
    known = (known or "").strip()
    if not log_name or not known:
        return False
    if log_name == known:
        return True
    if "#" in known and log_name.split("#", 1)[0] == known.split("#", 1)[0]:
        return True
    if "#" in log_name and log_name.split("#", 1)[0] == known.split("#", 1)[0]:
        return True
    return False


def name_matches_env_override(log_name: str) -> bool:
    return any(battle_tag_matches(log_name, k) for k in optional_env_player_names())


def format_identity_summary(
    local_player_id: Optional[int],
    opponent_player_id: Optional[int],
    player_names: dict,
    hero_card_ids: Optional[dict] = None,
    source: str = "",
) -> str:
    local_name = player_names.get(local_player_id, "?") if local_player_id else "?"
    opp_name = player_names.get(opponent_player_id, "?") if opponent_player_id else "?"
    parts = [
        f"我方: PlayerID={local_player_id} {local_name}",
        f"对手: PlayerID={opponent_player_id} {opp_name}",
    ]
    if hero_card_ids:
        parts.append(
            f"英雄: 我方={hero_card_ids.get(local_player_id, '?')} "
            f"对手={hero_card_ids.get(opponent_player_id, '?')}"
        )
    if source:
        parts.append(f"识别来源: {source}")
    return " | ".join(parts)
