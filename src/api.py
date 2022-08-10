"""Zendesk ticket blockifier.

A JSON file containing a list of tickets (produced by the zendesk-file-importer) is loaded
 and parsed into a list of blocks. Each block contains one or more tags extracted from the
 fields reference in the config.
"""
import io
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Type
from uuid import uuid4

import boto3
import requests
from steamship import Block, File, SteamshipError, Tag
from steamship.app import Response, create_handler
from steamship.base.mime_types import MimeTypes
from steamship.plugin.blockifier import Blockifier, Config
from steamship.plugin.inputs.raw_data_plugin_input import RawDataPluginInput
from steamship.plugin.outputs.block_and_tag_plugin_output import BlockAndTagPluginOutput
from steamship.plugin.service import PluginRequest


class AssemblyAIBlockifierConfig(Config):
    """Config object containing required configuration parameters to initialize a AmazonTranscribeBlockifier."""

    aws_access_key_id: str
    aws_secret_access_key: str
    aws_s3_bucket_name: str
    assembly_ai_api_token: str
    speaker_detection: bool = True
    enable_audio_intelligence: bool = True
    language_code: str = "en-US"
    max_retries: int = 60
    retry_timeout: int = 10


class TranscribeJobStatus(str, Enum):
    """Status of the transcription task."""

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


SUPPORTED_MIME_TYPES = (
    MimeTypes.MP3,
    MimeTypes.WAV,
    "video/mp4",
    "audio/mp4",
    "audio/webm",
    "video/webm",
)
BASE_URL = "https://api.assemblyai.com/v2"


