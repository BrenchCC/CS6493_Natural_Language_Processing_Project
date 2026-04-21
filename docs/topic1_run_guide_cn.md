# Topic1 运行指导（中文）

本指南用于本地运行 Topic1 的完整流程：推理、评估、汇总。
当前约定是：
- `scripts/` 只放下载脚本和运行用 `bash`。
- 核心 Python 代码在 `infer_exp/` 与 `evaluation/`。

## 1. 目录与配置
- 公共配置：`configs/yaml/base.yaml`
- 方法 demo：`configs/yaml/demos/*.yaml`
- 原始推理输出：`results/raw/`
- 评估输出：`results/evaluated/`
- 汇总输出：`results/summaries/`

## 2. 先装依赖（必须）

### 2.1 requirements 文件
项目提供依赖文件：
- `requirements.topic1.txt`（主入口，默认引用 `requirements.txt`）
- `requirements.tir-exec.txt`（仅 TIR/SR-SD-TIR 代码执行依赖）

核心包包括：
- `vllm`
- `datasets`
- `PyYAML`
- `huggingface_hub`
- `sympy`（TIR 代码执行常用）
- `numpy`
- `scipy`

### 2.2 Conda 安装命令（推荐）
```bash
conda create -n cs6493_topic1 python=3.10 -y
bash scripts/setup/install_requirements.sh cs6493_topic1 requirements.topic1.txt
```

### 2.3 非 Conda 安装命令
```bash
bash scripts/setup/install_requirements.sh
```

### 2.4 仅安装 TIR 代码执行依赖
Conda 模式（推荐）：
```bash
bash scripts/setup/install_tir_exec_requirements.sh cs6493_topic1 requirements.tir-exec.txt
```

当前环境模式：
```bash
bash scripts/setup/install_tir_exec_requirements.sh
```

说明：
- `scripts/setup/install_requirements.sh` 第1个参数是 Conda 环境名（可空）。
- 第2个参数是 requirements 文件路径，默认 `requirements.topic1.txt`。
- `scripts/setup/install_tir_exec_requirements.sh` 参数形式相同，默认 `requirements.tir-exec.txt`。

## 3. 下载模型（可选）
```bash
bash scripts/setup/download_hf_assets.sh
```

指定缓存目录：
```bash
bash scripts/setup/download_hf_assets.sh models/hf_cache
```

## 4. 准备固定样本（建议先做）
```bash
bash scripts/data/prepare_samples.sh 30 6493 data/processed
```

参数含义：
- 第1个参数：每个数据集抽样数量 `N`，默认 `30`
- 第2个参数：随机种子 `SEED`，默认 `6493`
- 第3个参数：输出目录 `OUTPUT_DIR`，默认 `data/processed`

## 5. 单模型一键全数据集推理（核心脚本）

你要的核心入口：
```bash
bash scripts/infer/run_single_model_all.sh <CONFIG_YAML> <MODEL_ID> [MAX_SAMPLES] [ONLY_DATASETS] [ONLY_METHODS]
```

示例1：单模型跑全部数据集 + 全部方法
```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/base.yaml Qwen/Qwen2.5-Math-1.5B-Instruct 30
```

示例2：只跑 `math500,gsm8k` 两个数据集
```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/base.yaml Qwen/Qwen2.5-Math-1.5B-Instruct 30 math500,gsm8k
```

示例3：只跑 `cot_zero,tir` 两种方法
```bash
bash scripts/infer/run_single_model_all.sh configs/yaml/base.yaml Qwen/Qwen2.5-Math-1.5B-Instruct 30 "" cot_zero,tir
```

这个脚本会：
- 固定只用你传入的一个模型；
- 按数据集批次顺序跑；
- 每个 `dataset x method` 生成对应 JSONL 结果到 `results/raw/`。

## 6. 常规推理入口（保留）
```bash
bash scripts/infer/run_experiments.sh configs/yaml/demos/tir_demo.yaml
```

如果你要直接用 Conda 子进程执行 TIR 代码块，可用：
```bash
bash scripts/infer/run_experiments.sh configs/yaml/demos/tir_conda_exec_demo.yaml
bash scripts/infer/run_experiments.sh configs/yaml/demos/sr_sd_tir_conda_exec_demo.yaml
```

说明：
- 不需要启动 OpenAI 兼容服务。
- 推理脚本会在内部直接初始化 `vllm.LLM`。
- 并发策略为：单模型实例 + 线程池调度 + micro-batch 生成。

## 7. 运行评估
```bash
bash scripts/eval/evaluate_runs.sh configs/yaml/base.yaml
```

评估会为每条样本补充：
- `accuracy`
- `response_length_tokens` / `response_length_chars`
- `reflection_count`
- `answer_count`
- `first_answer_token_idx`
- `tail_ratio`
- `length_factor` / `answer_factor` / `reflection_factor`
- `score_i`

