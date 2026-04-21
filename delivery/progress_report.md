# CS6493 NLP Group Project Progress Report

**Topic:** Topic 1 - Mathematical Reasoning Ability of Large Language Models  
**Course:** CS6493 Natural Language Processing  
**Student Name:** Chen Baizheng  
**Student ID:** 72510800  
**Date:** April 22, 2026

## 1. Project Positioning and Goal

This project studies mathematical reasoning of small open-weight LLMs under prompt-based strategies, with a focus on two dimensions:

1. **Answer correctness** (whether the model solves problems correctly)
2. **Reasoning efficiency** (whether the model continues unnecessary reasoning after it has likely found the answer)

The second dimension is the main extension beyond standard assignment requirements. Our objective is to build a coherent evaluation framework that can compare methods not only by accuracy but also by reasoning quality and stopping behavior.

## 2. Experimental Scope

### 2.1 Models

- `Qwen/Qwen2.5-Math-1.5B-Instruct`
- `deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B`

### 2.2 Datasets

- `HuggingFaceH4/MATH-500`
- `openai/gsm8k`
- `HuggingFaceH4/aime_2024`

Current controlled setting uses 30 sampled items per dataset for progress-stage validation, with planned expansion in final runs.

### 2.3 Method Set

**Required methods:**
- CoT zero-shot
- CoT few-shot
- Self-Refine
- Self-Consistency (`n = 5`)

**Extended methods:**
- TIR (Tool-Integrated Reasoning)
- SR-SD-TIR (plan -> solve-with-tools -> reflect)

## 3. Method Design Rationale

## 3.1 Baseline methods: what each one tests

- **CoT zero-shot**: reference baseline for direct reasoning without demonstrations.
- **CoT few-shot**: tests whether in-context exemplars improve structure and answer stability.
- **Self-Refine**: tests whether explicit second-pass self-critique can correct first-pass errors.
- **Self-Consistency**: tests whether diversity sampling + majority voting improves robustness.

These methods form a clear progression from single-pass prompting to multi-pass / multi-sample aggregation.

## 3.2 Extension design: why TIR and SR-SD-TIR

- **TIR** is designed for cases where textual reasoning alone is unstable in arithmetic/symbolic steps. It inserts executable code and uses execution feedback as an external check.
- **SR-SD-TIR** introduces staged control:
  1. planning sub-goals,
  2. solving with optional tools,
  3. reflective consolidation.

The design hypothesis is that staged reasoning can reduce wasted reasoning tokens and improve final consistency under the same model size budget.

## 3.3 Comparison logic

The comparison is not method-isolated only by final accuracy. Instead, all methods are analyzed under a shared protocol including:

- correctness,
- response budget,
- answer-emergence behavior,
- and over-reasoning tendency after answer emergence.

This gives a more behaviorally grounded comparison than a single headline score.

## 4. Evaluation Metric Design (Key Focus)

## 4.1 Core metrics (assignment-aligned)

- **Accuracy**: ratio of correctly solved problems.
- **Response length**: measured by token count and character count.

## 4.2 Behavior-aware metrics (our extension)

- **Reflection count**: count of reflection-style signals (e.g., verify, reconsider).
- **Answer count**: number of answer-signal occurrences in a response.
- **First answer token index**: where answer first appears.
- **Tail ratio**: proportion of generated tokens after first answer appears.

Interpretation:
- high `answer_count` + high `tail_ratio` often indicates repeated or unnecessary post-answer reasoning.

## 4.3 Composite score design in [0,1]

Per-sample score:

`score_i = c * (answer_factor ^ 0.3) * (length_factor ^ 0.4) * (reflection_factor ^ 0.3)`

where `c in {0,1}` is correctness gate and final score is clipped to `[0,1]`.

Factor design:

- `length_factor`: penalizes excessive length beyond reference budget.
- `answer_factor = count_factor * tail_factor`:
  - `count_factor` penalizes excessive answer repetitions beyond target `a_star`.
  - `tail_factor` penalizes excessive post-answer continuation (`tail_ratio`).
