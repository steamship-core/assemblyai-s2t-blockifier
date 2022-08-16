"""Parsers to extract tags from transcription responses."""
from steamship import Tag


def parse_speaker_tags(transcription_response):
    """Extract speaker tags from transcription response."""
    tags = []
    if "utterances" in transcription_response:
        utterance_index = 0
        for utterance in transcription_response["utterances"] or []:
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
    return tags


def parse_timestamps(transcription_response):
    """Extract timestamp tags from transcription response."""
    tags = []
    word_index = 0
    for word in transcription_response["words"]:
        word_length = len(word["text"])
        tags.append(
            Tag.CreateRequest(
                kind="timestamp",
                start_idx=word_index,
                end_idx=word_index + word_length,
                name=word["text"],
                value={"start_time": word["start"], "end_time": word["end"]},
            )
        )
        word_index += word_length + 1
    return tags


def parse_entities(transcription_response):
    """Extract entity tags from transcription response."""
    tags = []
    if "entities" in transcription_response:
        for entity in transcription_response["entities"]:
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


def parse_chapters(transcription_response):
    """Extract chapters and corresponding summaries from transcription response."""
    tags = []
    if "chapters" in transcription_response:
        for ix, chapter in enumerate(transcription_response["chapters"]):
            tags.append(
                Tag.CreateRequest(
                    kind="chapter",
                    name=f"{ix}",
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


def parse_sentiments(transcription_response):
    """Extract sentiment tags from transcription response."""
    tags = []
    if "sentiment_analysis_results" in transcription_response:
        ix = 0
        for sentiment in transcription_response["sentiment_analysis_results"]:
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


def parse_summary(transcription_response):
    """Extract summary from transcription response."""
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


def parse_topics(transcription_response):
    """Extract topic tags from transcription response."""
    tags = []
    if "results" in transcription_response.get("iab_categories_result", {}):
        ix = 0
        for topic_fragment in transcription_response["iab_categories_result"]["results"]:
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
