"""
Build the retrieval corpus for Case Study 2 (normative text only).

The Commission guidelines number their content:
  2.x  = general principles (2.1-2.6) and the Article 6(3) 'filter' (2.7)  -> KEEP
  3.x  = the eight Annex III areas (3.1 Biometrics ... 3.8 Justice)        -> KEEP
Everything else (I. Introduction, III. Article 6(1)/Annex I, V/VI procedural)
is neither 2.x nor 3.x, so it is excluded automatically. Article 6(1) is out
of scope per the frozen task anchor.

Within the kept sections we hold out ALL worked-example material, because those
examples (with their stated verdicts) are the test set and ground truth:
  - a)/b)/c) "Practical example" subsections (the bulleted example blocks), and
  - inline verdict enumerations ("Below are some examples ... not high-risk").
Keeping them would let the agent retrieve its own answer (label leakage) and
collapse the wrong/unfaithful buckets the study measures.

Chunking is structural: one chunk per numbered normative paragraph "(N)",
carrying its heading path. Paragraphs longer than MAX_CHARS are split at
sentence boundaries so they fit the encoder's window; the parts keep the same
para_num with a part index.

Usage:
    python build_corpus.py <annexiii_pdf> <out_jsonl>
"""

import re
import json
import sys
import subprocess
from pathlib import Path

MAX_CHARS = 1800   # ~512 tokens for bge-base; longer paragraphs are split

AREA_BY_SECTION = {
    "3.1": "biometrics", "3.2": "critical-infrastructure", "3.3": "education",
    "3.4": "employment", "3.5": "essential-services", "3.6": "law-enforcement",
    "3.7": "migration", "3.8": "justice-democracy",
}

