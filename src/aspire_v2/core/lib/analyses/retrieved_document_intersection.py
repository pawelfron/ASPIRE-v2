from ..interfaces import Analysis, AnalysisForm, Result
from ...models import RetrievalTask, RetrievalRun
from ..results import TableResult
import numpy as np
import pandas as pd

from django import forms


class RetrievedDocumentIntersectionForm(AnalysisForm):
    prefix = "retrieved_document_intersection"

    baseline_run = forms.ChoiceField(
        label="Baseline run", choices=[("", "Select a baseline run")]
    )
    cutoff = forms.IntegerField(
        label="Cutoff value", min_value=1, max_value=1000, initial=10
    )

    def __init__(self, *args, retrieval_task=None, retrieval_runs=None, **kwargs):
        super().__init__(
            *args,
            retrieval_task=retrieval_task,
            retrieval_runs=retrieval_runs,
            **kwargs,
        )

        if retrieval_task and retrieval_runs:
            self.fields["baseline_run"].choices = [("", "Select a baseline run")] + [
                (retrieval_run.id, retrieval_run.title)
                for retrieval_run in retrieval_runs
            ]


class RetrievedDocumentInterseciton(Analysis):
    name = "Retrieved Document Intersection"
    form_class = RetrievedDocumentIntersectionForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        cutoff = int(parameters["cutoff"])
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

        # Create a 3D numpy array to represent the data
        data = np.zeros((n_runs, n_queries, n_docs), dtype=bool)

        # Fill the array
        for i, retrieval_run in enumerate(retrieval_runs):
            for _, row in retrieval_run.dataframe.iterrows():
                if row["rank"] <= cutoff:
                    q_idx = list(query_map.keys()).index(row["query_id"])
                    d_idx = doc_map[row["doc_id"]]
                    data[i, q_idx, d_idx] = True

        # Compute intersections
        baseline_run = list(
            filter(
                lambda run: str(run.id) != parameters["baseline_run"],
                retrieval_runs,
            )
        )[0]
        baseline_idx = retrieval_runs.index(baseline_run)
        baseline_data = data[baseline_idx]
        intersections = (data & baseline_data).sum(axis=(1, 2))

        # Compute totals
        totals = np.minimum(data.sum(axis=2), cutoff).sum(axis=1)

        # Create DataFrame
        df = pd.DataFrame(
            {
                "Intersected Documents": intersections,
                "Total Documents": totals,
            },
            index=[retrieval_run.title for retrieval_run in retrieval_runs],
        )

        df = df.drop(baseline_run.title)  # Remove baseline from results
        df["Intersection Percentage"] = (
            df["Intersected Documents"] / df["Total Documents"] * 100
        ).round(2)

        return TableResult(df)
