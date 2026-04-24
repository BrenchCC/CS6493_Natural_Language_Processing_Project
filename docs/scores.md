Brench, 下面这版可以直接作为 coding agent 的修改说明。

````markdown
# 得分计算算法修改说明

## 1. 目标

当前评估算法需要从单纯正确率扩展为：

1. 正确率优先
2. 错题直接得 0 分
3. 只在答对的样本上，进一步评价回答是否简洁、是否重复答案、是否存在过多反思
4. 最终同时输出：
   - accuracy
   - mean_efficiency_on_correct
   - joint_score
   - 各子因子均值

核心原则：

- `accuracy` 是主指标
- `score_i` 是正确性门控后的综合得分
- `efficiency_i` 只在正确样本上有意义
- `c = 0` 时，`score_i = 0`

---

## 2. 单样本输入字段

每条样本至少需要包含以下字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `is_correct` | int | 是否答对，取值为 0 或 1 |
| `response_length` | int | 输出长度，可以是 token 数或字符数，但全局必须一致 |
| `answer_count` | int | 除最终答案外，正文中额外答案信号出现次数 |
| `tail_ratio` | float | 第二次答案信号后剩余 token 占总 token 的比例，范围 `[0, 1]` |
| `reflection_count` | int | 反思词或自我修正信号命中次数 |

字段命名可按现有代码适配，但语义必须保持一致。

---

## 3. 推荐参数

```python
SCORING_CONFIG = {
    "length_ref": 1024,
    "tau_length": 512,

    "answer_count_ref": 1,
    "tau_answer_count": 1.0,

    "tail_ratio_ref": 0.2,
    "tau_tail_ratio": 0.2,

    "reflection_count_ref": 1,
    "tau_reflection": 2.0,

    "weight_length": 0.5,
    "weight_answer": 0.3,
    "weight_reflection": 0.2,
}
````

要求：

```python
weight_length + weight_answer + weight_reflection == 1.0
```

如果已有配置系统，将这些参数接入现有 config。

---

## 4. 单样本得分公式

### 4.1 长度因子

```python
length_factor = exp(-max(0, response_length - length_ref) / tau_length)
```

含义：

* 不超过 `length_ref` 时不扣分
* 超过参考长度后指数衰减
* 只惩罚过长，不惩罚过短

---

### 4.2 答案重复因子

答案因子由两部分组成：

```python
answer_factor = count_factor * tail_factor
```

#### count_factor

```python
count_factor = exp(-max(0, answer_count - answer_count_ref) / tau_answer_count)
```

含义：

* 允许少量中间答案信号
* 超过 `answer_count_ref` 后开始惩罚

#### tail_factor

```python
if answer_count < 2:
    tail_factor = 1.0
else:
    tail_factor = exp(-max(0, tail_ratio - tail_ratio_ref) / tau_tail_ratio)
```

含义：

* 只有出现明显重复答案时，才启用拖尾惩罚
* 避免 `answer_count` 和 `tail_ratio` 重复扣分过重

---

### 4.3 反思因子

```python
reflection_factor = exp(-max(0, reflection_count - reflection_count_ref) / tau_reflection)
```

含义：

* 少量反思不扣分
* 只惩罚过多反思
* 不使用 `abs(reflection_count - reflection_count_ref)`

原因：

* 目标是减少冗余反思
* 完全没有反思不应该被惩罚

---

### 4.4 正确性门控

```python
efficiency_score = (
    answer_factor ** weight_answer
    * length_factor ** weight_length
    * reflection_factor ** weight_reflection
)

