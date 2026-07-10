# end_turn_p0.py — 回合结束（已接入 end_turn_board.py）

from __future__ import annotations

from .end_turn_board import END_TURN_BY_CARD

P0_END_TURN_IDS = tuple(END_TURN_BY_CARD.keys())


def _register_p0_end_turn() -> None:
    """回合结束已注册卡牌。"""
    for cid in (
        "TOY_647", "TOY_601", "TOY_601t",
        "RLK_720", "RLK_706", "SCH_337", "EDR_453",
        "CATA_475", "AV_340", "CORE_BT_493", "CATA_999",
    ):
        assert cid in END_TURN_BY_CARD


_register_p0_end_turn()
