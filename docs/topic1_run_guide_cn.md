# Topic 1 实验框架使用说明

本文档说明当前 Topic 1 实验框架的实际运行方式、结果目录结构、两个模型配置文件的用途，以及评估得分配置的含义。

## 1. 运行前准备

### 1.1 建议环境
- 推荐直接使用已有 `conda` 环境：`llm_train`
- 若环境缺少依赖，可执行：

```bash
conda activate llm_train
pip install -r requirements.txt
```

### 1.1.1 模型下载

当前配置默认优先解析本地模型目录，建议先执行：

```bash
bash scripts/models/download_models.sh
```

下载后本地目录默认为：
- `models/DeepSeek-R1-Distill-Qwen-1.5B`
- `models/Qwen2.5-Math-1.5B-Instruct`

### 1.2 固定样本数据
当前默认使用以下三份固定样本：

- `data/processed/math500_sample.jsonl`
- `data/processed/gsm8k_sample.jsonl`
- `data/processed/aime2024_sample.jsonl`

若要重新抽样：

```bash
bash scripts/data/prepare_samples.sh 50 6493 data/processed
```

说明：
- `math500` 与 `gsm8k` 当前默认上限为 `50`
- `aime2024` 当前默认上限为 `30`

---

## 2. 配置文件说明

### 2.1 基础配置
- `configs/yaml/base.yaml`
  - 同时包含两个模型
  - 适合跑完整实验矩阵

### 2.2 单模型配置
- `configs/yaml/qwen_math.yaml`
  - 只保留 `Qwen/Qwen2.5-Math-1.5B-Instruct`
  - 适合单独跑 Qwen 系列实验
- `configs/yaml/deepseek_r1_math.yaml`
  - 只保留 `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`
  - 适合单独跑 DeepSeek-R1 系列实验

### 2.3 两个模型的思考模式差异

#### `Qwen/Qwen2.5-Math-1.5B-Instruct`
- 属于普通文本模型
- 不依赖 `<think>` 通道
- 通过 `cot_zero` / `cot_few_shot` / `self_refine` / `self_consistency` 这类 prompt 方法显式触发推理
- 配置中表现为：
  - `reasoning_mode: prompt_cot`
  - `enable_thinking: null`
  - `cannot_disable_thinking: false`

#### `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`
- 属于原生思考模型
- 会输出 `<think> ... </think>` 风格思考内容
- 当前默认开启 thinking，但配置上**允许显式切换**
- 配置中表现为：
  - `reasoning_mode: native_thinking`
  - `enable_thinking: true`
  - `cannot_disable_thinking: false`

这两个配置都会写进运行摘要，方便后续分析时区分“提示推理模型”和“原生思考模型”。

---

## 3. 推荐运行方式

### 3.1 跑单模型 + 单方法 + 3 数据集
这是当前框架推荐的最小实验单元。

#### 跑 Qwen + `cot_zero`

```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/qwen_math.yaml "Qwen/Qwen2.5-Math-1.5B-Instruct" 50 "" cot_zero
```

#### 跑 DeepSeek-R1 + `self_consistency`

```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/deepseek_r1_math.yaml "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B" 30 "" self_consistency
```

参数说明：
- 第 1 个参数：配置文件路径
- 第 2 个参数：模型名
- 第 3 个参数：样本上限覆盖值，传 `0` 表示使用 YAML 里的默认值
- 第 4 个参数：数据集过滤，空字符串表示默认跑 `math500,gsm8k,aime2024`
- 第 5 个参数：方法过滤，支持逗号分隔

### 3.1.1 跑 `tir`

`tir` 当前是工具循环模式，不是普通单轮 prompt：

- 模型输出 ` ```python ` 代码块后会暂停
- 框架执行代码并将结果以 ` ```output ` 回填
- 每轮最多执行一个代码块
- 最终答案要求使用 `Final Answer: \boxed{...}`

示例：

```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/qwen_math.yaml "Qwen/Qwen2.5-Math-1.5B-Instruct" 30 "gsm8k" tir
```

