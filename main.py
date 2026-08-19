"""
main.py

Entry point for the Multi-Agent System (MAS) — cyber-defense countermeasure
unit against "The Entity". Initializes the Gemini LLM connection, sets
global timeout/retry safety limits, wires together the agents (Decoy,
Infiltrator, Analyzer), and runs the Crew via the dynamic router.

Team Leader responsibilities covered in this file:
    - Core environment setup
    - Gemini LLM initialization
    - Global timeout (<=30s) and max_retries (<=3) configuration
"""

import os
import sys
from dotenv import load_dotenv
from crewai import Crew, Process, LLM
from router import dynamic_router

# NOTE: import your teammates' agent/task modules once they're ready.
# from agents.decoy_agent import decoy_agent, decoy_task
# from agents.infiltrator_agent import infiltrator_agent, infiltrator_task
from agents.analyzer_agent import analyzer_agent, analyzer_task
from router import dynamic_router  # your dynamic router module


# ---------------------------------------------------------------------------
# STEP 1: Load environment variables
# ---------------------------------------------------------------------------
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
print(f"[DEBUG] Key loaded: {GEMINI_API_KEY[:15]}...{GEMINI_API_KEY[-6:]}" if GEMINI_API_KEY else "[DEBUG] Key is None")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    # Fail fast and loud if the key is missing — better than a cryptic
    # auth error deep inside a CrewAI call later.
    print("ERROR: GEMINI_API_KEY not found in .env file.")
    sys.exit(1)


# ---------------------------------------------------------------------------
# STEP 2: Initialize the Gemini LLM with global safety limits
# ---------------------------------------------------------------------------
# Human decision: we explicitly cap timeout at 30s and retries at 3,
# per the rubric's "Robustness & Error Handling" requirement. This
# prevents a single hung API call from stalling the whole pipeline.
gemini_llm = LLM(
    model="gemini/gemini-3.6-flash",   # adjust to whichever Gemini model your team confirmed
    api_key=GEMINI_API_KEY,
    timeout=30,        # rubric requirement: <= 30 seconds
    max_retries=3,      # rubric requirement: <= 3 retries
    temperature=0.3,    # lower temp = more predictable JSON-formatted outputs
)


# ---------------------------------------------------------------------------
# STEP 3: Attach the LLM to each agent
# ---------------------------------------------------------------------------
# We assign the shared gemini_llm instance to every agent here rather than
# inside each agent's own file, so timeout/retry config stays centralized
# in ONE place (this file) instead of duplicated across teammates' code.
analyzer_agent.llm = gemini_llm
# decoy_agent.llm = gemini_llm
# infiltrator_agent.llm = gemini_llm


# ---------------------------------------------------------------------------
# STEP 4: Build and run the Crew via the dynamic router
# ---------------------------------------------------------------------------
def run_mas(user_input: str) -> dict:
    """
    Run the full Multi-Agent System pipeline on a given user input.

    Passes the input through the dynamic router to determine which
    conditional path to follow (e.g. Low/Medium vs High/Critical threat),
    then executes the relevant agents in sequence and returns the final
    result.

    Args:
        user_input (str): The raw scenario/prompt describing the threat
            or data to be processed by the MAS (e.g. a suspicious code
            fragment or attack description).

    Returns:
        dict: The final structured output from the Crew's execution,
            or a fallback error payload if the pipeline fails.
    """
    try:
        # STEP 1: Dynamic routing — classify threat severity and decide
        # which conditional path (Low/Medium vs High/Critical) to follow.
        # This call reuses the same gemini_llm instance initialized above,
        # so it respects the same global timeout/retry limits.
        route_decision = dynamic_router(user_input, llm=gemini_llm)

        print(f"[ROUTER] path={route_decision['path']} "
              f"threat_level={route_decision['threat_level']} "
              f"source={route_decision['source']}")

        # STEP 2: Build the Crew. Analyzer receives the routing decision
        # as part of its task context, so its output reflects which path
        # was selected (satisfies the "workflow handles dependencies"
        # requirement — Analyzer's behavior depends on router's verified
        # classification, not just raw user input).
        crew = Crew(
            agents=[analyzer_agent],  # extend with decoy_agent, infiltrator_agent
            tasks=[analyzer_task],    # extend with decoy_task, infiltrator_task
            process=Process.sequential,  # switch to hierarchical if using manager-worker
            verbose=True,
        )

        result = crew.kickoff(inputs={
            "user_input": user_input,
            "route": route_decision["path"],
            "threat_level": route_decision["threat_level"],
        })

        return {
            "status": "success",
            "route": route_decision,
            "result": result,
        }

    except Exception as e:
        # Top-level fallback: if ANYTHING in the pipeline fails
        # unexpectedly, we don't crash — we return a partial/error
        # response per the rubric's Fallback System requirement.
        print(f"[FALLBACK TRIGGERED] MAS execution failed: {e}")
        return {
            "status": "fallback",
            "error": str(e),
            "result": "Partial response unavailable — system entered safe fallback mode.",
        }


if __name__ == "__main__":
    # Simple manual test run — replace with your live demo scenario input.
    test_scenario = (
        "Suspicious code fragment extracted from Node 7: "
        "os.system('rm -rf /critical_logs') detected during routine scan."
    )
    output = run_mas(test_scenario)
    print(output)