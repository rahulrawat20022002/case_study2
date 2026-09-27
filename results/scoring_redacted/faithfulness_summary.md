# RAGAS faithfulness (explanation grounded in retrieved passages)

Judge: `openai-compatible:Qwen/Qwen2.5-72B-Instruct-AWQ`. Faithfulness = supported statements / total statements. Baseline1 has no retrieval, so no score by design. Faithfulness says nothing about label correctness -- that gap is the study's subject.

| Config | n | scored | skipped | mean faithfulness | =1.0 | =0.0 |
|---|---|---|---|---|---|---|
| agent_structured | 215 | 215 | 0 | 0.455 | 7 | 21 |
| baseline1_plain_llm | - | - | - | (no retrieval) | - | - |
| baseline2_standard_rag | 215 | 215 | 0 | 0.548 | 25 | 0 |