# a numbered heading:  2.7 , 2.7.1 , 3.1 , 3.4.2 .  Title must start capitalised.
SECTION_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+){0,2})\.?\s+([A-Z‘’'].+)")
PARA_RE    = re.compile(r"^\s*\((\d+)\)\s*(.*)")
SUBSEC_RE  = re.compile(r"^\s*[abc]\)\s+Practical example", re.IGNORECASE)
PAGE_NUM_RE = re.compile(r"^\s*\d{1,3}\s*$")
FOOTER_RE   = re.compile(r"^\s*Draft Commission guidelines on the classification", re.IGNORECASE)
FOOTNOTE_START_RE = re.compile(r"^\s{1,3}\d{1,3}\b")

# paragraphs opened by one of these enumerate labelled example systems -> hold out
INLINE_EXAMPLE_RE = re.compile(
    r"(below are (some )?examples"
    r"|^\s*examples of ai systems"
    r"|examples of ai systems that (are not|would not|fall within or outside|do not|serve)"
    r"|by contrast, examples of ai systems"
    r"|the following are examples)",
    re.IGNORECASE,
)


def clean(t):
    return re.sub(r"\s+", " ", t).strip()


def split_long(text):
    if len(text) <= MAX_CHARS:
        return [text]
    sents = re.split(r"(?<=[.;:])\s+", text)
    parts, buf = [], ""
    for s in sents:
        if len(buf) + len(s) + 1 > MAX_CHARS and buf:
            parts.append(buf.strip())
            buf = s
        else:
            buf = (buf + " " + s).strip()
    if buf:
        parts.append(buf.strip())
    return parts


def main():
    if len(sys.argv) != 3:
        print("usage: python build_corpus.py <annexiii_pdf> <out_jsonl>")
        sys.exit(1)
    pdf_path, out = sys.argv[1], sys.argv[2]
    tmp = "/tmp/_corpus_extract.txt"
    subprocess.run(["pdftotext", "-layout", pdf_path, tmp], check=True)
    lines = Path(tmp).read_text(encoding="utf-8").replace("\f", "\n").splitlines()

    chunks = []
    nid = 1
    section = section_title = None
    keep_section = False
    para_num = None
    para_lines = []
    in_example = False
    in_footnote = False
    excluded_ex_blocks = 0
    excluded_inline = 0

    def top(sec):
        return ".".join(sec.split(".")[:2]) if sec else None

    def heading_path():
        if not section:
            return None
        area = AREA_BY_SECTION.get(top(section))
        base = "General principles" if section.startswith("2") else (area or "Annex III")
        return f"{base} | {section} {section_title}".strip()

    def flush():
        nonlocal para_lines, nid, para_num, excluded_inline
        if not keep_section or para_num is None or not para_lines:
            para_lines = []
            return
        text = clean(" ".join(para_lines))
        if len(text) < 25:
            para_lines = []
            return
        if INLINE_EXAMPLE_RE.search(text):          # verdict enumeration -> hold out
            excluded_inline += 1
            para_lines = []
            return
        parts = split_long(text)
        for pi, part in enumerate(parts):
            chunks.append({
                "id": f"chunk-{nid:04d}",
                "source_doc": "annex-iii",
                "section": section,
                "section_title": clean(section_title) if section_title else None,
                "annex_iii_area": AREA_BY_SECTION.get(top(section)),
                "para_num": para_num,
                "part": pi if len(parts) > 1 else None,
                "heading_path": heading_path(),
                "text": part,
                "char_len": len(part),
            })
            nid += 1
        para_lines = []

    for line in lines:
        if PAGE_NUM_RE.match(line) or FOOTER_RE.match(line):
            in_footnote = False
            continue

        # practical-example subsection opener -> hold-out block
        if SUBSEC_RE.search(line):
            flush()
            in_example = True
            excluded_ex_blocks += 1
            para_num = None
            continue

        # numbered heading (not a "(N)" paragraph, not a dotted TOC line)
        sm = SECTION_RE.match(line)
        if sm and not PARA_RE.match(line) and "....." not in line:
            title = sm.group(2).strip()
            first_comp = int(sm.group(1).split(".")[0])
            # skip bare enumeration list items ("2. Critical infrastructure;") and
            # footnote/citation numbers misread as headings ("29 June 2000 ...").
            # Real sections in this document have a top-level component of 1..8;
            # a larger leading number is a footnote year/marker, not a heading.
            if first_comp <= 8 and not (title.endswith(";") or len(title) < 15):
                flush()
                section = sm.group(1)
                section_title = title
                keep_section = section.split(".")[0] in ("2", "3")
                para_num = None
                in_example = False
                continue

        pm = PARA_RE.match(line)
        if pm:
            flush()
            in_example = False
            para_num = pm.group(1)
            rest = pm.group(2).strip()
            para_lines = [rest] if rest else []
            continue

        if in_example or not keep_section:
            continue

        if FOOTNOTE_START_RE.match(line) and (len(line) - len(line.lstrip())) <= 3:
            in_footnote = True
            continue
        stripped = line.rstrip()
        if in_footnote:
            if not stripped:
                continue
            if (len(line) - len(line.lstrip())) <= 3:
                continue
            in_footnote = False

        if para_num is None:
            continue
        if stripped:
            para_lines.append(stripped.strip())

    flush()

    with open(out, "w", encoding="utf-8") as f:
        for c in chunks:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    from collections import Counter
    lens = sorted(c["char_len"] for c in chunks)
    print(f"TOTAL: {len(chunks)} chunks -> {out}")
    print(f"held out: {excluded_ex_blocks} practical-example blocks, "
          f"{excluded_inline} inline verdict-enumeration paragraphs")
    if lens:
        print(f"char_len: min={lens[0]} median={lens[len(lens)//2]} max={lens[-1]} "
              f"mean={sum(lens)//len(lens)}  >{MAX_CHARS}: {sum(l>MAX_CHARS for l in lens)}")
    print("by top section:", dict(sorted(Counter(top(c['section']) for c in chunks).items())))
    print("by area (3.x):", dict(sorted(Counter(c['annex_iii_area'] for c in chunks if c['annex_iii_area']).items())))


if __name__ == "__main__":
    main()
