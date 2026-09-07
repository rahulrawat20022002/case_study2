# Case Study 2 — Phase 2: agent build (system under test)

The system under test for the "faithful but wrong" evaluation. One shared
retrieval pipeline over the Commission guidelines, three prompt configurations,
one generator. This directory contains everything needed to reproduce the
build; the evaluation harness (RAGAS faithfulness judge + correctness lookup)
is Phase 3.

## What was decided in this phase

**Corpus is normative text only.** The retrieval corpus is chunked from the
Commission guidelines' numbered normative paragraphs (sections 2.x general
principles including the Article 6(3) filter, and 3.x the eight Annex III
areas). The worked examples — the a/b/c "Practical example" blocks and inline
verdict enumerations — are **held out**, because those examples with their
stated verdicts are the test set and ground truth. Leaving them in the corpus
would let the agent retrieve its own answer (label leakage) and collapse the
wrong/unfaithful buckets the study exists to measure. Article 6(1)/Annex I
(section III) is excluded as out of scope per the frozen task anchor. Result:
**361 normative chunks**, all eight areas represented, zero example/verdict
leakage (verified).

**Structural chunking**, one chunk per numbered paragraph, carrying its heading
path; paragraphs longer than 1800 chars are split at sentence boundaries to fit
the encoder window.

**Retrieval** is hybrid BM25 + bge-base-en-v1.5 dense over Chroma, fused with
fixed alpha 0.5 (both score vectors min-max normalised). top-5 goes to the
generator; top-10 is logged per row for post-hoc analysis without re-running.

**Three configurations**, identical retrieval and identical generation settings
(claude-sonnet-4-6, temperature 0), only the prompt differs:
- `baseline1_plain_llm` — no retrieval, label + short reason only.
- `baseline2_standard_rag` — top-5 passages + generic prompt, label + grounded explanation.
- `agent_structured` — same passages, prompt walks Article 6(2) / Annex III / the 6(3) filter.

## Files

```
config/pipeline.yaml     every knob in one place (frozen values noted)
src/build_corpus.py      guidelines PDF -> normative chunks (examples held out)
src/encoder.py           bge-base encoder factory (+ offline test stand-in)
src/embed_and_index.py   embed chunks -> Chroma collection (run once)
src/retriever.py         hybrid BM25 + dense retrieval, alpha 0.5
src/prompts.py           the three configurations
src/run_generation.py    retrieve -> prompt -> generate -> parse -> log
results/corpus_chunks.jsonl   the 361-chunk corpus (built, committed)
results/architecture.svg/.png the Phase 2 architecture figure
```

## Run order

```bash
pip install -r requirements.txt          # on your own machine (see note below)

python src/build_corpus.py data/guidelines/Draft_Guidelines_on_the_classification_of_high_risk_AI_Annex_III.pdf results/corpus_chunks.jsonl
python src/embed_and_index.py config/pipeline.yaml        # builds results/chroma
python src/retriever.py config/pipeline.yaml              # smoke-test a query

python src/sanity_run.py                                  # 9-row stratified sanity
python src/run_generation.py                             # full 215, all configs
```

## Generator access: Vertex AI (default) or first-party API

The generator is claude-sonnet-4-6 either way; `generation.provider` in the
config picks the access path.

**Vertex AI (billed to your GCP project).** One-time setup:
```bash
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com
# In the Cloud console -> Vertex AI -> Model Garden, find Claude Sonnet 4.6
# and click Enable / accept terms once.
pip install -U "anthropic[vertex]"
```
Then set `generation.provider: vertex` and your `vertex.project_id` in
`config/pipeline.yaml` (region "global" is fine, no premium). If a call errors
on the model name, Model Garden will show the exact id (sometimes with an
`@version` suffix); put it in `vertex.model_override`. No key env var needed;
auth comes from `gcloud`.

**First-party API instead.** Set `generation.provider: anthropic` and
`export ANTHROPIC_API_KEY=sk-ant-...`.

## Note on the embedding model

`build_corpus.py`, `retriever.py`, and `run_generation.py` were validated in
the build session; the embedding step downloads bge-base-en-v1.5 from Hugging
Face, which the build sandbox's network blocked. Run the embed step where you
have normal internet (your machine). For offline plumbing tests only, set
`CS2_FAKE_EMBED=1` to swap in a non-semantic hashing encoder — never use it for
eval results.
