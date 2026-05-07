import pytest


@pytest.mark.skip(reason="not yet implemented")
def test_export_json_f8eb4019() -> None:
    """
    Given a flow `main.yaml` references a subflow via `flow: child`
    When the user runs `flowr export --format json main.yaml`
    Then the output contains separate flow entries for `main` and `child`, and a `defaultFlow` key indicating the root
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_json_7187f2ad() -> None:
    """
    Given a flow `main.yaml` references a subflow via `flow: child`
    When the user runs `flowr export --format json --flat main.yaml`
    Then all subflow states are merged into the root flow's nodes list with prefixed IDs
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_json_f79514e5() -> None:
    """
    Given a flow definition with states containing `attrs`
    When the user runs `flowr export --format json --no-attrs examples/simple.yaml`
    Then the output JSON omits the `attrs` field from all nodes
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_json_99a274dd() -> None:
    """
    Given a directory `flows/` contains `alpha.yaml` and `beta.yaml`
    When the user runs `flowr export --format json flows/`
    Then the output is a JSON array of flow entries sorted alphabetically, with a top-level `defaultFlow` key
    """
