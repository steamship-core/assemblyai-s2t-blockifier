# AssemblyAI Transcribe blockifier

This project contains a Steamship Blockifier that transcribes and analyzes audio files via AssemblyAI.

## Configuration

This plugin must be configured with the following fields:

| Parameter | Description | DType | Required |
|-------------------|----------------------------------------------------|--------|--|
| speaker_detection | Enable speaker detection | bool |True|
| enable_audio_intelligence | Enable Audio Intelligence (note that this incurs a higher cost) | True |

## Getting Started

### Usage

To authenticate with Steamship, install the Steamship CLI with:

```bash
> npm install -g @steamship/cli
```

And then login with:

```bash
> ship login
```

```python
from steamship import Steamship, PluginInstance, File, MimeTypes

PLUGIN_HANDLE = "assemblyai-s2t-blockifier"
PLUGIN_CONFIG = {
    "speaker_detection": True,
    "enable_audio_intelligence": True
}

client = Steamship(profile="staging")  # Without arguments, credentials in ~/.steamship.json will be used.
s2t_plugin_instance = PluginInstance.create(
    client, plugin_handle=PLUGIN_HANDLE, config=PLUGIN_CONFIG
).data
audio_path = "FILL_IN"
file = File.create(client, filename=str(audio_path.resolve()), mime_type=MimeTypes.MP3).data
tag_results = file.tag(plugin_instance=s2t_plugin_instance.handle)
tag_results.wait()

file = file.refresh().data
for block in file.blocks:
    print(block.text)
```

## Developing

Development instructions are located in [DEVELOPING.md](DEVELOPING.md)

## Testing

Testing instructions are located in [TESTING.md](TESTING.md)

## Deploying

Deployment instructions are located in [DEPLOYING.md](DEPLOYING.md)
