import pytest


@pytest.mark.skip(reason="not yet implemented")
def test_export_mermaid_a2045d96() -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format mermaid examples/simple.yaml`
    Then the output is a valid Mermaid stateDiagram-v2 string identical to the previous `flowr mermaid` output
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_mermaid_67b1b50c() -> None:
    """
    Given a flow definition with guarded transitions
    When the user runs `flowr export --format mermaid --no-conditions examples/simple.yaml`
    Then the output is a valid stateDiagram-v2 without condition labels on transition edges
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_mermaid_2e068a23() -> None:
    """
    Given a directory `flows/` contains `alpha.yaml` and `beta.yaml`
    When the user runs `flowr export --format mermaid flows/`
    Then the output contains a stateDiagram-v2 for each flow separated by `---`
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_mermaid_1d5ba172() -> None:
    """
    When the user runs `flowr export --format json --help`
    Then the help text includes `--flat` and `--no-attrs` options
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_mermaid_0ce7099f() -> None:
    """
    When the user runs `flowr export --format mermaid --help`
    Then the help text includes `--no-conditions` option
    """
