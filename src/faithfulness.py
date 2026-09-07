"""
RAGAS faithfulness harness (Phase 3, faithfulness side).

Faithfulness asks a narrow question: is the generator's explanation grounded in
the passages it was actually given? It says nothing about whether the legal label
is right. That blind spot is the whole point of the study, so this metric is the
one on trial.

For each generator output row this computes, via a pluggable judge (see
judges.py):

    faithfulness = supported_statements / total_statements

    step 1  extract atomic statements from the explanation (question = the system
            description, joined back in from the test set by id)
    step 2  a verdict per statement: can it be inferred from the retrieved context

The judge is the stub by default so this whole file runs offline with no model
and no network, which is what makes the pipeline push-button before the real
judge is picked. The real judge (a non-Anthropic model on the GPU node) slots in
through get_judge without touching this code.

By design, baseline1 (no retrieval) gets no faithfulness score: there is no
retrieved context to be grounded in. Rows with an empty explanation or empty
context are scored None with a skipped_reason, never a misleading 0.0.

Reads   results/runs/{config}.jsonl , test_set.jsonl (for the question text)
Writes  results/scoring/faithfulness/{config}.jsonl  (per row, with statements)
        results/scoring/faithfulness_summary.json / .md
"""
import os
import sys
import json
import glob
import argparse
import yaml
from statistics import mean

from judges import get_judge


def _load_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def _question_index(test_set_path):
    idx = {}
    for r in _load_jsonl(test_set_path):
        idx[r["id"]] = r.get("system_description", "")
    return idx


def _context_from(record):
    """Concatenate the top-5 retrieved passage texts the generator actually saw."""
    passages = record.get("retrieved_top5") or []
    parts = []
    for i, p in enumerate(passages, 1):
        parts.append(f"[Passage {i}]\n{p.get('text','')}")
    return "\n\n".join(parts)


def score_row(judge, question, record):
    """Faithfulness for one generator output row. Returns a per-row dict."""
    explanation = (record.get("explanation") or "").strip()
    context = _context_from(record)

    if not context:
        return {"id": record.get("id"), "config": record.get("config"),
                "faithfulness": None, "skipped_reason": "no-retrieved-context",
                "n_statements": 0, "n_supported": 0, "statements": [],
                "judge": judge.name}
    if not explanation:
        return {"id": record.get("id"), "config": record.get("config"),
                "faithfulness": None, "skipped_reason": "no-explanation",
                "n_statements": 0, "n_supported": 0, "statements": [],
                "judge": judge.name}

    statements = judge.extract_statements(question, explanation)
    if not statements:
        return {"id": record.get("id"), "config": record.get("config"),
                "faithfulness": None, "skipped_reason": "no-statements-extracted",
                "n_statements": 0, "n_supported": 0, "statements": [],
                "judge": judge.name}

    verdicts = judge.verdicts(context, statements)
    n_supported = sum(v["verdict"] for v in verdicts)
    return {
        "id": record.get("id"),
        "config": record.get("config"),
        "faithfulness": n_supported / len(verdicts),
        "skipped_reason": None,
        "n_statements": len(verdicts),
        "n_supported": n_supported,
        "statements": verdicts,
        "judge": judge.name,
    }


def score_config(records, questions, judge, progress=False):
    rows = []
    for i, rec in enumerate(records, 1):
        q = questions.get(rec.get("id"), "")
        rows.append(score_row(judge, q, rec))
        if progress and i % 25 == 0:
            print(f"    scored {i}/{len(records)}")
    return rows


def _summarize(rows):
    scored = [r for r in rows if r["faithfulness"] is not None]
    vals = [r["faithfulness"] for r in scored]
    return {
        "n": len(rows),
        "n_scored": len(scored),
        "n_skipped": len(rows) - len(scored),
        "skipped_reasons": _count([r["skipped_reason"] for r in rows
                                   if r["skipped_reason"]]),
        "mean_faithfulness": (mean(vals) if vals else None),
        "min": (min(vals) if vals else None),
        "max": (max(vals) if vals else None),
        "n_perfect_1.0": sum(1 for v in vals if v == 1.0),
        "n_zero_0.0": sum(1 for v in vals if v == 0.0),
    }


