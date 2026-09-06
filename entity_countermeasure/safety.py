"""Safety and fallback utilities for the Entity MAS."""

import json
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any, Callable


def parse_agent_json(raw_response: str) -> dict[str, Any]:
    """Parse an agent response into a Python dictionary.

    Args:
        raw_response: Raw JSON string returned by an agent.

    Returns:
        Parsed response as a dictionary.

    Raises:
        ValueError: If the response is not valid JSON.
    """
    # Human modification: explicit JSON handling prevents malformed
    # LLM output from crashing the whole multi-agent workflow.
    try:
        return json.loads(raw_response)

    except json.JSONDecodeError as error:
        raise ValueError(
            f"Agent returned invalid JSON: {error}"
        ) from error


def get_state_value(state: dict[str, Any], key: str) -> Any:
    """Safely obtain a required value from the workflow state.

    Args:
        state: Current multi-agent workflow state.
        key: Required dictionary key.

    Returns:
        Value stored under the requested key.

    Raises:
        ValueError: If the required state value does not exist.
    """
    # Human modification: state validation prevents downstream agents
    # from using missing outputs from an earlier failed agent.
    try:
        return state[key]

    except KeyError as error:
        raise ValueError(
            f"Required workflow state '{key}' is missing."
        ) from error


def call_external_service(service_call: Callable[[], Any]) -> Any:
    """Execute a model or service call with connection protection.

    Args:
        service_call: Function that performs the service or API request.

    Returns:
        Result produced by the service.

    Raises:
        RuntimeError: If a connection failure occurs.
    """
    # Human modification: API disconnections are converted into a
    # controlled exception so the fallback system can respond safely.
    try:
        return service_call()

    except ConnectionError as error:
        raise RuntimeError(
            "LLM/API connection was interrupted."
        ) from error


def run_with_fallback(
    operation: Callable[[], Any],
    partial_data: dict[str, Any] | None = None,
    timeout_seconds: float = 4.0,
) -> dict[str, Any]:
    """Run an operation and return a safe fallback if it fails.

    Args:
        operation: Agent or tool operation to execute.
        partial_data: Successfully processed information already available.
        timeout_seconds: Maximum time to wait before activating fallback.

    Returns:
        Successful operation result or a risk-warning fallback dictionary.
    """
    available_data = partial_data or {}

    # Human modification: a 4-second default was selected to provide a
    # safety margin below the assignment's required 5-second fallback time.
    executor = ThreadPoolExecutor(max_workers=1)

    future = executor.submit(operation)

    try:
        result = future.result(timeout=timeout_seconds)

        return {
            "status": "success",
            "result": result,
        }

    except TimeoutError:
        future.cancel()

        # Human modification: partial workflow data is preserved so a failed
        # later-stage agent does not discard useful results from earlier stages.
        return {
            "status": "fallback",
            "risk_warning": "Agent exceeded the safe execution window.",
            "reason": "TIMEOUT",
            "partial_response": available_data,
        }

    except (ConnectionError, RuntimeError) as error:
        return {
            "status": "fallback",
            "risk_warning": "Agent or LLM connection failed.",
            "reason": str(error),
            "partial_response": available_data,
        }

    except Exception as error:
        return {
            "status": "fallback",
            "risk_warning": "Unexpected agent/tool failure.",
            "reason": str(error),
            "partial_response": available_data,
        }

    finally:
        executor.shutdown(
            wait=False,
            cancel_futures=True,
        )