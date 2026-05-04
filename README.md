# CS6493 Natural Language Processing Project

## Topic 1: Mathematical Reasoning of Small Open-Weight LLMs

本项目用于完成 CS6493 课程 Topic 1 的实验框架，统一实验单元为：`一个模型 + 一种提示方法 + 3 份数据集 + 自动评估 + 运行汇总`。

当前框架支持：
1. 固定抽样数据准备
2. 本地 vLLM 推理
3. API 推理与 reasoning usage 记录
4. 逐样本自动评估与复合打分
5. 跨数据集聚合汇总
6. 报告筛选表导出
7. 运行日志与完整产物落盘

## 实验设置

### 模型
- `Qwen/Qwen2.5-Math-1.5B-Instruct`
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`

### 数据集
- `HuggingFaceH4/MATH-500`
- `openai/gsm8k`
- `HuggingFaceH4/aime_2024`

### 方法
- `cot_zero`
- `cot_few_shot`
- `self_refine`
- `self_consistency`
- `plan_solve`
- `tir`

其中：
- `plan_solve` 采用两阶段流程：先生成简短计划，再按计划完成求解
- `tir` 当前采用 agentic 工具循环：模型输出 ` ```python ` 代码块后暂停，框架在隔离 Python 子进程中执行代码，再将结果以 ` ```output ` 回填，模型继续推理
- `tir` 最终答案要求严格输出为 `Final Answer: \boxed{...}`

## 项目结构

```text
configs/yaml/                  # 基础配置与模型专用 YAML
data/processed/                # 固定抽样后的 JSONL
docs/                          # 项目说明文档
infer_exp/                     # 实验主调度与配置解析
evaluation/                    # 指标提取、打分与汇总
prompts/                       # 各提示方法实现与注册
scripts/data/                  # 数据准备脚本
scripts/infer/                 # 推理脚本
scripts/eval/                  # 评估与汇总脚本
vllm_server/                   # 本地 vLLM 引擎封装
tests/                         # 单元测试
results/raw/                   # 原始推理结果
results/evaluated/             # 评估后逐样本结果
results/summaries/             # 聚合统计与运行摘要
results/logs/                  # 运行日志
results/raw_reasoning_usage/   # API reasoning 运行的原始结果
results/evaluated_reasoning_usage/   # 带 reasoning usage 的逐样本结果
results/summaries_reasoning_usage/   # reasoning usage 运行汇总
results/logs_reasoning_usage/        # reasoning usage 运行日志
delivery/reports/              # 最终中英文报告与 PDF
scripts/reports/               # 报告筛选与导出脚本
```

## 环境准备

建议 Python 版本：`3.10+`

推荐新建虚拟环境后安装依赖：

```bash
pip install -U pip
pip install -r requirements.txt
```

### 模型下载

当前 YAML 默认优先解析本地模型目录，推荐先执行：

```bash
bash scripts/models/download_models.sh
```

默认下载位置：
- `models/DeepSeek-R1-Distill-Qwen-1.5B`
- `models/Qwen2.5-Math-1.5B-Instruct`

## 配置文件

### 基础配置
- `configs/yaml/base.yaml`：包含两个模型，适合跑完整实验矩阵

### 单模型配置
- `configs/yaml/qwen_math.yaml`：仅保留 Qwen 配置
- `configs/yaml/deepseek_r1_math.yaml`：仅保留 DeepSeek-R1 配置
- `configs/yaml/api_qwen_math_reasoning_usage.yaml`：Qwen 的 API reasoning 配置
- `configs/yaml/api_deepseek_r1_math_reasoning_usage.yaml`：DeepSeek 的 API reasoning 配置

### 两个模型的推理模式差异
- `Qwen/Qwen2.5-Math-1.5B-Instruct` 是文本模型，依赖 `cot` 类 prompt 显式触发推理
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B` 是原生思考模型，当前默认开启 `thinking`，但配置允许显式切换

## 快速开始

### 1. 准备固定样本

```bash
bash scripts/data/prepare_samples.sh 50 6493 data/processed
```

说明：
- 第 1 个参数：每个数据集抽样上限
- 第 2 个参数：随机种子
- 第 3 个参数：输出目录
- 当前配置默认读取上限为：`math500=50`、`gsm8k=50`、`aime2024=30`

### 2. 运行单个实验单元

运行 `Qwen + cot_zero + 3 个数据集`：

