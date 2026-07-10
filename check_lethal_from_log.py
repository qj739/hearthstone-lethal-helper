#!/usr/bin/env python3
"""从 Power.log 关键节点回放并检查斩杀判断。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from hdt_python.power_parser import PowerLogParser, GameState
from hdt_python.lethal_checker import LethalChecker
from hdt_python.board_damage import entity_has_taunt, collect_hand_charge_minions

LOG = Path(__file__).parent / "Power.log"


def parse_to(lines, start: int, end_line: int) -> GameState:
    gs = GameState()
    p = PowerLogParser(str(LOG), gs)
    for line in lines[start:end_line]:
        line = line.rstrip("\n\r")
        if line:
            p.process_line(line)
    return gs


def report(label: str, gs: GameState, end_line: int) -> None:
    lc = LethalChecker(gs)
    local = gs.local_player_id
    opp = gs.opponent_player_id
    hero = gs.get_hero(opp) if opp else None
    hp_info = "?"
    eff = "?"
    armor = 0
    if hero:
        dmg = hero.tags.get("DAMAGE", 0)
        maxhp = hero.health or hero.tags.get("HEALTH", 30)
        armor = hero.tags.get("ARMOR", 0)
        cur = hero.current_health
        hp_info = f"{cur} (DAMAGE={dmg}, max={maxhp})"
        eff = lc.get_opponent_effective_hp()

    mana = "?"
    mana_h = gs.get_hero(local) if local else None
    if mana_h:
        res = mana_h.tags.get("RESOURCES", 0)
        used = mana_h.tags.get("RESOURCES_USED", 0)
        mana = res - used

    print(f"\n=== {label} (line {end_line}) ===")
    print(f"我方={local} 对手={opp} 法力={mana} 对手有效血={eff} ({hp_info} 甲{armor})")

    board = gs.get_board(local) if local else []
    print("我方场面:")
    for m in board:
        print(
            f"  {m.card_id} {m.atk}/{m.current_health} "
            f"打脸={m.can_attack_hero} 可攻={m.can_attack} "
            f"剩余攻击={m.remaining_attacks} EXHAUSTED={m.tags.get('EXHAUSTED')}"
        )

    opp_board = gs.get_board(opp) if opp else []
    print("对手场面:")
    for m in opp_board:
        taunt = " [嘲]" if entity_has_taunt(m) else ""
        print(f"  {m.card_id} {m.atk}/{m.current_health}{taunt}")

    hand = gs.get_hand(local) if local else []
    print("手牌:", [f"{c.card_id}(c{c.cost})" for c in hand])

    charges = collect_hand_charge_minions(gs, local) if local else []
    if charges:
        print("手牌冲锋:", [(c.card_id, cost, atk) for c, cost, atk in charges])

    total, sources, lethal = lc.calculate_lethal()
    overlay = lc.overlay_board_face_damage()
    pure, minion_f, weapon_f, spell_f, hp_f = lc.overlay_board_breakdown()
    max_f, prob, rnd, top = lc.overlay_face_stats()
    note = lc.overlay_spell_note()

    print(f"快速斩杀: total={total} lethal={lethal}")
    for s in sources:
        print(f"  - {s.source_type}: {s.damage} ({s.description})")
    print(
        f"Overlay场攻: total={overlay} "
        f"(纯场面={pure} 随从={minion_f} 武器={weapon_f} 法术={spell_f} 技能={hp_f})"
    )
    print(f"  MC最高={max_f} 斩杀概率={prob:.0%} 含随机法术={rnd} top2={top}")
    if note:
        print(f"  推荐打法: {note}")


def main():
    with open(LOG, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()

    start = 0
    for i in range(len(lines) - 1, -1, -1):
        if "CREATE_GAME" in lines[i] and "GameState.DebugPrintPower" in lines[i]:
            start = i
            break

    print(f"Power.log 共 {len(lines)} 行，最后一局从第 {start + 1} 行开始")

    checkpoints = [
        ("斩杀回合开始 (MAIN_ACTION)", 31268),
        ("扎卡利 7 攻打脸后", 31551),
        ("巨鳗面具 buff 后 / 抛石鱼人斩杀前", 32314),
    ]
    for label, end in checkpoints:
        gs = parse_to(lines, start, end)
        report(label, gs, end)


if __name__ == "__main__":
    main()
