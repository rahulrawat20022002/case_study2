"""
Phase 2 sanity run (item 5). Runs all three configurations on a small stratified
sample and prints a side-by-side comparison, plus writes full outputs (with
explanations and retrieved passages) to results/runs/sanity_<config>.jsonl for
manual reading. This is for eyeballing wiring and output quality, NOT for eval.

    export ANTHROPIC_API_KEY=sk-ant-...
    python src/sanity_run.py            # ~9 rows x 3 configs
"""
import os
import sys
import json
import yaml
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from prompts import BUILDERS
from retriever import HybridRetriever
from run_generation import call_generator, parse_output, get_client


def stratified_ids(rows, n_each=3):
    hr = [r for r in rows if r["label"] == "high-risk"]
    nr = [r for r in rows if r["label"] == "not-high-risk" and r.get("edge_case_type") == "none"]
    fl = [r for r in rows if r.get("edge_case_type") == "article-6-3-filter"]
    seen, pick = set(), []
    for r in hr:                       # high-risk across distinct areas
        if r["annex_iii_area"] not in seen:
            pick.append(r); seen.add(r["annex_iii_area"])
        if len(pick) >= n_each:
            break
    pick += nr[:n_each] + fl[:n_each]
    return pick


def main(cfg_path="config/pipeline.yaml"):
    cfg = yaml.safe_load(open(cfg_path))
    gen_cfg = cfg["generation"]
    rows_all = [json.loads(l) for l in open(cfg["paths"]["test_set"], encoding="utf-8")]
    rows = stratified_ids(rows_all)

    retriever = HybridRetriever(cfg_path)
    client = get_client(gen_cfg)

    runs_dir = Path(cfg["paths"]["runs_dir"]); runs_dir.mkdir(parents=True, exist_ok=True)
    preds = {}   # id -> {config: label}
    for conf in cfg["configurations"]:
        name = conf["name"]
        out = open(runs_dir / f"sanity_{name}.jsonl", "w", encoding="utf-8")
        for row in rows:
            top5 = retriever.search(row["system_description"])[0] if conf["retrieval"] else []
            system, user = BUILDERS[name](row, top5)
            raw, usage = call_generator(client, gen_cfg, system, user)
            p = parse_output(raw)
            preds.setdefault(row["id"], {})[name] = p["label"]
            out.write(json.dumps({
                "id": row["id"], "config": name, "gold": row["label"],
                "pred": p["label"], "explanation": p["explanation"],
                "retrieved_areas": [h.get("area") for h in top5],
                "retrieved_ids": [h["id"] for h in top5], "raw": raw,
            }, ensure_ascii=False) + "\n")
        out.close()
        print(f"ran {name}")

    # comparison table
    names = [c["name"] for c in cfg["configurations"]]
    w = max(len(n) for n in names)
    print("\n" + "id".ljust(10), "gold".ljust(14), *[n[:16].ljust(16) for n in names])
    hits = {n: 0 for n in names}
    for row in rows:
        rid = row["id"]; gold = row["label"]
        cells = []
        for n in names:
            pl = preds[rid].get(n)
            if pl == gold: hits[n] += 1
            cells.append((("=" if pl == gold else "x") + " " + str(pl))[:16].ljust(16))
        print(rid.ljust(10), gold.ljust(14), *cells)
    print("\naccuracy on sample:", {n: f"{hits[n]}/{len(rows)}" for n in names})
    print("full outputs + explanations -> results/runs/sanity_*.jsonl")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "config/pipeline.yaml")
