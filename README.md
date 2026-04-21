# CS6493 Natural Language Processing Project

## Topic 1: Mathematical Reasoning of Small Open-Weight LLMs

本项目用于完成 CS6493 课程 Topic 1 的实验框架，目标是比较不同提示方法在数学推理任务上的表现，并在准确率之外评估推理效率与过度推理行为。

核心流程：
1. 数据准备（固定抽样）
2. 本地 vLLM 推理（不依赖 OpenAI 兼容服务）
3. 指标评估与单题打分
4. 聚合统计与结果汇总

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
- `tir`
- `sr_sd_tir`

## 项目结构

```text
configs/yaml/                  # 基础配置与 demo 配置
data/processed/                # 固定抽样后的 JSONL
infer_exp/                     # 推理主流程
evaluation/                    # 指标提取、评分与汇总
prompts/                       # 各方法提示模板
vllm_server/                   # 本地 vLLM 引擎封装
scripts/setup/                 # 环境与模型下载脚本
scripts/data/                  # 数据准备脚本
scripts/infer/                 # 推理脚本
scripts/eval/                  # 评估与汇总脚本
tests/                         # 单元测试
results/raw/                   # 原始推理结果
results/evaluated/             # 评估后结果
results/summaries/             # 聚合统计 CSV
```

## 环境准备

建议 Python 版本：`3.10+`

### 方式 1：直接安装（推荐）

```bash
pip install -U pip
pip install -r requirements.txt
```

### 方式 2：使用脚本安装

```bash
bash scripts/setup/install_requirements.sh "" requirements.txt
```

说明：
- `scripts/setup/install_requirements.sh` 的默认依赖文件仍是 `requirements.topic1.txt`。
- 当前仓库使用 `requirements.txt`，请显式传入第二个参数。

## 快速开始

### 1. 准备固定样本（建议）

```bash
bash scripts/data/prepare_samples.sh 30 6493 data/processed
```

参数：
- 第 1 个：每个数据集样本数（默认 `30`）
- 第 2 个：随机种子（默认 `6493`）
- 第 3 个：输出目录（默认 `data/processed`）

### 2. 运行推理

单模型跑全部数据集与全部方法：

```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/base.yaml Qwen/Qwen2.5-Math-1.5B-Instruct 30
```

仅跑指定数据集：

```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/base.yaml Qwen/Qwen2.5-Math-1.5B-Instruct 30 math500,gsm8k
```

仅跑指定方法：

```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/base.yaml Qwen/Qwen2.5-Math-1.5B-Instruct 30 "" cot_zero,tir
```

或按 demo 配置运行单方法：

```bash
bash scripts/infer/run_experiments.sh configs/yaml/demos/tir_demo.yaml
```

### 3. 评估结果

```bash
bash scripts/eval/evaluate_runs.sh configs/yaml/base.yaml
```

### 4. 生成汇总表

```bash
bash scripts/eval/summarize_scores.sh configs/yaml/base.yaml
```

## 输出产物

### 原始推理输出
- 目录：`results/raw/`
- 文件名模式：`{model_alias}__{dataset}__{method}__{timestamp}.jsonl`
- 运行摘要：`run_summary__{timestamp}.json`

### 评估输出
- 目录：`results/evaluated/`
- 每条样本新增字段：
  - `accuracy`
  - `response_length_tokens`
  - `response_length_chars`
  - `reflection_count`
  - `answer_count`
  - `first_answer_token_idx`
  - `tail_ratio`
  - `length_factor`
  - `answer_factor`
  - `reflection_factor`
  - `score_i`

### 汇总输出
- `results/summaries/aggregate_scores.csv`
- `results/summaries/single_metric_stats.csv`

## 关键配置说明（`configs/yaml/base.yaml`）

### `run`
- `output_dir`：原始结果目录
- `evaluated_dir`：评估结果目录
- `summary_dir`：汇总目录
- `num_workers`：线程数
- `micro_batch_size`：微批大小

### `vllm`
- `tensor_parallel_size`：张量并行大小
- `gpu_memory_utilization`：显存占用比例
- `max_model_len`：最大上下文长度
- `max_num_seqs`：并发序列数

### `datasets`
- `name`：数据集名称
- `sample_path`：固定样本 JSONL 路径
- `max_samples`：读取上限

### `method_configs`
- 通用采样参数：`temperature`、`top_p`、`max_tokens`
- `self_consistency`：`n_samples`
- `tir/sr_sd_tir`：`exec_timeout_sec`、`exec_python_mode`、`exec_conda_env`

### `scoring`
- `weights`：`answer`、`length`、`reflection`
- `params`：`a_star`、`tau_a`、`r_star`、`tau_r`、`rho_star`、`tau_tail`、`L_ref`、`tau_d`
- `length_overrides`：按数据集/方法覆写长度惩罚参数

## 复现与公平性建议

为保证不同实验可对比：
1. 固定 `datasets[].sample_path` 指向同一批 JSONL。
2. 固定 `max_samples` 与方法参数。
3. 先小规模跑通，再扩大样本和并发。

如果你只关心“题目一致”，建议首次抽样后锁定样本目录，例如复制 `data/processed` 到单独目录并长期复用。

## 模型下载（可选）

```bash
bash scripts/setup/download_hf_assets.sh models/hf_cache
```

## 单元测试

```bash
pytest -q tests
```

## 常见问题

1. `ImportError: No module named vllm`
- 执行 `pip install -r requirements.txt`。

2. 显存不足（OOM）
- 调小 `vllm.max_model_len`、`vllm.max_num_seqs`、`run.micro_batch_size`、`run.num_workers`。

3. 找不到样本文件
- 检查 `datasets[].sample_path` 是否存在且路径正确。

4. TIR 执行代码失败
- 检查 `exec_python_mode` 与 `exec_conda_env` 配置是否正确。
