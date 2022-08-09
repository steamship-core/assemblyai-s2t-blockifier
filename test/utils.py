"""Collection of utility function to support testing."""
import json
from test import TEST_DATA
from typing import Any, Dict
from steamship import Tag


def load_config() -> Dict[str, Any]:
    """Load config from test data."""
    return json.load((TEST_DATA / "config.json").open())


def verify_response(response, speaker_detection: bool) -> None:
    """Verify response from the blockifier."""
    assert response.data is not None
    assert response.data.file is not None
    file = response.data.file
    verify_file(file, speaker_detection)


def verify_file(file, speaker_detection: bool) -> None:
    """Verify the blockified file."""
    assert len(file.tags) == 0
    assert file.blocks is not None
    assert len(file.blocks) == 1
    assert file.blocks[0] is not None
    block = file.blocks[0]
    assert block.text is not None
    if speaker_detection:
        verify_block_tags(block)


def verify_block_tags(block):
    """Verify the block."""
    assert len(block.tags) > 0
    assert isinstance(block.tags[0], (Tag, Tag.CreateRequest))