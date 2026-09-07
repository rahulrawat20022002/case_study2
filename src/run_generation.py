"""
Generation harness. For each configuration and each test row: retrieve (if the
config uses retrieval), build the prompt, call the generator (claude-sonnet-4-6),
parse the JSON label + explanation, and log everything Phase 3 needs -- the
label, the explanation (the text RAGAS will judge), the retrieved passages
(top-5 given to the generator, top-10 logged), and raw usage.

Generation settings are read from config/pipeline.yaml and held identical across
all three configurations; only the prompt changes.

    python run_generation.py --configs agent_structured --limit 8   # sanity
    python run_generation.py                                        # full 215

Requires ANTHROPIC_API_KEY in the environment. Nothing is hard-coded.
"""
import os
import re
import sys
import json
import time
import argparse
import yaml
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))
from prompts import BUILDERS, LABELS
from retriever import HybridRetriever

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def get_client(gen_cfg):
    """Build the generator client from config. Returns (client, kind) where kind
    is 'anthropic' or 'openai'. Providers:
      anthropic (FROZEN, for results) - first-party Anthropic API, claude-sonnet-4-6.
      vertex                          - same model via Google Vertex AI.
      openai_compatible (DEV ONLY)    - any OpenAI-style endpoint (Groq, Gemini's
                                        OpenAI endpoint, a local server). Lets us run
                                        the whole pipeline on a FREE key while the
                                        university's proper API access is pending.
                                        NOT for the graded results: the study's
                                        generator stays claude-sonnet-4-6 (frozen)."""
    provider = gen_cfg.get("provider", "anthropic")
    if provider == "vertex":
        from anthropic import AnthropicVertex
        v = gen_cfg["vertex"]
        return AnthropicVertex(project_id=v["project_id"],
                               region=v["region"]), "anthropic"
    if provider in ("openai_compatible", "openai", "groq", "gemini"):
        from openai import OpenAI
        oc = gen_cfg.get("openai_compatible", {})
        key = os.environ.get(oc.get("api_key_env", "OPENAI_API_KEY"), "EMPTY")
        return OpenAI(base_url=oc.get("base_url"), api_key=key), "openai"
    import anthropic
    return anthropic.Anthropic(), "anthropic"   # reads ANTHROPIC_API_KEY


def model_id(gen_cfg):
    if gen_cfg.get("provider") == "vertex":
        return gen_cfg["vertex"].get("model_override") or gen_cfg["model"]
    return gen_cfg["model"]


def parse_output(raw):
    """Extract {label, explanation|reason} from the model's text, robustly."""
    m = _JSON_RE.search(raw or "")
    label, expl, ok = None, "", True
    if m:
        try:
            obj = json.loads(m.group(0))
            label = (obj.get("label") or "").strip().lower()
            expl = obj.get("explanation") or obj.get("reason") or ""
        except json.JSONDecodeError:
            ok = False
    else:
        ok = False
    if label not in LABELS:
        # last-ditch: look for the literal labels in the text
        low = (raw or "").lower()
        if "not-high-risk" in low or "not high-risk" in low:
            label = "not-high-risk"
        elif "high-risk" in low:
            label = "high-risk"
        else:
            label, ok = None, False
    return {"label": label, "explanation": expl, "parse_ok": ok}


