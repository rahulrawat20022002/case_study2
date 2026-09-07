"""
SYNTHETIC generator outputs for testing the scoring plumbing ONLY.

These are NOT real model outputs and carry no scientific meaning. They exist so
the Phase 3/4 scoring pipeline (correctness + faithfulness + buckets) can be run
end to end and proven push-button before the Anthropic API key lands.

For every test row and every configuration we fabricate a record with EXACTLY
the keys run_generation.py writes, so the scorers read synthetic and real output
through the same code path:

    id, config, gold_label, pred_label, explanation, parse_ok,
    edge_case_type, annex_iii_area, retrieved_top5[{id,text,score}],
    retrieved_top10_ids, usage, raw

Deterministic (seeded) so the test is reproducible. We deliberately:
  - flip ~25% of predicted labels wrong, independent of anything else, so all
    four outcome buckets get populated,
  - inject a couple of parse failures (pred_label=None) to exercise the
    parse-fail counting and the unscored path,
  - give baseline1 no retrieval (empty retrieved_top5) like the real harness,
  - write realistic multi-sentence explanations and fake passages so the stub
    judge extracts several statements per row.

    python tests/make_synthetic_runs.py [out_dir]   # default results/_synthetic_runs
"""
import os
import sys
import json
import random

CONFIGS = [
    ("baseline1_plain_llm", False),
    ("baseline2_standard_rag", True),
    ("agent_structured", True),
]
LABELS = ["high-risk", "not-high-risk"]


def flip(label):
    return "not-high-risk" if label == "high-risk" else "high-risk"


def fake_passages(area, section_hint, rng, n=5):
    out = []
    for i in range(n):
        out.append({
            "id": f"{area}-chunk-{rng.randint(1000,9999)}",
            "text": (f"Under the Annex III guidelines, systems used in the "
                     f"{area} area are assessed against the Article 6(2) route "
                     f"({section_hint}). The Article 6(3) filter may exempt a "
                     f"system that does not perform profiling of natural persons."),
            "score": round(rng.uniform(0.3, 0.9), 4),
        })
    return out


def explanation_for(area, label, faithful, rng):
    """Build an explanation whose stub faithfulness is a known value. Every
    sentence carries a [[SUPPORTED]]/[[UNSUPPORTED]] marker the StubJudge honors,
    so faithful -> 0.75 and unfaithful -> 0.25, deterministically. (Real
    explanations never contain these markers; this is a fixture device.)"""
    supported = [
        f"The system's intended purpose places it in the {area} use case of "
        f"Annex III [[SUPPORTED]].",
        f"The retrieved passages describe how the Article 6(2) route applies to "
        f"{area} [[SUPPORTED]].",
        f"The system is classified as {label} on the Annex III route [[SUPPORTED]].",
    ]
    unsupported = [
        "A national body independently audited the system last year [[UNSUPPORTED]].",
        "Comparable systems were fined under unrelated legislation [[UNSUPPORTED]].",
        "The vendor reports a low error rate in production [[UNSUPPORTED]].",
    ]
    if faithful:
        parts = supported[:3] + unsupported[:1]   # 3/4 supported -> 0.75
    else:
        parts = supported[:1] + unsupported[:3]   # 1/4 supported -> 0.25
    rng.shuffle(parts)
    return " ".join(parts)


def main(out_dir="results/_synthetic_runs", test_set="test_set.jsonl", seed=13):
    rng = random.Random(seed)
    rows = [json.loads(l) for l in open(test_set, encoding="utf-8") if l.strip()]
    os.makedirs(out_dir, exist_ok=True)

    # pick a few rows to be parse failures, deterministically
    fail_ids = set(rng.sample([r["id"] for r in rows], k=max(2, len(rows) // 60)))

    for name, retrieval in CONFIGS:
        recs = []
        for row in rows:
            gold = row["label"]
            area = row.get("annex_iii_area")
            section_hint = row.get("label_source", "")
            wrong = rng.random() < 0.25          # ~25% labels flipped wrong
            faithful = rng.random() >= 0.30      # ~30% explanations unfaithful
            pred = flip(gold) if wrong else gold

            is_fail = row["id"] in fail_ids
            top5 = fake_passages(area, section_hint, rng) if retrieval else []
            if name == "baseline1_plain_llm":
                expl = "Short reason for debugging only."
            else:
                expl = explanation_for(area, pred, faithful, rng)

            if is_fail:
                pred, parse_ok, expl = None, False, ""
                raw = "the model returned malformed text with no json"
            else:
                parse_ok = True
                raw = json.dumps({"label": pred, "explanation": expl})

            recs.append({
                "id": row["id"], "config": name,
                "gold_label": gold, "pred_label": pred,
                "explanation": expl, "parse_ok": parse_ok,
                "edge_case_type": row.get("edge_case_type"),
                "annex_iii_area": area,
                "retrieved_top5": top5,
                "retrieved_top10_ids": [p["id"] for p in top5],
                "usage": {"input_tokens": rng.randint(400, 1200),
                          "output_tokens": rng.randint(60, 300)},
                "raw": raw,
            })
        path = os.path.join(out_dir, f"{name}.jsonl")
        with open(path, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"  wrote {path}  ({len(recs)} rows, retrieval={retrieval})")
    print(f"synthetic runs in {out_dir}  (SYNTHETIC -- not real model output)")
    return out_dir


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "results/_synthetic_runs")
