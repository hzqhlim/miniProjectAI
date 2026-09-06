"""Manual tests for the Infiltrator custom tool."""

from tools.retrieve_mock_intelligence import retrieve_mock_intelligence


def test_successful_retrieval() -> None:
    """Test successful retrieval of the mock intelligence artifact."""
    print("\n===== SUCCESSFUL RETRIEVAL TEST =====")

    result = retrieve_mock_intelligence.run(
        artifact_name="entity_fragment.txt",
        threat_level="HIGH",
    )

    print(result)


def test_missing_artifact() -> None:
    """Test safe handling of a missing intelligence artifact."""
    print("\n===== MISSING ARTIFACT TEST =====")

    result = retrieve_mock_intelligence.run(
        artifact_name="missing_file.txt",
        threat_level="HIGH",
    )

    print(result)


def main() -> None:
    """Run the Infiltrator custom-tool tests."""
    test_successful_retrieval()
    test_missing_artifact()


if __name__ == "__main__":
    main()