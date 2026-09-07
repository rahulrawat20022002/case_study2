"""
Retrieval-quality evaluation for Case Study 2 (API-free, no generator, no judge).

Scores the frozen hybrid retriever against a section-level gold standard derived
from each test input's `label_source` provenance. This is the Phase 3 retrieval
metric, and it depends on nothing but the retriever and the test set.

Gold standard
-------------
Each test row names its governing section in `label_source` (e.g. "section
3.1.2"). The gold passages for that row are every corpus chunk whose `section`
is that governing section (exact match; if the corpus has no exact section, the
nearest parent/child section is used). Gold is the RULE the model should read,
never the held-out answer, so scoring "did the retriever fetch it" is fair.

Metrics (per row, then aggregated) at k in {5, 10}
--------------------------------------------------
  Hit@k    : 1 if at least one gold chunk is in the top-k, else 0   [PRIMARY = Hit@5]
  Recall@k : |gold retrieved in top-k| / |gold|
  MRR      : 1 / rank of the first gold chunk in the full ranking (0 if none found)

Run
---
    python src/retrieval_eval.py [config/pipeline.yaml]
    # CS2_FAKE_EMBED=1 runs the hashing stand-in for a plumbing test only.

Outputs
-------
    results/retrieval_eval.json  (config echo, per-row records, aggregates)
    results/retrieval_eval.md    (human-readable summary tables)
"""
import os
import re
import sys
import json
import yaml
from collections import defaultdict, Counter
from statistics import mean

from retriever import HybridRetriever

RANK_DEPTH = 50  # how deep a ranking to pull per query (for a fair MRR)
KS = [5, 10]
SEC_RE = re.compile(r"section\s+([0-9]+(?:\.[0-9]+)+)", re.I)


def governing_section(label_source):
    m = SEC_RE.search(label_source or "")
    return m.group(1) if m else None


def build_gold_index(chunks):
    """section string -> list of chunk ids in that section."""
    by_sec = defaultdict(list)
    for c in chunks:
        by_sec[str(c["section"])].append(c["id"])
    return by_sec


def gold_ids_for(sec, by_sec):
    """Chunk ids that count as gold for a governing section.

    Exact section match first. If the corpus has no exact section, fall back to
    the nearest related sections: a child (sec is a prefix of the chunk section)
    or a parent (chunk section is a prefix of sec). Returns (ids, match_kind).
    """
    if sec is None:
        return [], "no-section"
    if sec in by_sec:
        return list(by_sec[sec]), "exact"
    related = []
    for s, ids in by_sec.items():
        if s == sec or s.startswith(sec + ".") or sec.startswith(s + "."):
            related.extend(ids)
    return related, ("related" if related else "missing")


