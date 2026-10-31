import pytest

from tools import prepare_powerbi


def model(folder, path="immutable_build/powerbi", measure="Customer Count", table="Customers"):
    target = folder / "BankingCustomerAnalytics.SemanticModel"
    definition = target / "definition"
    (definition / "tables").mkdir(parents=True)
    (definition / "expressions.tmdl").write_text(
        f'expression GoldDataPath = "{path}" meta [IsParameterQuery=true]\n'
    )
    (definition / "tables" / f"{table}.tmdl").write_text(
        f"table {table}\n\tmeasure '{measure}' = 1\n"
    )
    return target


def test_matching_cache_is_copied_without_modifying_original(tmp_path, monkeypatch):
    monkeypatch.setattr(prepare_powerbi, "PBI", tmp_path)
    source = model(tmp_path / ".local" / "saved")
    (source / ".pbi").mkdir()
    (source / ".pbi/cache.abf").write_bytes(b"trusted-local-cache")
    destination = tmp_path / ".local" / "prepared"
    model(destination)
    result = prepare_powerbi.restore_compatible_cache(destination)
    assert result["compatible_local_cache_restored"]
    assert (destination / source.name / ".pbi/cache.abf").read_bytes() == b"trusted-local-cache"
    assert (source / ".pbi/cache.abf").read_bytes() == b"trusted-local-cache"


@pytest.mark.parametrize(
    "difference", [{"path": "different_build/powerbi"}, {"measure": "Other"}, {"table": "Other"}]
)
def test_incompatible_cache_never_enters_prepared_project(tmp_path, monkeypatch, difference):
    monkeypatch.setattr(prepare_powerbi, "PBI", tmp_path)
    source = model(tmp_path / ".local" / "saved", **difference)
    (source / ".pbi").mkdir()
    (source / ".pbi/cache.abf").write_bytes(b"incompatible-cache")
    destination = tmp_path / ".local" / "prepared"
    target = model(destination)
    assert not prepare_powerbi.restore_compatible_cache(destination)[
        "compatible_local_cache_restored"
    ]
    assert not (target / ".pbi/cache.abf").exists()
