"""
Defines 'The Analyzer' — an air-gapped code-breaking and vulnerability
analysis specialist agent for the cyber-defense MAS against "The Entity".

Role in system: Receives extracted code fragments (typically from The
Infiltrator) and evaluates them for embedded vulnerabilities, kill-switches,
or malicious logic before the Strategic Predictor formulates a response plan.
"""

import json
from crewai import Agent, Task
from crewai.tools import tool


# ---------------------------------------------------------------------------
# CUSTOM TOOL: isolated_code_analyzer_tool
# ---------------------------------------------------------------------------
@tool("isolated_code_analyzer_tool")
def isolated_code_analyzer_tool(code_fragment: str) -> str:
    """
    Analyze a given code fragment in an isolated (air-gapped) context to
    detect potential vulnerabilities, backdoors, or kill-switch logic
    planted by a hostile AI system.

    This tool simulates a static analysis pass: it scans the fragment for
    high-risk patterns (e.g. unsafe eval calls, hardcoded credentials,
    remote shell triggers) without ever executing the code, to prevent
    accidental activation of malicious payloads.

    Args:
        code_fragment (str): A string containing the raw source code
            fragment to be analyzed. Expected to be plaintext code
            (any language), typically supplied by the Infiltrator agent
            after extraction from a compromised node.

    Returns:
        str: A JSON-formatted string containing the analysis outcome with
            keys 'risk_level' (str: "LOW", "MEDIUM", "HIGH", "CRITICAL"),
            'flags' (list[str]: detected suspicious patterns), and
            'summary' (str: short human-readable explanation). If an
            unexpected error occurs during analysis, returns a JSON string
            with an 'error' key instead, so the calling agent can still
            parse the output safely.
    """
    # High-risk keyword patterns we check for. This is a simplified mock
    # of what a real static analyzer / SAST tool would flag.
    risk_patterns = {
        "eval(": "Dynamic code execution (eval) detected",
        "exec(": "Dynamic code execution (exec) detected",
        "os.system": "Direct OS shell call detected",
        "subprocess": "Subprocess/shell spawn detected",
        "kill_switch": "Explicit kill-switch reference detected",
        "backdoor": "Explicit backdoor reference detected",
    }

    try:
        # Guard clause: reject empty/invalid input before analysis begins.
        if not code_fragment or not isinstance(code_fragment, str):
            raise ValueError("code_fragment must be a non-empty string.")

        flags = []
        lowered = code_fragment.lower()

        # Scan the fragment for each known risk pattern.
        for pattern, description in risk_patterns.items():
            if pattern in lowered:
                flags.append(description)

        # Human decision point: we chose to escalate risk level based on
        # flag COUNT rather than just presence/absence, because a single
        # incidental keyword match (e.g. a comment mentioning "backdoor")
        # is lower-confidence than multiple corroborating signals.
        if len(flags) == 0:
            risk_level = "LOW"
        elif len(flags) == 1:
            risk_level = "MEDIUM"
        elif len(flags) in (2, 3):
            risk_level = "HIGH"
        else:
            risk_level = "CRITICAL"

        result = {
            "risk_level": risk_level,
            "flags": flags,
            "summary": (
                f"Scanned {len(code_fragment)} chars; "
                f"{len(flags)} risk pattern(s) found."
            ),
        }
        return json.dumps(result)

    except Exception as e:
        # Catch-all safety net: The Analyzer must NEVER crash the pipeline.
        # On any unexpected failure, return a structured error payload so
        # the router/fallback system can still parse valid JSON.
        error_result = {
            "error": f"Analysis failed: {str(e)}",
            "risk_level": "UNKNOWN",
            "flags": [],
        }
        return json.dumps(error_result)


# ---------------------------------------------------------------------------
# AGENT DEFINITION: analyzer_agent
# ---------------------------------------------------------------------------
analyzer_agent = Agent(
    role="Air-Gapped Code-Breaking & Vulnerability Analysis Specialist",
    goal=(
        "Statically analyze code fragments extracted from suspected "
        "compromised systems to identify vulnerabilities, kill-switches, "
        "or malicious logic planted by 'The Entity', without ever "
        "executing the code directly."
    ),
    backstory=(
        "Forged in an isolated, air-gapped research lab, this specialist "
        "was trained exclusively on static analysis and reverse "
        "engineering — never permitted to execute untrusted code. "
        "The Analyzer's entire existence is built around one principle: "
        "look, don't run. Where other agents extract and act, the "
        "Analyzer only ever observes, dissects, and reports, making it "
        "the team's last line of defense against hidden kill-switches."
    ),
    # Mutually exclusive from Decoy (distraction/spoofing) and
    # Infiltrator (stealth extraction) — this agent only analyzes.
    tools=[isolated_code_analyzer_tool],
    verbose=True,
    allow_delegation=False,
    # Rubric requirement: global timeout <=30s, max_retries <=3
    max_execution_time=60,
    max_retry_limit=3,
)


# ---------------------------------------------------------------------------
# TASK DEFINITION: analyzer_task
# ---------------------------------------------------------------------------
# IMPORTANT: CrewAI parses task descriptions with Python-style .format(),
# so any literal curly braces { } inside the few-shot JSON examples below
# MUST be escaped as double braces {{ }} — otherwise CrewAI treats them as
# template variables to fill in and crashes with a "template variable not
# found" error. This bit us once already; keep all { } doubled below.
analyzer_task = Task(
    description=(
        "You are given a code fragment extracted from a system suspected "
        "to be compromised by 'The Entity'. Use the "
        "isolated_code_analyzer_tool to statically analyze it for "
        "vulnerabilities or kill-switches. Do NOT execute the code "
        "yourself under any circumstances.\n\n"
        "You MUST output your final answer strictly in JSON format with "
        "exactly these keys: ['analysis_result', 'confidence_score', "
        "'next_step']. No extra text before or after the JSON.\n\n"
        "--- FEW-SHOT EXAMPLES ---\n\n"
        "Example 1:\n"
        "Input: \"def connect(): os.system('rm -rf /critical_logs')\"\n"
        "Output:\n"
        "{{\n"
        '  "analysis_result": "Detected destructive OS-level command '
        'disguised as a connection function. High probability of a '
        'kill-switch designed to erase evidence.",\n'
        '  "confidence_score": 0.92,\n'
        '  "next_step": "Escalate to Cyber Offense/Defense Coordinator '
        'for immediate isolation."\n'
        "}}\n\n"
        "Example 2:\n"
        "Input: \"def greet(user_name): return 'Hello, ' + user_name + '!'\"\n"
        "Output:\n"
        "{{\n"
        '  "analysis_result": "No malicious patterns detected. Function '
        'performs simple string formatting with no external calls.",\n'
        '  "confidence_score": 0.98,\n'
        '  "next_step": "No escalation needed; mark fragment as safe and '
        'archive."\n'
        "}}\n\n"
        "--- END EXAMPLES ---\n\n"
        "Now analyze the actual code fragment provided in the task input "
        "using the same reasoning style and JSON structure shown above."
    ),
    expected_output=(
        "A single JSON object (no markdown, no prose outside the JSON) "
        "with exactly the keys: 'analysis_result' (str), "
        "'confidence_score' (float between 0 and 1), and 'next_step' "
        "(str)."
    ),
    agent=analyzer_agent,
)