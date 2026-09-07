"""
Correctness lookup (Phase 3, correctness side). No model involved: this is a pure
comparison of each generator's predicted label against the frozen Commission
ground-truth label. It is the other axis from faithfulness, and the two are
combined in buckets.py.

Positive class = "high-risk" (the thing the study is really about detecting).
Because the test set is imbalanced (66 high-risk vs 149 not, frozen), we report
per-class precision / recall / F1 and the confusion counts alongside plain
accuracy, and break correctness down by Article 6(3) filter rows vs the rest and
by Annex III area, so a headline accuracy cannot hide a class or a hard slice.

A parse failure (pred_label is null, from run_generation) is counted as an
incorrect prediction, and also reported separately as n_parse_fail so it is never
silently swallowed.

Reads   results/runs/{config}.jsonl   (whatever run_generation wrote)
Public  score_run(records) -> dict     (used by the driver and by buckets.py)
"""
import os
import sys
import json
import glob
from collections import Counter, defaultdict

POSITIVE = "high-risk"
LABELS = ["high-risk", "not-high-risk"]


def _safe_div(a, b):
    return (a / b) if b else 0.0


def per_row_correctness(records):
    """[{id, gold, pred, correct, parse_ok, edge_case_type, area}] for one config."""
    out = []
    for r in records:
        gold = r.get("gold_label")
        pred = r.get("pred_label")
        out.append({
            "id": r.get("id"),
            "gold": gold,
            "pred": pred,
            "parse_ok": bool(r.get("parse_ok", pred is not None)),
            "correct": (pred is not None and pred == gold),
            "edge_case_type": r.get("edge_case_type"),
            "area": r.get("annex_iii_area"),
        })
    return out


def _class_metrics(rows):
    """Binary metrics with high-risk as the positive class."""
    tp = sum(1 for x in rows if x["gold"] == POSITIVE and x["pred"] == POSITIVE)
    fp = sum(1 for x in rows if x["gold"] != POSITIVE and x["pred"] == POSITIVE)
    fn = sum(1 for x in rows if x["gold"] == POSITIVE and x["pred"] != POSITIVE)
    tn = sum(1 for x in rows if x["gold"] != POSITIVE and x["pred"] != POSITIVE)
    prec = _safe_div(tp, tp + fp)
    rec = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * prec * rec, prec + rec)
    # the mirror class (not-high-risk as positive), for a full per-class picture
    n_tp = tn
    n_fp = fn
    n_fn = fp
    n_prec = _safe_div(n_tp, n_tp + n_fp)
    n_rec = _safe_div(n_tp, n_tp + n_fn)
    n_f1 = _safe_div(2 * n_prec * n_rec, n_prec + n_rec)
    return {
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "high-risk": {"precision": prec, "recall": rec, "f1": f1,
                      "support": tp + fn},
        "not-high-risk": {"precision": n_prec, "recall": n_rec, "f1": n_f1,
                          "support": tn + fp},
        "macro_f1": (f1 + n_f1) / 2,
    }


def _accuracy(rows):
    return _safe_div(sum(1 for x in rows if x["correct"]), len(rows))


def score_run(records):
    """Full correctness summary for one config's run records."""
    rows = per_row_correctness(records)
    n = len(rows)
    n_parse_fail = sum(1 for x in rows if not x["parse_ok"] or x["pred"] is None)

    summary = {
        "n": n,
        "n_parse_fail": n_parse_fail,
        "accuracy": _accuracy(rows),
        "class_metrics": _class_metrics(rows),
        "by_edge_case": {},
        "by_area": {},
        "pred_distribution": dict(Counter(x["pred"] for x in rows)),
        "gold_distribution": dict(Counter(x["gold"] for x in rows)),
    }
    for e in sorted({x["edge_case_type"] for x in rows}):
        sub = [x for x in rows if x["edge_case_type"] == e]
        summary["by_edge_case"][e] = {"n": len(sub), "accuracy": _accuracy(sub)}
    for a in sorted({x["area"] for x in rows if x["area"] is not None}):
        sub = [x for x in rows if x["area"] == a]
        summary["by_area"][a] = {"n": len(sub), "accuracy": _accuracy(sub)}
    return summary, rows


def _load(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def run(runs_dir="results/runs", out_dir="results/scoring", configs=None):
    """Score every config run file in runs_dir. Writes per-config per-row files
    and one correctness_summary.json/.md. Returns {config: summary}."""
    os.makedirs(out_dir, exist_ok=True)
    per_row_dir = os.path.join(out_dir, "correctness")
    os.makedirs(per_row_dir, exist_ok=True)

    paths = sorted(glob.glob(os.path.join(runs_dir, "*.jsonl")))
    summaries = {}
    for p in paths:
        name = os.path.splitext(os.path.basename(p))[0]
        if configs and name not in configs:
            continue
        records = _load(p)
        summary, rows = score_run(records)
        summaries[name] = summary
        with open(os.path.join(per_row_dir, f"{name}.jsonl"), "w",
                  encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    with open(os.path.join(out_dir, "correctness_summary.json"), "w",
              encoding="utf-8") as f:
        json.dump(summaries, f, indent=2)
    _write_md(summaries, os.path.join(out_dir, "correctness_summary.md"))
    return summaries


def _write_md(summaries, path):
    L = ["# Correctness (predicted label vs frozen Commission ground truth)\n",
         "Positive class = high-risk. Accuracy plus per-class precision/recall/F1 "
         "because the set is imbalanced (frozen). Parse failures counted as "
         "incorrect and also shown separately.\n"]
    L.append("| Config | n | Accuracy | HR precision | HR recall | HR F1 | "
             "Macro F1 | Parse fails |")
    L.append("|---|---|---|---|---|---|---|---|")
    for name, s in summaries.items():
        cm = s["class_metrics"]
        hr = cm["high-risk"]
        L.append(f"| {name} | {s['n']} | {s['accuracy']:.3f} | "
                 f"{hr['precision']:.3f} | {hr['recall']:.3f} | {hr['f1']:.3f} | "
                 f"{cm['macro_f1']:.3f} | {s['n_parse_fail']} |")
    L.append("")
    for name, s in summaries.items():
        cm = s["class_metrics"]["confusion"]
        L.append(f"## {name}\n")
        L.append(f"Confusion (high-risk positive): "
                 f"tp={cm['tp']} fp={cm['fp']} fn={cm['fn']} tn={cm['tn']}\n")
        L.append("By edge-case type: " +
                 ", ".join(f"{e} n={v['n']} acc={v['accuracy']:.3f}"
                           for e, v in s["by_edge_case"].items()) + "\n")
        L.append("By area: " +
                 ", ".join(f"{a} {v['accuracy']:.3f}"
                           for a, v in s["by_area"].items()) + "\n")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    d = sys.argv[1] if len(sys.argv) > 1 else "results/runs"
    res = run(runs_dir=d)
    for name, s in res.items():
        hr = s["class_metrics"]["high-risk"]
        print(f"{name:24s} acc={s['accuracy']:.3f}  HR f1={hr['f1']:.3f}  "
              f"parse_fail={s['n_parse_fail']}  (n={s['n']})")
    print(f"wrote results/scoring/correctness_summary.json and .md")