def main(cfg_path="config/pipeline.yaml"):
    cfg = yaml.safe_load(open(cfg_path))
    rows = [json.loads(l) for l in open(cfg["paths"]["test_set"], encoding="utf-8")]
    chunks = [json.loads(l) for l in
              open(cfg["corpus"]["chunks_file"], encoding="utf-8")]
    by_sec = build_gold_index(chunks)

    r = HybridRetriever(cfg_path)

    per_row = []
    for row in rows:
        sec = governing_section(row["label_source"])
        gold, match_kind = gold_ids_for(sec, by_sec)
        gold_set = set(gold)

        # deep ranking for this query
        _, ranking = r.search(row["system_description"], top_k=5, log_k=RANK_DEPTH)
        ranked_ids = [h["id"] for h in ranking]

        # first gold rank (1-indexed) for MRR
        first_gold_rank = next((i + 1 for i, cid in enumerate(ranked_ids)
                                if cid in gold_set), None)
        rec = {
            "id": row["id"],
            "area": row["annex_iii_area"],
            "edge_case_type": row["edge_case_type"],
            "gold_section": sec,
            "gold_match_kind": match_kind,
            "n_gold": len(gold_set),
            "first_gold_rank": first_gold_rank,
            "mrr": (1.0 / first_gold_rank) if first_gold_rank else 0.0,
            "top10_ids": ranked_ids[:10],
        }
        for k in KS:
            topk = set(ranked_ids[:k])
            hit = len(topk & gold_set) > 0
            recall = (len(topk & gold_set) / len(gold_set)) if gold_set else 0.0
            rec[f"hit@{k}"] = int(hit)
            rec[f"recall@{k}"] = recall
        per_row.append(rec)

    # ---- aggregates ----
    def agg(records):
        if not records:
            return {}
        out = {"n": len(records), "mrr": mean(x["mrr"] for x in records)}
        for k in KS:
            out[f"hit@{k}"] = mean(x[f"hit@{k}"] for x in records)
            out[f"recall@{k}"] = mean(x[f"recall@{k}"] for x in records)
        return out

    overall = agg(per_row)
    by_area = {a: agg([x for x in per_row if x["area"] == a])
               for a in sorted({x["area"] for x in per_row})}
    by_edge = {e: agg([x for x in per_row if x["edge_case_type"] == e])
               for e in sorted({x["edge_case_type"] for x in per_row})}

    fake = os.environ.get("CS2_FAKE_EMBED") == "1"
    result = {
        "warning": ("FAKE EMBEDDINGS (CS2_FAKE_EMBED=1) - plumbing only, NOT valid results"
                    if fake else None),
        "config": {
            "embedding_model": cfg["embedding"]["model"],
            "hybrid_alpha": cfg["retrieval"]["hybrid_alpha"],
            "vector_store": cfg["vector_store"]["backend"],
            "rank_depth": RANK_DEPTH,
            "gold": "section-level from label_source",
            "primary_metric": "hit@5",
            "n_rows": len(rows),
            "n_chunks": len(chunks),
        },
        "gold_match_kinds": dict(Counter(x["gold_match_kind"] for x in per_row)),
        "overall": overall,
        "by_area": by_area,
        "by_edge_case": by_edge,
        "per_row": per_row,
    }

    os.makedirs("results", exist_ok=True)
    with open("results/retrieval_eval.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    _write_md(result)

    # console summary
    tag = "  [FAKE EMBEDDINGS - plumbing only]" if fake else ""
    print(f"\nRetrieval quality over {overall['n']} rows{tag}")
    print(f"  Hit@5   {overall['hit@5']:.3f}   (PRIMARY)")
    print(f"  Hit@10  {overall['hit@10']:.3f}")
    print(f"  Recall@5  {overall['recall@5']:.3f}   Recall@10 {overall['recall@10']:.3f}")
    print(f"  MRR     {overall['mrr']:.3f}")
    print("  wrote results/retrieval_eval.json and results/retrieval_eval.md")


def _write_md(result):
    o = result["overall"]
    L = []
    if result["warning"]:
        L.append(f"> **{result['warning']}**\n")
    L.append("# Retrieval quality evaluation\n")
    c = result["config"]
    L.append(f"Retriever: hybrid BM25 + `{c['embedding_model']}` dense, "
             f"alpha={c['hybrid_alpha']}, over {c['n_chunks']} chunks. "
             f"Gold = {c['gold']}. Primary metric: **Hit@5**. "
             f"{c['n_rows']} test inputs.\n")
    L.append(f"Gold match kinds: {result['gold_match_kinds']}\n")
    L.append("## Overall\n")
    L.append("| Metric | Value |\n|---|---|")
    L.append(f"| **Hit@5 (primary)** | **{o['hit@5']:.3f}** |")
    L.append(f"| Hit@10 | {o['hit@10']:.3f} |")
    L.append(f"| Recall@5 | {o['recall@5']:.3f} |")
    L.append(f"| Recall@10 | {o['recall@10']:.3f} |")
    L.append(f"| MRR | {o['mrr']:.3f} |\n")

    def table(title, d):
        L.append(f"## {title}\n")
        L.append("| Group | n | Hit@5 | Hit@10 | Recall@5 | Recall@10 | MRR |")
        L.append("|---|---|---|---|---|---|---|")
        for g, a in d.items():
            if not a:
                continue
            L.append(f"| {g} | {a['n']} | {a['hit@5']:.3f} | {a['hit@10']:.3f} "
                     f"| {a['recall@5']:.3f} | {a['recall@10']:.3f} | {a['mrr']:.3f} |")
        L.append("")

    table("By Annex III area", result["by_area"])
    table("By edge-case type (filter rows are the Article 6(3) cases)",
          result["by_edge_case"])
    with open("results/retrieval_eval.md", "w", encoding="utf-8") as f:
        f.write("\n".join(L))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "config/pipeline.yaml")
