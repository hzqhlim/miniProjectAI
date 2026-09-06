"""Run The Entity Multi-Agent System with dynamic routing."""

import json
import os
import sys
from typing import Any

from crewai import Crew, LLM, Process
from dotenv import load_dotenv

from agents.analyzer_agent import (
    analyzer_agent,
    analyzer_task,
)
from agents.decoy_agent import (
    decoy_agent,
    decoy_task,
)
from agents.infiltrator_agent import (
    infiltrator_agent,
    infiltrator_task,
)
from router import dynamic_router


# =========================================================
# ENVIRONMENT SETUP
# =========================================================

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print(
        "ERROR: GEMINI_API_KEY was not found "
        "inside the .env file."
    )
    sys.exit(1)


# =========================================================
# GEMINI LLM CONFIGURATION
# =========================================================

# Human modification:
# The timeout and retry limits are explicitly configured
# to satisfy the project's robustness requirements.
gemini_llm = LLM(
    model="gemini/gemini-3.6-flash",
    api_key=GEMINI_API_KEY,
    timeout=30,
    max_retries=3,
    temperature=0.3,
)


# Assign the same Gemini LLM to all specialist agents.
decoy_agent.llm = gemini_llm
infiltrator_agent.llm = gemini_llm
analyzer_agent.llm = gemini_llm


# =========================================================
# LOW / MEDIUM WORKFLOW
# =========================================================

