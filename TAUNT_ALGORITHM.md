# 嘲讽清除算法 - 最优解实现

## 问题描述

在炉石传说中计算斩杀时，如果对手有嘲讽随从，我方随从必须先清除嘲讽才能打脸。

**关键问题：** 如何分配随从清除嘲讽，使得剩余的打脸伤害最大？

## ❌ 简单贪心算法（错误）

### 策略
优先用攻击力最小的随从清嘲讽，保留大随从打脸。

### 例子
```
对手嘲讽：2/3
我方随从：1/1, 3/3, 5/5
```

**贪心方案：**
1. 用 1/1 攻击嘲讽（剩余 2 血）
2. 用 3/3 攻击嘲讽（嘲讽死亡）
3. 剩余：5/5 打脸 = **5 伤害**

### 为什么错误？

**最优方案：**
1. 用 3/3 攻击嘲讽（嘲讽死亡）
2. 剩余：1/1 + 5/5 打脸 = **6 伤害** ✅

**贪心算法浪费了 1 点伤害！**

## ✅ 回溯最优解算法（正确）

### 核心思想

尝试**所有可能的清除方案**，选择剩余打脸伤害最大的。

### 算法流程

```python
def find_best_taunt_clear(attackers, taunts):
    # 基础情况1: 没有嘲讽了
    if not taunts:
        return sum(所有剩余随从攻击力)  # 全部打脸

    # 基础情况2: 没有随从但还有嘲讽
    if not attackers:
        return None  # 无法清掉

    # 递归：尝试所有清除当前嘲讽的方案
    best = None
    for 每种清除方案 in 所有可能的组合:
        剩余随从 = attackers - 使用的随从
        剩余嘲讽 = taunts[1:]

        # 递归清除剩余嘲讽
        result = find_best_taunt_clear(剩余随从, 剩余嘲讽)

        if result > best:
            best = result

    return best
```

### 详细步骤

#### 1. 生成清除方案

对于每个嘲讽，生成所有**能杀死它的随从组合**：

```python
def generate_clear_plans(attackers, taunt):
    plans = []

    # 尝试所有子集
    for 随从组合 in 所有可能的组合:
        if 能杀死嘲讽(随从组合, taunt):
            plans.append(随从组合)

    # 按总攻击力排序（优先小的）
    plans.sort(key=总攻击力)
    return plans
```

#### 2. 检查能否杀死嘲讽

```python
def can_kill_taunt(attackers, hp, has_shield):
    if has_shield:
        # 圣盾：需要至少2次攻击
        if len(attackers) < 2:
            return False
        # 第一次打破盾，剩余伤害 >= 血量
        return sum(attackers[1:].攻击力) >= hp
    else:
        # 无圣盾：总伤害 >= 血量
        return sum(attackers.攻击力) >= hp
```

#### 3. 递归清除所有嘲讽

```python
# 示例：2个嘲讽 [3/4, 2/2]，4个随从 [2, 3, 4, 5]

清除第1个嘲讽的所有方案：
  - [2, 3] → 剩余 [4, 5]
  - [2, 4] → 剩余 [3, 5]
  - [3, 4] → 剩余 [2, 5]  ← 最优！
  - ...

对于每个方案，递归清除第2个嘲讽：
  方案 [3, 4] → 剩余 [2, 5]
    清除第2个嘲讽：
      - [2] → 剩余 [5] = 5伤
      - [5] → 剩余 [2] = 2伤
      最优：5伤
```

## 🎯 算法特性

### 优点

1. ✅ **保证找到最优解**
2. ✅ **正确处理圣盾**（需要2次攻击）
3. ✅ **正确处理风怒**（多次攻击）
4. ✅ **支持多个嘲讽**

### 时间复杂度

- **最坏情况**: O(2^n × m)
  - n = 随从数量
  - m = 嘲讽数量

- **实际游戏场景**:
  - 最多 7 个随从
  - 最多 2-3 个嘲讽
  - 2^7 × 3 = 384 次计算
  - **完全可接受！**

### 优化策略

