"""
Build test_set_redacted.jsonl: same 215 rows, same ids and gold labels, but the
system_description no longer contains the Commission's verdict or legal
reasoning (label leakage found after the first full run, 24 Sep 2026).

Step 1  drop every sentence that names a legal instrument or states a legal
        conclusion (keyword filter below).
Step 2  apply hand-written redactions from redaction_overrides.py where the
        verdict sits inside a descriptive sentence or reasoning survives step 1.
The gold label is never shown to the model; it stays only as the answer key.

    python redact_test_set.py            # writes test_set_redacted.jsonl + redaction_diff.csv
"""
import csv
import json
import re

from redaction_overrides import OVERRIDES, TRIM_SENTENCES, VERDICT_STRIPS

LEGAL = re.compile(
    r"high-?\s?risk|annex|article\s*\d|art\.\s*\d|point\s*\d|use case|exception|"
    r"exempt|excluded|out of scope|outside (the )?scope|not covered|is covered|"
    r"\bfalls?\b|qualif|classif(y|ied|ication) as|safety component|safety function|"
    r"profiling|recital|GDPR|AI Act|filter mechanism|materially influenc|"
    r"narrow procedural|preparatory task|should (not )?be considered|cannot be|"
    r"could apply|section \d|\d+\(\d\)|\bsubject to\b", re.I)

SPLIT = re.compile(r"(?<=[.;])\s+(?=[A-Z(])")


def auto_redact(text):
    sents = SPLIT.split(text.strip())
    return " ".join(s for s in sents if not LEGAL.search(s))


def main(src="test_set.jsonl", dst="test_set_redacted.jsonl", diff="redaction_diff.csv"):
    rows = [json.loads(l) for l in open(src, encoding="utf-8")]
    review = json.load(open("redaction_user_review.json", encoding="utf-8"))
    out, log = [], []
    for r in rows:
        orig = r["system_description"]
        rv = review.get(r["id"], {}).get("reviewer_text")
        if rv:
            new, how = rv, "reviewer"
            for old, rep in VERDICT_STRIPS.get(r["id"], []):
                assert old in new, f"{r['id']}: strip target not found"
                new = new.replace(old, rep)
            new = new.strip()
        elif OVERRIDES.get(r["id"]):
            new, how = OVERRIDES[r["id"]], "manual"
        else:
            new = auto_redact(orig)
            for frag in TRIM_SENTENCES.get(r["id"], []):
                new = " ".join(s for s in SPLIT.split(new) if frag not in s)
            how = "auto" if new != orig.strip() else "unchanged"
        assert new.strip(), f"{r['id']} redacted to empty"
        rec = dict(r)
        rec["system_description"] = new
        rec["system_description_original"] = orig
        rec["redaction"] = how
        out.append(rec)
        log.append([r["id"], r["label"], r.get("edge_case_type"), how, orig, new])
    with open(dst, "w", encoding="utf-8") as f:
        for rec in out:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    with open(diff, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "gold_label", "edge_case_type", "redaction", "original", "redacted", "your_check (ok / fix)"])
        w.writerows(log)
    counts = {}
    for x in out:
        counts[x["redaction"]] = counts.get(x["redaction"], 0) + 1
    print(f"wrote {dst} ({len(out)} rows) and {diff}; {counts}")


if __name__ == "__main__":
    main()
