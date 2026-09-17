# -*- coding: utf-8 -*-
"""Export Azeroth's Most Wanted (CAP_) class-set cards for review."""
import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
en = json.loads((ROOT / "tools/_tmp_cards/cards_enUS.json").read_text(encoding="utf-8"))
zh = {
    c["id"]: c
    for c in json.loads((ROOT / "tools/_tmp_cards/cards_zhCN.json").read_text(encoding="utf-8"))
}
old = {c["id"] for c in json.loads((ROOT / "json/cards.json").read_text(encoding="utf-8"))}

# All CAP_ cards (collectible + tokens)
caps = [c for c in en if str(c.get("id", "")).startswith("CAP_")]
coll = [c for c in caps if c.get("collectible")]
tokens = [c for c in caps if not c.get("collectible")]

print(f"CAP_ total={len(caps)} collectible={len(coll)} tokens={len(tokens)}")
print(f"in local cards.json: {sum(1 for c in coll if c['id'] in old)} / {len(coll)}")

order = ["PRIEST", "ROGUE", "WARLOCK", "WARRIOR", "NEUTRAL"]
by_class = defaultdict(list)
for c in coll:
    by_class[c.get("cardClass", "?")].append(c)

lines = []
lines.append("# 艾泽拉斯头号通缉（Azeroth's Most Wanted）新卡收集")
lines.append("")
lines.append("> 来源：HearthstoneJSON `latest`（2026-09-01 拉取）")
lines.append("> 版本：Patch **36.4**（2026-08-25）· Escape from Violet Hold **职业套装**")
lines.append("> 卡牌 ID 前缀：`CAP_`（主扩展为 `JAIL_`）")
lines.append("")
lines.append("## 总览")
lines.append("")
lines.append("| 项目 | 数量 |")
lines.append("|------|------|")
lines.append(f"| 可收集新卡 | **{len(coll)}** |")
lines.append(f"| 衍生/标记牌（不可收集） | {len(tokens)} |")
lines.append(f"| 本地 `json/cards.json` 已收录 | {sum(1 for c in coll if c['id'] in old)} |")
lines.append("")
lines.append("构成：牧师 / 潜行者 / 术士 / 战士各 **7** 张 + 中立史诗 **通缉海报** = **29**。")
lines.append("")
lines.append("### 主题与传说")
lines.append("")
lines.append("| 职业 | 传说 | 主题 |")
lines.append("|------|------|------|")
lines.append("| 潜行者 | 马迪亚斯·肖尔 | 潜行 / SI:7 |")
lines.append("| 术士 | 教父卡扎库斯 | 黑幕庭审 / 陷害 |")
lines.append("| 牧师 | 雷斯·范盖斯特 | 复生 / 亡语灵体 |")
lines.append("| 战士 | 克罗雷船长 | 海盗火炮手 |")
lines.append("| 中立 | 通缉海报（史诗） | 发现高费随从+预备 |")
lines.append("")

rarity_rank = {"LEGENDARY": 0, "EPIC": 1, "RARE": 2, "COMMON": 3}


def fmt_stats(c):
    t = c.get("type")
    if t == "MINION":
        return f"{c.get('attack', 0)}/{c.get('health', 0)}"
    if t == "WEAPON":
        return f"{c.get('attack', 0)}/{c.get('durability') or c.get('health', 0)}"
    return "-"


def fmt_text(c):
    z = zh.get(c["id"], {})
    return (z.get("text") or c.get("text") or "").replace("\n", " ").replace("|", "/")


for cls in order:
    cards = sorted(
        by_class.get(cls, []),
        key=lambda x: (rarity_rank.get(x.get("rarity"), 9), x.get("cost") or 0, x["id"]),
    )
    if not cards:
        continue
    lines.append(f"## {cls}")
    lines.append("")
    lines.append("| ID | 中文名 | 英文名 | 费用 | 类型 | 稀有 | 身材 | 效果 |")
    lines.append("|----|--------|--------|------|------|------|------|------|")
    for c in cards:
        z = zh.get(c["id"], {})
        lines.append(
            "| `{id}` | {zh} | {en} | {cost} | {typ} | {rar} | {stats} | {text} |".format(
                id=c["id"],
                zh=z.get("name") or c.get("name"),
                en=c.get("name"),
                cost=c.get("cost"),
                typ=c.get("type"),
                rar=c.get("rarity"),
                stats=fmt_stats(c),
                text=fmt_text(c)[:180],
            )
        )
    lines.append("")

# tokens that matter for lethal (summons, choices)
lines.append("## 关键/衍生牌（节选，影响斩杀模拟）")
lines.append("")
important = []
for c in tokens:
    name = (zh.get(c["id"], {}).get("name") or c.get("name") or "")
    text = fmt_text(c)
    # keep minions / weapons / choice spells with damage/summon keywords
    if c.get("type") in ("MINION", "WEAPON") or any(
        k in text for k in ("伤害", "召唤", "消灭", "攻击", "Deal", "Summon", "Destroy")
    ):
        important.append(c)

important = sorted(important, key=lambda x: x["id"])[:80]
lines.append("| ID | 中文名 | 类型 | 费用 | 身材 | 效果 |")
lines.append("|----|--------|------|------|------|------|")
for c in important:
    z = zh.get(c["id"], {})
    lines.append(
        "| `{id}` | {zh} | {typ} | {cost} | {stats} | {text} |".format(
            id=c["id"],
            zh=z.get("name") or c.get("name"),
            typ=c.get("type"),
            cost=c.get("cost"),
            stats=fmt_stats(c),
            text=fmt_text(c)[:140],
        )
    )
lines.append("")

# lethal relevance quick triage
lines.append("## 斩杀助手接入优先级（初判）")
lines.append("")
lines.append("| 优先级 | 卡牌 | 理由 |")
lines.append("|--------|------|------|")
lines.append("| P0 | `CAP_106` 克罗雷船长 / 火炮手体系 | 回合末/攻击时随机直伤，影响斩杀与疲劳线 |")
lines.append("| P0 | `CAP_806` 雷斯·范盖斯特 | 复生复活并立即攻击，场面爆发 |")
lines.append("| P0 | `CAP_005` 马迪亚斯·肖尔 | 潜行攻击减费，可能联动奥秘/直伤手牌 |")
lines.append("| P1 | `CAP_405` 教父卡扎库斯 | 自定义庭审衍生牌，效果多样需枚举 |")
lines.append("| P1 | `CAP_407` 通缉海报 | 发现高费+预备，间接影响手牌斩杀 |")
lines.append("| P1 | 战士武器 `CAP_103` 等 | 武器攻脸/火炮协同 |")
lines.append("| P2 | 其余光环/资源/套系组件 | 视竞技场出场率再排 |")
lines.append("")
lines.append("## 本地数据状态")
lines.append("")
lines.append("- 当前仓库 `json/cards.json` / `cards_zhCN.json` **仍为 2026-06-11**，几乎未收录 `JAIL_`/`CAP_`。")
lines.append("- 建议下一步：用本次拉取的 HSJSON 覆盖更新本地卡表，再跑竞技场缺口扫描。")
lines.append("")

out = ROOT / "docs" / "AZEROTHS_MOST_WANTED_CARDS.md"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
print("wrote", out)
print("collectible by class:")
for cls in order:
    print(" ", cls, len(by_class.get(cls, [])))
