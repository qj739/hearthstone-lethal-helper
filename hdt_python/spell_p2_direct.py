# spell_p2_direct.py — P2 直伤法术

from __future__ import annotations

from .spell_board import (
    scaled_spell_damage as _sd,
    BoardSpellDef,
    _apply_optimal_single_target_damage,
    _register,
    hand_effect_active,
)


def _apply_precise_shot(taunts, fighters, *, mult, enemy_shield, spell_power=0, card=None, **_kw) -> SpellApplyResult:
    """精确射击：亮边 5 伤，否则 3 伤；仅打脸（无嘲）或点嘲讽随从。"""
    dmg = 5 if hand_effect_active(card) else 3
    return _apply_optimal_single_target_damage(
        taunts, fighters, _sd(dmg, mult=mult, spell_power=spell_power), enemy_shield=enemy_shield,
    )


def _register_p2_direct() -> None:
    _register(
        BoardSpellDef(
            card_ids=("TIME_600",),
            base_cost=2,
            name="精确射击",
            apply=_apply_precise_shot,
            uses_random=False,
        )
    )


_register_p2_direct()
