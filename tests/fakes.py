"""Lightweight stand-ins for Django retrieval models."""

from __future__ import annotations

import io
import uuid
from types import SimpleNamespace

import pandas as pd

TOPICS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<topics>
  <topic number="q1">alpha retrieval ranking</topic>
  <topic number="q2">beta search evaluation</topic>
</topics>
"""

QRELS_TEXT = """q1 0 d1 0
q1 0 d2 1
q1 0 d3 2
q2 0 d1 1
q2 0 d4 0
q2 0 d5 1
"""

RUN_A_TEXT = """q1\tQ0\td2\t1\t10.0\trun-a
q1\tQ0\td3\t2\t9.0\trun-a
q1\tQ0\td1\t3\t8.0\trun-a
q1\tQ0\td99\t4\t7.0\trun-a
q2\tQ0\td1\t1\t10.0\trun-a
q2\tQ0\td5\t2\t9.0\trun-a
q2\tQ0\td4\t3\t8.0\trun-a
"""

RUN_B_TEXT = """q1\tQ0\td2\t1\t9.5\trun-b
q1\tQ0\td10\t2\t8.5\trun-b
q2\tQ0\td1\t1\t9.5\trun-b
q2\tQ0\td11\t2\t8.0\trun-b
"""


class FakeFieldFile:
    """Enough of Django's FieldFile API for the data loaders."""

    def __init__(self, data: str | bytes):
        self._data = data.encode() if isinstance(data, str) else data

    def open(self, mode: str = "rb"):
        return io.BytesIO(self._data)


def make_qrels_dataframe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "query_id": ["q1", "q1", "q1", "q2", "q2", "q2"],
            "iteration": ["0"] * 6,
            "doc_id": ["d1", "d2", "d3", "d1", "d4", "d5"],
            "relevance": [0, 1, 2, 1, 0, 1],
        }
    )


def make_binary_qrels_dataframe() -> pd.DataFrame:
    qrels = make_qrels_dataframe()
    qrels = qrels.copy()
    qrels["relevance"] = qrels["relevance"].clip(upper=1)
    return qrels


def make_run_dataframe(title: str = "run-a") -> pd.DataFrame:
    text = RUN_A_TEXT if title == "run-a" else RUN_B_TEXT
    return pd.read_csv(
        io.StringIO(text),
        sep="\t",
        names=["query_id", "iteration", "doc_id", "rank", "score", "tag"],
    )


def make_fake_task(qrels: pd.DataFrame | None = None) -> SimpleNamespace:
    frame = make_qrels_dataframe() if qrels is None else qrels
    return SimpleNamespace(
        id=uuid.uuid4(),
        title="task",
        qrels_dataframe=frame,
        qrels=FakeFieldFile(QRELS_TEXT),
        topics=FakeFieldFile(TOPICS_XML),
    )


def make_fake_run(
    task: SimpleNamespace,
    title: str = "run-a",
    dataframe: pd.DataFrame | None = None,
    run_id: uuid.UUID | None = None,
) -> SimpleNamespace:
    frame = make_run_dataframe(title) if dataframe is None else dataframe
    return SimpleNamespace(
        id=run_id or uuid.uuid4(),
        title=title,
        dataframe=frame,
        ir_task=task,
        file=FakeFieldFile(RUN_A_TEXT if title == "run-a" else RUN_B_TEXT),
    )


def make_fake_runs(task: SimpleNamespace) -> list[SimpleNamespace]:
    return [
        make_fake_run(task, title="run-a"),
        make_fake_run(task, title="run-b"),
    ]
