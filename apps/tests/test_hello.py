"""Hello unit test module."""

from ai.hello import hello


def test_hello():
    """Test the hello function."""
    assert hello() == "Hello ai"