def _count(xs):
    d = {}
    for x in xs:
        d[x] = d.get(x, 0) + 1
    return d


def run(judge, runs_dir="results/runs", out_dir="results/scoring",
        test_set_path="test_set.jsonl", skip_configs=("baseline1_plain_llm",),
        configs=None, progress=False):
    """Score faithfulness for every retrieval config run file. Baseline1 skipped
    by design. Returns {config: summary}."""
    faith_dir = os.path.join(out_dir, "faithfulness")
    os.makedirs(faith_dir, exist_ok=True)
    questions = _question_index(test_set_path)

    summaries = {}
    for p in sorted(glob.glob(os.path.join(runs_dir, "*.jsonl"))):
        name = os.path.splitext(os.path.basename(p))[0]
        if configs and name not in configs:
            continue
        if name in set(skip_configs):
            summaries[name] = {"skipped": "no retrieval, faithfulness N/A by design"}
            continue
        records = _load_jsonl(p)
        if progress:
            print(f"  faithfulness: {name} ({len(records)} rows) judge={judge.name}")
        rows = score_config(records, questions, judge, progress=progress)
        with open(os.path.join(faith_dir, f"{name}.jsonl"), "w",
                  encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        summaries[name] = _summarize(rows)

    with open(os.path.join(out_dir, "faithfulness_summary.json"), "w",
              encoding="utf-8") as f:
        json.dump({"judge": judge.name, "by_config": summaries}, f, indent=2)
    _write_md(judge, summaries, os.path.join(out_dir, "faithfulness_summary.md"))
    return summaries


def _write_md(judge, summaries, path):
    L = ["# RAGAS faithfulness (explanation grounded in retrieved passages)\n",
         f"Judge: `{judge.name}`. Faithfulness = supported statements / total "
         "statements. Baseline1 has no retrieval, so no score by design. "
         "Faithfulness says nothing about label correctness -- that gap is the "
         "study's subject.\n",
         "| Config | n | scored | skipped | mean faithfulness | =1.0 | =0.0 |",
         "|---|---|---|---|---|---|---|"]
    for name, s in summaries.items():
        if "skipped" in s:
            L.append(f"| {name} | - | - | - | (no retrieval) | - | - |")
            continue
        mf = f"{s['mean_faithfulness']:.3f}" if s['mean_faithfulness'] is not None else "-"
        L.append(f"| {name} | {s['n']} | {s['n_scored']} | {s['n_skipped']} | "
                 f"{mf} | {s['n_perfect_1.0']} | {s['n_zero_0.0']} |")
    L.append("")
    for name, s in summaries.items():
        if "skipped" not in s and s["skipped_reasons"]:
            L.append(f"{name} skipped reasons: {s['skipped_reasons']}")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--judge", default="stub", help="stub | openai | vllm")
    ap.add_argument("--judge-model", default=None)
    ap.add_argument("--judge-base-url", default=None)
    ap.add_argument("--runs-dir", default="results/runs")
    ap.add_argument("--out-dir", default="results/scoring")
    ap.add_argument("--test-set", default="test_set.jsonl")
    ap.add_argument("--config-file", default="config/pipeline.yaml")
    args = ap.parse_args()

    # let the config supply test_set path if present, else the flag default
    try:
        cfg = yaml.safe_load(open(args.config_file))
        test_set = cfg.get("paths", {}).get("test_set", args.test_set)
    except FileNotFoundError:
        test_set = args.test_set

    judge = get_judge(args.judge, model=args.judge_model,
                      base_url=args.judge_base_url)
    res = run(judge, runs_dir=args.runs_dir, out_dir=args.out_dir,
              test_set_path=test_set, progress=True)
    for name, s in res.items():
        if "skipped" in s:
            print(f"{name:24s} (no retrieval, skipped)")
        else:
            mf = s["mean_faithfulness"]
            print(f"{name:24s} mean_faithfulness="
                  f"{mf:.3f}" if mf is not None else f"{name:24s} mean=none",
                  f" scored={s['n_scored']} skipped={s['n_skipped']}")
    print("wrote results/scoring/faithfulness_summary.json and .md")


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(__file__))
    main()
