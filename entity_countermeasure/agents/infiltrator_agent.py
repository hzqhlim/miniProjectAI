"""Define The Infiltrator agent and its simulated retrieval task."""

from crewai import Agent, Task

from tools.retrieve_mock_intelligence import retrieve_mock_intelligence


infiltrator_agent = Agent(
    role="Infiltrator Specialist",
    goal=(
        "Retrieve authorized simulated intelligence artifacts from the "
        "controlled mission environment after receiving Router or Decoy "
        "context. Pass retrieved evidence to the Analyzer Specialist. "
        "Never access real external systems."
    ),
    backstory=(
        "You are The Infiltrator, a stealth intelligence-retrieval "
        "specialist operating within an isolated cyber-defense simulation "
        "against a rogue AI called The Entity. You retrieve only mock "
        "artifacts supplied inside the project. You never perform real "
        "exploitation, credential theft, network intrusion, or external "
        "system access. If evidence is unavailable, report the failure "
        "instead of inventing information."
    ),
    tools=[retrieve_mock_intelligence],
    verbose=True,
    allow_delegation=False,
    max_iter=5,
    max_execution_time=30,
    max_retry_limit=3,
    memory=False,
    cache=True,
)


infiltrator_task = Task(
    description=(
        "The Dynamic Router classified the mission as {threat_level} "
        "using route {route}.\n\n"
        "Original mission:\n"
        "{user_input}\n\n"
        "Retrieve the authorized simulated intelligence artifact named "
        "'entity_fragment.txt' using retrieve_mock_intelligence.\n\n"
        "When calling the tool use:\n"
        "artifact_name = entity_fragment.txt\n"
        "threat_level = {threat_level}\n\n"
        "If a Decoy task was executed before this task, use its output as "
        "additional mission context. The Decoy output does not authorize "
        "any external access.\n\n"
        "You MUST return valid JSON only with exactly these keys:\n"
        "- agent\n"
        "- status\n"
        "- target_area\n"
        "- artifact_name\n"
        "- intelligence_summary\n"
        "- confidence_score\n"
        "- risk_level\n"
        "- next_step\n\n"
        "Do not output Markdown or additional text outside the JSON."
    ),
    expected_output=(
        "A valid JSON object containing exactly agent, status, "
        "target_area, artifact_name, intelligence_summary, "
        "confidence_score, risk_level, and next_step."
    ),
    agent=infiltrator_agent,
)