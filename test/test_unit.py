"""Test assemblyai-s2t-blockifier via unit tests."""
from time import perf_counter

import requests

from test import TEST_DATA
from test.utils import load_config, verify_response

import pytest as pytest
from steamship import Steamship
from steamship.base import TaskState
from steamship.plugin.inputs.raw_data_plugin_input import RawDataPluginInput
from steamship.plugin.request import PluginRequest

from src.api import AssemblyAIBlockifier

ENVIRONMENT = "prod"


def _read_test_audio_file(filename: str) -> str:
    with (TEST_DATA / filename).open("rb") as f:
        return f.read()


@pytest.mark.parametrize("speaker_detection", (True, False))
def test_blockifier(speaker_detection: bool):
    """Test AssemblyAI (S2T) Blockifier without edge cases."""
    config = load_config()
    client = Steamship(profile=ENVIRONMENT)
    config["speaker_detection"] = speaker_detection
    blockifier = AssemblyAIBlockifier(client=client, config=config)
    request = PluginRequest(
        data=RawDataPluginInput(
            data=_read_test_audio_file("test_conversation.mp3"), default_mime_type="audio/mp3"
        )
    )
    response = blockifier.run(request)

    assert response.status.state == TaskState.running
    assert response.status.remote_status_input.get("transcription_id") is not None

    while response.status.state == TaskState.running:
        request = PluginRequest(
            is_status_check=True,
            status=response.status,
        )
        response = blockifier.run(request)

    verify_response(response)


@pytest.mark.parametrize("speaker_detection", (True, False))
def test_blockifier_new(speaker_detection: bool):
    """Test AssemblyAI (S2T) Blockifier without edge cases."""
    config = load_config()
    config = {**config, "enable_audio_intelligence":False, "speaker_detection":False}
    client = Steamship(profile=ENVIRONMENT)
    config["speaker_detection"] = speaker_detection
    blockifier = AssemblyAIBlockifier(client=client, config=config)
    request = PluginRequest(
        data=RawDataPluginInput(
            data=requests.get("https://api.telegram.org/file/bot5700318507:AAFx4Y_ibuXr9KlYZ4sUqmH7hoCHWjtuyMc/voice/file_6.oga").content
        )
    )
    t0 = perf_counter()
    response = blockifier.run(request)

    assert response.status.state == TaskState.running
    assert response.status.remote_status_input.get("transcription_id") is not None

    while response.status.state == TaskState.running:
        request = PluginRequest(
            is_status_check=True,
            status=response.status,
        )
        response = blockifier.run(request)


    t1 = perf_counter() - t0
    verify_response(response)