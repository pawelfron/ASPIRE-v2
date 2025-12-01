from xml.etree import ElementTree

import numpy as np
import pandas as pd

from ...models import RetrievalTask, RetrievalRun


def load_qrel_file(retrieval_task: RetrievalTask) -> pd.DataFrame:
    df = pd.read_csv(
        retrieval_task.qrels,
        sep=" ",
        names=["query_id", "iteration", "doc_id", "relevance"],
        dtype={
            "query_id": "object",
            "iteration": "object",
            "doc_id": "object",
            "relevance": np.int32,
        },
    )

    return df


def load_queries_file(retrieval_task: RetrievalTask) -> pd.DataFrame:
    tree = ElementTree.parse(retrieval_task.topics)

    ids = []
    texts = []

    for topic in tree.getroot().findall(".//topic"):
        ids.append(topic.get("number"))
        texts.append("".join(topic.itertext()))

    return pd.DataFrame({"query_id": ids, "query_text": texts})


def load_run_file(retrtieval_run: RetrievalRun) -> pd.DataFrame:
    df = pd.read_csv(
        retrtieval_run.file,
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

    return df
