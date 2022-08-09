"""Test zendesk-blockifier via integration tests."""

from test import TEST_DATA
from test.utils import load_config, verify_file
from typing import Any, Dict

import pytest
from steamship import File, Plugin, PluginInstance, Steamship
from steamship.base.mime_types import MimeTypes

BLOCKIFIER_HANDLE = "assemblyai-s2t-blockifier"
ENVIRONMENT = "prod"


def _get_plugin_instance(client: Steamship, handle: str, config: Dict[str, Any]) -> PluginInstance:
    plugin = Plugin.get(client, handle).data
    assert plugin is not None
    assert plugin.id is not None
    plugin_instance = PluginInstance.create(
        client, plugin_handle=handle, upsert=True, plugin_id=plugin.id, config=config
    ).data
    assert plugin_instance is not None
    assert plugin_instance.id is not None
    return plugin_instance


@pytest.mark.parametrize("speaker_detection", (True, False))
def test_blockifier(speaker_detection):
    """Test the Zendesk File Importer via an integration test."""
    client = Steamship(profile=ENVIRONMENT)
    config = load_config()
    config["speaker_detection"] = speaker_detection
    blockifier = _get_plugin_instance(client=client, handle=BLOCKIFIER_HANDLE, config=config)
    audio_path = TEST_DATA / "test_conversation.mp3"
    file = File.create(client, filename=str(audio_path.resolve()), mime_type=MimeTypes.MP3).data
    file.blockify(plugin_instance=blockifier.handle).wait(max_timeout_s=600, retry_delay_s=60)
    file = file.refresh().data

    verify_file(file, speaker_detection)
