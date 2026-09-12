# API budget and justification — Case Study 2

## The request

The study needs paid API access to the **generator model only**. Every other component runs locally on the university GPU at no cost. Expected spend is small:

- One full graded run (215 test cases × 3 configurations = 645 calls): **about $4** at standard rates, **about $2** with the Batch API.
- Realistic total including sanity iterations, two or three full runs at checkpoints, and a low-cost second-model comparison: **about $10 to $20**.
- **Requested credit with headroom: about $30** (or the equivalent in OpenAI / Google Cloud credit). The floor for the core result is about $5.

## Where the cost is, and where it is not

The only paid part of the whole system is generator inference. Everything else is free and local.

| Component | Model | Where it runs | Cost |
|---|---|---|---|
| Generator (system under test) | claude-sonnet-4-6 | Anthropic API | ~$4 per full run |
| Judge (RAGAS faithfulness) | Qwen2.5-72B-Instruct-AWQ | University GPU (local, vLLM) | free |
| Retriever + embedding | BAAI/bge-base-en-v1.5 | Local | free |
| Vector store + corpus | Chroma + BM25 | Local | free |

**Token basis** (measured from the frozen 215-case test set): average system description about 139 tokens, top-5 retrieved passages about 927 tokens. One full run is roughly **0.62M input + 0.14M output tokens**. At Sonnet 4.6 rates of $3 / $15 per million tokens that is about **$4**, halved to about **$2** with the Batch API.

## Why the study needs a strong (paid) generator

The contribution is a measurement result: whether an automated faithfulness metric can rate a legally wrong answer as well grounded in the retrieved text. This result is only meaningful against a strong model.

A weak or cheap model produces obviously wrong, ungrounded answers that any metric catches. Using one would trivialise the finding. A frontier model produces confident, fluent, well-grounded answers that are still legally wrong, which is exactly the failure the faithfulness metric cannot detect. The strong model is therefore the hardest test for the metric, not a convenience. The credit buys the adversarial best case the finding depends on.

## The low-cost question is already answered, and can become a result

Two points on cost, both in the study's favour:

1. **The study is already low cost by construction.** In most evaluation studies the expensive part is the judge, because it runs a large model over every output. Here the judge is a free local model on the university GPU. The entire evaluation harness reproduces for free; the only external cost is a few euros of generator inference.

2. **Accessibility can be turned into a finding.** Alongside the frontier generator, the same pipeline can run a **small open model** (for example Mistral or a small Llama, run locally at no cost) as a second generator. Comparing where the faithfulness metric breaks on the strong model versus the cheap one directly addresses whether low-cost models can be trusted for compliance classification. This needs the frontier model as the reference point, and it costs nothing extra. It also satisfies the earlier point about testing at least two models to avoid model-specific conclusions.

## Summary

Requested: about **$30** of Anthropic credit, or the equivalent OpenAI / Google Cloud credit. Expected real spend is **$5 to $15**. The frontier generator is required as the strongest test of the metric. Every other component is free on university hardware. A free local open model can be added as a low-cost comparison, which answers the accessibility question directly rather than avoiding it.