```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/qwen_math.yaml "Qwen/Qwen2.5-Math-1.5B-Instruct" 50 "" cot_zero
```

运行 `DeepSeek-R1 + self_consistency + 3 个数据集`：

```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/deepseek_r1_math.yaml "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B" 30 "" self_consistency
```

参数说明：
- 第 1 个参数：配置文件路径
- 第 2 个参数：模型名
- 第 3 个参数：样本上限覆盖值，传 `0` 表示沿用 YAML 默认值
- 第 4 个参数：数据集过滤，空字符串表示默认跑 `math500,gsm8k,aime2024`
- 第 5 个参数：方法过滤，支持逗号分隔

### 3. 运行完整实验矩阵

```bash
bash scripts/infer/run_experiments.sh configs/yaml/base.yaml
```

该命令会读取 `configs/yaml/base.yaml` 中声明的模型与方法组合，依次执行整套实验。

也支持附加过滤参数：

```bash
bash scripts/infer/run_experiments.sh configs/yaml/base.yaml "Qwen/Qwen2.5-Math-1.5B-Instruct" "cot_zero,tir" "gsm8k" 20
```

### 4. 单独执行评估

```bash
bash scripts/eval/evaluate_runs.sh configs/yaml/base.yaml
```

### 5. 单独生成汇总

```bash
bash scripts/eval/summarize_scores.sh configs/yaml/base.yaml
```

### 6. 运行 API reasoning 实验

Qwen 的 `plan_solve,tir`：

```bash
bash scripts/infer/run_api_qwen_reasoning.sh
```

DeepSeek 的 `plan_solve,tir`：

```bash
bash scripts/infer/run_api_deepseek_reasoning.sh
```

带参数示例：

```bash
bash scripts/infer/run_api_qwen_reasoning.sh configs/yaml/api_qwen_math_reasoning_usage.yaml 50 "gsm8k,aime2024" "plan_solve,tir"
```

说明：
- 这些脚本默认写入 `results/*_reasoning_usage/`
- 会记录完整生成长度所需的 usage / reasoning 元数据
- `tir` 的代码执行环境由 YAML 中 `execution_conda_env` 控制

### 7. 生成报告筛选表

从常规汇总和 reasoning usage 汇总中，按 `model + method + dataset` 与 `model + method(overall)` 各保留一条报告用结果：

```bash
python scripts/reports/select_report_scores.py \
  --aggregate results/summaries/aggregate_scores.csv \
  --aggregate results/summaries_reasoning_usage/aggregate_scores.csv
```

输出：
- `results/summaries/report_selected_dataset_scores.csv`
- `results/summaries/report_selected_overall_scores.csv`

筛选规则：
- 仅保留 `cot_zero`、`cot_few_shot`、`self_refine`、`self_consistency`、`plan_solve`、`tir`
- 同组内优先选择 `joint_score` 更高的结果
- 对 `plan_solve` 与 `tir`，如果存在带完整 usage 的结果，则优先从这些结果中挑选
- 输出表不会暴露 `run_id`、`source_file` 与内部 `avg_api_*` 字段

## 输出产物

### 原始推理结果
- 目录：`results/raw/`
- 文件模式：`{model_alias}__{dataset}__{method}__{run_id}.jsonl`
- 典型字段：`question`、`gold_answer`、`input_messages`、`raw_response`、`final_response`、`intermediate_outputs`、`metadata`、`error`

### 逐样本评测结果
- 目录：`results/evaluated/`
- 新增字段：`parsed_prediction`、`accuracy`、`response_length_tokens`、`response_length_chars`、`reflection_count`、`answer_count`、`first_answer_token_idx`、`tail_ratio`、`length_factor`、`count_factor`、`tail_factor`、`answer_factor`、`reflection_factor`、`efficiency_i`、`score_i`

对于 API reasoning 运行：
- 目录：`results/evaluated_reasoning_usage/`
- 额外会保留完整生成成本所需的 usage / reasoning 元数据

### 聚合统计
- `results/summaries/aggregate_scores.csv`
- `results/summaries/single_metric_stats.csv`
- `results/summaries_reasoning_usage/aggregate_scores.csv`
- `aggregate_scores.csv` 重点字段包括：`accuracy`、`joint_score`、`mean_sample_score`、`mean_efficiency_on_correct`、`correct_count`、`total_count`、`mean_*_factor_on_correct`
- `single_metric_stats.csv` 按单一指标输出 `mean / min / max`

