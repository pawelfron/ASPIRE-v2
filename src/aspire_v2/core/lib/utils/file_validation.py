"""Validate uploaded qrels, topics, and run files before they are stored.

The checks match the readers in ``data_loaders_v2`` and on the retrieval models:
qrels are space-separated TREC judgments, topics are XML ``<topic number="...">``
elements, and runs are tab-separated TREC run lines.
"""

import math
from xml.etree import ElementTree

import numpy as np
from django.core.exceptions import ValidationError

_INT32_MIN = int(np.iinfo(np.int32).min)
_INT32_MAX = int(np.iinfo(np.int32).max)

QRELS_HELP = (
    "TREC qrels file. Each line is four space-separated fields: "
    "query id, iteration, document id, and integer relevance."
)
TOPICS_HELP = 'XML topics file with one <topic number="..."> element per query.'
RUN_HELP = (
    "TREC run file. Each line is six tab-separated fields: "
    "query id, iteration, document id, rank, score, and run tag."
)


def validate_qrels_file(uploaded) -> None:
    lines = _text_lines(uploaded)
    saw_row = False
    for line_number, line in enumerate(lines, start=1):
        if line == "":
            continue
        fields = line.split(" ")
        if len(fields) != 4 or any(field == "" for field in fields):
            raise ValidationError(
                f"Line {line_number} of the qrels file must contain exactly four "
                "non-empty space-separated fields: query id, iteration, "
                "document id, and relevance."
            )
        _require_int32(fields[3], line_number, "qrels file", "relevance")
        saw_row = True
    if not saw_row:
        raise ValidationError(f"The qrels file is empty. {QRELS_HELP}")


def validate_topics_file(uploaded) -> None:
    uploaded.seek(0)
    try:
        raw = uploaded.read()
        if not raw or not raw.strip():
            raise ValidationError(f"The topics file is empty. {TOPICS_HELP}")
        uploaded.seek(0)
        try:
            tree = ElementTree.parse(uploaded)
        except ElementTree.ParseError as exc:
            raise ValidationError(f"Topics file is not valid XML ({exc}).") from exc

        topics = topic_elements(tree.getroot())
        if not topics:
            raise ValidationError(
                "Topics file must contain at least one <topic> element. " + TOPICS_HELP
            )
        for index, topic in enumerate(topics, start=1):
            number = topic.get("number")
            if number is None or number.strip() == "":
                raise ValidationError(
                    f"Topic {index} must have a non-empty number attribute."
                )
    finally:
        uploaded.seek(0)


def validate_run_file(uploaded) -> None:
    lines = _text_lines(uploaded)
    saw_row = False
    for line_number, line in enumerate(lines, start=1):
        if line == "":
            continue
        fields = line.split("\t")
        if len(fields) != 6 or any(field == "" for field in fields):
            raise ValidationError(
                f"Line {line_number} of the run file must contain exactly six "
                "non-empty tab-separated fields: query id, iteration, "
                "document id, rank, score, and run tag."
            )
        _require_int32(fields[3], line_number, "run file", "rank")
        _require_finite_float(fields[4], line_number)
        saw_row = True
    if not saw_row:
        raise ValidationError(f"The run file is empty. {RUN_HELP}")


def topic_elements(root: ElementTree.Element) -> list[ElementTree.Element]:
    """Topic nodes the queries loader reads, including a root ``<topic>``."""
    topics = root.findall(".//topic")
    if root.tag == "topic":
        return [root, *topics]
    return topics


def _text_lines(uploaded) -> list[str]:
    uploaded.seek(0)
    try:
        raw = uploaded.read()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("The file must be UTF-8 text.") from exc
        return text.splitlines()
    finally:
        uploaded.seek(0)


def _require_int32(value: str, line_number: int, kind: str, field_name: str) -> None:
    try:
        number = int(value)
    except ValueError as exc:
        raise ValidationError(
            f"Line {line_number} of the {kind} has a {field_name} "
            "that is not an integer."
        ) from exc
    if number < _INT32_MIN or number > _INT32_MAX:
        raise ValidationError(
            f"Line {line_number} of the {kind} has a {field_name} "
            "outside the 32-bit integer range."
        )


def _require_finite_float(value: str, line_number: int) -> None:
    try:
        number = float(value)
    except ValueError as exc:
        raise ValidationError(
            f"Line {line_number} of the run file has a score that is not a number."
        ) from exc
    if not math.isfinite(number):
        raise ValidationError(
            f"Line {line_number} of the run file has a score that is not finite."
        )