- `reflection_factor`: keeps moderate reflection preferable over both no-reflection and over-reflection.

Current default parameters:

- weights: `answer = 0.3`, `length = 0.4`, `reflection = 0.3`
- `a_star = 2`, `tau_a = 2`
- `r_star = 2`, `tau_r = 2`
- `rho_star = 0.25`, `tau_tail = 0.20`

## 4.4 Planned statistical reporting

For each `model x dataset x method` group, we report:

- mean / median / mode of composite scores,
- single-metric means (accuracy, length, reflection_count, answer_count, tail_ratio),
- per-question records for error analysis.

This two-level reporting (group summary + per-item trace) is intended to support both macro comparison and qualitative diagnosis.

## 5. Reproducibility and Fairness Controls

To ensure fairness and comparability:

1. shared datasets and fixed sample files;
2. consistent prompt-method interface;
3. method-level configuration managed by YAML;
4. shared evaluation pipeline and score formula.

For question consistency across runs, sampled JSONL files are fixed and reused. As long as these files are unchanged, compared runs use the same question set.

## 6. Progress Status

At this stage, the **research protocol and metric framework are finalized**. The main remaining work is empirical execution at scale and final analysis writing.

### Completed

- method portfolio definition and comparison protocol
- metric and composite score design
- evaluation output schema and summary strategy
- run configuration structure for controlled experiments

### Ongoing / Next

- full matrix execution (`model x dataset x method`)
- sensitivity checks for key score parameters
- final comparative discussion with complete quantitative evidence

## 7. Next-Step Commitments

Before final submission, we will:

1. complete required-method full runs;
2. run extension methods under matched conditions;
3. deliver full quantitative tables and interpretation;
4. conclude with trade-off analysis among correctness, efficiency, and reasoning behavior.

## References

1. Wei, J., Wang, X., Schuurmans, D., et al. (2022). Chain-of-thought prompting elicits reasoning in large language models. *NeurIPS*.
2. Wang, X., Wei, J., Schuurmans, D., et al. (2022). Self-consistency improves chain of thought reasoning in language models. *arXiv:2203.11171*.
3. Madaan, A., Tandon, N., Gupta, P., et al. (2023/2024). Self-Refine: Iterative refinement with self-feedback. *NeurIPS*.
4. Zhou, D., Scharli, N., Hou, L., et al. (2022). Least-to-Most prompting enables complex reasoning in large language models. *arXiv:2205.10625*.
5. Zhang, Z., Zhang, A., Li, M., Smola, A. (2022). Automatic chain of thought prompting in large language models. *arXiv:2210.03493*.
6. Gou, Z., Shao, Z., Gong, Y., et al. (2023). ToRA: A tool-integrated reasoning agent for mathematical problem solving. *arXiv:2309.17452*.
7. Shao, Z., Wang, P., Zhu, Q., et al. (2024). DeepSeekMath: Pushing the limits of mathematical reasoning in open language models. *arXiv preprint*.
8. Cobbe, K., Kosaraju, V., Bavarian, M., et al. (2021). Training verifiers to solve math word problems. *arXiv:2110.14168*.
9. Cobbe, K., et al. (2021). GSM8K: Grade school math 8K benchmark. *arXiv:2110.14168*.
10. Hendrycks, D., et al. (2021). Measuring mathematical problem solving with the MATH dataset. *NeurIPS*.
11. Lightman, H., Kosaraju, V., Burda, Y., et al. (2023). Let's verify step by step. *arXiv:2305.20050*.
12. Shinn, N., Cassano, F., Berman, E., et al. (2023). Reflexion: Language agents with verbal reinforcement learning. *arXiv preprint*.
13. Zhou, P., Madaan, A., Potharaju, S. P., et al. (2024). Self-Discover: Large language models self-compose reasoning structures. *arXiv preprint*.
14. Team, HuggingFaceH4. (2024). MATH-500 dataset release.
15. Team, HuggingFaceH4. (2024). AIME 2024 dataset release.
