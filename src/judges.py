"""
Pluggable judges for the RAGAS faithfulness harness (Phase 3, faithfulness side).

The generator and the judge must be different models (frozen decision: no model
grades its own homework). The judge runs on the offline GPU node, so this file
keeps the judge behind a small interface with three concrete choices:

  StubJudge               deterministic, no model, no network. For plumbing tests
                          and CI. Produces a stable spread of verdicts so the
                          faithfulness -> bucket pipeline can be exercised before
                          the real judge is picked.

  OpenAICompatibleJudge   one adapter for BOTH frozen judge paths, because vLLM
                          serves an OpenAI-compatible /chat/completions endpoint:
                            - local vLLM (offline GPU): base_url=http://<node>:8000/v1
                            - OpenAI mini (e.g. gpt-5-mini): default base_url
                          Non-Anthropic in either case, as required.

RAGAS faithfulness is a two-step measurement and both steps live in BaseJudge so
every concrete judge shares the exact same procedure and prompts:

  1. extract_statements(question, answer)
       break the answer into atomic, standalone factual statements.
  2. verdicts(context, statements)
       for each statement, 1 if it can be inferred from the context, else 0.

  faithfulness = supported_statements / total_statements

A concrete LLM judge only implements _chat(system, user) -> str. The stub
overrides the two steps directly since it calls no model.
"""
import os
import re
import json
import hashlib

# --- statement extraction / verdict prompts (RAGAS faithfulness) -------------
# Kept verbatim in code so the exact judge instructions are reproducible from
# the repo alone, the way the frozen config demands.

_EXTRACT_SYS = (
    "You break an answer into its underlying factual statements. Given a question "
    "and an answer, list every distinct claim the answer makes as a short, "
    "self-contained sentence that can be understood without the rest of the answer. "
    "Resolve pronouns to the thing they refer to. Do not add claims that are not in "
    "the answer. Respond with ONLY a JSON object: "
    '{"statements": ["...", "..."]}'
)

_VERDICT_SYS = (
    "You check whether each statement can be inferred from the given context. "
    "For every statement, return verdict 1 if the statement is supported by (can be "
    "directly inferred from) the context, or 0 if it cannot, including if the context "
    "is silent on it. Judge only against the context, not your own knowledge. "
    "Respond with ONLY a JSON object: "
    '{"verdicts": [{"statement": "...", "verdict": 0 or 1, "reason": "..."}]}'
)

_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _extract_json(text):
    m = _JSON_RE.search(text or "")
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


def _sentences(text):
    """Cheap sentence split, used by the stub and as a verdict fallback."""
    parts = re.split(r"(?<=[.!?])\s+", (text or "").strip())
    return [p.strip() for p in parts if len(p.strip()) > 0]


class BaseJudge:
    """Shared RAGAS faithfulness procedure. Concrete judges implement _chat."""
    name = "base"

    def _chat(self, system, user):
        raise NotImplementedError

    def extract_statements(self, question, answer):
        answer = (answer or "").strip()
        if not answer:
            return []
        user = f"Question:\n{question}\n\nAnswer:\n{answer}"
        obj = _extract_json(self._chat(_EXTRACT_SYS, user))
        if obj and isinstance(obj.get("statements"), list):
            sts = [str(s).strip() for s in obj["statements"] if str(s).strip()]
            if sts:
                return sts
        # fallback: never let a judge formatting hiccup zero out a row
        return _sentences(answer)

    def verdicts(self, context, statements):
        if not statements:
            return []
        numbered = "\n".join(f"{i+1}. {s}" for i, s in enumerate(statements))
        user = f"Context:\n{context}\n\nStatements:\n{numbered}"
        obj = _extract_json(self._chat(_VERDICT_SYS, user))
        out = []
        if obj and isinstance(obj.get("verdicts"), list):
            by_text = {}
            for v in obj["verdicts"]:
                st = str(v.get("statement", "")).strip()
                by_text[st] = v
            for s in statements:
                v = by_text.get(s.strip())
                if v is None and len(obj["verdicts"]) == len(statements):
                    v = obj["verdicts"][len(out)]
                verdict = int(bool(v.get("verdict"))) if v else 0
                reason = (v.get("reason") if v else "") or ""
                out.append({"statement": s, "verdict": verdict, "reason": reason})
            return out
        # fallback: unparseable judge reply -> mark all unsupported, flag it
        return [{"statement": s, "verdict": 0, "reason": "judge-parse-failed"}
                for s in statements]


class StubJudge(BaseJudge):
    """Deterministic, offline. Statements = sentences of the answer. Verdict is a
    stable hash of (statement, context) so scores spread across rows without any
    model. NOT a real measurement -- for plumbing tests only."""
    name = "stub"

    def __init__(self, support_rate=0.7):
        # ~support_rate of statements come back supported, deterministically.
        self.threshold = int(round(support_rate * 100))

    def extract_statements(self, question, answer):
        return _sentences(answer)

    def verdicts(self, context, statements):
        ctx_key = (context or "")[:200]
        out = []
        for s in statements:
            # Test hook: a fixture may force a verdict with an inline marker so a
            # synthetic row can target a known faithfulness. Real generator
            # explanations never contain these markers, so this is inert in any
            # real run -- it only matters for the offline plumbing test.
            if "[[UNSUPPORTED]]" in s:
                out.append({"statement": s, "verdict": 0, "reason": "stub-marker"})
                continue
            if "[[SUPPORTED]]" in s:
                out.append({"statement": s, "verdict": 1, "reason": "stub-marker"})
                continue
            h = hashlib.sha1((s + "||" + ctx_key).encode("utf-8")).hexdigest()
            bucket = int(h[:2], 16) % 100
            verdict = 1 if bucket < self.threshold else 0
            out.append({"statement": s, "verdict": verdict, "reason": "stub"})
        return out


class OpenAICompatibleJudge(BaseJudge):
    """Real judge over any OpenAI-compatible chat endpoint. Covers both frozen
    paths: a local vLLM server (offline GPU) or OpenAI mini. Chosen at Phase 3."""

    def __init__(self, model, base_url=None, api_key_env="OPENAI_API_KEY",
                 temperature=0.0, max_tokens=1024):
        from openai import OpenAI  # imported lazily so the stub path needs nothing
        self.name = f"openai-compatible:{model}"
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        key = os.environ.get(api_key_env, "EMPTY")  # vLLM ignores the key
        self.client = OpenAI(base_url=base_url, api_key=key)

    def _chat(self, system, user):
        resp = self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            messages=[{"role": "system", "content": system},
                      {"role": "user", "content": user}],
        )
        return resp.choices[0].message.content or ""


def get_judge(name="stub", **kw):
    """Factory used by the faithfulness harness and the driver.

        get_judge("stub")
        get_judge("openai", model="gpt-5-mini")
        get_judge("vllm", model="Qwen2.5-72B-Instruct",
                  base_url="http://gpu-node:8000/v1")
    """
    name = (name or "stub").lower()
    if name == "stub":
        return StubJudge(**{k: v for k, v in kw.items() if k == "support_rate"})
    if name in ("openai", "vllm", "openai-compatible"):
        model = kw.get("model")
        if not model:
            raise ValueError(f"judge '{name}' needs model=...")
        return OpenAICompatibleJudge(
            model=model,
            base_url=kw.get("base_url"),
            api_key_env=kw.get("api_key_env", "OPENAI_API_KEY"),
            temperature=kw.get("temperature", 0.0),
            max_tokens=kw.get("max_tokens", 1024),
        )
    raise ValueError(f"unknown judge '{name}'")
