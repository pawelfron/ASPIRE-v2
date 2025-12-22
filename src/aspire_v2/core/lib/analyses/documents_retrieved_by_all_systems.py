from ..interfaces import Analysis, AnalysisForm, Result
from ...models import RetrievalTask, RetrievalRun
from ..results import CompositeResult, ValueResult
import numpy as np
from collections import Counter

from django import forms


class DocumentsRetrievedByAllSystemsForm(AnalysisForm):
    prefix = "documents_retrieved_by_all_systems"

    cutoff = forms.IntegerField(
        label="Cutoff value", min_value=1, max_value=1000, initial=1
    )
    sample_size = forms.IntegerField(
        label="Size of the retrived documents sample",
        min_value=1,
        max_value=10,
        initial=10,
    )


class DocumentsRetrievedByAllSystems(Analysis):
    name = "Documents Retrieved By All Systems"
    form_class = DocumentsRetrievedByAllSystemsForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        cutoff = int(parameters["cutoff"])
        sample_size = int(parameters["sample_size"])

        all_queries = set()
        all_docs = set()
        for retrieval_run in retrieval_runs:
            df = retrieval_run.dataframe
            all_queries.update(df["query_id"])
            all_docs.update(df["doc_id"])

        query_map = {q: q for q in all_queries}
        doc_map = {d: i for i, d in enumerate(all_docs)}

        n_queries = len(all_queries)
        n_docs = len(all_docs)
        n_runs = len(retrieval_runs)

        data = np.zeros((n_runs, n_queries, n_docs), dtype=bool)

        for i, retrieval_run in enumerate(retrieval_runs):
            for _, row in retrieval_run.dataframe.iterrows():
                if row["rank"] <= cutoff:
                    q_idx = list(query_map.keys()).index(row["query_id"])
                    d_idx = doc_map[row["doc_id"]]
                    data[i, q_idx, d_idx] = True

        docs_retrieved_by_all = data.all(axis=0)

        retrieved_docs = []
        queries_with_retrieved_docs = set()
        for q_idx, d_idx in zip(*np.where(docs_retrieved_by_all)):
            query_id = list(query_map.keys())[q_idx]
            doc_id = list(doc_map.keys())[list(doc_map.values()).index(d_idx)]
            retrieved_docs.append(doc_id)
            queries_with_retrieved_docs.add(query_id)

        doc_counts = Counter(retrieved_docs)

        most_frequent_docs = [doc for doc, _ in doc_counts.most_common(sample_size)]

        return CompositeResult(
            {
                "Number of common queries": ValueResult(
                    len(queries_with_retrieved_docs)
                ),
                "Queries with documents retrieved by all systems": ValueResult(
                    ", ".join(sorted(queries_with_retrieved_docs))
                ),
                "Sample of documents retrieved by all systems": ValueResult(
                    ", ".join(most_frequent_docs)
                ),
            }
        )
