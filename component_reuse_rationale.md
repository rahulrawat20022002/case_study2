# Reused and removed components — Case Study 2 agent

## What was reused

The retrieval substrate is reused from a prior working RAG orchestrator (PolicyNeural). Only three of its components are used: document ingestion, embedding, and retrieval. This is stated once in the method section as reused infrastructure and is not claimed as a contribution of this study. Reusing a known-good retrieval stack keeps the build effort focused on the evaluation, which is the actual contribution.

## What was removed, and why

Every other component of the prior orchestrator was deliberately switched off: the two DebateAgents, the VerifierAgent, the EvaluatorAgent, the MemoryAgent, the TopicModelAgent, the PlannerAgent, the GuardrailsAgent, and the SummarizerAgent. The removals fall into three groups.

The debate, verifier, and evaluator agents were removed because they would confound the measurement. Each of them re-checks, argues over, or re-scores the model's answer before it is emitted. If the pipeline already corrects and judges itself internally, the faithfulness of the final answer can no longer be attributed to the generator, and the RAGAS faithfulness score would measure the whole self-correcting apparatus rather than the single generation step the study is designed to probe.

The MemoryAgent was removed because it adapts retrieval per query based on past interactions. That would make retrieval non-deterministic and case-dependent, so the same input could retrieve different passages on different runs. Reproducibility is a fixed requirement of the study, and a retrieval layer that tunes itself per row would destroy it.

The TopicModelAgent, PlannerAgent, GuardrailsAgent, and SummarizerAgent were removed simply as irrelevant to the task. The task is a single-shot legal classification of one system description; there is no multi-step plan to build, no topic model to maintain, no content to guard or summarise.

## The principle behind it

The goal is a fixed, reproducible retrieval substrate so that the only moving parts under evaluation are the generator and the groundedness of its explanation. Anything that would either mask the generator's behaviour or make a run irreproducible was removed; only the plain retrieve-then-generate path was kept.
