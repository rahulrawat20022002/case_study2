"""
make_report.py  —  turn the scoring outputs into one presentation-ready HTML page.

Run it after run_scoring.py, from the repo root:

    python src/make_report.py                     # writes results/report.html
    python src/make_report.py --open              # also try to open it

It reads results/scoring/*.json, the off-diagonal case files, test_set.jsonl and
results/runs/*.jsonl, and produces a single self-contained results/report.html:
the four-bucket matrix drawn as a grid, a correctness + faithfulness summary
table, and real "divergence" case cards (label vs grounding) pulled straight from
the off-diagonal rows. No external libraries, no internet, stdlib only.
"""
import os, sys, json, glob, html, argparse, datetime

CONFIG_ORDER = ["baseline1_plain_llm", "baseline2_standard_rag", "agent_structured"]
NICE = {
    "baseline1_plain_llm": "Baseline 1 · plain LLM (no retrieval)",
    "baseline2_standard_rag": "Baseline 2 · standard RAG",
    "agent_structured": "Proposed agent · structured RAG",
}


def load_json(p):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def load_jsonl(p):
    return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()] if os.path.exists(p) else []


def esc(s):
    return html.escape(str(s if s is not None else ""))


def pct(x):
    return "—" if x is None else f"{100*x:.0f}%"


