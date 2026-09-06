"""Test The Decoy agent independently before MAS integration."""

import os

from crewai import Crew, LLM, Process
from dotenv import load_dotenv

from agents.decoy_agent import (
    decoy_agent,
    decoy_task,
)


def main() -> None:
    """Execute the standalone Decoy-agent test."""
    load_dotenv()

    gemini_api_key = os.getenv("GEMINI_API_KEY")

    if not gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY was not found in the .env file."
        )

    # Gemini 3.6 Flash with the rubric-required timeout/retry limits.
    gemini_llm = LLM(
    model="gemini/gemini-3.6-flash",
    api_key=gemini_api_key,
    timeout=30,
    max_retries=3,
    temperature=0.3,
)

    decoy_agent.llm = gemini_llm

    decoy_crew = Crew(
        agents=[
            decoy_agent,
        ],
        tasks=[
            decoy_task,
        ],
        process=Process.sequential,
        verbose=True,
    )

    test_scenario = (
        "A simulated hostile AI is aggressively scanning a "
        "protected environment and showing signs of a critical "
        "compromise. Create a harmless synthetic decoy for "
        "defensive observation."
    )

    print(
        "\n========================================"
    )
    print(
        "       THE DECOY AGENT TEST"
    )
    print(
        "========================================"
    )

    result = decoy_crew.kickoff(
        inputs={
            "user_input": test_scenario,
            "threat_level": "HIGH",
            "route": "HIGH_CRITICAL",
        }
    )

    print(
        "\n========================================"
    )
    print(
        "       DECOY AGENT RESULT"
    )
    print(
        "========================================\n"
    )

    print(result)


if __name__ == "__main__":
    main()