"""Define The Analyzer agent and its isolated static-analysis tool."""

import json

from crewai import Agent, Task
from crewai.tools import tool


@tool("isolated_code_analyzer_tool")
def isolated_code_analyzer_tool(code_fragment: str) -> str:
    """Analyze simulated evidence without executing it.

    Args:
        code_fragment: Simulated code or intelligence text supplied by
            the previous workflow stage.

    Returns:
        JSON string containing risk level, detected flags, and summary.

    The function performs only local string analysis and never executes
    the supplied content.
    """
    risk_patterns = {
        "eval(": "Dynamic code execution (eval) detected",
        "exec(": "Dynamic code execution (exec) detected",
        "os.system": "Direct OS shell call detected",
        "subprocess": "Subprocess or shell spawn detected",
        "kill_switch": "Explicit kill-switch reference detected",
        "backdoor": "Explicit backdoor reference detected",
        "shutdown": "Shutdown-related behavior detected",
        "authentication fallback": (
            "Repeated authentication fallback indicator detected"
        ),
    }

    try:
        if not code_fragment or not isinstance(code_fragment, str):
            raise ValueError(
                "code_fragment must be a non-empty string."
            )

        flags = []
        lowered = code_fragment.lower()

        for pattern, description in risk_patterns.items():
            if pattern in lowered:
                flags.append(description)

        # Human modification: risk is based on multiple corroborating
        # indicators rather than treating every keyword as critical.
        if len(flags) == 0:
            risk_level = "LOW"
        elif len(flags) == 1:
            risk_level = "MEDIUM"
        elif len(flags) in (2, 3):
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        return json.dumps(
            {
                "risk_level": risk_level,
                "flags": flags,
                "summary": (
                    f"Scanned {len(code_fragment)} characters; "
                    f"{len(flags)} risk pattern(s) found."
                ),
            },
            indent=2,
        )

    except Exception as error:
        return json.dumps(
            {
                "error": f"Analysis failed: {error}",
                "risk_level": "UNKNOWN",
                "flags": [],
            },
            indent=2,
        )


analyzer_agent = Agent(
    role="Air-Gapped Code-Breaking & Vulnerability Analysis Specialist",
    goal=(
        "Statically analyze simulated intelligence retrieved by The "
        "Infiltrator to identify suspicious indicators, vulnerabilities, "
        "kill-switches, or malicious logic without executing the evidence."
    ),
    backstory=(
        "You are The Analyzer, an air-gapped analysis specialist in the "
        "countermeasure unit fighting a simulated rogue AI called The "
        "Entity. You examine evidence but never execute untrusted content. "
        "Your role is strictly defensive: observe, analyze, and recommend "
        "the safest next action."
    ),
    tools=[isolated_code_analyzer_tool],
    verbose=True,
    allow_delegation=False,

    # Corrected from 60 seconds to the project's <=30 second limit.
    max_execution_time=30,
    max_retry_limit=3,
)


analyzer_task = Task(
    description=(
        "You are the final specialist in a sequential multi-agent "
        "cyber-defense workflow.\n\n"
        "Original user mission:\n"
        "{user_input}\n\n"
        "Router classification: {threat_level}\n"
        "Selected route: {route}\n\n"
        "The previous Infiltrator task retrieved simulated intelligence. "
        "Use the previous task output as your primary evidence, especially "
        "its intelligence_summary field.\n\n"
        "Use isolated_code_analyzer_tool to statically inspect that "
        "evidence. Never execute retrieved content.\n\n"
        "You MUST output your final answer strictly as valid JSON with "
        "exactly these keys:\n"
        "- analysis_result\n"
        "- confidence_score\n"
        "- next_step\n\n"

        "--- FEW-SHOT EXAMPLES ---\n\n"

        "Example 1:\n"
        "Input: \"def connect(): os.system('rm -rf /critical_logs')\"\n"
        "Output:\n"
        "{{\n"
        '  "analysis_result": "Detected a destructive OS-level command '
        'that represents a serious defensive risk.",\n'
        '  "confidence_score": 0.92,\n'
        '  "next_step": "Isolate the simulated affected node and '
        'preserve available evidence."\n'
        "}}\n\n"

        "Example 2:\n"
        "Input: \"def greet(name): return 'Hello ' + name\"\n"
        "Output:\n"
        "{{\n"
        '  "analysis_result": "No malicious patterns detected.",\n'
        '  "confidence_score": 0.98,\n'
        '  "next_step": "Archive the simulated evidence as low risk."\n'
        "}}\n\n"

        "--- END EXAMPLES ---\n\n"
        "Do not output Markdown or prose outside the JSON."
    ),
    expected_output=(
        "One JSON object containing exactly analysis_result, "
        "confidence_score, and next_step."
    ),
    agent=analyzer_agent,
)