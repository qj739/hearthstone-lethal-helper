"""额外回合：TURN 奇偶与 CURRENT_PLAYER 冲突时，应以 CURRENT_PLAYER 为准。"""
from hdt_python.power_parser import GameState, Entity
from hdt_python.board_damage import is_players_turn, board_active_turn_for_display


def _make_gs(*, turn: int, active: int, first: int = 1, local: int = 1) -> GameState:
    gs = GameState()
    gs.local_player_id = local
    gs.opponent_player_id = 2 if local == 1 else 1
    gs.first_player_id = first
    gs.active_player_id = active
    gs.in_game = True

    ge = Entity(1)
    ge.tags["TURN"] = turn
    gs.game_entity_id = 1
    gs.entities[1] = ge
    return gs


def test_extra_turn_prefers_current_player_over_turn_parity():
    """先手连续额外回合：TURN 变偶数，但仍是我方 CURRENT_PLAYER。"""
    # 先手：奇数 TURN 才轮到自己；额外第二回合 TURN=24 时奇偶会误判
    gs = _make_gs(turn=24, active=1, first=1, local=1)
    assert is_players_turn(gs, 1) is True
    assert is_players_turn(gs, 2) is False
    assert gs.is_local_turn() is True
    assert board_active_turn_for_display(gs, 1) is True


def test_normal_turn_parity_fallback_when_active_unknown():
    """尚无 active_player_id 时，回退 TURN 奇偶。"""
    gs = _make_gs(turn=21, active=1, first=1, local=1)
    gs.active_player_id = None
    assert is_players_turn(gs, 1) is True
    assert is_players_turn(gs, 2) is False

    gs.entities[1].tags["TURN"] = 22
    assert is_players_turn(gs, 1) is False
    assert is_players_turn(gs, 2) is True


def test_second_player_extra_turn_odd_turn_number():
    """后手额外回合：TURN 为奇数时奇偶也会误判，仍信 CURRENT_PLAYER。"""
    gs = _make_gs(turn=23, active=2, first=1, local=2)
    assert is_players_turn(gs, 2) is True
    assert is_players_turn(gs, 1) is False
    assert gs.is_local_turn() is True


if __name__ == "__main__":
    test_extra_turn_prefers_current_player_over_turn_parity()
    test_normal_turn_parity_fallback_when_active_unknown()
    test_second_player_extra_turn_odd_turn_number()
    print("OK extra-turn local detection")