### 3.2 跑单模型 + 多方法

```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/qwen_math.yaml "Qwen/Qwen2.5-Math-1.5B-Instruct" 50 "" cot_zero,cot_few_shot,self_refine
```

### 3.3 跑完整实验矩阵

```bash
bash scripts/infer/run_experiments.sh configs/yaml/base.yaml
```

该命令会读取 `base.yaml` 中的模型列表与方法列表，依次执行所有组合。

---

## 4. 结果目录说明

当前所有结果都统一写在 `results/` 下。

### 4.1 完整推理结果
- 目录：`results/raw/`
- 文件内容：每条样本的完整推理结果 JSONL
- 典型字段包括：
  - `run_id`
  - `model_name`
  - `method_name`
  - `dataset_name`
  - `question`
  - `gold_answer`
  - `input_messages`
  - `raw_response`
  - `final_response`
  - `intermediate_outputs`
  - `metadata`
  - `error`

这部分是**最完整的原始产物**，后续若要复查模型输出、分析思考链、统计特殊行为，优先看这里。

### 4.2 逐样本评测结果
- 目录：`results/evaluated/`
- 文件内容：在 raw 基础上补充评测字段
- 典型新增字段包括：
  - `parsed_prediction`
  - `accuracy`
  - `response_length_tokens`
  - `response_length_chars`
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

### 4.3 综合指标表
- 目录：`results/summaries/`
- 文件：`aggregate_scores.csv`

该文件用于看**每个数据集和 overall 的综合聚合结果**，适合直接拿来做报告表格。

### 4.4 单一指标统计表
- 目录：`results/summaries/`
- 文件：`single_metric_stats.csv`

该文件按单个指标分别统计 `mean / min / max`，适合做更细的误差分析与作图。

### 4.5 运行日志
- 目录：`results/logs/`
- 文件模式：`run_log__{run_id}__{model_alias}__{method}.log`

运行时会有两份一致的日志输出：
- 终端实时打印
- `results/logs/` 下的 `.log` 文件持续追加保存

为避免刷屏：
- 不再输出逐样本成功日志
- 推理阶段按数据集显示 `tqdm` 进度条
- 评估阶段按结果文件显示 `tqdm` 进度条

日志记录的内容包括：
- run 开始
- 引擎构建开始/结束
- 数据集开始/结束
- 单样本失败
- raw 写盘开始/结束
- 评估开始
- summary 开始
- run 完成

### 4.6 运行摘要
- 目录：`results/summaries/`
- 文件模式：`run_summary__{run_id}__{model_alias}__{method}.json`

该文件会集中记录：
- 当前 run 的模型与方法
- 每个数据集的聚合结果
- overall 聚合结果
- 产物文件路径
- 模型思考模式设置

---

## 5. 评估与汇总命令

### 5.1 单独执行评估

```bash
bash scripts/eval/evaluate_runs.sh configs/yaml/base.yaml
```

说明：
- 该命令会遍历 `results/raw/` 下的 JSONL
- 对每个测试集文件做逐样本评测
- 当前评测阶段支持**每个测试集文件内部多线程加速**
- 线程数由 `run.eval_num_workers` 控制

### 5.2 单独生成汇总

```bash
bash scripts/eval/summarize_scores.sh configs/yaml/base.yaml
```

---

## 6. 评分配置解释

评分配置位于 YAML 的 `scoring` 段，用来控制复合得分 `score_i` 的计算。

### 6.1 评分思想
当前复合得分遵循一个原则：

- **先看是否答对**
- 在答对前提下，再根据回答长度、答案信号次数、反思行为等进行衰减

也就是说：
- 如果题目答错，`score_i = 0`
- 如果答对，得分会根据输出是否过长、是否多次重复答案、是否存在明显过度反思继续下降

### 6.2 `weights`

#### `weights.answer`
- 控制“答案行为”这一项的权重
- 主要对应：
  - `answer_count`
  - `tail_ratio`
