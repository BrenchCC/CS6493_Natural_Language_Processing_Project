# 得分计算算法修改说明

## 1. 目标

当前评估逻辑不是只看 `accuracy`，而是采用“正确性门控 + 效率惩罚”的两层设计：

1. 先判断答案是否正确
2. 错题直接记 `0`
3. 只在正确样本上，进一步考察回答是否过长、是否重复给答案、是否有过度反思
4. 同时输出逐样本得分与跨数据集聚合指标

核心原则：

- `accuracy` 是主指标
- `score_i` 是最终单样本得分
- `efficiency_i` 只在答对后才有实际意义
- `joint_score` 当前实现中等于 `mean_sample_score`

---

## 2. 单样本输入与派生字段

当前评测阶段会先从回答文本中抽取行为指标，再交给 `scoring.py` 计算得分。

### 2.1 主要输入字段

| 字段 | 类型 | 说明 |
|---|---|---|
| `accuracy` / `is_correct` | int | 是否答对，取值为 0 或 1 |
| `response_length_tokens` | int | 最终回答的近似 token 长度；按 `max(字符数 / 4, 单词数 / 0.75)` 向上取整估计 |
| `response_length_chars` | int | 最终回答字符长度 |
| `total_response_length_tokens` | int | 全流程生成文本的近似 token 长度；多轮/多采样方法会合并中间输出 |
| `total_response_length_chars` | int | 全流程生成文本字符长度 |
| `answer_count` | int | 全文命中的答案信号总次数 |
| `reflection_count` | int | 反思词命中次数 |
| `tail_ratio` | float | 从第一个答案信号开始的尾部字符占比 |

### 2.2 当前实现的语义细节

- `first_answer_token_idx` 名称里虽然有 `token`，实际记录的是**字符位置**。
- `tail_ratio` 按字符比例计算，而不是 tokenizer 级 token 比例。
- `answer_count` 是对全文答案信号模式直接计数，不会显式排除最后一次答案。
- `accuracy`、`answer_count`、`reflection_count`、`tail_ratio` 仍基于最终回答文本计算。
- `length_factor` 优先使用 `total_response_length_tokens`；如果该字段缺失，才回退到 `response_length_tokens` / 字符长度。
- 对多轮方法，`total_response_length_*` 的语义如下：
  - `self_refine`：`solve + critique + refine`
  - `plan_solve`：`plan + solve`
  - `self_ask`：`ask + answer`
  - `self_consistency`：所有 sampled responses
  - `tir`：完整 tool transcript

---

## 3. 当前默认参数

```python
SCORING_CONFIG = {
    "weights": {
        "answer": 0.5,
        "length": 0.3,
        "reflection": 0.2,
    },
    "params": {
        "length_ref": 1024,
        "tau_length": 512.0,
        "answer_count_ref": 1,
        "tau_answer_count": 1.0,
        "tail_ratio_ref": 0.2,
        "tau_tail_ratio": 0.2,
        "reflection_count_ref": 1,
        "tau_reflection": 2.0,
        "correct_score_floor": 0.6,
    },
}
```

要求：

```python
weights["answer"] + weights["length"] + weights["reflection"] == 1.0
```

说明：代码仍兼容旧别名参数，如 `L_ref`、`tau_d`、`a_star`、`tau_a` 等，但文档主名称以当前字段为准。

---

## 4. 单样本得分公式

### 4.1 长度因子

```python
length_factor = exp(-max(0, response_length - length_ref) / tau_length)
```

含义：

- 当前 `response_length` 优先指 `total_response_length_tokens`
- 不超过 `length_ref` 不扣分
- 超过参考长度后指数衰减
- 只惩罚过长，不惩罚过短

### 4.2 答案重复因子

```python
count_factor = exp(-max(0, answer_count - answer_count_ref) / tau_answer_count)

if answer_count < 2:
    tail_factor = 1.0
else:
    tail_factor = exp(-max(0, tail_ratio - tail_ratio_ref) / tau_tail_ratio)

answer_factor = count_factor * tail_factor
```

含义：

- `count_factor` 惩罚答案信号过多
- `tail_factor` 只在出现明显重复答案时才启用
- 这样可避免 `answer_count` 与 `tail_ratio` 双重过罚

### 4.3 反思因子

```python
reflection_factor = exp(-max(0, reflection_count - reflection_count_ref) / tau_reflection)
```

含义：

- 少量反思不扣分
- 只惩罚过多反思
- 当前实现是**单边惩罚**，不是对称惩罚

