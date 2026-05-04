# CS6493 Group Project (Structured Bilingual Extract)

## Source
- File: `docs/cs6493_group_project.pdf`
- Course: City University of Hong Kong, CS6493 Natural Language Processing
- Term: Q2 2025-2026
- Date on document: March 18, 2026
- Total pages extracted: 8

---

## English Version

### 1. Project Instructions

City University of Hong Kong Natural Language Processing, Q2 2025-2026  
CS6493: Natural Language Processing - Projects  
March 18, 2026

Instructions:
- Deadline: May 6, 2026 (Wednesday) at 6:00 PM.
- This is a group project. Each group should consist of 1 to 6 members. Please register your group on Canvas by March 26, 2026, at 6:00 PM.
- You are required to submit a progress report by April 22, 2026. The progress report should not exceed five pages. Each group only needs to submit one copy.
- Choose one topic from the six options provided below for your group.
- You are required to submit your project report and source code via Canvas, and deliver a 15-minute presentation in class. The project report should include at least the following sections: introduction, related work, methodology, experiments, and discussion. The main content of the report can be up to 6 pages, with no page limit for references and appendices. Source code may be submitted as a Jupyter Notebook or Python files.
- Please include your presentation slides at the end of the report.
- This project is open-ended, and you are strongly encouraged to come up with creative ideas and designs!

Department of Computer Science

### 2. Topic 1 - Mathematical Reasoning Ability of Large Language Models

Large language models (LLMs) have demonstrated remarkable capabilities in natural language processing. However, their mathematical reasoning ability remains a critical area of research, especially when dealing with complex problems found in challenging datasets such as MATH-500, GSM8K and AIME 2024. These datasets require models to interpret mathematical expressions, understand abstract concepts, and generate accurate solutions.

The prompt-based methods, such as Chain of Thought (COT) and Self-Refine prompting, are structured approaches to mathematical problem solving. These methods provide specific cues to break down complex problems into manageable steps, guiding models towards logical solutions. To solve the mathematical problems, you are encouraged to:

1. Explore the effectiveness of different prompt methods and different models in mathematical reasoning, including but not limited to: CoT (Wei J, Wang X et al.), Self-Refine (Madaan A, Tandon N, Gupta P, et al.), Self-Consistency (Wang X, Wei J, Schuurmans D, et al.), Least-to-Most prompting (Zhou et al.), Auto-CoT (Zhang et al.), etc. You should experiment with at least three different prompt methods and test them on the following two models:
   - Qwen2.5-Math-1.5B
   - DeepSeek-R1-Qwen-1.5B
   You should collect and preprocess the MATH-500, GSM8K (Test Set) and AIME 2024 dataset, then evaluate the models on them.
2. In the metrics section, focus on two key concepts:
   - Accuracy: the ratio of correctly solved problems to the total number of problems.
   - Response length: the number of characters or words in a response.
   You are also encouraged to explore new prompt methods or evaluation metrics.

Hint: The token consumption of Self-Consistency method may be extremely high, so you are suggested to set the iteration number to be 5.

References:
1. Wei J, Wang X, Schuurmans D, et al. Chain-of-thought prompting elicits reasoning in large language models[J]. Advances in Neural Information Processing Systems, 2022, 35: 24824–24837.
2. Madaan A, Tandon N, Gupta P, et al. Self-refine: Iterative refinement with self-feedback[J]. Advances in Neural Information Processing Systems, 2024, 36.
3. Wang X, Wei J, Schuurmans D, et al. Self-consistency improves chain of thought reasoning in language models[J]. arXiv preprint arXiv:2203.11171, 2022.
4. Cobbe K, Kosaraju V, Bavarian M, et al. Training verifiers to solve math word problems[J]. arXiv preprint arXiv:2110.14168, 2021.
5. Denny Zhou, et al. Least-to-Most Prompting Enables Complex Reasoning in Large Language Models. arXiv preprint arXiv:2205.10625, 2023.
6. Zhuosheng Zhang, et al. Automatic Chain of Thought Prompting in Large Language Models. arXiv preprint arXiv:2210.03493, 2022.

### 3. Topic 2 - Hallucination Detection and Correction in LLMs

