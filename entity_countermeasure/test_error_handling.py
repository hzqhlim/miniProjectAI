"""Tests for the Entity MAS error-handling mechanisms."""

from safety import (
    call_external_service,
    get_state_value,
    parse_agent_json,
)


def test_invalid_json() -> None:
    """Test handling of malformed LLM JSON output."""
    print("\nTEST 1: Invalid JSON")

    try:
        parse_agent_json("{invalid json}")

    except ValueError as error:
        print(f"PASS: {error}")

    else:
        print("FAIL: Invalid JSON was not detected.")


def test_missing_state() -> None:
    """Test handling of a missing workflow state value."""
    print("\nTEST 2: Missing workflow state")

    try:
        get_state_value({}, "threat_level")

    except ValueError as error:
        print(f"PASS: {error}")

    else:
        print("FAIL: Missing workflow state was not detected.")


def disconnected_service() -> None:
    """Simulate an unavailable LLM or API connection."""
    raise ConnectionError(
        "Simulated Gemini API disconnection."
    )


def test_connection_failure() -> None:
    """Test handling of an LLM or API connection failure."""
    print("\nTEST 3: API Connection Failure")

    try:
        call_external_service(disconnected_service)

    except RuntimeError as error:
        print(f"PASS: {error}")

    else:
        print("FAIL: API connection failure was not detected.")


def main() -> None:
    """Run all error-handling tests."""
    print("===== ERROR HANDLING TESTS =====")

    test_invalid_json()
    test_missing_state()
    test_connection_failure()

    print("\n===== ALL TESTS COMPLETED =====")


if __name__ == "__main__":
    main()