### 4.4 正确性门控

```python
efficiency_i = (
    answer_factor ** weight_answer
    * length_factor ** weight_length
    * reflection_factor ** weight_reflection
)

score_i = accuracy * (
    correct_score_floor
    + (1 - correct_score_floor) * efficiency_i
)
score_i = clip(score_i, 0.0, 1.0)
```

含义：

- 错题直接为 0
- 对题后以 `correct_score_floor` 保留主要准确率贡献
- 效率项只调节正确样本剩余部分
- 所有子因子都约束在 `(0, 1]`

---

## 5. 聚合指标

### 5.1 `accuracy`

```python
accuracy = mean(record["accuracy"])
```

### 5.2 `mean_efficiency_on_correct`

```python
mean_efficiency_on_correct = mean(record["efficiency_i"] for record in correct_records)
```

若没有正确样本，则记为 `0.0`。

### 5.3 `joint_score`

accuracy-first 评分下：

```python
joint_score = accuracy * (
    correct_score_floor
    + (1 - correct_score_floor) * mean_efficiency_on_correct
)
```

当前实现里直接写为：

```python
joint_score = mean_sample_score
```

即所有样本 `score_i` 的均值。

### 5.4 正确样本上的子因子均值

当前会聚合：

- `mean_length_factor_on_correct`
- `mean_answer_factor_on_correct`
- `mean_reflection_factor_on_correct`
- `mean_count_factor_on_correct`
- `mean_tail_factor_on_correct`

这些字段主要用于诊断 `joint_score` 下滑是由长度、答案重复还是反思惩罚导致。

---

## 6. 实际输出文件

### 6.1 `results/evaluated/*.jsonl`

逐样本评测结果会包含：

- `parsed_prediction`
- `accuracy`
- `response_length_tokens`
- `response_length_chars`
- `total_response_length_tokens`
- `total_response_length_chars`
- `reflection_count`
- `answer_count`
- `first_answer_token_idx`
- `tail_ratio`
- `length_factor`
- `count_factor`
- `tail_factor`
- `answer_factor`
- `reflection_factor`
- `efficiency_i`
- `score_i`

### 6.2 `results/summaries/aggregate_scores.csv`

按 `run_id + model + method + dataset` 聚合，核心列包括：

- `accuracy`
- `avg_response_length_tokens`
- `avg_response_length_chars`
- `avg_total_response_length_tokens`
- `avg_total_response_length_chars`
- `avg_score_i`
- `joint_score`
- `mean_sample_score`
- `mean_efficiency_on_correct`
- `correct_count`
- `total_count`
- `mean_length_factor_on_correct`
- `mean_answer_factor_on_correct`
- `mean_reflection_factor_on_correct`
- `mean_count_factor_on_correct`
- `mean_tail_factor_on_correct`

### 6.3 `results/summaries/single_metric_stats.csv`

对单一指标输出：

- `metric`
- `mean`
- `min`
- `max`

---

## 7. 实现注意事项

### 7.1 输入校验

需要保证：

```python
accuracy in {0, 1}
response_length >= 0
answer_count >= 0
reflection_count >= 0
0.0 <= tail_ratio <= 1.0
tau_length > 0
tau_answer_count > 0
tau_tail_ratio > 0
tau_reflection > 0
weight_answer + weight_length + weight_reflection == 1.0
```

### 7.2 缺失字段处理

如果 `total_response_length_tokens`、`response_length_tokens`、`total_response_length_chars` 与 `response_length_chars` 都缺失，会抛出：

```python
ValueError("Missing required metric field: response_length")
```

### 7.3 近似性质说明

- `response_length_tokens` 是近似值，不是 tokenizer 真正切词数；当前近似规则为 1 token ≈ 4 个字符，或 1 token ≈ 0.75 个英文单词，因此 75 个单词约等于 100 tokens
- `tail_ratio` 与 `first_answer_token_idx` 都是基于字符串位置计算

---

## 8. 与旧版本设计的主要差异

1. `reflection_factor` 从双边惩罚改成单边惩罚
2. `tail_factor` 只在 `answer_count >= 2` 时启用
3. `length_factor` 只惩罚过长，不惩罚过短
4. 默认权重改为 `answer=0.5 / length=0.3 / reflection=0.2`，正确样本分数下限为 `0.6`
5. 汇总输出从单一总分扩展为 `joint_score + mean_efficiency_on_correct + 子因子均值`
