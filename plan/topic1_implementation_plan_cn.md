# Topic1 简单计划；

## 1. 目标与范围
- 目标：完成题目1从数据准备、推理、评估到汇总报表的可运行框架（不含 PPT 与最终报告正文）。
- 必做方法：`cot_zero`、`cot_few_shot`、`self_refine`、`self_consistency (n = 5)`。
- 扩展方法：`tir`( Tool-Integrated Reasoning (TIR))。
  - qwen2.5-Math-1.5B-Instruct的TIR实现
  ```python
    # TIR
  messages = [
      {"role": "system", "content": "Please integrate natural language reasoning with programs to solve the problem above, and put your final answer within \\boxed{}."},
      {"role": "user", "content": prompt}
  ]
  ```
  - 参考：
  ```markdown
  Integrate step-by-step reasoning and Python code to solve math problems using the following guidelines:

- Analyze the question and write functions to solve the problem; the function should not take any arguments.
- Present the final result in LaTeX using a `\boxed{}` without any units.
- Utilize the `pi` symbol and `Rational` from Sympy for $\pi$ and fractions, and simplify all fractions and square roots without converting them to decimal values.;
  ```
- 固定模型：`Qwen/Qwen2.5-Math-1.5B-Instruct`、`deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`。
- 固定数据集：`MATH-500`、`GSM8K`、`AIME 2024`（每集默认抽样 50，AIME全量 30）。

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
- `answer_count`：答案信号出现次数。(检测\\boxed{{answer}},除去最后的答案输出)
- `second_answer_token_idx`：第二个答案出现位置。
- `tail_ratio`：第二次答案后剩余 token 占比。

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

