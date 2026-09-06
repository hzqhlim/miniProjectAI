"""Manual test for The Decoy custom tool."""

from agents.decoy_agent import (
    mock_network_traffic_generator,
)


def main() -> None:
    """Test the simulated Decoy traffic generator."""
    print(
        "\n===== DECOY TOOL TEST ====="
    )

    result = mock_network_traffic_generator.run(
        traffic_type="web",
        count=3,
    )

    print(result)


if __name__ == "__main__":
    main()