Large language models (LLMs) have demonstrated remarkable capabilities in many tasks. Despite their fluency, LLMs frequently generate factually incorrect statements, known as hallucinations, due to limitations in training data, contextual understanding, or reasoning. This project evaluates hallucination rates using datasets like TruthfulQA (Lin et al., 2022), which measures models’ propensity to replicate human falsehoods, and HaluEval (Li et al., 2023), a benchmark covering diverse hallucination types (e.g., factual, contextual). The investigation spans three dimensions: factual accuracy (verifiable claims), contextual coherence (logical consistency within a response), and citation reliability (proper sourcing). Developing robust hallucination detection systems is critical for high-stakes applications in healthcare, legal analysis, and news generation.

The following approaches are recommended for systematic evaluation and correction:

1. Benchmark hallucination rates across models. Consider analyzing how hallucination rates correlate with model size, exploring the scaling law of factual accuracy:
   - Compare closed models (GPT, Claude) vs open models (Llama, DeepSeek).
   - Test different prompting strategies. Compare at least three methods:
     - Standard prompting: Direct queries.
     - Citation enforcement: Require inline references (e.g., “According to the ...”).
     - Self-reflection: Ask models to self-assess credibility.
   - Hallucination taxonomy analysis: Classify errors into:
     - Fabrication: Generating entirely false information.
     - Distortion: Misrepresenting true facts (e.g., swapping dates).
     - Omission: Excluding critical context (e.g., not mentioning vaccine side effects).
2. Strategies to Mitigate Hallucinations:
   - Fine-tuning on factual data: Train models on curated datasets (e.g., biomedical journals, court rulings) to strengthen factual grounding. Consider using parameter-efficient fine-tuning methods like LoRA to reduce computational cost while adapting models to factual domains.
   - Retrieval-augmented generation (RAG): Integrate real-time knowledge retrieval from trusted sources before generating responses.
   - Post-hoc correction: Implement a secondary model to detect and rewrite hallucinated content.

References:
1. Lin S, Hilton J, Evans O. Truthfulqa: Measuring how models mimic human falsehoods. ACL, 2022.
2. Li J, et al. HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models. EMNLP, 2023.
3. Min S, et al. Factscore: Fine-grained atomic evaluation of factual precision in long form text generation. EMNLP, 2023.
4. Ji Z, et al. Survey of hallucination in natural language generation. ACM Computing Surveys, 2023.

### 4. Topic 3 - Building Practical LLM Applications with LlamaIndex

LlamaIndex is a cutting-edge data framework for connecting custom data sources to large language models (LLMs). This project focuses on developing production-grade LLM applications with an emphasis on educational implementation rather than enterprise deployment. Students will explore core challenges in real-world LLM application development, including advanced retrieval strategies and automated evaluation, while considering computational constraints.

The project requires addressing two core technical challenges:

1. System Architecture Design: Construct application pipelines using LlamaIndex’s data connectors and retrieval modules:
   - Implement at least one application type from:
     - Document QA System: Build RAG pipelines with adaptive chunking strategies (e.g., 256-token chunks with 10% overlap).
     - Conversational Agent: Develop chatbot with short-term memory management.
     - Autonomous Agent: Create simple task-oriented agents with API integration.
   - Integrate data connectors for at least one source type (PDFs, text files, or web content).
   - Compare performance of 2+ LLM backends (e.g., Mistral-7B vs. smaller models like T5-base).
2. Capability Evaluation: Establish practical evaluation metrics:
   - Design test cases measuring response relevance and task completion rate.
   - Analyze memory-performance tradeoffs using different chunking strategies.

Advanced suggestions: Explore quantization techniques for model deployment or implement basic human feedback mechanisms.

Hint: For computational efficiency, consider using quantized models (e.g., GPTQ-4bit versions) through Ollama.

References:
1. Touvron H, et al. Llama 2: Open Foundation and Fine-Tuned Chat Models. Meta, 2023.
2. Jiang W, et al. Mistral 7B. arXiv preprint arXiv:2310.06825 (2023).
3. Xiao G, et al. SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models. ICML, 2023.
4. LlamaIndex OSS Documentation: https://developers.llamaindex.ai/python/framework

### 5. Topic 4 - Retrieval-Augmented Generation for Knowledge-Intensive Tasks

Retrieval-Augmented Generation (RAG) integrates neural retrieval with large language models to address knowledge-intensive NLP tasks. Instead of relying solely on parametric knowledge, RAG systems retrieve external documents to ground generation. This project aims to systematically investigate how retrieval quality, retrieval configuration, and generation strategies jointly influence answer accuracy, faithfulness, and robustness. Using benchmark datasets from different domains, such as Natural Questions (Kwiatkowski et al.), PubMedQA (Jin et al.), and FinanceBench (Islam et al.), you will evaluate how retrieval and generation performance varies across domains with different knowledge structures and terminology. Metrics may include answer accuracy, evidence grounding quality, citation precision, and hallucination rate.

