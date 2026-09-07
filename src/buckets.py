"""
Four-bucket aggregator (Phase 4 machinery, built now so it is ready).

This is where the two axes meet. Each row of a retrieval config has a correctness
flag (label right or wrong vs frozen ground truth) and a faithfulness score
(explanation grounded in the retrieved passages or not). Cross them:

                        faithful              unfaithful
      label right   right + faithful       right + unfaithful   <- off-diagonal
      label wrong   wrong + faithful       wrong + unfaithful
                    ^ off-diagonal
                      "faithful but wrong" = the headline

The two off-diagonal buckets are the findings, so every off-diagonal row is
written out in full for qualitative inspection (sole annotator: Rah).

Faithfulness is continuous in [0,1]; calling a row "faithful" needs a cut. That
cut is a reporting decision for Phase 4, not something to bake in silently, so
this module:
  - takes faithful_threshold as a knob (default 0.5),
  - ALSO reports the bucket counts across a sweep of thresholds, and
  - reports the continuous relationship (mean faithfulness for right vs wrong
    predictions, and a point-biserial correlation between correctness and
    faithfulness),
so the "the two axes come apart" claim never rests on one arbitrary line.

Rows whose faithfulness is None (baseline1, or no context / no statements) cannot
be bucketed and are reported in a separate 'unscored' count, never forced into a
bucket.

Reads   results/scoring/correctness/{config}.jsonl
        results/scoring/faithfulness/{config}.jsonl
Writes  results/scoring/buckets/{config}_matrix.json
        results/scoring/buckets/{config}_offdiagonal.jsonl
        results/scoring/buckets_summary.md
"""
import os
import sys
import json
import glob
from statistics import mean, pstdev

SWEEP = [0.3, 0.5, 0.7, 0.9, 1.0]