## 8. 运行汇总
```bash
bash scripts/eval/summarize_scores.sh configs/yaml/base.yaml
```

汇总文件：
- `results/summaries/aggregate_scores.csv`
- `results/summaries/single_metric_stats.csv`

## 9. 参数怎么填写与调整（重点）
编辑：`configs/yaml/base.yaml`

### 9.1 运行参数（`run`）
- `output_dir`：原始输出目录
- `evaluated_dir`：评估后输出目录
- `summary_dir`：汇总表输出目录
- `num_workers`：线程数，建议从 `2~4` 起步
- `micro_batch_size`：批大小，OOM 时先降到 `2/4`

### 9.2 vLLM 参数（`vllm`）
- `tensor_parallel_size`：用几张卡填几（单卡填 `1`）
- `gpu_memory_utilization`：显存占用比例，建议 `0.80~0.92`
- `max_model_len`：上下文长度，显存不足时减小
- `max_num_seqs`：并发序列数，显存不足时减小
- `dtype`：通常 `auto`

### 9.3 数据参数（`datasets`）
- `name`：数据集别名
- `sample_path`：固定样本 JSONL 路径（最关键）
- `max_samples`：本次运行最多取前多少条

### 9.4 方法参数（`method_configs`）
- 通用：`temperature`、`top_p`、`max_tokens`
- `self_consistency`：`n_samples`
- `tir/sr_sd_tir`：`exec_timeout_sec`
- `tir/sr_sd_tir`：`exec_python_mode`（`current` 或 `conda`）
- `tir/sr_sd_tir`：`exec_conda_env`（仅 `exec_python_mode = conda` 时生效）

示例（让 TIR 在指定 Conda 环境中执行 python 代码块）：
```yaml
method_configs:
  tir:
    exec_timeout_sec: 8
    exec_python_mode: conda
    exec_conda_env: cs6493_topic1
  sr_sd_tir:
    exec_timeout_sec: 8
    exec_python_mode: conda
    exec_conda_env: cs6493_topic1
```

填写建议：
- `exec_python_mode = current`：直接使用当前解释器（最快，环境最简单）。
- `exec_python_mode = conda`：强制在指定 Conda 环境执行，避免默认环境缺包。
- `exec_conda_env` 必须填真实环境名，否则执行反馈会出现 `config_error`。

建议：
- 先用小样本调通；
- 再逐步增大 `max_samples`、`num_workers`、`micro_batch_size`。

### 9.5 评分参数（`scoring`）
当前默认：
- 权重：`answer = 0.3, length = 0.4, reflection = 0.3`
- `a_star = 2, tau_a = 2`
- `r_star = 2, tau_r = 2`
- `rho_star = 0.25, tau_tail = 0.20`

可在 `scoring.params` 中直接改。

## 10. 如何保证“每次做的题都一样”（重点）
你关心的是“题目集合一致”，不是“模型输出文本完全一致”。

### 10.1 我采用的保证机制
1. **先固定样本文件**：
   - 用同一个命令生成一次：
   ```bash
   bash scripts/data/prepare_samples.sh 30 6493 data/processed
   ```
2. **后续推理不再抽样**：
   - 推理只读取 `datasets[].sample_path` 指向的 JSONL；
   - 只要这些文件不变，题目就不变。
3. **固定读取上限**：
   - `max_samples` 固定后，每次取的条数与顺序都一致。

### 10.2 你的实际操作建议
- 第一次抽样后，立即备份：
```bash
cp -R data/processed data/processed_locked
```
- 在 `base.yaml` 中把 `sample_path` 改到 `data/processed_locked/*.jsonl`。
- 后续不要再覆盖 `processed_locked`，即可长期保证题目一致。

### 10.3 额外说明
- 对于 `temperature > 0` 的方法（如 Self-Consistency），题目一样时，输出可能仍有随机性。
- 若你还希望输出更稳定，可把对应方法的 `temperature` 设低或设为 `0`（会影响方法原始设定）。

## 11. 常见问题
1. `ImportError: No module named vllm`
- 先执行依赖安装（第2节）。

2. TIR 执行报 `sympy` 缺失
- 执行依赖安装（`requirements.topic1.txt` 内已包含 `sympy`）。

3. TIR 执行反馈出现 `config_error` 且提示 `exec_conda_env is empty`
- 在 `method_configs.tir` 或 `method_configs.sr_sd_tir` 中填入：
  - `exec_python_mode: conda`
  - `exec_conda_env: <你的环境名>`

4. GPU 显存不足
- 在 `configs/yaml/base.yaml` 调小：
  - `vllm.max_model_len`
  - `vllm.max_num_seqs`
  - `run.micro_batch_size`
  - `run.num_workers`

5. 数据文件不存在
- 确认 `datasets[].sample_path` 指向存在的 JSONL 文件。
