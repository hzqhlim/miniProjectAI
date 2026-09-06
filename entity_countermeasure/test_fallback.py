"""Fallback timing test for the Entity MAS."""

import time

from safety import run_with_fallback


def simulated_infinite_agent() -> str:
    """Simulate an agent that becomes stuck for testing purposes.

    Returns:
        A completion message if the simulated delay finishes.
    """
    time.sleep(20)

    return "Agent unexpectedly completed."


def main() -> None:
    """Run the fallback timing demonstration."""
    partial_data = {
        "router_status": "completed",
        "threat_level": "HIGH",
        "available_evidence": "Partial mission evidence retained",
    }

    start_time = time.perf_counter()

    result = run_with_fallback(
        operation=simulated_infinite_agent,
        partial_data=partial_data,
        timeout_seconds=4.0,
    )

    elapsed = time.perf_counter() - start_time

    print("\n========== FALLBACK TEST ==========")
    print(result)

    print(
        f"\nFallback response time: "
        f"{elapsed:.2f} seconds"
    )

    fallback_triggered = (
        result.get("status") == "fallback"
    )

    if elapsed < 5 and fallback_triggered:
        print(
            "RESULT: PASS - fallback activated "
            "under 5 seconds."
        )

    else:
        print(
            "RESULT: FAIL - fallback requirement "
            "was not satisfied."
        )


if __name__ == "__main__":
    main()