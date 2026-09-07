"""
Extract worked examples from the EU Commission Draft Guidelines on the
classification of high-risk AI systems (Annex III document).
 
v2 robust:
  - Prefers annex_iii_point from the a/b/c subsection heading (more reliable
    than the section header) and falls back to the section header only for c
    sections that don't restate the point.
  - Handles page breaks with intervening footnotes without truncating bullets.
  - Skips page numbers, page footers, and footnote blocks.
  - Resets point tracking on section transitions to avoid stale carry-over.
  - Post-extraction validation adds a 'needs_review' flag on suspicious rows.
 
USAGE:
    python extract_test_set.py <pdf_path> <output_jsonl_path>
"""
 
import re
import json
import sys
import subprocess
from pathlib import Path
 
 
AREA_BY_TOP_SECTION = {
    "3.1": "biometrics",
    "3.2": "critical-infrastructure",
    "3.3": "education",
    "3.4": "employment",
    "3.5": "essential-services",
    "3.6": "law-enforcement",
    "3.7": "migration",
    "3.8": "justice-democracy",
}
 
CRITICAL_INFRA_SUBTOPICS = {
    "3.2.2": "digital",
    "3.2.3": "road-traffic",
    "3.2.4": "water",
    "3.2.5": "gas",
    "3.2.6": "heating",
    "3.2.7": "electricity",
}
 
VALID_AREAS = set(AREA_BY_TOP_SECTION.values())
 
SECTION_RE = re.compile(r"^\s*(3\.\d+(?:\.\d+)?)\.\s+(.+)")
POINT_IN_TEXT_RE = re.compile(r"[Pp]oint\s+(\d+)\s*\(([a-z])\)")
SUBSEC_A_RE = re.compile(r"^\s*a\)\s+Practical example.{0,80}falling within the high-risk use case", re.IGNORECASE)
SUBSEC_B_RE = re.compile(r"^\s*b\)\s+Practical example.{0,80}falling outside", re.IGNORECASE)
SUBSEC_C_RE = re.compile(r"^\s*c\)\s+Practical example.{0,80}exempted", re.IGNORECASE)
PARA_RE = re.compile(r"^\s*\((\d+)\)")
BULLET_RE = re.compile(r"^(\s*)[\-\u2013\u2014]\s+(.*)")
ARTICLE_63_RE = re.compile(r"Article\s+6\(3\)\(([a-d])\)")
 
FOOTNOTE_START_RE = re.compile(r"^\s{1,3}\d{1,3}\b")
PAGE_NUM_RE = re.compile(r"^\s*\d{1,3}\s*$")
 
BAD_ENDINGS = (
    " from", " of", " to", " by", " with", " on", " in", " for", " and",
    " or", " that", " which", " such as", " including", " e.g.,", ",",
)
 
 
def clean_text(text):
    return re.sub(r"\s+", " ", text).strip()
 
 
def top_section(section_num):
    parts = section_num.split(".")
    return ".".join(parts[:2]) if len(parts) >= 2 else section_num
 
 
def is_footnote_or_page_junk(line):
    if PAGE_NUM_RE.match(line):
        return True
    if FOOTNOTE_START_RE.match(line) and len(line) - len(line.lstrip()) <= 3:
        return True
    return False
 
 
