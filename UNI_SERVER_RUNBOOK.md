# Running Case Study 2 on the university server

Everything runs from one notebook: `run_pipeline.ipynb`. Open it on the uni
portal and run the cells top to bottom.

## One-time: get the files onto the portal
1. Push this repo to a private GitHub repo (from your Mac — see the chat for the
   exact commands).
2. On the uni portal, open a terminal and `git clone <your repo url>`, then open
   `run_pipeline.ipynb`.

## The two switches (top of the notebook, section 2)
- **Generator**
  - Free dev run (default): `GEN_PROVIDER="openai_compatible"`,
    `GEN_MODEL="gemini-2.0-flash"`, paste a free Google AI Studio key.
  - Real graded run: `GEN_PROVIDER="anthropic"`, `GEN_MODEL="claude-sonnet-4-6"`,
    paste `ANTHROPIC_API_KEY`.
- **Judge**
  - Dev: `JUDGE="stub"` (offline, instant, not a real measurement).
  - Real: `JUDGE="vllm"` (the frozen 70B open model on this GPU).
- **Run size**: `RUN_FULL=False` does 8 rows per config to test; `True` does the
  full 215 x 3.

## What each section does
0. Environment probe — checks internet + GPU.
1. Install dependencies (once, needs internet).
2. Config — the two switches above.
3. Corpus — uses the committed 400-chunk corpus (no poppler needed).
4. Embed + index — downloads the bge model, builds the vector store.
5. Retrieval quality — optional check, no API. Expect Hit@5 ~0.83.
6. Generation — writes results/runs/{config}.jsonl.
7. Judge + scoring — stub, or starts a vLLM server with the 70B and scores.
8. Results — correctness, faithfulness, and the four-bucket matrix.

## Suggested first pass on the server
Free generator + stub judge + `RUN_FULL=False`. That proves the whole pipeline
runs on the uni box end to end without spending anything. Then switch to the 70B
judge, then to the frozen generator + full run when the uni API is ready.

Reminder: free-model runs are for debugging. The manuscript numbers use the
frozen generator (claude-sonnet-4-6) and the 70B judge.
