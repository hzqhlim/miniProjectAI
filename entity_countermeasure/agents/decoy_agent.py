"""Define The Decoy agent and its simulated traffic-generation tool."""

import json

from crewai import Agent, Task
from crewai.tools import tool
from pydantic import BaseModel


class DecoyOutput(BaseModel):
    """Define the required structured output from The Decoy."""

    decoy_type: str
    objective: str
    simulated_activity: list[str]
    defensive_value: str


@tool("mock_network_traffic_generator")
def mock_network_traffic_generator(
    traffic_type: str,
    count: int = 3,
) -> str:
    """Generate harmless simulated traffic for defensive testing.

    Args:
        traffic_type: Type of synthetic traffic to generate.
        count: Number of synthetic traffic records to generate.

    Returns:
        JSON string containing harmless simulated traffic records.

    This tool performs simulation only. It does not connect to networks,
    send packets, scan systems, or interact with external infrastructure.
    """
    try:
        if count < 1:
            raise ValueError(
                "count must be at least 1."
            )

        if count > 10:
            count = 10

        allowed_types = {
            "web",
            "dns",
            "authentication",
            "generic",
        }

        normalized_type = (
            traffic_type.lower().strip()
        )

        # Human modification: unexpected LLM traffic labels are converted
        # to a safe generic simulation instead of causing tool failure.
        if normalized_type not in allowed_types:
            normalized_type = "generic"

        records = []

        # Human modification: all records are fictional and local-only so
        # the project demonstrates tool use without touching real systems.
        for index in range(
            1,
            count + 1,
        ):
            records.append(
                {
                    "record_id": index,
                    "traffic_type": normalized_type,
                    "source": (
                        f"SIMULATED_SOURCE_{index}"
                    ),
                    "destination": (
                        "SIMULATED_DECOY_NODE"
                    ),
                    "status": "synthetic",
                }
            )

        return json.dumps(
            {
                "status": "success",
                "simulation_only": True,
                "records": records,
            },
            indent=2,
        )

    except ValueError as error:
        return json.dumps(
            {
                "status": "failed",
                "simulation_only": True,
                "error": str(error),
                "records": [],
            },
            indent=2,
        )

    except TypeError as error:
        return json.dumps(
            {
                "status": "failed",
                "simulation_only": True,
                "error": (
                    f"Invalid tool argument: {error}"
                ),
                "records": [],
            },
            indent=2,
        )

    except Exception as error:
        return json.dumps(
            {
                "status": "failed",
                "simulation_only": True,
                "error": (
                    f"Unexpected simulation error: "
                    f"{error}"
                ),
                "records": [],
            },
            indent=2,
        )


decoy_agent = Agent(
    role="Decoy Specialist",
    goal=(
        "Create harmless synthetic defensive telemetry "
        "for HIGH or CRITICAL simulated threats."
    ),
    backstory=(
        "You are The Decoy, a tactical deception "
        "specialist in a simulated cyber-defense team "
        "fighting a fictional rogue AI called The Entity. "
        "You generate only harmless synthetic telemetry. "
        "You never access, scan, attack, spoof, or contact "
        "real systems or external infrastructure."
    ),
    tools=[
        mock_network_traffic_generator,
    ],
    verbose=True,
    allow_delegation=False,
    max_iter=3,
    max_execution_time=30,
    max_retry_limit=3,
    memory=False,
    cache=True,
)


decoy_task = Task(
    description=(
        "Mission:\n"
        "{user_input}\n\n"
        "Threat level: {threat_level}\n"
        "Selected route: {route}\n\n"

        "Create one harmless simulated defensive decoy.\n\n"

        "You MUST call mock_network_traffic_generator "
        "exactly once using:\n"
        "traffic_type = generic\n"
        "count = 3\n\n"

        "After using the tool, return ONLY valid JSON "
        "with exactly these keys:\n"
        "- decoy_type\n"
        "- objective\n"
        "- simulated_activity\n"
        "- defensive_value\n\n"

        "Few-shot Example 1\n"
        "Input: A simulated hostile AI scans web services.\n"
        "Output:\n"
        "{{\n"
        '  "decoy_type": "fake_web_service",\n'
        '  "objective": "Divert simulated scanning",\n'
        '  "simulated_activity": [\n'
        '    "Generate synthetic web traffic"\n'
        "  ],\n"
        '  "defensive_value": '
        '"Safe defensive telemetry"\n'
        "}}\n\n"

        "Few-shot Example 2\n"
        "Input: A simulated hostile process attempts "
        "authentication.\n"
        "Output:\n"
        "{{\n"
        '  "decoy_type": "fake_auth_service",\n'
        '  "objective": '
        '"Observe simulated authentication behavior",\n'
        '  "simulated_activity": [\n'
        '    "Generate synthetic login traffic"\n'
        "  ],\n"
        '  "defensive_value": '
        '"Safe behavioral evidence"\n'
        "}}\n\n"

        "Do not output Markdown.\n"
        "Do not add explanations outside the JSON.\n"
        "Do not interact with real systems."
    ),
    expected_output=(
        "A valid JSON object containing exactly "
        "decoy_type, objective, simulated_activity, "
        "and defensive_value."
    ),
    agent=decoy_agent,
    output_pydantic=DecoyOutput,
)