def execute_low_medium(
    user_input: str,
    route_decision: dict[str, Any],
) -> Any:
    """Execute the LOW/MEDIUM workflow.

    Args:
        user_input: Original simulated mission.
        route_decision: Result returned by the Dynamic Router.

    Returns:
        Final CrewAI result produced by the Analyzer.
    """
    print(
        "\n[WORKFLOW] "
        "LOW/MEDIUM -> Infiltrator -> Analyzer"
    )

    # Human modification:
    # LOW/MEDIUM threats skip The Decoy because defensive
    # deception is unnecessary for lower-risk missions.
    infiltrator_task.context = []

    analyzer_task.context = [
        infiltrator_task,
    ]

    crew = Crew(
        agents=[
            infiltrator_agent,
            analyzer_agent,
        ],
        tasks=[
            infiltrator_task,
            analyzer_task,
        ],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff(
        inputs={
            "user_input": user_input,
            "route": route_decision["path"],
            "threat_level": (
                route_decision["threat_level"]
            ),
        }
    )


# =========================================================
# HIGH / CRITICAL WORKFLOW
# =========================================================

def execute_high_critical(
    user_input: str,
    route_decision: dict[str, Any],
) -> Any:
    """Execute the HIGH/CRITICAL workflow.

    Args:
        user_input: Original simulated mission.
        route_decision: Result returned by the Dynamic Router.

    Returns:
        Final CrewAI result produced by the Analyzer.
    """
    print(
        "\n[WORKFLOW] "
        "HIGH/CRITICAL -> "
        "Decoy -> Infiltrator -> Analyzer"
    )

    # Human modification:
    # HIGH/CRITICAL threats activate The Decoy first
    # to demonstrate conditional multi-agent routing.
    infiltrator_task.context = [
        decoy_task,
    ]

    # Human modification:
    # The Analyzer receives the Infiltrator output as its
    # primary evidence. The Infiltrator already received
    # any available Decoy context.
    analyzer_task.context = [
        infiltrator_task,
    ]

    crew = Crew(
        agents=[
            decoy_agent,
            infiltrator_agent,
            analyzer_agent,
        ],
        tasks=[
            decoy_task,
            infiltrator_task,
            analyzer_task,
        ],
        process=Process.sequential,
        verbose=True,
    )

    return crew.kickoff(
        inputs={
            "user_input": user_input,
            "route": route_decision["path"],
            "threat_level": (
                route_decision["threat_level"]
            ),
        }
    )


# =========================================================
# SELF-EVALUATION
# =========================================================

def evaluate_result(
    user_input: str,
    route_decision: dict[str, Any],
    result: Any,
) -> dict[str, Any]:
    """Evaluate whether the MAS produced a usable result.

    Args:
        user_input: Original mission scenario.
        route_decision: Router classification result.
        result: Final CrewAI output.

    Returns:
        Structured self-evaluation result.
    """
    result_text = str(result).strip()

    if not user_input.strip():
        return {
            "evaluation_status": "FAILED",
            "original_input_received": False,
            "route_verified": False,
            "output_available": bool(result_text),
            "risk_warning": (
                "Original mission input was empty."
            ),
        }

    if not result_text:
        return {
            "evaluation_status": "FAILED",
            "original_input_received": True,
            "route_verified": False,
            "output_available": False,
            "risk_warning": (
                "Crew returned an empty final response."
            ),
        }

    valid_route = route_decision["path"] in {
        "LOW_MEDIUM",
        "HIGH_CRITICAL",
    }

    if not valid_route:
        return {
            "evaluation_status": "FAILED",
            "original_input_received": True,
            "route_verified": False,
            "output_available": True,
            "risk_warning": (
                "Router returned an invalid workflow path."
            ),
        }

    return {
        "evaluation_status": "PASS",
        "original_input_received": True,
        "route_verified": True,
        "output_available": True,
        "risk_warning": None,
    }


# =========================================================
# COMPLETE MAS EXECUTION
# =========================================================

def run_mas(
    user_input: str,
) -> dict[str, Any]:
    """Run the complete dynamically routed MAS.

    Args:
        user_input: Simulated threat scenario.

    Returns:
        Successful MAS result or controlled fallback data.
    """
    route_decision = None

    try:
        route_decision = dynamic_router(
            user_input,
            llm=gemini_llm,
        )

        print(
            "\n[ROUTER] "
            f"path={route_decision['path']} "
            f"threat_level="
            f"{route_decision['threat_level']} "
            f"source={route_decision['source']}"
        )

        if (
            route_decision["path"]
            == "LOW_MEDIUM"
        ):
            result = execute_low_medium(
                user_input,
                route_decision,
            )

        elif (
            route_decision["path"]
            == "HIGH_CRITICAL"
        ):
            result = execute_high_critical(
                user_input,
                route_decision,
            )

        else:
            raise ValueError(
                "Router produced an unsupported path."
            )

        evaluation = evaluate_result(
            user_input,
            route_decision,
            result,
        )

        return {
            "status": "success",
            "route": route_decision,
            "result": str(result),
            "self_evaluation": evaluation,
        }

    except Exception as error:
        partial_response = {
            "original_input": user_input,
        }

        if route_decision is not None:
            partial_response.update(
                {
                    "router_status": "completed",
                    "route": (
                        route_decision.get(
                            "path"
                        )
                    ),
                    "threat_level": (
                        route_decision.get(
                            "threat_level"
                        )
                    ),
                }
            )

        return {
            "status": "fallback",
            "risk_warning": (
                "The MAS encountered an unexpected "
                "execution failure."
            ),
            "reason": str(error),
            "partial_response": partial_response,
        }


# =========================================================
# PROFESSIONAL TERMINAL REPORT
# =========================================================

def display_final_report(
    output: dict[str, Any],
) -> None:
    """Display the final MAS result clearly.

    Args:
        output: Result returned by run_mas.
    """
    print(
        "\n============================================================"
    )
    print(
        "                 THE ENTITY - FINAL REPORT"
    )
    print(
        "============================================================"
    )

    if output.get("status") == "success":
        route = output["route"]
        evaluation = (
            output["self_evaluation"]
        )

        try:
            analyzer_result = json.loads(
                output["result"]
            )

        except (
            json.JSONDecodeError,
            TypeError,
        ):
            analyzer_result = {
                "analysis_result": (
                    output["result"]
                ),
                "confidence_score": 0,
                "next_step": (
                    "Review available mission "
                    "evidence."
                ),
            }

        print("\nSYSTEM STATUS")
        print("-------------")
        print("Status          : SUCCESS")

        print(
            "Routing Method  : "
            f"{route['source'].upper()}"
        )

        print(
            "Threat Level    : "
            f"{route['threat_level']}"
        )

        print(
            "Selected Route  : "
            f"{route['path']}"
        )

        print("\nROUTER ASSESSMENT")
        print("-----------------")

        print(
            route.get(
                "reasoning",
                "No router reasoning available.",
            )
        )

        print("\nANALYZER RESULT")
        print("---------------")
        print("Analysis:")

        print(
            analyzer_result.get(
                "analysis_result",
                "No analysis available.",
            )
        )

        confidence = (
            analyzer_result.get(
                "confidence_score",
                0,
            )
        )

        if isinstance(
            confidence,
            (int, float),
        ):
            if confidence <= 1:
                confidence_percent = (
                    confidence * 100
                )
            else:
                confidence_percent = (
                    confidence
                )
        else:
            confidence_percent = 0

        print(
            "\nConfidence Score : "
            f"{confidence_percent:.0f}%"
        )

        print("\nRecommended Action:")

        print(
            analyzer_result.get(
                "next_step",
                "No recommendation available.",
            )
        )

        print("\nSELF-EVALUATION")
        print("---------------")

        print(
            "Evaluation       : "
            f"{evaluation['evaluation_status']}"
        )

        print(
            "Input Received   : "
            f"{'YES' if evaluation['original_input_received'] else 'NO'}"
        )

        print(
            "Route Verified   : "
            f"{'YES' if evaluation['route_verified'] else 'NO'}"
        )

        print(
            "Output Available : "
            f"{'YES' if evaluation['output_available'] else 'NO'}"
        )

        print(
            "Risk Warning     : "
            f"{evaluation['risk_warning'] or 'NONE'}"
        )

        print(
            "\n============================================================"
        )
        print(
            "                  MISSION COMPLETED"
        )
        print(
            "============================================================"
        )

    else:
        print("\nSYSTEM STATUS")
        print("-------------")
        print("Status       : FALLBACK")

        print(
            "Risk Warning : "
            f"{output.get('risk_warning', 'Unknown warning')}"
        )

        print(
            "Reason       : "
            f"{output.get('reason', 'Unknown failure')}"
        )

        print("\nPARTIAL RESPONSE")
        print("----------------")

        partial_response = (
            output.get(
                "partial_response",
                {},
            )
        )

        for key, value in (
            partial_response.items()
        ):
            print(
                f"{key} : {value}"
            )

        print(
            "\n============================================================"
        )
        print(
            "                MISSION ENDED SAFELY"
        )
        print(
            "============================================================"
        )


# =========================================================
# INTERACTIVE MISSION INPUT
# =========================================================

def get_mission_input() -> str:
    """Request a simulated mission scenario from the user.

    Returns:
        Mission scenario entered through the terminal.
    """
    print(
        "\n============================================================"
    )
    print(
        "          THE ENTITY COUNTERMEASURE SYSTEM"
    )
    print(
        "============================================================"
    )

    print(
        "\nEnter a simulated mission scenario."
    )

    print(
        "The Dynamic Router will automatically "
        "classify the threat and select the workflow."
    )

    print(
        "\nExample LOW/MEDIUM:"
    )

    print(
        "The Entity produced a minor configuration "
        "warning on a monitored node."
    )

    print(
        "\nExample HIGH/CRITICAL:"
    )

    print(
        "The Entity is attempting a critical system "
        "override and emergency shutdown on Node 7."
    )

    print(
        "\n------------------------------------------------------------"
    )

    mission = input(
        "MISSION > "
    ).strip()

    return mission


# =========================================================
# MAIN PROGRAM
# =========================================================

def main() -> None:
    """Run The Entity MAS using interactive mission input."""
    user_input = get_mission_input()

    # Human modification:
    # Empty terminal input is rejected before any LLM call,
    # preventing unnecessary API usage and invalid routing.
    if not user_input:
        print(
            "\nERROR: Mission scenario cannot be empty."
        )
        return

    print(
        "\nAnalyzing mission and selecting "
        "the appropriate agent workflow..."
    )

    output = run_mas(
        user_input
    )

    display_final_report(
        output
    )


if __name__ == "__main__":
    main()