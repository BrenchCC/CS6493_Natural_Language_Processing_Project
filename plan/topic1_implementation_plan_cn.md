# Topic1 实施计划（已定稿）

## 1. 目标与范围
- 目标：完成题目1从数据准备、推理、评估到汇总报表的可运行框架（不含 PPT 与最终报告正文）。
- 必做方法：`cot_zero`、`cot_few_shot`、`self_refine`、`self_consistency (n = 5)`。
- 扩展方法：`tir`、`sr_sd_tir`。
- 固定模型：`Qwen/Qwen2.5-Math-1.5B-Instruct`、`deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`。
- 固定数据集：`MATH-500`、`GSM8K`、`AIME 2024`（每集默认抽样 30，AIME 可全量 30）。

## 2. 执行架构（本地 vLLM，不走 OpenAI 服务）
- 推理入口：`infer_exp/run_experiments.py --config <yaml>`。
- 模型加载：脚本内直接初始化 `vllm.LLM`，不依赖 `openai` 兼容 HTTP server, 代码放在vllm_server，可自定义参数。
- 并发策略：单模型实例 + 线程池任务调度 + micro-batch 聚合调用 `llm.generate`。
- 方法统一接口：`build_prompt()`、`decode_strategy()`、`post_process()`。
- 输出产物：按 `model x dataset x method` 写入原始推理结果 JSONL（含 full text、final answer、token 统计）。

## 3. 评分算法（总分严格在 [0,1]）
### 3.1 基础指标
- `accuracy`：是否答对（`c in {0, 1}`）。
- `response_length`：token/字符长度。
- `reflection_count`：反思词命中次数。
- `answer_count`：答案信号出现次数。
- `first_answer_token_idx`：首个答案出现位置。
- `tail_ratio`：首答后剩余 token 占比。

### 3.2 单题得分
- 总公式：
  - `score_i = c * (answer_factor ^ 0.3) * (length_factor ^ 0.4) * (reflection_factor ^ 0.3)`
  - `score_i = clip(score_i, 0, 1)`
- `length_factor`：
  - `length_factor = exp(-max(0, L - L_ref) / tau_d)`
- `answer_factor`：
  - `answer_factor = count_factor * tail_factor`
  - `count_factor = exp(-max(0, a - a_star) / tau_a)`
  - `tail_factor = exp(-max(0, tail_ratio - rho_star) / tau_tail)`
- `reflection_factor`：
  - `reflection_factor = exp(-abs(r - r_star) / tau_r)`

### 3.3 默认参数
- `a_star = 2`
- `tau_a = 2`
- `r_star = 2`
- `tau_r = 2`
- `rho_star = 0.25`
- `tau_tail = 0.20`
- `L_ref`、`tau_d` 在 yaml 按数据集/方法可覆盖。

## 4. 配置与目录约定
- 配置目录：`configs/yaml/`。
- 结构：`base + demos`。
  - `configs/yaml/base.yaml`：公共项（数据、模型、vLLM、评分）。
  - `configs/yaml/demos/*.yaml`：每个方法一个 demo，仅覆盖差异配置。
- CLI 一致：
  - `python scripts/infer/run_experiments.py --config configs/yaml/demos/<method>_demo.yaml`
  - `python evaluation/evaluate_runs.py --config ...`
  - `python evaluation/summarize_scores.py --config ...`

## 5. 评估输出与汇总
- 逐题输出：`accuracy, response_length, reflection_count, answer_count, first_answer_token_idx, tail_ratio, score_i`。
- 聚合输出：按 `model x dataset x method` 生成 `mean / median / mode`。
- 额外报表：单指标统计表（accuracy/length/reflection/answer）。

## 6. 测试计划
- 单元测试：
  - 答案抽取与等价判定。
  - `answer_count`、`tail_ratio` 计算。
  - 评分边界（`0 <= score_i <= 1`）和门控（答错必为 0）。
  - 单调性（固定其余条件时，`a` 增大或 `tail_ratio` 增大应降分）。
- 集成测试：
  - 本地 vLLM 推理冒烟。
  - `self_consistency n = 5` 全链路。
  - `base + demo` 配置合并与参数覆盖验证。

## 7. 当前执行策略
- 先交完整框架与可提交材料，不强制跑全量真实实验。
- 进度报告内容允许使用明确标注的占位结果。
