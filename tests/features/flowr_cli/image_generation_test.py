"""Tests for image generation story."""

import pytest


@pytest.mark.deprecated
@pytest.mark.skip(reason="image generation deferred to v2")
def test_flowr_cli_3ff0d648() -> None:
    """
    Given: a flow definition and the image rendering tool is available
    When: the developer runs the image command on that file
    Then: an image file is created on disk
    """


@pytest.mark.deprecated
@pytest.mark.skip(reason="image generation deferred to v2")
def test_flowr_cli_a3eecc07() -> None:
    """
    Given: a flow definition and the image rendering tool is not installed
    When: the developer runs the image command on that file
    Then: the output indicates the rendering tool is not available
    """
