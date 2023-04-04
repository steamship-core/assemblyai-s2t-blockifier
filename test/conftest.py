"""Set up testing environment."""
import pytest
from steamship import Steamship


@pytest.fixture
def steamship_client() -> Steamship:
    """Init steamship client."""
    return Steamship()
