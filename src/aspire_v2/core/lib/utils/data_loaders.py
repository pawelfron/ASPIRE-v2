from xml.etree import ElementTree

import numpy as np
import pandas as pd

from resources.models import ResourceFile


def load_qrel_file(qrel_file: ResourceFile) -> pd.DataFrame:
    df = pd.read_csv(
        qrel_file.file,
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


def load_queries_file(queries_file: ResourceFile) -> pd.DataFrame:
    tree = ElementTree.parse(queries_file.file)

    ids = []
    texts = []

    for topic in tree.getroot().findall(".//topic"):
        ids.append(topic.get("number"))
        texts.append("".join(topic.itertext()))

    return pd.DataFrame({"query_id": ids, "query_text": texts})


def load_run_file(run_file: ResourceFile) -> pd.DataFrame:
    df = pd.read_csv(
        run_file.file,
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
