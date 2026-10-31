import copy

import pandas as pd
import pytest

from src.contracts.validate import contract, evolution, validate
from src.platform.errors import ContractViolationError


@pytest.fixture
def spec():
    return {
        "dataset": "events",
        "contract_version": "1.0",
        "primary_key": ["id"],
        "allow_extra_columns": False,
        "fields": {
            "id": {"type": "string", "nullable": False},
            "count": {"type": "integer", "min": 0, "nullable": False},
            "kind": {"type": "string", "allowed_values": ["A", "B"], "nullable": False},
            "date": {"type": "date", "nullable": False},
        },
    }


@pytest.fixture
def data():
    return pd.DataFrame(
        {
            "id": ["one", "two"],
            "count": [1, 2],
            "kind": ["A", "B"],
            "date": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        }
    )


def test_full_contract_and_version(spec, data):
    assert validate(data, spec, version="1.0")["status"] == "PASS"
    with pytest.raises(ContractViolationError):
        validate(data, spec, version="2.0")
    with pytest.raises(ContractViolationError):
        validate(data, spec)


@pytest.mark.parametrize(
    "problem", ["missing", "type", "null", "duplicate", "category", "date", "range", "extra"]
)
def test_contract_failure_modes(spec, data, problem):
    if problem == "missing":
        data = data.drop(columns="id")
    if problem == "type":
        data["count"] = ["x", "y"]
    if problem == "null":
        data.loc[0, "id"] = None
    if problem == "duplicate":
        data.loc[1, "id"] = "one"
    if problem == "category":
        data.loc[1, "kind"] = "C"
    if problem == "date":
        data["date"] = ["2026/01/01", "not-a-date"]
    if problem == "range":
        data.loc[1, "count"] = -1
    if problem == "extra":
        data["unexpected"] = 0
    with pytest.raises(ContractViolationError):
        validate(data, spec, version="1.0")


def test_structural_only_does_not_publish_bad_rows(spec, data):
    data.loc[1, "count"] = -1
    assert validate(data, spec, version="1.0", structural_only=True)["scope"] == "structure"
    with pytest.raises(ContractViolationError):
        validate(data, spec, version="1.0")


def test_schema_evolution(spec):
    changed = copy.deepcopy(spec)
    changed["fields"]["optional"] = {"type": "string", "required": False, "nullable": True}
    assert evolution(spec, changed)["classification"] == "Non-Breaking"
    for change in ["remove", "type", "key", "required", "narrow"]:
        changed = copy.deepcopy(spec)
        if change == "remove":
            changed["fields"].pop("id")
        if change == "type":
            changed["fields"]["count"]["type"] = "string"
        if change == "key":
            changed["primary_key"] = ["kind"]
        if change == "required":
            changed["fields"]["new"] = {"type": "string"}
        if change == "narrow":
            changed["fields"]["count"]["min"] = 1
        assert evolution(spec, changed)["classification"] == "Breaking"


@pytest.mark.parametrize(
    "name",
    [
        "customers",
        "products",
        "payroll",
        "campaigns",
        "digital_interactions",
        "services",
        "customer_satisfaction",
    ],
)
def test_seven_owned_versioned_contracts(name):
    c = contract(name)
    assert c["contract_version"] == "1.0" and c["owner"] and c["primary_key"] and c["fields"]
