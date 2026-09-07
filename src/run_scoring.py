"""
Phase 3/4 scoring driver -- the one push-button entry point.

The day the generator API key lands, run_generation.py writes
results/runs/{config}.jsonl for the three configurations. Then this:

    python src/run_scoring.py                       # stub judge, offline, instant
    python src/run_scoring.py --judge openai --judge-model gpt-5-mini
    python src/run_scoring.py --judge vllm --judge-model Qwen2.5-72B-Instruct \
           --judge-base-url http://gpu-node:8000/v1   # offline GPU node

does all three scoring pieces in order and drops every result under
results/scoring/:

    1. correctness  (correctness.py)  -- pred label vs frozen gold, no model
    2. faithfulness (faithfulness.py) -- RAGAS faithfulness via the chosen judge
    3. buckets      (buckets.py)      -- four-bucket matrix + off-diagonal rows

correctness needs no judge, so it always runs; faithfulness skips baseline1 by
design. Nothing here re-runs the generator or touches the retriever, so it stays
independent of the reused orchestrator, as frozen.
"""
import os
import sys
import argparse
import yaml

sys.path.insert(0, os.path.dirname(__file__))
import correctness
import faithfulness
import buckets
from judges import get_judge


def main():
    ap = argparse.ArgumentParser(description="Run all Phase 3/4 scoring.")
    ap.add_argument("--config-file", default="config/pipeline.yaml")
    ap.add_argument("--runs-dir", default=None,
                    help="dir of {config}.jsonl generator outputs "
                         "(default: paths.runs_dir from config)")
    ap.add_argument("--out-dir", default="results/scoring")
    ap.add_argument("--judge", default="stub", help="stub | openai | vllm")
    ap.add_argument("--judge-model", default=None)
    ap.add_argument("--judge-base-url", default=None)
    ap.add_argument("--faithful-threshold", type=float, default=0.5,
                    help="cut for calling a row 'faithful' in the bucket matrix "
                         "(reporting choice; a sweep is always reported too)")
    ap.add_argument("--configs", nargs="*", default=None,
                    help="restrict to these config names")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config_file))
    runs_dir = args.runs_dir or cfg.get("paths", {}).get("runs_dir", "results/runs")
    test_set = cfg.get("paths", {}).get("test_set", "test_set.jsonl")

    print(f"scoring runs in {runs_dir}  ->  {args.out_dir}")
    print(f"judge: {args.judge}"
          + (f" ({args.judge_model})" if args.judge_model else "")
          + (f" @ {args.judge_base_url}" if args.judge_base_url else ""))

    # 1. correctness
    print("\n[1/3] correctness")
    corr = correctness.run(runs_dir=runs_dir, out_dir=args.out_dir,
                           configs=args.configs)
    for name, s in corr.items():
        hr = s["class_metrics"]["high-risk"]
        print(f"    {name:24s} acc={s['accuracy']:.3f}  HR_f1={hr['f1']:.3f}  "
              f"parse_fail={s['n_parse_fail']}")

    # 2. faithfulness
    print("\n[2/3] faithfulness")
    judge = get_judge(args.judge, model=args.judge_model,
                      base_url=args.judge_base_url)
    faith = faithfulness.run(judge, runs_dir=runs_dir, out_dir=args.out_dir,
                             test_set_path=test_set, configs=args.configs,
                             progress=True)
    for name, s in faith.items():
        if "skipped" in s:
            print(f"    {name:24s} (no retrieval, skipped by design)")
        else:
            mf = s["mean_faithfulness"]
            mfs = f"{mf:.3f}" if mf is not None else "none"
            print(f"    {name:24s} mean_faithfulness={mfs}  "
                  f"scored={s['n_scored']}  skipped={s['n_skipped']}")

    # 3. buckets
    print("\n[3/3] four-bucket matrix")
    buck = buckets.run(out_dir=args.out_dir,
                       faithful_threshold=args.faithful_threshold,
                       configs=args.configs)
    for name, r in buck.items():
        m = r["matrix"]
        print(f"    {name}: RF={m['right_faithful']} RU={m['right_unfaithful']} "
              f"WF={m['wrong_faithful']} WU={m['wrong_unfaithful']} "
              f"(unscored={r['n_unscored']})")
        print(f"        headline 'faithful but wrong' = {m['wrong_faithful']}  |  "
              f"'right but unfaithful' = {m['right_unfaithful']}")

    print(f"\ndone. all outputs under {args.out_dir}/")
    print("  correctness_summary.{json,md}  faithfulness_summary.{json,md}  "
          "buckets_summary.{json,md}")
    print("  per-row: correctness/  faithfulness/  buckets/{*_matrix.json, "
          "*_offdiagonal.jsonl}")


if __name__ == "__main__":
    main()
