from xml.etree import ElementTree

import numpy as np
import pandas as pd

from ...models import RetrievalTask, RetrievalRun


def load_qrel_file(retrieval_task: RetrievalTask) -> pd.DataFrame:
    with retrieval_task.qrels.open("rb") as f:
        return pd.read_csv(
            f,
            sep=" ",
            names=["query_id", "iteration", "doc_id", "relevance"],
            dtype={
                "query_id": "object",
                "iteration": "object",
                "doc_id": "object",
                "relevance": np.int32,
            },
        )


def load_queries_file(retrieval_task: RetrievalTask) -> pd.DataFrame:
    # Reopen rather than read the field file where it stands: the same task object
    # is shared by every analysis in a report, and the second reader would
    # otherwise start at end of file.
    with retrieval_task.topics.open("rb") as f:
        tree = ElementTree.parse(f)

    ids = []
    texts = []

    for topic in tree.getroot().findall(".//topic"):
        ids.append(topic.get("number"))
        texts.append("".join(topic.itertext()))

    return pd.DataFrame({"query_id": ids, "query_text": texts})


def load_run_file(retrtieval_run: RetrievalRun) -> pd.DataFrame:
    with retrtieval_run.file.open("rb") as f:
        return pd.read_csv(
            f,
            sep="\t",
            names=["query_id", "iteration", "doc_id", "rank", "score", "tag"],
            dtype={
                "query_id": "object",
                "iteration": "object",
                "doc_id": "object",
                "rank": np.int32,
                "score": np.float64,
                "tag": "object",
            },
        )