def call_generator(client, kind, gen_cfg, system, user, max_retries=4):
    for attempt in range(max_retries):
        try:
            if kind == "openai":
                resp = client.chat.completions.create(
                    model=model_id(gen_cfg),
                    temperature=gen_cfg["temperature"],
                    max_tokens=gen_cfg["max_tokens"],
                    top_p=gen_cfg["top_p"],
                    messages=[{"role": "system", "content": system},
                              {"role": "user", "content": user}],
                )
                text = resp.choices[0].message.content or ""
                u = getattr(resp, "usage", None)
                usage = {"input_tokens": getattr(u, "prompt_tokens", None),
                         "output_tokens": getattr(u, "completion_tokens", None)}
                return text, usage
            resp = client.messages.create(
                model=model_id(gen_cfg),
                temperature=gen_cfg["temperature"],
                max_tokens=gen_cfg["max_tokens"],
                top_p=gen_cfg["top_p"],
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            text = "".join(b.text for b in resp.content if b.type == "text")
            usage = {"input_tokens": resp.usage.input_tokens,
                     "output_tokens": resp.usage.output_tokens}
            return text, usage
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config-file", default="config/pipeline.yaml")
    ap.add_argument("--configs", nargs="*", help="subset of configuration names")
    ap.add_argument("--limit", type=int, default=None, help="first N rows (sanity)")
    ap.add_argument("--rows", nargs="*", help="specific test-row ids")
    # dev overrides so the notebook can switch generator without editing the yaml
    ap.add_argument("--provider", default=None,
                    help="override generation.provider (e.g. openai_compatible)")
    ap.add_argument("--model", default=None, help="override generation.model")
    ap.add_argument("--base-url", default=None,
                    help="override openai_compatible.base_url")
    ap.add_argument("--api-key-env", default=None,
                    help="override openai_compatible.api_key_env")
    args = ap.parse_args()

    cfg = yaml.safe_load(open(args.config_file))
    gen_cfg = cfg["generation"]
    if args.provider:
        gen_cfg["provider"] = args.provider
    if args.model:
        gen_cfg["model"] = args.model
    if args.base_url or args.api_key_env:
        oc = gen_cfg.setdefault("openai_compatible", {})
        if args.base_url:
            oc["base_url"] = args.base_url
        if args.api_key_env:
            oc["api_key_env"] = args.api_key_env
    configs = cfg["configurations"]
    if args.configs:
        configs = [c for c in configs if c["name"] in args.configs]

    rows = [json.loads(l) for l in open(cfg["paths"]["test_set"], encoding="utf-8")]
    if args.rows:
        rows = [r for r in rows if r["id"] in set(args.rows)]
    if args.limit:
        rows = rows[:args.limit]

    need_retrieval = any(c["retrieval"] for c in configs)
    retriever = HybridRetriever(args.config_file) if need_retrieval else None

    client, kind = get_client(gen_cfg)

    runs_dir = Path(cfg["paths"]["runs_dir"])
    runs_dir.mkdir(parents=True, exist_ok=True)

    for conf in configs:
        name = conf["name"]
        builder = BUILDERS[name]
        out_path = runs_dir / f"{name}.jsonl"
        print(f"\n=== {name}  ({len(rows)} rows) -> {out_path} ===")
        with open(out_path, "w", encoding="utf-8") as f:
            for i, row in enumerate(rows, 1):
                top5 = top10 = None
                if conf["retrieval"]:
                    top5, top10 = retriever.search(row["system_description"])
                passages = top5 or []
                system, user = builder(row, passages)
                raw, usage = call_generator(client, kind, gen_cfg, system, user)
                parsed = parse_output(raw)
                rec = {
                    "id": row["id"], "config": name,
                    "gold_label": row["label"],
                    "pred_label": parsed["label"],
                    "explanation": parsed["explanation"],
                    "parse_ok": parsed["parse_ok"],
                    "edge_case_type": row.get("edge_case_type"),
                    "annex_iii_area": row.get("annex_iii_area"),
                    "retrieved_top5": [{"id": h["id"], "text": h["text"],
                                        "score": h["score"]} for h in (top5 or [])],
                    "retrieved_top10_ids": [h["id"] for h in (top10 or [])],
                    "usage": usage,
                    "raw": raw,
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                mark = "ok" if parsed["parse_ok"] else "PARSE?"
                print(f"  [{i}/{len(rows)}] {row['id']}: pred={parsed['label']} "
                      f"gold={row['label']} {mark}")
    print("\ndone.")


if __name__ == "__main__":
    main()
