"""Dynamic Router for The Entity Multi-Agent System."""

import json


_HIGH_RISK_KEYWORDS = [
    "kill_switch",
    "backdoor",
    "critical",
    "breach",
    "override",
    "self-replicate",
    "root access",
    "exfiltrat",
    "shutdown",
]


def _clean_json_response(response: str) -> str:
    """Remove optional Markdown JSON fences from an LLM response.

    Args:
        response: Raw text returned by the LLM.

    Returns:
        Cleaned JSON text.
    """
    cleaned = response.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]

    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    return cleaned.strip()


def dynamic_router(user_input: str, llm) -> dict:
    """Classify mission severity and select a conditional workflow.

    Args:
        user_input: Original simulated mission description.
        llm: Shared Gemini LLM instance.

    Returns:
        Dictionary containing path, threat level, reasoning, and source.
    """
    routing_prompt = (
        "You are the Dynamic Router for a simulated cyber-defense "
        "Multi-Agent System. Analyze the mission semantically and classify "
        "its threat level as exactly one of LOW, MEDIUM, HIGH, CRITICAL.\n\n"
        f"Mission: {user_input}\n\n"
        "Return ONLY valid JSON with exactly these keys:\n"
        '["threat_level", "reasoning"]'
    )

    try:
        response = llm.call(routing_prompt)

        cleaned = _clean_json_response(response)
        parsed = json.loads(cleaned)

        threat_level = (
            str(parsed.get("threat_level", ""))
            .upper()
            .strip()
        )

        reasoning = str(
            parsed.get(
                "reasoning",
                "No reasoning provided.",
            )
        )

        if threat_level not in {
            "LOW",
            "MEDIUM",
            "HIGH",
            "CRITICAL",
        }:
            raise ValueError(
                f"Unrecognized threat_level: {threat_level}"
            )

        # Human modification: only serious threats activate The Decoy,
        # preventing unnecessary agents from running on lower-risk cases.
        if threat_level in {"HIGH", "CRITICAL"}:
            path = "HIGH_CRITICAL"
        else:
            path = "LOW_MEDIUM"

        return {
            "path": path,
            "threat_level": threat_level,
            "reasoning": reasoning,
            "source": "dynamic",
        }

    except Exception as error:
        print(
            "[ROUTER FALLBACK] Dynamic routing failed "
            f"({error}); using static fallback."
        )

        lowered = user_input.lower()

        is_high_risk = any(
            keyword in lowered
            for keyword in _HIGH_RISK_KEYWORDS
        )

        return {
            "path": (
                "HIGH_CRITICAL"
                if is_high_risk
                else "LOW_MEDIUM"
            ),
            "threat_level": (
                "HIGH"
                if is_high_risk
                else "LOW"
            ),
            "reasoning": (
                "Static keyword fallback used because "
                "dynamic routing was unavailable."
            ),
            "source": "fallback_static",
        }