def extract(pdf_path, out_path):
    txt_path = "/tmp/annexiii_extracted.txt"
    subprocess.run(["pdftotext", "-layout", pdf_path, txt_path], check=True)
    raw = Path(txt_path).read_text(encoding="utf-8").replace("\f", "\n")
    lines = raw.splitlines()
 
    current_section = None
    current_point_from_section = None
    current_point_from_subsec = None
    current_para = None
    current_subsec = None
    current_bullet_lines = []
    current_bullet_indent = None
    in_footnote_zone = False
    rows = []
    next_id = 1
 
    def active_point():
        return current_point_from_subsec or current_point_from_section
 
    def flush_bullet():
        nonlocal current_bullet_lines, next_id
        if not current_bullet_lines or current_subsec is None:
            current_bullet_lines = []
            return
        pt = active_point()
        if pt is None and current_section and top_section(current_section) == "3.2":
            pt = "2"
        if pt is None:
            current_bullet_lines = []
            return
 
        description = clean_text(" ".join(current_bullet_lines))
        if len(description) < 30:
            current_bullet_lines = []
            return
 
        area = AREA_BY_TOP_SECTION.get(top_section(current_section or ""), "unknown")
 
        if current_subsec == "a":
            label, edge = "high-risk", "none"
        elif current_subsec == "b":
            label, edge = "not-high-risk", "none"
        else:
            label, edge = "not-high-risk", "article-6-3-filter"
 
        notes_parts = []
        m = ARTICLE_63_RE.search(description)
        if m:
            notes_parts.append(f"Filter condition: Article 6(3)({m.group(1)})")
        if current_section in CRITICAL_INFRA_SUBTOPICS:
            notes_parts.append(f"Sub-topic: {CRITICAL_INFRA_SUBTOPICS[current_section]}")
        notes = "; ".join(notes_parts)
 
        label_source = (
            f"Annex III guidelines, section {current_section}, "
            f"{current_subsec}) subsection, para ~{current_para}"
            if current_para
            else f"Annex III guidelines, section {current_section}, {current_subsec}) subsection"
        )
 
        needs_review_reasons = []
        if area not in VALID_AREAS:
            needs_review_reasons.append("unknown_area")
        if not re.match(r"^\d+(\([a-z]\))?$", pt):
            needs_review_reasons.append("malformed_point")
        if any(description.rstrip().endswith(end) for end in BAD_ENDINGS):
            needs_review_reasons.append("possibly_truncated")
        if len(description) > 1200:
            needs_review_reasons.append("very_long")
        if current_subsec == "c" and "6(3)" not in description:
            needs_review_reasons.append("filter_row_missing_6_3_ref")
 
        row = {
            "id": f"anx3-{next_id:03d}",
            "source": "annex-iii",
            "annex_iii_area": area,
            "annex_iii_point": pt,
            "system_description": description,
            "label": label,
            "label_source": label_source,
            "edge_case_type": edge,
            "notes": notes,
            "needs_review": needs_review_reasons or None,
        }
        rows.append(row)
        next_id += 1
        current_bullet_lines = []
 
    for line in lines:
        m = SECTION_RE.match(line)
        if m:
            flush_bullet()
            current_section = m.group(1)
            title = m.group(2)
            pt = POINT_IN_TEXT_RE.search(title)
            current_point_from_section = f"{pt.group(1)}({pt.group(2)})" if pt else None
            current_point_from_subsec = None
            current_subsec = None
            in_footnote_zone = False
            continue
 
        pm = PARA_RE.match(line)
        if pm:
            flush_bullet()
            current_para = pm.group(1)
            current_subsec = None
            current_point_from_subsec = None
            in_footnote_zone = False
            continue
 
        subsec_hit = None
        for letter, pattern in [("a", SUBSEC_A_RE), ("b", SUBSEC_B_RE), ("c", SUBSEC_C_RE)]:
            if pattern.search(line):
                subsec_hit = letter
                break
        if subsec_hit:
            flush_bullet()
            current_subsec = subsec_hit
            pt = POINT_IN_TEXT_RE.search(line)
            if pt:
                current_point_from_subsec = f"{pt.group(1)}({pt.group(2)})"
            elif subsec_hit in ("a", "b"):
                current_point_from_subsec = None
            in_footnote_zone = False
            continue
 
        if is_footnote_or_page_junk(line):
            in_footnote_zone = True
            continue
 
        stripped = line.rstrip()
        if in_footnote_zone:
            leading = len(line) - len(line.lstrip())
            if not stripped:
                continue
            if leading <= 3:
                continue
            in_footnote_zone = False
 
        if current_subsec is None:
            continue
 
        bm = BULLET_RE.match(line)
        if bm:
            flush_bullet()
            current_bullet_indent = len(bm.group(1))
            current_bullet_lines = [bm.group(2).strip()]
            continue
 
        if current_bullet_lines and stripped:
            leading = len(line) - len(line.lstrip())
            # Any positive indent counts as continuation. Page breaks can
            # reset the layout indent, so we don't require indent to exceed
            # the original bullet marker column.
            if leading > 0:
                current_bullet_lines.append(stripped.strip())
                continue
 
        if not stripped:
            continue
 
        flush_bullet()
 
    flush_bullet()
 
    for r in rows:
        if r["needs_review"] is None:
            del r["needs_review"]
 
    with open(out_path, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
 
    return rows
 
 
def summarise(rows):
    by_area, by_point = {}, {}
    by_label = {"high-risk": 0, "not-high-risk": 0}
    by_edge = {"none": 0, "article-6-3-filter": 0}
    flagged = 0
    flag_reasons = {}
    for r in rows:
        by_area[r["annex_iii_area"]] = by_area.get(r["annex_iii_area"], 0) + 1
        by_point[r["annex_iii_point"]] = by_point.get(r["annex_iii_point"], 0) + 1
        by_label[r["label"]] += 1
        by_edge[r["edge_case_type"]] += 1
        if "needs_review" in r:
            flagged += 1
            for reason in r["needs_review"]:
                flag_reasons[reason] = flag_reasons.get(reason, 0) + 1
 
    print(f"Extracted {len(rows)} rows")
    print("\nBy area:")
    for k in sorted(by_area):
        print(f"  {k}: {by_area[k]}")
    print("\nBy point:")
    for k in sorted(by_point):
        print(f"  {k}: {by_point[k]}")
    print(f"\nBy label: {by_label}")
    print(f"By edge_case_type: {by_edge}")
    print(f"\nFlagged for review: {flagged}")
    for k in sorted(flag_reasons):
        print(f"  {k}: {flag_reasons[k]}")
 
 
if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python extract_test_set.py <pdf_path> <output_jsonl>")
        sys.exit(1)
    rows = extract(sys.argv[1], sys.argv[2])
    summarise(rows)
 
