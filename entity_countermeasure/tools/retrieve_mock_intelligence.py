"""Custom intelligence retrieval tool for the Infiltrator agent."""

import json
from pathlib import Path

from crewai.tools import tool


@tool("retrieve_mock_intelligence")
def retrieve_mock_intelligence(
    artifact_name: str,
    threat_level: str = "LOW",
) -> str:
    """Retrieve an authorized mock intelligence artifact.

    Args:
        artifact_name: Name of the simulated intelligence file located
            inside the project's data directory.
        threat_level: Threat classification provided by the router.
            Expected values are LOW, MEDIUM, HIGH, or CRITICAL.

    Returns:
        A JSON string containing the retrieval status, artifact name,
        intelligence summary, confidence score, risk level, and next step.

    The function is restricted to the local data directory and does not
    perform network access or interact with external systems.
    """
    try:
        data_directory = Path(__file__).resolve().parent.parent / "data"
        data_directory.mkdir(exist_ok=True)

        # Human modification: only the filename component is accepted so an
        # AI-generated tool call cannot escape the authorized local data folder.
        safe_name = Path(artifact_name).name

        artifact_path = data_directory / safe_name

        valid_levels = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

        # Human modification: the threat level is validated because an LLM
        # may return an unexpected label that could break downstream routing.
        normalized_threat = threat_level.upper().strip()

        if normalized_threat not in valid_levels:
            normalized_threat = "LOW"

        if not artifact_path.exists():
            raise FileNotFoundError(
                f"Simulated artifact '{safe_name}' was not found."
            )

        content = artifact_path.read_text(encoding="utf-8")

        return json.dumps(
            {
                "agent": "Infiltrator Specialist",
                "status": "success",
                "target_area": "Authorized simulated mission node",
                "artifact_name": safe_name,
                "intelligence_summary": content,
                "confidence_score": 95,
                "risk_level": normalized_threat,
                "next_step": "Send retrieved artifact to Analyzer Specialist",
            },
            indent=2,
        )

    except FileNotFoundError as error:
        return json.dumps(
            {
                "agent": "Infiltrator Specialist",
                "status": "failed",
                "target_area": "Authorized simulated mission node",
                "artifact_name": Path(artifact_name).name,
                "intelligence_summary": str(error),
                "confidence_score": 0,
                "risk_level": threat_level.upper().strip(),
                "next_step": "Activate fallback using available mission data",
            },
            indent=2,
        )

    except PermissionError as error:
        return json.dumps(
            {
                "agent": "Infiltrator Specialist",
                "status": "failed",
                "target_area": "Authorized simulated mission node",
                "artifact_name": Path(artifact_name).name,
                "intelligence_summary": f"Permission error: {error}",
                "confidence_score": 0,
                "risk_level": threat_level.upper().strip(),
                "next_step": "Activate fallback",
            },
            indent=2,
        )

    except OSError as error:
        return json.dumps(
            {
                "agent": "Infiltrator Specialist",
                "status": "failed",
                "target_area": "Authorized simulated mission node",
                "artifact_name": Path(artifact_name).name,
                "intelligence_summary": f"Local file error: {error}",
                "confidence_score": 0,
                "risk_level": threat_level.upper().strip(),
                "next_step": "Activate fallback",
            },
            indent=2,
        )