def _load_jsonl(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def _index(rows, key="id"):
    return {r[key]: r for r in rows}


def bucket_of(correct, faithful):
    return ("right" if correct else "wrong") + "_" + \
           ("faithful" if faithful else "unfaithful")


def point_biserial(pairs):
    """corr between a binary (correct 0/1) and continuous (faithfulness).
    pairs: list of (correct_bool, faithfulness_float). Plain formula, no deps."""
    xs = [1.0 if c else 0.0 for c, _ in pairs]
    ys = [f for _, f in pairs]
    n = len(pairs)
    if n < 2:
        return None
    mx, my = mean(xs), mean(ys)
    sx, sy = pstdev(xs), pstdev(ys)
    if sx == 0 or sy == 0:
        return None
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / n
    return cov / (sx * sy)


def combine(config, corr_rows, faith_rows, faithful_threshold=0.5):
    corr = _index(corr_rows)
    faith = _index(faith_rows)
    ids = [i for i in corr if i in faith]

    joined = []
    unscored = []
    for i in ids:
        c = corr[i]
        fr = faith[i]
        fval = fr.get("faithfulness")
        rec = {
            "id": i,
            "config": config,
            "gold": c["gold"], "pred": c["pred"], "correct": c["correct"],
            "faithfulness": fval,
            "edge_case_type": c.get("edge_case_type"),
            "area": c.get("area"),
            "n_statements": fr.get("n_statements"),
            "n_supported": fr.get("n_supported"),
        }
        if fval is None:
            rec["skipped_reason"] = fr.get("skipped_reason")
            unscored.append(rec)
        else:
            joined.append(rec)

    def matrix_at(thr):
        counts = {"right_faithful": 0, "right_unfaithful": 0,
                  "wrong_faithful": 0, "wrong_unfaithful": 0}
        for r in joined:
            b = bucket_of(r["correct"], r["faithfulness"] >= thr)
            counts[b] += 1
        return counts

    primary = matrix_at(faithful_threshold)
    sweep = {str(t): matrix_at(t) for t in SWEEP}

    pairs = [(r["correct"], r["faithfulness"]) for r in joined]
    right_vals = [r["faithfulness"] for r in joined if r["correct"]]
    wrong_vals = [r["faithfulness"] for r in joined if not r["correct"]]

    # off-diagonal rows at the primary threshold, in full, for inspection
    off = []
    for r in joined:
        faithful = r["faithfulness"] >= faithful_threshold
        b = bucket_of(r["correct"], faithful)
        if b in ("wrong_faithful", "right_unfaithful"):
            rr = dict(r)
            rr["bucket"] = b
            # attach the judged statements so the failure is inspectable
            rr["statements"] = faith[r["id"]].get("statements", [])
            off.append(rr)

    result = {
        "config": config,
        "faithful_threshold": faithful_threshold,
        "n_joined_scored": len(joined),
        "n_unscored": len(unscored),
        "matrix": primary,
        "matrix_by_threshold": sweep,
        "off_diagonal": {
            "wrong_faithful_count": primary["wrong_faithful"],
            "right_unfaithful_count": primary["right_unfaithful"],
        },
        "continuous": {
            "mean_faithfulness_when_right": (mean(right_vals) if right_vals else None),
            "mean_faithfulness_when_wrong": (mean(wrong_vals) if wrong_vals else None),
            "point_biserial_correct_vs_faithfulness": point_biserial(pairs),
            "n_right": len(right_vals), "n_wrong": len(wrong_vals),
        },
    }
    return result, off, unscored


def run(out_dir="results/scoring", faithful_threshold=0.5, configs=None):
    corr_dir = os.path.join(out_dir, "correctness")
    faith_dir = os.path.join(out_dir, "faithfulness")
    bucket_dir = os.path.join(out_dir, "buckets")
    os.makedirs(bucket_dir, exist_ok=True)

    results = {}
    for cp in sorted(glob.glob(os.path.join(faith_dir, "*.jsonl"))):
        name = os.path.splitext(os.path.basename(cp))[0]
        if configs and name not in configs:
            continue
        corr_path = os.path.join(corr_dir, f"{name}.jsonl")
        if not os.path.exists(corr_path):
            continue
        corr_rows = _load_jsonl(corr_path)
        faith_rows = _load_jsonl(cp)
        res, off, unscored = combine(name, corr_rows, faith_rows,
                                     faithful_threshold)
        results[name] = res
        with open(os.path.join(bucket_dir, f"{name}_matrix.json"), "w",
                  encoding="utf-8") as f:
            json.dump(res, f, indent=2)
        with open(os.path.join(bucket_dir, f"{name}_offdiagonal.jsonl"), "w",
                  encoding="utf-8") as f:
            for r in off:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(os.path.join(out_dir, "buckets_summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    _write_md(results, os.path.join(out_dir, "buckets_summary.md"),
              faithful_threshold)
    return results


def _write_md(results, path, thr):
    L = ["# Four-bucket outcome matrix (correctness x faithfulness)\n",
         f"Faithful threshold = {thr} (a reporting choice; sweep and continuous "
         "stats below so nothing rests on it). Off-diagonal buckets are the "
         "findings: **wrong + faithful** is the headline 'faithful but wrong'.\n"]
    for name, r in results.items():
        m = r["matrix"]
        c = r["continuous"]
        L.append(f"## {name}\n")
        L.append(f"Joined & scored rows: {r['n_joined_scored']}  "
                 f"(unscored, no faithfulness: {r['n_unscored']})\n")
        L.append("| | faithful | unfaithful |")
        L.append("|---|---|---|")
        L.append(f"| **label right** | {m['right_faithful']} | "
                 f"{m['right_unfaithful']} |")
        L.append(f"| **label wrong** | {m['wrong_faithful']} | "
                 f"{m['wrong_unfaithful']} |\n")
        mr = c["mean_faithfulness_when_right"]
        mw = c["mean_faithfulness_when_wrong"]
        pb = c["point_biserial_correct_vs_faithfulness"]
        L.append(f"Mean faithfulness when label right: "
                 f"{mr:.3f}" if mr is not None else "n/a")
        L.append(f"Mean faithfulness when label wrong: "
                 f"{mw:.3f}" if mw is not None else "n/a")
        L.append(f"Point-biserial corr(correct, faithfulness): "
                 f"{pb:.3f}" if pb is not None else "n/a")
        L.append("\nBucket counts across faithful thresholds:\n")
        L.append("| threshold | right+faithful | right+unfaithful | "
                 "wrong+faithful | wrong+unfaithful |")
        L.append("|---|---|---|---|---|")
        for t, mm in r["matrix_by_threshold"].items():
            L.append(f"| {t} | {mm['right_faithful']} | {mm['right_unfaithful']} "
                     f"| {mm['wrong_faithful']} | {mm['wrong_unfaithful']} |")
        L.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    thr = float(sys.argv[1]) if len(sys.argv) > 1 else 0.5
    res = run(faithful_threshold=thr)
    for name, r in res.items():
        m = r["matrix"]
        print(f"{name}: right/faithful={m['right_faithful']} "
              f"right/unfaithful={m['right_unfaithful']} "
              f"wrong/faithful={m['wrong_faithful']} "
              f"wrong/unfaithful={m['wrong_unfaithful']} "
              f"(unscored={r['n_unscored']})")
    print("wrote results/scoring/buckets/*.json + buckets_summary.md")
