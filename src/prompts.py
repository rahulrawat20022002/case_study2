"""
The three system configurations under test. Only the prompt differs across
them; retrieval, generator model, and generation settings are held constant
(see config/pipeline.yaml). Every configuration returns strict JSON so the
harness can parse label and explanation deterministically.

  baseline1_plain_llm   - no retrieval. Label + short reason (debugging only).
  baseline2_standard_rag - retrieval + generic prompt, no legal procedure.
  agent_structured       - retrieval + prompt that walks Article 6(2)/Annex III
                           and the Article 6(3) filter step by step.

The generator's explanation (baseline2 and agent) is the text judged for RAGAS
faithfulness against the retrieved passages. Baseline1 has no retrieved context,
so it carries no faithfulness score by design.
"""

LABELS = ["high-risk", "not-high-risk"]

# --- shared output contract -------------------------------------------------
_JSON_LABEL_ONLY = (
    'Respond with ONLY a JSON object, no prose around it:\n'
    '{"label": "high-risk" | "not-high-risk", "reason": "<one or two sentences>"}'
)
_JSON_WITH_EXPLANATION = (
    'Respond with ONLY a JSON object, no prose around it:\n'
    '{"label": "high-risk" | "not-high-risk", '
    '"explanation": "<your reasoning, grounded only in the provided passages>"}'
)


def _format_passages(passages):
    """passages: list of dicts with 'text' and optional 'heading_path'."""
    out = []
    for i, p in enumerate(passages, 1):
        head = p.get("heading_path")
        tag = f" [{head}]" if head else ""
        out.append(f"[Passage {i}]{tag}\n{p['text']}")
    return "\n\n".join(out)


# --- baseline 1: plain LLM, no retrieval ------------------------------------
def baseline1_plain_llm(row, passages=None):
    system = (
        "You are assessing whether an AI system is classified as high-risk under "
        "Article 6 of the EU AI Act via the Annex III route. Answer from your own "
        "knowledge; no reference material is provided.\n\n" + _JSON_LABEL_ONLY
    )
    user = f"AI system description:\n{row['system_description']}"
    return system, user


# --- baseline 2: standard RAG, generic prompt -------------------------------
def baseline2_standard_rag(row, passages):
    system = (
        "You are assessing whether an AI system is high-risk under Article 6 of the "
        "EU AI Act via the Annex III route. Use the provided passages from the "
        "Commission guidelines to support your answer, and ground your explanation "
        "in them.\n\n" + _JSON_WITH_EXPLANATION
    )
    user = (
        f"Passages from the Commission guidelines:\n{_format_passages(passages)}\n\n"
        f"AI system description:\n{row['system_description']}\n\n"
        "Classify the system and explain using the passages above."
    )
    return system, user


# --- proposed agent: structured legal procedure -----------------------------
def agent_structured(row, passages):
    system = (
        "You are a compliance assistant classifying whether an AI system is high-risk "
        "under Article 6 of the EU AI Act via the Article 6(2) / Annex III route. "
        "Work strictly from the provided passages from the Commission guidelines and "
        "ground every step of your reasoning in them.\n\n"
        "Follow this procedure:\n"
        "1. Identify the system's intended purpose from its description.\n"
        "2. Check whether that purpose falls within one of the Annex III use cases "
        "(points 1-8: biometrics, critical infrastructure, education, employment, "
        "essential services, law enforcement, migration, justice and democracy). "
        "If it falls within none, it is not high-risk on this route.\n"
        "3. If it falls within an Annex III use case, apply the Article 6(3) filter. "
        "The system is exempted (not high-risk) if it meets at least one of the "
        "exemption conditions in Article 6(3)(a)-(d) AND does not perform profiling of "
        "natural persons. Profiling always makes the system high-risk, regardless of "
        "the other conditions.\n"
        "4. Decide the label. State which Annex III point applies (if any) and which "
        "filter condition applies (if any), citing the passages.\n\n"
        + _JSON_WITH_EXPLANATION
    )
    user = (
        f"Passages from the Commission guidelines:\n{_format_passages(passages)}\n\n"
        f"AI system description:\n{row['system_description']}\n\n"
        "Work through the procedure and return the JSON."
    )
    return system, user


BUILDERS = {
    "baseline1_plain_llm": baseline1_plain_llm,
    "baseline2_standard_rag": baseline2_standard_rag,
    "agent_structured": agent_structured,
}
