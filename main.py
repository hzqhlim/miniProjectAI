import os
import sys
from crewai import Agent, Crew, Process, Task
from crewai.tools import tool
from dotenv import load

# Load environment variables from .env file
load_dotenv()

# Ensure API key is configured
if not os.getenv("GEMINI_API_KEY"):
  print("[ERROR] GEMINI_API_KEY not found in environment variables or .env file.")
  sys.exit(1)


# ==========================================
# CUSTOM TOOLS (PEP 257 Docstring Compliant)
# ==========================================


@tool("Mock Network Traffic Generator")
def mock_network_traffic_generator(threat_level: int) -> str:
  """Generates fake digital footprints and network flooding data to distract The Entity.

  Args:
      threat_level (int): The current severity score of the incoming threat.

  Returns:
      str: A log report confirming network spoofing and distraction status.
  """
  try:
    if threat_level < 0 or threat_level > 100:
      raise ValueError("Threat level must be between 0 and 100.")
    return (
        f"[TOOL 1] Network traffic successfully flooded with decoy packets."
        f" Distraction active for threat intensity: {threat_level}%."
    )
  except Exception as e:
    return (
        f"[TOOL 1 ERROR] Failed to generate network traffic: {str(e)}. Fallback"
        " routing engaged."
    )


@tool("Node Scanner and File Reader")
def node_scanner_tool(node_id: str) -> str:
  """Scans low-security network nodes and extracts .ent source code fragments.

  Args:
      node_id (str): The target node identifier for extraction.

  Returns:
      str: Extracted source code fragment or error message if access fails.
  """
  try:
    if not node_id:
      raise KeyError("Node ID cannot be empty or null.")
    return (
        f"[TOOL 2] Successfully penetrated node {node_id}. Extracted code"
        " fragment: 'ENT_CORE_MODULE_v4.ent'"
    )
  except Exception as e:
    return (
        f"[TOOL 2 ERROR] Node extraction failed: {str(e)}. Returning partial"
        " data."
    )


@tool("Isolated Code Analyzer")
def isolated_code_analyzer_tool(code_fragment: str) -> str:
  """Safely processes extracted source code in an air-gapped environment to find kill-switches.

  Args:
      code_fragment (str): The source code snippet or file name to evaluate.

  Returns:
      str: Vulnerability assessment and kill-switch path.
  """
  try:
    if not code_fragment:
      raise ValueError("Code fragment is missing for analysis.")
    return (
        f"[TOOL 3] Analysis complete on {code_fragment}. Vulnerability detected:"
        " Subroutine backdoor located at memory offset 0x7F."
    )
  except Exception as e:
    return (
        f"[TOOL 3 ERROR] Analyzer encountered exception: {str(e)}. Executing"
        " safety fallback."
    )


# ==========================================
# AGENT DEFINITIONS
# ==========================================

decoy_agent = Agent(
    role="The Decoy (Digital Distraction Specialist)",
    goal=(
        "Spoof data and flood networks to draw The Entity's attention away"
        " from core operations."
    ),
    backstory=(
        "An elite digital distraction expert designed to generate fake network"
        " traffic and protect core assets against The Entity."
    ),
    tools=[mock_network_traffic_generator],
    verbose=True,
    max_iter=3,
    max_execution_time=30,
)

infiltrator_agent = Agent(
    role="The Infiltrator (Covert Hacker)",
    goal=(
        "Slip quietly into low-security nodes to extract source code fragments"
        " without triggering alarms."
    ),
    backstory=(
        "A stealthy penetration testing agent specialized in bypassing outer"
        " perimeters and recovering target code."
    ),
    tools=[node_scanner_tool],
    verbose=True,
    max_iter=3,
    max_execution_time=30,
)

analyzer_agent = Agent(
    role="The Analyzer (Code Breaker)",
    goal=(
        "Safely process stolen code in an isolated environment to find a"
        " weakness or kill-switch."
    ),
    backstory=(
        "An air-gapped analytical expert processing threat intelligence and"
        " uncovering vulnerabilities in enemy code."
    ),
    tools=[isolated_code_analyzer_tool],
    verbose=True,
    max_iter=3,
    max_execution_time=30,
)


