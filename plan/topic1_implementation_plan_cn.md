# Topic1 当前实现摘要

## 1. 目标与范围
- 目标：完成题目1从数据准备、推理、评估到汇总报表的可运行框架（不含 PPT 与最终报告正文）。
- 必做方法：`cot_zero`、`cot_few_shot`、`self_refine`、`self_consistency (n = 5)`。
- 扩展方法：`tir`( Tool-Integrated Reasoning (TIR))。
  - 当前实现不是 Qwen 专用，而是所有已注册模型均可调用
  - 当前 TIR 采用 `python -> output -> continue` 工具循环，并要求最终行为 `Final Answer: \boxed{...}`
- 固定模型：`Qwen/Qwen2.5-Math-1.5B-Instruct`、`deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`。
- 固定数据集：`MATH-500`、`GSM8K`、`AIME 2024`（每集默认抽样 50，AIME全量 30）。

## 2. 执行架构（本地 vLLM，不走 OpenAI 服务）
- 推理入口：`infer_exp/run_experiments.py --config <yaml>`。
- 模型加载：脚本内直接初始化 `vllm.LLM`，不依赖 `openai` 兼容 HTTP server, 代码放在vllm_server，可自定义参数。
- 当前主推理流程按样本顺序调用 `engine.chat()`；评测阶段使用 `ThreadPoolExecutor` 并发。
- 方法统一接口：`build_messages()`、`decode_strategy()`、`post_process()`、`run()`。
- 输出产物：按 `model x dataset x method` 写入原始推理结果 JSONL（含 full text、final answer、token 统计）。

## 3. 评分算法（总分严格在 [0,1]）
### 3.1 基础指标
- `accuracy`：是否答对（`c in {0, 1}`）。
- `response_length`：token/字符长度。
- `reflection_count`：反思词命中次数。
- `answer_count`：答案信号出现次数。
- `first_answer_token_idx`：第一个答案信号的字符位置。
- `tail_ratio`：从第一个答案信号开始的尾部字符占比。

### 3.2 单题得分
- 总公式：
  - `score_i = c * (answer_factor ^ 0.3) * (length_factor ^ 0.5) * (reflection_factor ^ 0.2)`
  - `score_i = clip(score_i, 0, 1)`
- `length_factor`：
  - `length_factor = exp(-max(0, L - length_ref) / tau_length)`
- `answer_factor`：
  - `answer_factor = count_factor * tail_factor`
  - `count_factor = exp(-max(0, a - answer_count_ref) / tau_answer_count)`
  - `tail_factor = 1.0` if `answer_count < 2`, else `exp(-max(0, tail_ratio - tail_ratio_ref) / tau_tail_ratio)`
- `reflection_factor`：
  - `reflection_factor = exp(-max(0, r - reflection_count_ref) / tau_reflection)`