sample_score = is_correct * efficiency_score
sample_score = clip(sample_score, 0.0, 1.0)
```

含义：

* 答错直接为 0
* 答对后再看效率和冗余程度
* 所有因子都在 `(0, 1]` 范围内

---

## 5. 汇总指标

对整个评估集输出以下指标。

### 5.1 accuracy

```python
accuracy = mean(is_correct)
```

---

### 5.2 mean_efficiency_on_correct

只在正确样本上计算：

```python
mean_efficiency_on_correct = mean(efficiency_score for sample if is_correct == 1)
```

如果没有正确样本：

```python
mean_efficiency_on_correct = 0.0
```

---

### 5.3 joint_score

推荐定义：

```python
joint_score = accuracy * mean_efficiency_on_correct
```

它等价于所有样本 `sample_score` 的均值：

```python
joint_score = mean(sample_score)
```

但建议代码里显式同时计算并校验二者是否一致。

---

### 5.4 子因子均值

建议只在正确样本上统计：

```python
mean_length_factor_on_correct
mean_answer_factor_on_correct
mean_reflection_factor_on_correct
mean_count_factor_on_correct
mean_tail_factor_on_correct
```

这些指标用于诊断模型为什么 joint_score 下降。

---

## 6. 推荐输出结构

```json
{
  "accuracy": 0.82,
  "mean_efficiency_on_correct": 0.76,
  "joint_score": 0.6232,
  "mean_sample_score": 0.6232,
  "correct_count": 82,
  "total_count": 100,
  "factor_stats_on_correct": {
    "mean_length_factor": 0.81,
    "mean_answer_factor": 0.88,
    "mean_reflection_factor": 0.74,
    "mean_count_factor": 0.91,
    "mean_tail_factor": 0.96
  },
  "config": {
    "length_ref": 1024,
    "tau_length": 512,
    "answer_count_ref": 1,
    "tau_answer_count": 1.0,
    "tail_ratio_ref": 0.2,
    "tau_tail_ratio": 0.2,
    "reflection_count_ref": 1,
    "tau_reflection": 2.0,
    "weight_length": 0.5,
    "weight_answer": 0.3,
    "weight_reflection": 0.2
  }
}
```

---

## 7. 实现注意事项

### 7.1 输入校验

需要检查：

```python
is_correct in {0, 1}
response_length >= 0
answer_count >= 0
reflection_count >= 0
0.0 <= tail_ratio <= 1.0
tau_length > 0
tau_answer_count > 0
tau_tail_ratio > 0
tau_reflection > 0
weight_length + weight_answer + weight_reflection == 1.0
```

---

### 7.2 缺失字段处理

如果缺失字段，建议直接抛出明确错误：

```python
ValueError("Missing required metric field: response_length")
```

不要静默填 0。

---

### 7.3 clip 逻辑

```python
sample_score = min(max(sample_score, 0.0), 1.0)
```

虽然理论上不会超过 1，但保留 clip，防止异常输入导致错误。

---

## 9. 和旧算法的关键差异

需要重点修改以下逻辑：

1. 保留 `is_correct` 作为硬门控
2. 将 `reflection_factor` 从双边惩罚改成单边惩罚
3. `tail_factor` 只在 `answer_count >= 2` 时启用
4. `length_factor` 只惩罚过长
5. 汇总时不要只输出一个总分，必须拆出：

   * accuracy
   * mean_efficiency_on_correct
   * joint_score
   * factor_stats_on_correct

---

## 10. 最终推荐公式

```text
length_factor
= exp(-max(0, L - L_ref) / tau_length)

count_factor
= exp(-max(0, answer_count - answer_count_ref) / tau_answer_count)

tail_factor
= 1, if answer_count < 2
= exp(-max(0, tail_ratio - tail_ratio_ref) / tau_tail_ratio), otherwise

answer_factor
= count_factor * tail_factor

reflection_factor
= exp(-max(0, reflection_count - reflection_count_ref) / tau_reflection)

efficiency_score
= answer_factor ^ weight_answer
  * length_factor ^ weight_length
  * reflection_factor ^ weight_reflection

sample_score
= is_correct * efficiency_score

joint_score
= mean(sample_score)
= accuracy * mean_efficiency_on_correct
```