class AssemblyAIBlockifier(Blockifier):
    """Blockifier that transcribes audio files into blocks.

    Attributes
    ----------
    config : AssemblyAIBlockifierConfig
        The required configuration used to instantiate a amazon-s2t-blockifier
    """

    config: AssemblyAIBlockifierConfig

    def config_cls(self) -> Type[Config]:
        """Return the Configuration class."""
        return AssemblyAIBlockifierConfig

    def transcribe_audio_file(self, file_uri: str) -> Optional[Dict[str, Any]]:
        """Transcribe an audio file stored on s3."""
        # Transcribe audio file
        headers = {
            "authorization": self.config.assembly_ai_api_token,
            "content-type": "application/json",
        }
        response = requests.post(
            f"{BASE_URL}/transcript",
            json={
                "audio_url": file_uri,
                "speaker_labels": self.config.speaker_detection,
                "language_detection": True,
                "auto_highlights": self.config.enable_audio_intelligence,
                "iab_categories": self.config.enable_audio_intelligence,
                "sentiment_analysis": self.config.enable_audio_intelligence,
                "auto_chapters": self.config.enable_audio_intelligence,
                "entity_detection": self.config.enable_audio_intelligence,
            },
            headers=headers,
        )

        response_json = response.json()
        transcript_id = response_json.get("id")

        # Wait for results
        max_tries = self.config.max_retries
        while max_tries > 0:
            max_tries -= 1

            response = requests.get(f"{BASE_URL}/transcript/{transcript_id}", headers=headers)
            response_json = response.json()
            job_status = response_json["status"]

            if response_json["status"] in {
                TranscribeJobStatus.COMPLETED,
                TranscribeJobStatus.ERROR,
            }:
                logging.info(f"Job {transcript_id} has status {job_status}.")
                if job_status == TranscribeJobStatus.COMPLETED:
                    return response_json
                else:
                    return None
            else:
                logging.info(f"Waiting for {transcript_id}. Current status is {job_status}.")
            time.sleep(self.config.retry_timeout)

    def run(self, request: PluginRequest[RawDataPluginInput]) -> Response[BlockAndTagPluginOutput]:
        """Blockify the saved JSON results of the Zendesk File Importer."""
        session = boto3.Session(
            aws_access_key_id=self.config.aws_access_key_id,
            aws_secret_access_key=self.config.aws_secret_access_key,
        )
        mime_type = request.data.default_mime_type

        if mime_type not in SUPPORTED_MIME_TYPES:
            raise SteamshipError(
                "Unsupported mimeType. "
                f"Currently, the following mimeTypes are supported: {SUPPORTED_MIME_TYPES}"
            )

        # Upload audio stream to s3
        data = io.BytesIO(request.data.data)
        s3_client = session.client("s3")
        media_format = mime_type.split("/")[1]
        unique_file_id = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{uuid4()}.{media_format}"
        s3_client.upload_fileobj(data, self.config.aws_s3_bucket_name, unique_file_id)

        # Generate presigned url
        signed_url = s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": self.config.aws_s3_bucket_name, "Key": unique_file_id},
            ExpiresIn=3600,
        )

        # Start Assembly AI Transcription
        transcription_response = self.transcribe_audio_file(file_uri=signed_url)

        if transcription_response:
            tags = []
            utterance_index = 0
            if self.config.speaker_detection:
                utterances = transcription_response["utterances"]
                for utterance in utterances:
                    utterance_length = len(utterance["text"])
                    tags.append(
                        Tag.CreateRequest(
                            kind="speaker",
                            start_idx=utterance_index,
                            end_idx=utterance_index + utterance_length,
                            name=utterance["speaker"],
                        )
                    )
                    utterance_index += utterance_length + 1

                    word_index = 0

                    for word in utterance["words"]:
                        word_length = len(word["text"])
                        tags.append(
                            Tag.CreateRequest(
                                kind="timestamp",
                                start_idx=word_index,
                                end_idx=word_index + word_length,
                                name=utterance["speaker"],
                            )
                        )
                        word_index += word_length + 1

            # Parse topics
            tags.extend(self._parse_topics(transcription_response))

            tags.extend(self._parse_summary(transcription_response))

            tags.extend(self._parse_sentiments(transcription_response))

            tags.extend(self._parse_chapters(transcription_response))

            tags.extend(self._parse_entities(transcription_response))

            return Response(
                data=BlockAndTagPluginOutput(
                    file=File.CreateRequest(
                        blocks=[
                            Block.CreateRequest(
                                text=transcription_response["text"],
                                tags=tags,
                            )
                        ]
                    )
                )
            )
        else:
            raise SteamshipError(
                message="Transcription of file was unsuccessful. "
                "Please check Amazon Transcribe for error message."
            )

    @staticmethod
    def _parse_entities(transcription_response):
        tags = []
        if "entities" in transcription_response:
            entities = transcription_response["entities"]
            for entity in entities:
                tags.append(
                    Tag.CreateRequest(
                        kind="entities",
                        name=entity["entity_type"],
                        value={"value": entity["text"]},
                        start_idx=None,  # TODO
                        end_idx=None,  # TODO
                    )
                )
        return tags

    @staticmethod
    def _parse_chapters(transcription_response):
        tags = []
        if "chapters" in transcription_response:
            chapters = transcription_response["chapters"]
            for chapter in chapters:
                tags.append(
                    Tag.CreateRequest(
                        kind="chapter",
                        value={
                            "summary": chapter["summary"],
                            "headline": chapter["headline"],
                            "gist": chapter["gist"],
                            "start_time": chapter["start"],
                            "end_time": chapter["end"],
                        },
                        start_idx=None,  # TODO
                        end_idx=None,  # TODO
                    )
                )
        return tags

    @staticmethod
    def _parse_sentiments(transcription_response):
        tags = []
        if "sentiment_analysis_results" in transcription_response:
            sentiment_analysis_results = transcription_response["sentiment_analysis_results"]
            ix = 0
            for sentiment in sentiment_analysis_results:
                span_text = sentiment["text"]
                tags.append(
                    Tag.CreateRequest(
                        kind="sentiments",
                        name=sentiment["sentiment"],
                        value={"span_text": span_text, "confidence": sentiment["confidence"]},
                        start_idx=ix,
                        end_idx=ix + len(span_text),
                    )
                )
                ix += len(span_text) + 1
        return tags

    @staticmethod
    def _parse_summary(transcription_response):
        tags = []
        if "summary" in transcription_response.get("iab_categories_result", {}):
            summary = transcription_response["iab_categories_result"]["summary"]
            for topic, relevance in summary.items():
                tags.append(
                    Tag.CreateRequest(
                        kind="topic_summary",
                        name=topic,
                        value={"relevance": relevance},
                        end_idx=None,
                        start_idx=None,
                    )
                )
        return tags

    @staticmethod
    def _parse_topics(transcription_response):
        tags = []
        if "results" in transcription_response.get("iab_categories_result", {}):
            topics = transcription_response["iab_categories_result"]["results"]
            ix = 0
            for topic_fragment in topics:
                topic_length = len(topic_fragment["text"])
                for label in topic_fragment["labels"]:
                    tags.append(
                        Tag.CreateRequest(
                            kind="topic",
                            name=label["label"],
                            value={
                                "span_text": topic_fragment["text"],
                                "relevance": label["relevance"],
                            },
                            start_idx=ix,
                            end_idx=ix + topic_length,
                        )
                    )
                ix += topic_length + 1

        return tags


handler = create_handler(AssemblyAIBlockifier)
