"""
Cleanup pass on the 219-row scaffold.

Fixes 21 rows where the next example's heading got concatenated onto the
description. Drops 4 rows that are damaged beyond a clean automatic fix.

Writes cleaned file to test_set_clean.jsonl and prints a diff summary.
"""

import json
import sys
from pathlib import Path


# For each row id, the substring where the glued-on junk starts. Everything
# from that substring onwards (inclusive) is stripped. Chosen so that the
# preserved text ends on a complete sentence with terminal punctuation.
CUT_MARKERS = {
    "anx3-019": " 3.1.2.2.",
    "anx3-114": " Prioritisation",
    "anx3-120": " Proactive invitation with an eligibility check",
    "anx3-128": " Credit scores used by third parties other than the deployer",
    "anx3-131": " Support before or after a credit decision",
    "anx3-133": " Monitoring of credit exposure",
    "anx3-134": " Evaluation of a collateral",
    "anx3-135": " Providing credit or extended margin for leveraged trading products",
    "anx3-139": " Product design for life insurance",
    "anx3-154": " Supportive tools for human review",
    "anx3-183": " Vehicle-focused screening without mapping to a person",
    "anx3-185": " Post-decision data cleaning",
    "anx3-198": " Analytics that do not detect, recognise or identify persons",
    "anx3-202": " AI systems facilitating communication with the public",
    "anx3-204": " Case assignment systems",
    "anx3-208": " personnel for searching for decisions using classical methods",
    "anx3-209": " AI systems suggesting factual questions",
    "anx3-210": " Second use case:",
    "anx3-216": " Technical assistance in vote counting",
    "anx3-217": " Chatbots to provide information on the elections",
    "anx3-219": " Please note that not all chatbots are AI systems.",
}

# Rows to drop: description is a merge of two examples where the second
# example starts mid-sentence, or the description itself is truncated.
DROP_IDS = {"anx3-069", "anx3-149", "anx3-205", "anx3-213"}


def main():
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("test_set_auto.jsonl")
    dst = Path("test_set_clean.jsonl")

    rows = [json.loads(l) for l in open(src, encoding="utf-8")]
    print(f"Loaded: {len(rows)} rows")

    fixed = 0
    dropped = 0
    unfixed = []
    out = []

    for r in rows:
        rid = r["id"]

        if rid in DROP_IDS:
            dropped += 1
            continue

        if rid in CUT_MARKERS:
            marker = CUT_MARKERS[rid]
            desc = r["system_description"]
            idx = desc.find(marker)
            if idx == -1:
                unfixed.append((rid, "marker not found"))
                out.append(r)
                continue
            new_desc = desc[:idx].rstrip()
            # sanity: must now end on terminal punct
            if new_desc[-1] not in {".", "?", "!", ")"}:
                unfixed.append((rid, f"cut leaves bad ending: ...{new_desc[-40:]!r}"))
                out.append(r)
                continue
            r = dict(r)
            r["system_description"] = new_desc
            fixed += 1

        out.append(r)

    with open(dst, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Fixed:   {fixed} rows (glued heading stripped)")
    print(f"Dropped: {dropped} rows (damaged beyond auto-fix)")
    print(f"Written: {len(out)} rows to {dst}")

    if unfixed:
        print("\nRows that need manual attention:")
        for rid, why in unfixed:
            print(f"  {rid}: {why}")


if __name__ == "__main__":
    main()