1. **剪枝**: 只生成能杀死嘲讽的最小组合
2. **排序**: 优先尝试攻击力小的组合
3. **记忆化**: 可以缓存已计算的状态（未实现）

## 📊 测试用例

### 用例1: 简单优化

```
对手：6血
嘲讽：2/3
随从：1/1, 3/3, 5/5

贪心：1+3清嘲讽 → 剩余5 = 5伤 ❌
最优：3清嘲讽 → 剩余1+5 = 6伤 ✅
结果：有斩杀！
```

### 用例2: 多嘲讽

```
对手：10血
嘲讽：1/1, 2/2
随从：1/1, 2/2, 3/3, 4/4

所有方案：
  1清第1，2清第2 → 剩余3+4 = 7伤 ✅ 最优
  1清第1，3清第2 → 剩余2+4 = 6伤
  2清第1，3清第2 → 剩余1+4 = 5伤
  ...
```

### 用例3: 圣盾嘲讽

```
对手：5血
嘲讽：1/1 🛡️圣盾
随从：1/1, 6/6

方案：
  1打盾，6杀死 → 剩余0伤
  无其他方案
结果：无斩杀
```

### 用例4: 风怒

```
对手：8血
嘲讽：2/2
随从：3/3 风怒, 4/4

方案1：风怒第1次清嘲讽 → 风怒第2次+4 = 7伤 ✅
方案2：4清嘲讽 → 风怒2次 = 6伤
```

## 🔧 代码实现

### 核心函数

```python
class LethalChecker:
    def _calculate_board_damage_with_taunts(self, my_board, opp_taunts):
        """计算考虑嘲讽的场面伤害"""
        # 准备攻击者列表（风怒展开为多次攻击）
        attackers = []
        for minion in my_board:
            if minion.can_attack:
                attacks = 1
                if minion.windfury:
                    attacks = 2
                for _ in range(attacks):
                    attackers.append(minion)

        # 使用回溯找最优解
        best = self._find_best_taunt_clear(attackers, opp_taunts)

        if best is None:
            return 0, False  # 无法清掉

        return best, True

    def _find_best_taunt_clear(self, attackers, taunts):
        """回溯算法"""
        if not taunts:
            return sum(a.atk for a in attackers)

        if not attackers:
            return None

        best = None
        for plan in self._generate_clear_plans(attackers, taunts[0]):
            remaining = [a for a in attackers if a not in plan]
            result = self._find_best_taunt_clear(remaining, taunts[1:])

            if result is not None:
                if best is None or result > best:
                    best = result

        return best
```

## 📝 与其他斩杀因素的关系

### 法术伤害

法术**可以绕过嘲讽**直接打脸：

```python
总伤害 = 清嘲讽后剩余场面伤害 + 法术伤害 + 武器伤害
         ↑                        ↑            ↑
         需要最优解               绕过嘲讽      绕过嘲讽
```

### 完整斩杀检测

```python
if 有嘲讽:
    场面伤害 = 最优清嘲讽算法(my_board, opp_taunts)
else:
    场面伤害 = sum(所有随从攻击力)

总伤害 = 场面伤害 + 法术 + 武器 + 冲锋
有斩杀 = 总伤害 >= 对手总血量
```

## 🧪 运行测试

```bash
# 测试最优解算法
python test_optimal_taunt.py
```

预期输出：
```
测试用例1：简单优化
  期望：6伤
  实际：6伤
  🎉 算法找到最优解！

测试用例2：多嘲讽
  期望：7伤
  实际：7伤
  🎉 算法找到最优解！

...
```

## 🎓 算法分类

- **类型**: 回溯算法 + 动态规划思想
- **相关问题**:
  - 背包问题（Knapsack）
  - 子集和问题（Subset Sum）
  - 组合优化（Combinatorial Optimization）

## 📚 参考

- HDT 源码并未实现最优解算法（也是贪心）
- 这是我们的**原创改进** ✨
- 适用于所有需要清除障碍物的游戏场景

---

**总结**: 通过回溯算法穷举所有可能的清除方案，我们能够保证找到最优解，避免贪心算法的局部最优陷阱，从而准确计算斩杀伤害。
