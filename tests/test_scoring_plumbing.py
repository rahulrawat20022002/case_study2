"""
End-to-end plumbing test for the Phase 3/4 scoring pipeline.

Runs entirely offline with the stub judge. It fabricates synthetic generator
outputs (tests/make_synthetic_runs.py), runs correctness + faithfulness + buckets
over them, and asserts every piece produced sane output. If this passes, the
pipeline is push-button: swap the synthetic dir for the real results/runs and the
stub judge for the chosen judge, and nothing else changes.

    python tests/test_scoring_plumbing.py

Writes fixtures + scoring to results/_synthetic_* so the real results/runs (which
will hold the REAL generator outputs) is never touched. Prints PASS/FAIL and
exits non-zero on failure.
"""
import os
import sys
import json


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, HERE)
os.chdir(ROOT)

import make_synthetic_runs
import correctness
import faithfulness
import buckets
from judges import get_judge

import tempfile
_SCRATCH = os.path.join(tempfile.gettempdir(), "cs2_scoring_plumbing")
RUNS_DIR = os.path.join(_SCRATCH, "runs")     # synthetic, outside the repo
OUT_DIR = os.path.join(_SCRATCH, "scoring")   # so results/ stays clean for real runs

failures = []


def check(cond, msg):
    print(("  ok   " if cond else "  FAIL ") + msg)
    if not cond:
        failures.append(msg)


def jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def main():
    for d in (RUNS_DIR, OUT_DIR):
        os.makedirs(d, exist_ok=True)

    print("\n== fabricate synthetic generator outputs ==")
    make_synthetic_runs.main(out_dir=RUNS_DIR)
    for name in ("baseline1_plain_llm", "baseline2_standard_rag", "agent_structured"):
        p = os.path.join(RUNS_DIR, f"{name}.jsonl")
        check(os.path.exists(p), f"synthetic run file exists: {name}")
        recs = jsonl(p)
        need = {"id", "config", "gold_label", "pred_label", "explanation",
                "parse_ok", "edge_case_type", "annex_iii_area",
                "retrieved_top5", "retrieved_top10_ids", "usage", "raw"}
        check(need.issubset(recs[0].keys()),
              f"{name} record has the exact run_generation contract keys")

    print("\n== [1/3] correctness ==")
    corr = correctness.run(runs_dir=RUNS_DIR, out_dir=OUT_DIR)
    check(set(corr) == {"baseline1_plain_llm", "baseline2_standard_rag",
                        "agent_structured"}, "correctness scored all 3 configs")
    for name, s in corr.items():
        check(s["n"] == 215, f"{name}: scored 215 rows")
        check(0.0 <= s["accuracy"] <= 1.0, f"{name}: accuracy in [0,1]")
        check(s["n_parse_fail"] >= 1, f"{name}: parse failures counted "
              f"({s['n_parse_fail']})")
        hr = s["class_metrics"]["high-risk"]
        check(hr["support"] == 66, f"{name}: high-risk support = 66 (matches gold)")
    check(os.path.exists(os.path.join(OUT_DIR, "correctness_summary.md")),
          "correctness_summary.md written")

    print("\n== [2/3] faithfulness (stub judge, offline) ==")
    judge = get_judge("stub")
    faith = faithfulness.run(judge, runs_dir=RUNS_DIR, out_dir=OUT_DIR,
                             test_set_path="test_set.jsonl")
    check(faith["baseline1_plain_llm"].get("skipped") is not None,
          "baseline1 skipped by design (no retrieval)")
    for name in ("baseline2_standard_rag", "agent_structured"):
        s = faith[name]
        check(s["n_scored"] >= 200, f"{name}: most rows scored ({s['n_scored']})")
        check(s["mean_faithfulness"] is not None
              and 0.0 <= s["mean_faithfulness"] <= 1.0,
              f"{name}: mean faithfulness in [0,1] "
              f"({s['mean_faithfulness']:.3f})")
        # a scored row must carry per-statement verdicts
        rows = jsonl(os.path.join(OUT_DIR, "faithfulness", f"{name}.jsonl"))
        scored = [r for r in rows if r["faithfulness"] is not None]
        check(scored and scored[0]["n_statements"] >= 1,
              f"{name}: statements extracted per scored row")
        check(all("verdict" in v for v in scored[0]["statements"]),
              f"{name}: each statement carries a verdict")

    print("\n== [3/3] four-bucket matrix ==")
    buck = buckets.run(out_dir=OUT_DIR, faithful_threshold=0.5)
    check(set(buck) == {"baseline2_standard_rag", "agent_structured"},
          "buckets built for the 2 retrieval configs (baseline1 has no faithfulness)")
    for name, r in buck.items():
        m = r["matrix"]
        total = sum(m.values())
        check(total == r["n_joined_scored"], f"{name}: bucket counts sum to joined rows")
        for b in ("right_faithful", "right_unfaithful", "wrong_faithful",
                  "wrong_unfaithful"):
            check(m[b] > 0, f"{name}: bucket '{b}' populated ({m[b]})")
        check(m["wrong_faithful"] > 0,
              f"{name}: HEADLINE 'faithful but wrong' bucket populated "
              f"({m['wrong_faithful']})")
        off = os.path.join(OUT_DIR, "buckets", f"{name}_offdiagonal.jsonl")
        offrows = jsonl(off)
        expected_off = m["wrong_faithful"] + m["right_unfaithful"]
        check(len(offrows) == expected_off,
              f"{name}: off-diagonal file has all off-diagonal rows "
              f"({len(offrows)} == {expected_off})")
        check(offrows and "statements" in offrows[0],
              f"{name}: off-diagonal rows carry judged statements for inspection")
        check(r["continuous"]["point_biserial_correct_vs_faithfulness"] is not None,
              f"{name}: continuous correlation computed")
        # sweep present
        check(set(r["matrix_by_threshold"]) == {"0.3","0.5","0.7","0.9","1.0"},
              f"{name}: threshold sweep present")
    check(os.path.exists(os.path.join(OUT_DIR, "buckets_summary.md")),
          "buckets_summary.md written")

    print("\n== summary ==")
    if failures:
        print(f"FAIL: {len(failures)} check(s) failed")
        for m in failures:
            print("   - " + m)
        sys.exit(1)
    print("PASS: scoring pipeline is push-button end to end (stub judge, offline).")
    print(f"(synthetic artifacts under scratch: {_SCRATCH}/ -- outside the repo)")


if __name__ == "__main__":
    main()
