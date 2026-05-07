import pytest


@pytest.mark.skip(reason="not yet implemented")
def test_export_core_8ababd33() -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format json examples/simple.yaml`
    Then the command delegates to the json adapter with exit code 0
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_core_6c684a46() -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format xml examples/simple.yaml`
    Then the command prints an error to stderr listing available formats and exits with code 1
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_core_43d8849f() -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export examples/simple.yaml`
    Then the command prints a usage error to stderr and exits with code 2
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_core_d0169acb() -> None:
    """
    Given no file exists at `nonexistent.yaml`
    When the user runs `flowr export --format json nonexistent.yaml`
    Then the command prints an error to stderr stating the path does not exist and exits with code 1
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_core_3c8f8a0a() -> None:
    """
    Given a flow definition file exists at `examples/simple.yaml`
    When the user runs `flowr export --format json examples/simple.yaml`
    Then the adapter's `export()` method is called with the loaded flow
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_core_e4152bc9() -> None:
    """
    Given a directory `flows/` contains multiple `.yaml` files
    When the user runs `flowr export --format json flows/`
    Then the adapter's `export_directory()` method is called with all loaded flows sorted alphabetically by filename
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_core_19cb145b() -> None:
    """
    Given the flowr CLI is installed
    When the user runs `flowr mermaid examples/simple.yaml`
    Then the command prints a usage error to stderr and exits with code 2
    """


@pytest.mark.skip(reason="not yet implemented")
def test_export_core_dad5b532() -> None:
    """
    Given the flowr package is imported
    Then the EXPORTERS dict contains keys `"json"` and `"mermaid"` mapping to their respective adapter instances
    """