- 越大表示越重视“不要反复给答案、不要在给出答案后继续拖尾”

#### `weights.length`
- 控制回答长度惩罚的权重
- 越大表示越偏好**更短、更克制**的回答

#### `weights.reflection`
- 控制反思行为惩罚的权重
- 越大表示越敏感于“过度反思”或“反复自我检查”

### 6.3 `params`

#### `length_ref`
- 长度参考值
- 当 `response_length_tokens` 超过它时，开始触发长度惩罚

#### `tau_length`
- 长度惩罚衰减速度
- 越小，超过 `length_ref` 后掉分越快

#### `answer_count_ref`
- 期望的答案信号次数上界
- 如果 `answer_count` 超过这个值，就开始被惩罚

#### `tau_answer_count`
- `answer_count` 惩罚衰减速度
- 越小，超过 `answer_count_ref` 后掉分越快

#### `tail_ratio_ref`
- 答案出现后允许的拖尾比例阈值
- 当前仅在 `answer_count >= 2` 时启用拖尾惩罚

#### `tau_tail_ratio`
- `tail_ratio` 惩罚衰减速度
- 越小，答案后拖尾会被更严厉惩罚

#### `reflection_count_ref`
- 少量反思允许存在
- 只有反思次数超过该参考值时才开始惩罚

#### `tau_reflection`
- 反思惩罚衰减速度
- 越小，对过度反思越敏感

### 6.4 什么时候调这些参数

#### 若你觉得模型输出太长
- 优先调：
  - 降低 `length_ref`
  - 降低 `tau_length`
  - 或提高 `weights.length`

#### 若你觉得模型重复写答案太多
- 优先调：
  - 降低 `answer_count_ref`
  - 降低 `tau_answer_count`
  - 或提高 `weights.answer`

#### 若你觉得模型给出答案后还在继续啰嗦
- 优先调：
  - 降低 `tail_ratio_ref`
  - 降低 `tau_tail_ratio`

#### 若你想弱化复合分，只更看重正确率
- 可以把 `weights.answer / length / reflection` 调得更平缓
- 或仅在分析阶段主要使用 `accuracy`

---

## 7. 多线程评测说明

评测调用阶段当前已经支持多线程。

配置项：

```yaml
run:
  eval_num_workers: 8
```

含义：
- 对每个测试集对应的 raw JSONL 文件，在评测时开 `4` 个线程并发处理样本
- 这只影响评测阶段，不影响模型推理阶段

建议：
- 小规模实验：`2~4`
- 中等规模实验：`4~8`
- 若 CPU 紧张或出现上下文切换开销过大，可适当调小

---

## 8. 一个常见工作流

### 工作流 A：先跑 Qwen 主实验

```bash
conda activate llm_train
bash scripts/infer/run_single_model_all.sh configs/yaml/qwen_math.yaml "Qwen/Qwen2.5-Math-1.5B-Instruct" 50 "" cot_zero,cot_few_shot,self_refine,self_consistency,tir
```

### 工作流 B：再跑 DeepSeek-R1 主实验

```bash
conda activate llm_train
bash scripts/infer/run_single_model_all.sh configs/yaml/deepseek_r1_math.yaml "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B" 30 "" cot_zero,cot_few_shot,self_refine,self_consistency,tir
```

### 工作流 C：最后统一补汇总

```bash
conda activate llm_train
bash scripts/eval/evaluate_runs.sh configs/yaml/base.yaml
bash scripts/eval/summarize_scores.sh configs/yaml/base.yaml
```

---

## 9. 建议保留的核心产物

如果后续要写报告，建议至少保留以下文件：

- `results/raw/*.jsonl`：完整推理结果
- `results/evaluated/*.jsonl`：逐样本评测结果
- `results/summaries/aggregate_scores.csv`：综合指标表
- `results/summaries/single_metric_stats.csv`：单指标表
- `results/logs/*.log`：运行日志
- `results/summaries/run_summary__*.json`：每次 run 的摘要

这样后续做表格、画图、查错和复现实验会比较完整。