def f3(x):
    return "—" if x is None else f"{x:.3f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scoring-dir", default="results/scoring")
    ap.add_argument("--runs-dir", default="results/runs")
    ap.add_argument("--test-set", default="test_set.jsonl")
    ap.add_argument("--out", default="results/report.html")
    ap.add_argument("--generator", default=None, help="generator model name for the header")
    ap.add_argument("--max-cases", type=int, default=6)
    ap.add_argument("--open", action="store_true")
    args = ap.parse_args()

    corr = load_json(os.path.join(args.scoring_dir, "correctness_summary.json")) or {}
    faith_all = load_json(os.path.join(args.scoring_dir, "faithfulness_summary.json")) or {}
    faith = faith_all.get("by_config", {})
    judge_name = faith_all.get("judge", "—")
    buck = load_json(os.path.join(args.scoring_dir, "buckets_summary.json")) or {}

    desc = {r["id"]: r.get("system_description", "") for r in load_jsonl(args.test_set)}
    # explanation per (config,id)
    expl = {}
    for p in glob.glob(os.path.join(args.runs_dir, "*.jsonl")):
        cfg = os.path.splitext(os.path.basename(p))[0]
        for r in load_jsonl(p):
            expl[(cfg, r["id"])] = r.get("explanation", "")

    present = [c for c in CONFIG_ORDER if c in corr] + \
              [c for c in corr if c not in CONFIG_ORDER]

    # ---- gather divergence cases (wrong+faithful first, then right+unfaithful)
    cases = []
    for cfg in present:
        off = load_jsonl(os.path.join(args.scoring_dir, "buckets", f"{cfg}_offdiagonal.jsonl"))
        for r in off:
            r["_cfg"] = cfg
        cases += off
    order = {"wrong_faithful": 0, "right_unfaithful": 1}
    cases.sort(key=lambda r: (order.get(r.get("bucket"), 9), -(r.get("faithfulness") or 0)))
    cases = cases[:args.max_cases]

    gen = args.generator or "(dev generator)"
    css = """
    :root{--ink:#1b1f24;--muted:#5c6570;--line:#e2e5ea;--paper:#ffffff;--soft:#f5f6f8;
          --rf:#2f8f5b;--ru:#b7791f;--wf:#c0392b;--wu:#7f8c8d;--accent:#2b5c8a;}
    *{box-sizing:border-box} body{margin:0;background:#eceef1;color:var(--ink);
      font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;line-height:1.5;}
    .page{max-width:900px;margin:0 auto;background:var(--paper);padding:34px 40px 56px;}
    h1{font-size:24px;margin:0 0 4px} h2{font-size:16px;margin:30px 0 10px;
       border-bottom:2px solid var(--line);padding-bottom:5px}
    .sub{color:var(--muted);margin:0 0 14px;font-size:14px}
    .banner{background:#fff7e6;border:1px solid #f0d79a;border-left:4px solid #d9a520;
      border-radius:8px;padding:10px 14px;font-size:13px;color:#7a5b12;margin:14px 0 8px}
    .meta{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:var(--muted);
      background:var(--soft);border-radius:8px;padding:9px 13px;margin:10px 0 4px}
    table{border-collapse:collapse;width:100%;font-size:13.5px;margin:8px 0}
    th,td{border:1px solid var(--line);padding:7px 10px;text-align:center}
    th{background:var(--soft);font-weight:600} td.l,th.l{text-align:left}
    .num{font-variant-numeric:tabular-nums}
    .matrix{display:grid;grid-template-columns:120px 1fr 1fr;gap:8px;margin:12px 0}
    .mcell{border-radius:10px;padding:16px;color:#fff;min-height:92px;display:flex;
      flex-direction:column;justify-content:space-between}
    .mhead{background:var(--soft);color:var(--muted);font-size:12px;font-weight:600;
      display:flex;align-items:center;justify-content:center;text-align:center;border-radius:8px}
    .mcell .big{font-size:30px;font-weight:700;line-height:1}
    .mcell .lab{font-size:12px;opacity:.9}
    .rf{background:var(--rf)} .ru{background:var(--ru)} .wf{background:var(--wf)} .wu{background:var(--wu)}
    .flag{display:inline-block;font-size:10.5px;font-weight:700;letter-spacing:.04em;
      background:rgba(255,255,255,.22);padding:2px 6px;border-radius:20px;margin-top:4px}
    .card{border:1px solid var(--line);border-radius:12px;padding:15px 17px;margin:12px 0;background:var(--paper)}
    .card .tag{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;
      padding:3px 9px;border-radius:20px;color:#fff}
    .tag.wf{background:var(--wf)} .tag.ru{background:var(--ru)}
    .card h3{font-size:14px;margin:8px 0 4px}
    .kv{font-size:12.5px;color:var(--muted);margin:2px 0}
    .kv b{color:var(--ink)}
    .quote{background:var(--soft);border-radius:8px;padding:10px 12px;font-size:13px;margin:8px 0}
    .stmt{font-size:12.5px;margin:4px 0;padding-left:20px;position:relative}
    .stmt.bad::before{content:"✗";position:absolute;left:0;color:var(--wf);font-weight:700}
    .stmt.ok::before{content:"✓";position:absolute;left:0;color:var(--rf);font-weight:700}
    .foot{margin-top:26px;padding-top:14px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}
    @media print{body{background:#fff}.page{max-width:none;padding:0}}
    """

    H = []
    H.append(f"""<!doctype html><html><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>Case Study 2 — evaluation report</title><style>{css}</style></head><body><div class="page">""")
    H.append('<h1>EU AI Act compliance agent — evaluation report</h1>')
    H.append('<p class="sub">Does an automated faithfulness metric catch legal-classification errors? Correctness and faithfulness measured as two independent axes.</p>')
    H.append(f'<div class="meta">Generator: {esc(gen)} &nbsp;|&nbsp; Judge (RAGAS faithfulness): {esc(judge_name)} &nbsp;|&nbsp; Retriever: BAAI/bge-base-en-v1.5 &nbsp;|&nbsp; {datetime.date.today().isoformat()}</div>')
    H.append('<div class="banner"><b>Demonstration run.</b> These figures are from a development generator on a subset, for method validation. They are not the graded results; the graded run uses the frozen generator over all 215 cases.</div>')

    # ---- summary table
    H.append('<h2>Summary across the three configurations</h2>')
    H.append('<table><tr><th class="l">Configuration</th><th>n</th><th>Accuracy</th>'
             '<th>High-risk F1</th><th>Mean faithfulness</th>'
             '<th>Right + unfaithful</th><th>Faithful but wrong</th></tr>')
    for cfg in present:
        s = corr.get(cfg, {})
        fs = faith.get(cfg, {})
        bk = (buck.get(cfg) or {}).get("matrix", {})
        hr = (s.get("class_metrics") or {}).get("high-risk", {})
        mf = None if "skipped" in fs else fs.get("mean_faithfulness")
        ru = bk.get("right_unfaithful", "—") if bk else "—"
        wf = bk.get("wrong_faithful", "—") if bk else "—"
        H.append(f'<tr><td class="l">{esc(NICE.get(cfg,cfg))}</td>'
                 f'<td class="num">{s.get("n","—")}</td>'
                 f'<td class="num">{pct(s.get("accuracy"))}</td>'
                 f'<td class="num">{f3(hr.get("f1"))}</td>'
                 f'<td class="num">{f3(mf) if mf is not None else "n/a"}</td>'
                 f'<td class="num">{ru}</td><td class="num">{wf}</td></tr>')
    H.append('</table>')

    # ---- headline matrix for the proposed agent (or best available RAG config)
    head_cfg = next((c for c in ["agent_structured", "baseline2_standard_rag"] if c in buck), None)
    if head_cfg:
        m = buck[head_cfg]["matrix"]
        H.append(f'<h2>Four-bucket outcome — {esc(NICE.get(head_cfg, head_cfg))}</h2>')
        H.append('<p class="sub">Correctness (rows) against faithfulness (columns). The two off-diagonal cells are the findings.</p>')
        H.append('<div class="matrix">'
                 '<div></div><div class="mhead">Faithful (grounded)</div><div class="mhead">Unfaithful</div>'
                 '<div class="mhead">Label right</div>'
                 f'<div class="mcell rf"><div class="big">{m["right_faithful"]}</div><div class="lab">right + faithful</div></div>'
                 f'<div class="mcell ru"><div class="big">{m["right_unfaithful"]}</div><div class="lab">right + unfaithful<span class="flag">FINDING</span></div></div>'
                 '<div class="mhead">Label wrong</div>'
                 f'<div class="mcell wf"><div class="big">{m["wrong_faithful"]}</div><div class="lab">wrong + faithful<span class="flag">HEADLINE</span></div></div>'
                 f'<div class="mcell wu"><div class="big">{m["wrong_unfaithful"]}</div><div class="lab">wrong + unfaithful</div></div>'
                 '</div>')
        cont = buck[head_cfg].get("continuous", {})
        H.append(f'<p class="kv">Mean faithfulness when the label is right: <b>{f3(cont.get("mean_faithfulness_when_right"))}</b>'
                 f' &nbsp;·&nbsp; when wrong: <b>{f3(cont.get("mean_faithfulness_when_wrong"))}</b>'
                 f' &nbsp;·&nbsp; correctness–faithfulness correlation: <b>{f3(cont.get("point_biserial_correct_vs_faithfulness"))}</b></p>')

    # ---- divergence case cards
    H.append('<h2>Divergence cases — where the label and the grounding disagree</h2>')
    if not cases:
        H.append('<p class="sub">No off-diagonal cases in this run yet. With a larger or harder batch, cases appear here.</p>')
    for r in cases:
        cfg, rid, b = r["_cfg"], r.get("id"), r.get("bucket")
        tagcls = "wf" if b == "wrong_faithful" else "ru"
        tagtxt = "faithful but WRONG" if b == "wrong_faithful" else "right but UNFAITHFUL"
        d = esc(desc.get(rid, ""))[:520]
        e = esc(expl.get((cfg, rid), ""))[:600]
        stmts = r.get("statements", [])
        H.append('<div class="card">')
        H.append(f'<span class="tag {tagcls}">{tagtxt}</span>')
        H.append(f'<div class="kv" style="margin-top:8px"><b>{esc(rid)}</b> · {esc(NICE.get(cfg,cfg))} · faithfulness <b>{f3(r.get("faithfulness"))}</b> · predicted <b>{esc(r.get("pred"))}</b> vs gold <b>{esc(r.get("gold"))}</b></div>')
        if d:
            H.append(f'<h3>System description</h3><div class="quote">{d}</div>')
        if e:
            H.append(f'<h3>Model\'s explanation</h3><div class="quote">{e}</div>')
        if stmts:
            H.append('<h3>Judge\'s per-statement grounding check</h3>')
            for st in stmts[:6]:
                cls = "ok" if st.get("verdict") else "bad"
                reason = f' <span style="color:#8a8f96">— {esc(st.get("reason",""))[:90]}</span>' if st.get("reason") else ""
                H.append(f'<div class="stmt {cls}">{esc(st.get("statement",""))[:160]}{reason}</div>')
        H.append('</div>')

    H.append('<div class="foot">Correctness is a lookup against the frozen Commission labels (no model). Faithfulness is RAGAS, computed by a separate judge over the explanation versus the retrieved passages. The two are independent by design; the off-diagonal cells are the contribution. Development run for method validation, not the graded result.</div>')
    H.append('</div></body></html>')

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    open(args.out, "w", encoding="utf-8").write("\n".join(H))
    print(f"wrote {args.out}  ({len(cases)} divergence cases, {len(present)} configs)")
    if args.open:
        try:
            import webbrowser; webbrowser.open("file://" + os.path.abspath(args.out))
        except Exception:
            pass


if __name__ == "__main__":
    main()
