"""Test zendesk-blockifier via unit tests."""
from test import TEST_DATA
from test.utils import load_config, verify_response

import pytest as pytest
from steamship import MimeTypes, Tag
from steamship.plugin.inputs.raw_data_plugin_input import RawDataPluginInput
from steamship.plugin.service import PluginRequest

from src.api import AssemblyAIBlockifier


def _read_test_audio_file(filename: str) -> str:
    with (TEST_DATA / filename).open("rb") as f:
        return f.read()


@pytest.mark.parametrize("speaker_detection", (True, False))
def test_blockifier(speaker_detection):
    """Test Amazon Transcribe (S2T) Blockifier without edge cases."""
    config = load_config()
    config["speaker_detection"] = speaker_detection
    blockifier = AssemblyAIBlockifier(config=config)
    request = PluginRequest(
        data=RawDataPluginInput(
            data=_read_test_audio_file("test_conversation.mp3"), default_mime_type="audio/mp3"
        )
    )
    response = blockifier.run(request)

    verify_response(response, speaker_detection)