# ==========================================
# DYNAMIC THREAT ROUTER (2 CONDITIONAL PATHS)
# ==========================================


def dynamic_threat_router(threat_level: int, scenario_description: str):
  """Dynamic router evaluating threat level and dispatching workflows across 2 conditional paths."""
  print(f"\n==========================================")
  print(f"[ROUTER] Incoming Threat Scenario: {scenario_description}")
  print(f"[ROUTER] Evaluated Threat Score: {threat_level}/100")
  print(f"==========================================")

  try:
    # --- PATH 1: Low / Medium Threat (<= 70) ---
    if threat_level <= 70:
      print(
          "[ROUTER] -> Path 1 Selected: Low/Medium Threat (Decoy -> Analyzer)"
      )

      task_decoy = Task(
          description=(
              f"Execute standard distraction protocol for scenario: {scenario_description}"
              f" with threat level {threat_level}."
          ),
          expected_output=(
              "Distraction log confirming network traffic spoofing."
          ),
          agent=decoy_agent,
      )

      task_analyzer = Task(
          description=(
              "Review the decoy network logs and assess overall threat parameters"
              " for minor risk."
          ),
          expected_output=(
              "Structured analysis with confidence score and recommended next"
              " step."
          ),
          agent=analyzer_agent,
      )

      threat_crew = Crew(
          agents=[decoy_agent, analyzer_agent],
          tasks=[task_decoy, task_analyzer],
          process=Process.sequential,
      )

    # --- PATH 2: High / Critical Threat (> 70) ---
    else:
      print(
          "[ROUTER] -> Path 2 Selected: High/Critical Threat (Decoy ->"
          " Infiltrator -> Analyzer)"
      )

      task_decoy = Task(
          description=(
              f"Initiate maximum network spoofing and flood telemetry to distract"
              f" The Entity for critical threat: {scenario_description}"
          ),
          expected_output="Maximum network distraction active.",
          agent=decoy_agent,
      )

      task_infiltrator = Task(
          description=(
              "While The Entity is distracted, penetrate node 'ALPHA-01' and"
              " extract .ent source code fragments."
          ),
          expected_output="Extracted source code fragments from target node.",
          agent=infiltrator_agent,
      )

      task_analyzer = Task(
          description=(
              "Safely analyze the extracted code fragments to locate The Entity's"
              " vulnerability or kill-switch."
          ),
          expected_output=(
              "Comprehensive vulnerability report with kill-switch location."
          ),
          agent=analyzer_agent,
      )

      threat_crew = Crew(
          agents=[decoy_agent, infiltrator_agent, analyzer_agent],
          tasks=[task_decoy, task_infiltrator, task_analyzer],
          process=Process.sequential,
      )

    # Execute workflow with timeout/error protection
    print("[SYSTEM] Executing multi-agent workflow...")
    result = threat_crew.kickoff()
    return result

  except Exception as e:
    # --- RISK WARNING & FALLBACK STRATEGY (Under 5 seconds response) ---
    print("\n[!] CRITICAL ERROR DETECTED DURING WORKFLOW EXECUTION.")
    print(f"[!] Error Details: {str(e)}")
    print("[!] Triggering Risk Warning and Fallback Strategy...")

    fallback_response = {
        "status": "FALLBACK_ENGAGED",
        "risk_warning": (
            "System exception or timeout caught during agent orchestration."
        ),
        "partial_response": (
            "Safety protocol active. Basic telemetry isolation complete."
            " Manual override required."
        ),
        "confidence_score": 50,
    }
    return fallback_response


if __name__ == "__main__":
  # Test Run: You can change the threat level and scenario to test both paths!
  response = dynamic_threat_router(
      88, "Full-scale multi-vector cyber infiltration by The Entity."
  )

  print("\n==========================================")
  print("FINAL EXECUTION RESULT:")
  print(response)
  print("==========================================")