### 运行摘要
- 文件模式：`results/summaries/run_summary__{run_id}__{model_alias}__{method}.json`
- 内容包含：每个数据集聚合结果、overall 聚合结果、模型思考模式设置、产物路径

### 运行日志
- 文件模式：`results/logs/run_log__{run_id}__{model_alias}__{method}.log`
- 推理运行时会通过 `logging` 实时打印到终端，同时将同样格式的日志文本追加写入该 `.log` 文件
- 不再打印逐样本成功日志；推理与评估进度改为通过 `tqdm` 进度条展示
- 日志事件包括：`run_started`、`engine_build_started`、`engine_build_completed`、`dataset_started`、`sample_failed`、`raw_write_started`、`evaluation_started`、`dataset_completed`、`summary_started`、`run_completed`

## 关键配置说明

配置主文件位于 `configs/yaml/base.yaml`。

### `run`
- `output_dir`：原始结果目录
- `evaluated_dir`：评估结果目录
- `summary_dir`：汇总目录
- `log_dir`：运行日志目录
- `num_workers`：保留的运行配置字段，当前主推理循环未按该值并发调度样本
- `eval_num_workers`：评测阶段单文件内部线程数
- `micro_batch_size`：保留字段，当前主推理脚本未直接消费

### `models.settings`
- `reasoning_mode`：区分 `prompt_cot` 与 `native_thinking`
- `enable_thinking`：是否向底层引擎透传 thinking 开关
- `cannot_disable_thinking`：标记模型是否天然不能关闭思考
- `disable_sampling`：是否在运行时强制关闭采样

### `datasets`
- `name`：数据集名称
- `sample_path`：固定样本 JSONL 路径
- `max_samples`：读取上限

### `method_configs`
- 通用采样参数：`temperature`、`top_p`、`max_tokens`
- 可选采样控制：`repetition_penalty`
- `plan_solve`：额外使用 `max_plan_steps`
- `self_consistency`：额外使用 `n_samples`
- `tir`：额外可配置 `max_tool_rounds`、`python_timeout`、`max_total_code_blocks`、`execution_conda_env`

### `scoring`
- `weights`：`answer`、`length`、`reflection` 三类惩罚权重
- `reflection_patterns`：用于统计过度反思信号的正则列表
- `params`：`length_ref`、`tau_length`、`answer_count_ref`、`tau_answer_count`、`tail_ratio_ref`、`tau_tail_ratio`、`reflection_count_ref`、`tau_reflection`、`correct_score_floor`

## 评估说明

- `accuracy`：答案抽取后与标准答案比对得到的正确率
- `response_length_tokens` / `response_length_chars`：最终提交答案长度
- `total_response_length_tokens` / `total_response_length_chars`：全流程生成长度
- `tail_ratio`：从第一个答案信号开始计算的尾部字符占比
- `efficiency_i`：答对后仅反映长度、答案重复与反思惩罚的效率项
- `score_i`：单题综合分数
- 评测阶段支持对每个数据集结果文件使用 `ThreadPoolExecutor` 做多线程加速，线程数由 `run.eval_num_workers` 控制

当前默认得分公式：

```text
efficiency_i =
    answer_factor^0.5
    * length_factor^0.3
    * reflection_factor^0.2

score_i =
    accuracy * (0.6 + 0.4 * efficiency_i)
```

说明：
- 错题直接记 `0`
- `length_factor` 优先基于 `total_response_length_tokens`
- `plan_solve`、`self_refine`、`self_consistency`、`tir` 会把中间过程计入总生成长度
- `tir` 的总生成长度包含完整工具循环 transcript

## 复现建议

为保证实验可比性：
1. 固定 `datasets[].sample_path`，长期复用同一批样本
2. 固定 `max_samples` 与方法参数
3. 先做小样本 smoke test，再扩大到正式样本规模

## 单元测试

```bash
pytest -q tests
```

## 更多说明

更完整的中文使用文档、结果目录解释和评分配置说明见：
- `docs/topic1_run_guide_cn.md`
- `docs/scores.md`

## 常见问题

1. `ImportError: No module named vllm`
- 执行 `pip install -r requirements.txt`

2. 显存不足（OOM）
- 优先调小 `vllm.max_model_len`、方法级 `max_tokens`，必要时降低 `tensor_parallel_size`

3. 找不到样本文件
- 检查 `datasets[].sample_path` 是否存在且路径正确

4. 评估速度较慢
- 提高 `run.eval_num_workers`，但注意不要超过机器可承受线程数
