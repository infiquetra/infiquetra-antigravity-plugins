"""Closed Antigravity workflow vocabulary and compatibility checks."""

from __future__ import annotations

from collections.abc import Mapping

WORKFLOW_SCHEMA = "antigravity.workflow-contract.v1"
WORKFLOW_KINDS = frozenset({"implementation", "remediation", "review", "test"})


def validate_workflow_contract(contract: object) -> list[str]:
    if not isinstance(contract, Mapping):
        return ["workflow contract must be an object"]
    errors: list[str] = []
    if set(contract) != {"schema", "kind", "inputs", "outputs"}:
        errors.append("workflow contract has unknown or missing fields")
    if contract.get("schema") != WORKFLOW_SCHEMA:
        errors.append("workflow contract schema is incompatible")
    if contract.get("kind") not in WORKFLOW_KINDS:
        errors.append("workflow kind is not in the target vocabulary")
    for field in ("inputs", "outputs"):
        values = contract.get(field)
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value for value in values)
            or len(values) != len(set(values))
        ):
            errors.append(f"{field} must be a non-empty unique string list")
    inputs = contract.get("inputs")
    outputs = contract.get("outputs")
    values = [*inputs, *outputs] if isinstance(inputs, list) and isinstance(outputs, list) else []
    if any(isinstance(value, str) and value.endswith("-execution") for value in values):
        errors.append("workflow contract contains a source package identity")
    return errors


def compatible(producer: Mapping[str, object], consumer: Mapping[str, object]) -> bool:
    if validate_workflow_contract(producer) or validate_workflow_contract(consumer):
        return False
    producer_outputs = producer["outputs"]
    consumer_inputs = consumer["inputs"]
    assert isinstance(producer_outputs, list)
    assert isinstance(consumer_inputs, list)
    return (
        producer["schema"] == consumer["schema"]
        and producer["kind"] == consumer["kind"]
        and set(producer_outputs) >= set(consumer_inputs)
    )
