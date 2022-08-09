# Amazon Transcribe blockifier

This project contains a Steamship Blockifier that enables use of Amazon Transcribe to transcribe audio files into text.

## Configuration

This plugin must be configured with the following fields:

| Parameter | Description | DType | Required |
|-------------------|----------------------------------------------------|--------|--|
| aws_access_key_id | AWS Access key that grants access to s3 and Amazon Transcribe | string |Yes|
| aws_secret_access_key | AWS Secret Access key that grans access to s3 and Amazon Transcribe | string |Yes|
| aws_s3_bucket_name | S3 bucket where the audio file and transcript will be stored. | string |Yes|
| speaker_detection | Enable speaker detection | string |Yes|
| n_speakers | Expected number of speaker in the audio fragment. | string |Yes|
| aws_region | AWS Region where Amazon Transcribe will be invoked. | string |No|
| language_code | [Language identifier](https://docs.aws.amazon.com/transcribe/latest/dg/supported-languages.html) of
the dominant language spoken in the audio. | string |No|

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
from steamship import Steamship, Plugin, PluginInstance, File, Block, Tag, MimeTypes

PLUGIN_HANDLE = 'oneai-tagger'
PLUGIN_CONFIG = {
    "aws_access_key_id": "FILL_IN",
    "aws_secret_access_key": "FILL_IN",
    "aws_s3_bucket_name": "FILL_IN",
    "aws_region": "us-west-2",
    "language_code": "en-US"
}

steamship = Steamship(profile="staging")  # Without arguments, credentials in ~/.steamship.json will be used.
s2t_plugin = Plugin.get(client=steamship, handle=PLUGIN_HANDLE).data  # Managed globally by Steamship
s2t_plugin_instance = PluginInstance.create(
    client=steamship,
    plugin_id=s2t_plugin.id,
    config=PLUGIN_CONFIG
).data
audio_path = "FILL_IN"
file = File.create(steamship, filename=str(audio_path.resolve()), mime_type=MimeTypes.MP3).data
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
