"""
Sanity checks for the scaffold JSONL before review.

Usage:
    python sanity_check.py path/to/scaffold.jsonl

Flags suspect rows across a handful of cheap checks. Prints a grouped
report. Nothing here modifies the file. IDs listed are the ones to
actually look at.
"""

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path


TERMINAL_PUNCT = {".", "?", "!", '"', "'", ")", "]"}
REQUIRED_FIELDS = [
    "id", "source", "annex_iii_area", "annex_iii_point",
    "system_description", "label", "label_source",
    "edge_case_type", "notes",
]


def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"  LINE {i} FAILED TO PARSE: {e}")
    return rows


def check_missing_fields(rows):
    """Fields that are missing, null, or empty string."""
    hits = []
    for r in rows:
        missing = [f for f in REQUIRED_FIELDS
                   if f not in r or r[f] in (None, "")]
        # notes and edge_case_type are allowed empty
        missing = [f for f in missing if f not in ("notes", "edge_case_type")]
        if missing:
            hits.append((r.get("id", "?"), missing))
    return hits


def check_exact_duplicates(rows):
    """Same system_description appearing more than once."""
    seen = defaultdict(list)
    for r in rows:
        desc = (r.get("system_description") or "").strip()
        if desc:
            seen[desc].append(r.get("id", "?"))
    return [(desc[:80] + "...", ids) for desc, ids in seen.items() if len(ids) > 1]


def check_near_duplicates(rows, threshold=0.85):
    """Cheap near-duplicate detection using shingled Jaccard on token sets.
    Not perfect but catches obvious copies with tiny edits."""
    def tokens(s):
        return set(s.lower().split())

    hits = []
    items = [(r.get("id", "?"), tokens(r.get("system_description") or ""))
             for r in rows]
    for i in range(len(items)):
        id_i, tok_i = items[i]
        if not tok_i:
            continue
        for j in range(i + 1, len(items)):
            id_j, tok_j = items[j]
            if not tok_j:
                continue
            inter = len(tok_i & tok_j)
            union = len(tok_i | tok_j)
            if union and inter / union >= threshold:
                hits.append((id_i, id_j, round(inter / union, 2)))
    return hits


def check_length_outliers(rows):
    """Descriptions unusually short or long relative to the corpus."""
    lengths = [(r.get("id", "?"), len(r.get("system_description") or ""))
               for r in rows]
    just_lengths = [l for _, l in lengths if l > 0]
    if not just_lengths:
        return [], []
    just_lengths.sort()
    n = len(just_lengths)
    p5 = just_lengths[max(0, int(n * 0.05) - 1)]
    p95 = just_lengths[min(n - 1, int(n * 0.95))]
    short = [(i, l) for i, l in lengths if 0 < l < min(p5, 60)]
    long_ = [(i, l) for i, l in lengths if l > max(p95, 800)]
    return short, long_


def check_truncated(rows):
    """Descriptions that do not end with terminal punctuation.
    Common symptom of the page-break truncation bug."""
    hits = []
    for r in rows:
        desc = (r.get("system_description") or "").rstrip()
        if desc and desc[-1] not in TERMINAL_PUNCT:
            hits.append((r.get("id", "?"), desc[-60:]))
    return hits


def check_label_vs_point(rows):
    """Rows whose label disagrees with the majority label of their
    Annex III point. Could be a legit edge case (which is why edge_case_type
    exists), but worth eyeballing when edge_case_type is empty."""
    by_point = defaultdict(list)
    for r in rows:
        point = r.get("annex_iii_point")
        if point:
            by_point[point].append(r)

    hits = []
    for point, group in by_point.items():
        if len(group) < 3:
            continue
        counts = Counter(r.get("label") for r in group)
        modal_label, _ = counts.most_common(1)[0]
        for r in group:
            if r.get("label") != modal_label and not r.get("edge_case_type"):
                hits.append((r.get("id", "?"), point,
                             r.get("label"), modal_label))
    return hits


def check_filter_case_labels(rows):
    """Filter cases (edge_case_type set) should generally be labelled
    not-high-risk under Article 6(3). Flag any that are labelled high-risk
    without an explicit note explaining why."""
    hits = []
    for r in rows:
        if r.get("edge_case_type") and str(r.get("label", "")).lower() in (
            "high-risk", "high_risk", "highrisk", "true", "1"
        ):
            if not (r.get("notes") or "").strip():
                hits.append((r.get("id", "?"), r.get("edge_case_type"),
                             r.get("label")))
    return hits


def check_label_values(rows):
    """Label vocabulary should be a small closed set. Report anything
    outside the two expected values."""
    allowed = {"high-risk", "not-high-risk"}
    hits = []
    for r in rows:
        lab = str(r.get("label", "")).strip().lower()
        if lab and lab not in allowed:
            hits.append((r.get("id", "?"), r.get("label")))
    return hits


def summarise(rows):
    print(f"\nTotal rows: {len(rows)}")
    areas = Counter(r.get("annex_iii_area") for r in rows)
    print("By Annex III area:")
    for area, n in sorted(areas.items(), key=lambda x: str(x[0])):
        print(f"  {area}: {n}")
    labels = Counter(str(r.get("label", "")).lower() for r in rows)
    print("Label distribution:")
    for lab, n in labels.most_common():
        print(f"  {lab}: {n}")
    edge = sum(1 for r in rows if r.get("edge_case_type"))
    print(f"Edge (filter) cases: {edge}")


def main():
    if len(sys.argv) != 2:
        print("Usage: python sanity_check.py path/to/scaffold.jsonl")
        sys.exit(1)

    path = Path(sys.argv[1])
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    rows = load(path)
    summarise(rows)

    print("\n=== CHECK 1: label outside allowed vocab ===")
    for hit in check_label_values(rows):
        print(f"  {hit[0]}  label={hit[1]!r}")

    print("\n=== CHECK 2: missing required fields ===")
    for row_id, missing in check_missing_fields(rows):
        print(f"  {row_id}  missing={missing}")

    print("\n=== CHECK 3: exact duplicate descriptions ===")
    for desc_preview, ids in check_exact_duplicates(rows):
        print(f"  ids={ids}  desc='{desc_preview}'")

    print("\n=== CHECK 4: near-duplicate descriptions (Jaccard >= 0.85) ===")
    for id_i, id_j, score in check_near_duplicates(rows):
        print(f"  {id_i} vs {id_j}  jaccard={score}")

    print("\n=== CHECK 5: description length outliers ===")
    short, long_ = check_length_outliers(rows)
    print(f"  Suspiciously short ({len(short)}):")
    for row_id, l in short:
        print(f"    {row_id}  len={l}")
    print(f"  Suspiciously long ({len(long_)}):")
    for row_id, l in long_:
        print(f"    {row_id}  len={l}")

    print("\n=== CHECK 6: truncated (no terminal punctuation) ===")
    trunc = check_truncated(rows)
    print(f"  {len(trunc)} rows")
    for row_id, tail in trunc:
        print(f"    {row_id}  ...{tail!r}")

    print("\n=== CHECK 7: label disagrees with modal label of its Annex III point ===")
    for row_id, point, label, modal in check_label_vs_point(rows):
        print(f"  {row_id}  point={point}  label={label!r}  modal={modal!r}")

    print("\n=== CHECK 8: filter case labelled high-risk without explanatory note ===")
    for row_id, etype, lab in check_filter_case_labels(rows):
        print(f"  {row_id}  edge_case_type={etype}  label={lab}")

    print("\nDone.")


if __name__ == "__main__":
    main()
