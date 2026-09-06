"""
Dynamic (LLM-driven) router for the cyber-defense Multi-Agent System.
Analyzes the semantic intent/severity of user input and routes to the
appropriate conditional path: Low/Medium threat vs High/Critical threat.

Design note: This router is explicitly DYNAMIC (not static/keyword-based)
per the assessment brief's requirement to declare router type. It uses the
Gemini LLM to semantically classify threat severity, rather than matching
fixed keywords, so it can generalize to inputs not seen during design.

Risk Mitigation: If the LLM call itself fails or returns unparseable
output, this module falls back to a simple static keyword check so the
pipeline never crashes and the demo can still proceed live.
"""

import json


# ---------------------------------------------------------------------------
# Static fallback keywords — used ONLY if the dynamic LLM call fails.
# This is a human-added safety net, not the primary routing mechanism.
# ---------------------------------------------------------------------------
_HIGH_RISK_KEYWORDS = [
    "kill_switch", "backdoor", "critical", "breach", "override",
    "self-replicate", "root access", "exfiltrat",
]


def dynamic_router(user_input: str, llm) -> dict:
    """
    Determine the routing path for a given user input using LLM-driven
    semantic analysis of threat severity.

    This function sends the input to the Gemini LLM with a strict prompt
    asking it to classify the threat level and return structured JSON.
    Two conditional paths are supported:
        - Path 1 (Low/Medium): standard defense workflow.
        - Path 2 (High/Critical): escalated workflow requiring the
          Strategic Predictor / Cyber Coordinator sequence.

    Args:
        user_input (str): The raw scenario or code fragment describing
            the potential threat, supplied by the user or upstream agent.
        llm: An initialized LLM client instance (e.g. the shared
            gemini_llm object from main.py) used to perform the
            semantic classification call.

    Returns:
        dict: A routing decision with keys:
            - "path" (str): "LOW_MEDIUM" or "HIGH_CRITICAL"
            - "threat_level" (str): "LOW", "MEDIUM", "HIGH", or "CRITICAL"
            - "reasoning" (str): brief explanation of the classification
            - "source" (str): "dynamic" if LLM classification succeeded,
              "fallback_static" if the static keyword fallback was used
    """
    routing_prompt = (
        "You are a threat-severity classifier for a cyber-defense system. "
        "Analyze the following input and classify its threat level as "
        "exactly one of: LOW, MEDIUM, HIGH, CRITICAL.\n\n"
        f"Input: {user_input}\n\n"
        "Respond ONLY in strict JSON format with keys: "
        '["threat_level", "reasoning"]. No extra text.'
    )

    try:
        # Primary routing path: dynamic, LLM-driven semantic classification.
        response = llm.call(routing_prompt)

        # LLM responses can include stray whitespace/markdown fences even
        # when instructed not to — strip these defensively before parsing.
        cleaned = response.strip().strip("```json").strip("```").strip()
        parsed = json.loads(cleaned)

        threat_level = parsed.get("threat_level", "").upper()
        reasoning = parsed.get("reasoning", "No reasoning provided.")

        if threat_level not in ("LOW", "MEDIUM", "HIGH", "CRITICAL"):
            # Guard against the LLM returning an unexpected label —
            # treat as parse failure and drop to fallback below.
            raise ValueError(f"Unrecognized threat_level: {threat_level}")

        path = "HIGH_CRITICAL" if threat_level in ("HIGH", "CRITICAL") else "LOW_MEDIUM"

        return {
            "path": path,
            "threat_level": threat_level,
            "reasoning": reasoning,
            "source": "dynamic",
        }

    except (json.JSONDecodeError, ValueError, Exception) as e:
        # Fallback path: if the dynamic LLM call fails for ANY reason
        # (timeout, malformed JSON, API error), we do NOT crash the
        # pipeline. Instead we fall back to a simple static keyword scan
        # so the router still produces a usable decision.
        print(f"[ROUTER FALLBACK] Dynamic routing failed ({e}); using static fallback.")

        lowered = user_input.lower()
        is_high_risk = any(keyword in lowered for keyword in _HIGH_RISK_KEYWORDS)

        return {
            "path": "HIGH_CRITICAL" if is_high_risk else "LOW_MEDIUM",
            "threat_level": "HIGH" if is_high_risk else "LOW",
            "reasoning": "Static keyword fallback used due to dynamic routing failure.",
            "source": "fallback_static",
        }