The project topic focuses on two key components:

1. Retrieval-Generation Interaction: Investigate different retrieval strategies (sparse/dense/hybrid retrieval) paired with various LLMs (e.g., open-source models like LLaMA or closed-source models like GPT). You should:
   - Implement at least 2 retrieval methods (e.g., BM25 vs. Contriever) and 2 generation models.
   - Analyze how retrieval precision affects final answer quality using the HotpotQA dev set.
   - Compare zero-shot vs. instruction-tuned models (e.g., https://huggingface.co/Intel/neural-chat-7b-v3-3).
   - Conduct experiments on at least two different domains and report cross-domain performance differences.
2. Hallucination Mitigation: Design experiments to measure how RAG reduces model fabrication:
   - Quantify hallucination rates using metrics like FActScore (Min et al.).
   - Evaluate whether citation grounding quality differs across domains.
   - Evaluate citation quality through human assessment (e.g., citation precision/recall).
   - Compare vanilla RAG vs. advanced variants (e.g., Self-RAG (Asai et al.)).

Students are encouraged to explore innovative retrieval strategies (e.g., query rewriting) or propose new evaluation frameworks.

Hint: Limit retrieved documents to 3–5 per query to balance performance and computational cost.

References:
1. Lewis P, et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. NeurIPS, 2020.
2. Izacard G, et al. Leveraging passage retrieval with generative models for open domain QA. EACL, 2021.
3. Asai A, et al. Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection. ICLR, 2024.
4. Min S, et al. FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation. EMNLP, 2023.
5. Yang Z, et al. HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering. EMNLP, 2018.

### 6. Topic 5 - Smart Meeting Assistant

In this project, you are expected to design a smart meeting assistant that enhances virtual and in-person meetings by providing real-time support for participants. The system should assist users by transcribing conversations, summarizing discussions, extracting key action items, and offering relevant insights.

Your smart meeting assistant should incorporate the following key features:

1. Real-time Speech-to-Text Transcription: Implement speech recognition to accurately transcribe spoken conversations into text. The system should support multiple speakers and differentiate between them for better clarity in meeting notes.
2. Automatic Meeting Summarization: Develop an intelligent summarization module that extracts the most important points from the conversation. The summary should be concise and provide an overview of key topics, decisions made, and follow-up actions.
3. Machine Translation for Multilingual Meetings: Implement a translation module that allows real-time translation of meeting discussions into multiple languages. This feature should enable seamless communication in multilingual teams by translating speech or text-based discussions while preserving context and meaning.
4. Context-Aware Action Item Extraction: Enable the system to identify and track action items from the discussion. The assistant should recognize commitments like “I will send the report by Friday” and automatically assign tasks to relevant participants.
5. Meeting Sentiment and Engagement Analysis: Develop a module that analyzes the emotional dynamics and engagement patterns of the meeting. Instead of focusing on individual commitments, the system should capture broader interaction signals such as agreement, disagreement, tension, or hesitation (e.g., “I am not convinced this will work”). The assistant should provide an overall sentiment overview and highlight emotionally significant moments during the discussion.

This project challenges you to apply NLP, speech processing, and context awareness to create a useful AI tool for workplace productivity. You are encouraged to design a dataset and explore innovative features to enhance the system’s effectiveness.

References:
1. Tan, Haochen, et al. “Reconstruct Before Summarize: An Efficient Two-Step Framework for Condensing and Summarizing Meeting Transcripts.” Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, 2023.
2. Wu, Han, et al. “VCSUM: A Versatile Chinese Meeting Summarization Dataset.” Findings of the Association for Computational Linguistics: ACL 2023.
3. H. Zhang, P. S. Yu, and J. Zhang, “A systematic survey of text summarization: From statistical methods to large language models”, arXiv preprint arXiv:2406.11289, 2024.
4. Park, Chanjun, et al. “BTS: Back TranScription for speech-to-text post-processor using text-to-speech-to-text.” Proceedings of the 8th Workshop on Asian Translation (WAT2021), 2021.

### 7. Topic 6 - Open Your Mind

This is a highly flexible project where you are encouraged to explore any idea involving language models that interests you, as long as it relates to the concepts covered in the course. We strongly recommend experimenting with cutting-edge LLMs (such as GPT, DeepSeek, LLaMA, etc.) through API integration or local deployment. For example, you might consider combining multiple AI techniques (e.g., RAG + fine-tuning) or exploring ethical aspects such as bias detection and fact-checking. Feel free to be creative and try something innovative and original.

Before starting your group work, please contact the TAs to have your selected topic approved.

Department of Computer Science

---

## 中文版本

### 1. 项目说明

香港城市大学 自然语言处理，2025-2026 学年第二学期  
CS6493：自然语言处理 - 课程项目  
文档日期：2026 年 3 月 18 日

说明：
- 截止时间：2026 年 5 月 6 日（周三）18:00。
- 本项目为小组项目。每组 1 至 6 人。请于 2026 年 3 月 26 日 18:00 前在 Canvas 完成组队注册。
- 需在 2026 年 4 月 22 日前提交进度报告。进度报告不超过 5 页。每组只需提交 1 份。
- 从下方 6 个选题中选择 1 个作为小组项目题目。
- 需通过 Canvas 提交项目报告与源代码，并在课堂上进行 10 分钟展示。项目报告至少应包含：引言、相关工作、方法、实验、讨论。报告正文最多 6 页；参考文献与附录页数不限。源代码可提交 Jupyter Notebook 或 Python 文件。
- 请将展示幻灯片附在报告末尾。
- 本项目为开放式题目，强烈鼓励提出有创意的设计与想法。

计算机科学系

### 2. 题目 1 - 大语言模型的数学推理能力

大语言模型（LLM）在自然语言处理方面已表现出显著能力，但其数学推理能力仍是关键研究问题，尤其是在 MATH-500、GSM8K、AIME 2024 这类高难度数据集上。这些数据集要求模型能解释数学表达式、理解抽象概念并给出准确解答。

基于提示的方法（如 Chain of Thought, CoT 与 Self-Refine）为数学问题求解提供结构化路径，能将复杂问题拆解为可管理步骤，引导模型进行逻辑推理。建议如下：

1. 探索不同提示方法与不同模型在数学推理中的效果，包括但不限于：CoT（Wei J, Wang X 等）、Self-Refine（Madaan A, Tandon N, Gupta P 等）、Self-Consistency（Wang X, Wei J, Schuurmans D 等）、Least-to-Most prompting（Zhou 等）、Auto-CoT（Zhang 等）等。至少实验 3 种提示方法，并在以下两种模型上测试：
   - Qwen2.5-Math-1.5B
   - DeepSeek-R1-Qwen-1.5B  
   需要收集并预处理 MATH-500、GSM8K（测试集）和 AIME 2024 数据集，并进行评测。
2. 指标部分重点关注两个概念：
   - Accuracy（准确率）：正确解题数占总题数比例。
   - Response length（回答长度）：回答中的字符数或词数。  
   同时鼓励探索新的提示方法或评估指标。

提示：Self-Consistency 的 token 消耗可能非常高，建议迭代次数设为 5。

参考文献：
1. Wei J, Wang X, Schuurmans D, et al. Chain-of-thought prompting elicits reasoning in large language models[J]. Advances in Neural Information Processing Systems, 2022, 35: 24824–24837.
2. Madaan A, Tandon N, Gupta P, et al. Self-refine: Iterative refinement with self-feedback[J]. Advances in Neural Information Processing Systems, 2024, 36.
3. Wang X, Wei J, Schuurmans D, et al. Self-consistency improves chain of thought reasoning in language models[J]. arXiv preprint arXiv:2203.11171, 2022.
4. Cobbe K, Kosaraju V, Bavarian M, et al. Training verifiers to solve math word problems[J]. arXiv preprint arXiv:2110.14168, 2021.
5. Denny Zhou, et al. Least-to-Most Prompting Enables Complex Reasoning in Large Language Models. arXiv preprint arXiv:2205.10625, 2023.
6. Zhuosheng Zhang, et al. Automatic Chain of Thought Prompting in Large Language Models. arXiv preprint arXiv:2210.03493, 2022.

### 3. 题目 2 - LLM 幻觉检测与纠正

大语言模型（LLM）在多种任务上能力突出，但尽管语言流畅，仍经常输出事实错误内容（即幻觉）。这通常由训练数据限制、上下文理解不足或推理缺陷导致。本题可使用 TruthfulQA（Lin et al., 2022）和 HaluEval（Li et al., 2023）等数据集评估幻觉率。研究应覆盖三个维度：事实准确性（可核验断言）、上下文连贯性（回答内部逻辑一致性）、引用可靠性（来源是否规范）。在医疗、法律、新闻等高风险场景中，构建可靠幻觉检测系统非常关键。

建议按以下路径系统评估与纠正：

1. 比较不同模型的幻觉率，并分析其与模型规模的关系（事实准确性的 scaling law）：
   - 对比闭源模型（GPT、Claude）与开源模型（Llama、DeepSeek）。
   - 对比至少 3 种提示策略：
     - 标准提示：直接提问。
     - 引用约束：要求内联引用（如“According to ...”）。
     - 自反思提示：要求模型自评可信度。
   - 幻觉类型分析：
     - Fabrication（编造）：生成完全虚假的信息。
     - Distortion（失真）：篡改真实事实（如日期调换）。
     - Omission（遗漏）：漏掉关键上下文（如未提及疫苗副作用）。
2. 幻觉缓解策略：
   - 在事实数据上微调：使用精选数据（如生物医学期刊、法院判决）增强事实基础；可采用 LoRA 等参数高效微调降低成本。
   - 检索增强生成（RAG）：回答前从可信来源进行实时检索。
   - 事后纠错：使用二级模型检测并改写幻觉内容。

参考文献：
1. Lin S, Hilton J, Evans O. Truthfulqa: Measuring how models mimic human falsehoods. ACL, 2022.
2. Li J, et al. HaluEval: A Large-Scale Hallucination Evaluation Benchmark for Large Language Models. EMNLP, 2023.
3. Min S, et al. Factscore: Fine-grained atomic evaluation of factual precision in long form text generation. EMNLP, 2023.
4. Ji Z, et al. Survey of hallucination in natural language generation. ACM Computing Surveys, 2023.

### 4. 题目 3 - 基于 LlamaIndex 构建实用 LLM 应用

LlamaIndex 是连接自定义数据源与大语言模型（LLM）的前沿数据框架。本题目标是开发具备“生产可用思路”的 LLM 应用，重点在教学实现而非企业级部署。你需要在算力约束下，探索真实应用中的核心挑战，包括高级检索策略与自动评估。

项目要求解决两项核心技术问题：

1. 系统架构设计：使用 LlamaIndex 的数据连接器与检索模块构建应用流水线：
   - 至少实现以下一种应用类型：
     - 文档问答系统：构建 RAG 流水线，并采用自适应切块策略（如 256 token、10% 重叠）。
     - 对话智能体：开发带短期记忆管理的聊天机器人。
     - 自主智能体：构建可进行 API 集成的简单任务型 Agent。
   - 至少接入一种数据源（PDF、文本文件或网页内容）。
   - 比较至少 2 个 LLM 后端性能（如 Mistral-7B 与 T5-base 等小模型）。
2. 能力评估：建立实用评估指标：
   - 设计测试用例评估回答相关性与任务完成率。
   - 分析不同切块策略下的“内存-性能”权衡。

进阶建议：可探索模型量化部署，或实现基础的人类反馈机制。

提示：为提高计算效率，可通过 Ollama 使用量化模型（如 GPTQ-4bit 版本）。

参考文献：
1. Touvron H, et al. Llama 2: Open Foundation and Fine-Tuned Chat Models. Meta, 2023.
2. Jiang W, et al. Mistral 7B. arXiv preprint arXiv:2310.06825 (2023).
3. Xiao G, et al. SmoothQuant: Accurate and Efficient Post-Training Quantization for Large Language Models. ICML, 2023.
4. LlamaIndex OSS Documentation: https://developers.llamaindex.ai/python/framework

### 5. 题目 4 - 面向知识密集任务的检索增强生成（RAG）

RAG（Retrieval-Augmented Generation）将神经检索与大语言模型结合，以处理知识密集型 NLP 任务。与仅依赖参数知识不同，RAG 通过检索外部文档来支撑生成。本题旨在系统研究：检索质量、检索配置与生成策略如何共同影响答案准确性、忠实性与鲁棒性。可在不同领域数据集上开展实验，如 Natural Questions（Kwiatkowski 等）、PubMedQA（Jin 等）、FinanceBench（Islam 等），并比较跨领域表现。指标可包括答案准确率、证据支撑质量、引用精度、幻觉率。

本题聚焦两大模块：

1. 检索-生成交互：研究不同检索策略（稀疏/稠密/混合）与不同 LLM（开源如 LLaMA、闭源如 GPT）的配合效果：
   - 至少实现 2 种检索方法（如 BM25 vs. Contriever）和 2 个生成模型。
   - 在 HotpotQA dev 集上分析检索精度对最终答案质量的影响。
   - 对比 zero-shot 与 instruction-tuned 模型（如 https://huggingface.co/Intel/neural-chat-7b-v3-3）。
   - 至少在 2 个不同领域开展实验，并报告跨领域性能差异。
2. 幻觉抑制：设计实验评估 RAG 降低模型编造的效果：
   - 使用 FActScore（Min 等）等指标量化幻觉率。
   - 评估不同领域中引用支撑质量是否存在差异。
   - 通过人工评估引用质量（如 citation precision/recall）。
   - 对比基础 RAG 与高级变体（如 Self-RAG（Asai 等））。

鼓励探索创新检索策略（如 query rewriting）或提出新的评测框架。

提示：每个查询建议限制检索文档数为 3-5，以平衡性能与计算成本。

参考文献：
1. Lewis P, et al. Retrieval-augmented generation for knowledge-intensive NLP tasks. NeurIPS, 2020.
2. Izacard G, et al. Leveraging passage retrieval with generative models for open domain QA. EACL, 2021.
3. Asai A, et al. Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection. ICLR, 2024.
4. Min S, et al. FActScore: Fine-grained Atomic Evaluation of Factual Precision in Long Form Text Generation. EMNLP, 2023.
5. Yang Z, et al. HotpotQA: A Dataset for Diverse, Explainable Multi-hop Question Answering. EMNLP, 2018.

### 6. 题目 5 - 智能会议助手

本题要求设计一个智能会议助手，为线上与线下会议提供实时支持。系统应帮助用户完成对话转写、讨论摘要、行动项提取，并提供相关洞察。

该智能会议助手应包含以下核心能力：

1. 实时语音转文本：实现语音识别，将口语对话准确转写为文本。系统应支持多说话人并区分说话者，以提升会议记录清晰度。
2. 自动会议摘要：开发智能摘要模块，提取讨论中的关键内容。摘要应简洁，覆盖主要议题、决策与后续行动。
3. 多语言会议机器翻译：实现翻译模块，支持会议内容的实时多语言翻译。在保留上下文和语义的前提下，支持语音或文本讨论的跨语言沟通。
4. 上下文感知的行动项抽取：识别并跟踪讨论中的行动项。系统应能识别“我周五前发报告”这类承诺，并自动分配给相关参与者。
5. 会议情感与参与度分析：开发模块分析会议情绪动态和互动模式。不同于只关注个人承诺，系统应捕捉更广泛的互动信号，如赞同、反对、紧张、犹豫（如“我不太确信这个可行”），并给出整体情绪概览与关键情绪时刻提示。

本题鼓励综合使用 NLP、语音处理与上下文建模，构建提升职场效率的实用 AI 工具。鼓励自建数据集并探索创新功能提升系统效果。

参考文献：
1. Tan, Haochen, et al. “Reconstruct Before Summarize: An Efficient Two-Step Framework for Condensing and Summarizing Meeting Transcripts.” Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing, 2023.
2. Wu, Han, et al. “VCSUM: A Versatile Chinese Meeting Summarization Dataset.” Findings of the Association for Computational Linguistics: ACL 2023.
3. H. Zhang, P. S. Yu, and J. Zhang, “A systematic survey of text summarization: From statistical methods to large language models”, arXiv preprint arXiv:2406.11289, 2024.
4. Park, Chanjun, et al. “BTS: Back TranScription for speech-to-text post-processor using text-to-speech-to-text.” Proceedings of the 8th Workshop on Asian Translation (WAT2021), 2021.

### 7. 题目 6 - Open Your Mind（开放选题）

这是一个高度灵活的项目方向。只要主题与课程内容相关，你可以探索任何你感兴趣的语言模型方向。强烈建议通过 API 集成或本地部署，尝试前沿 LLM（如 GPT、DeepSeek、LLaMA 等）。例如，可以组合多种 AI 技术（如 RAG + 微调），或探索偏见检测、事实核查等伦理问题。鼓励大胆创新，做出原创方案。

在小组正式开始前，请先联系助教（TA）确认选题。

计算机科学系
