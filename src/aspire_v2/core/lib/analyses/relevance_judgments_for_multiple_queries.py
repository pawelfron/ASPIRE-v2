from ..interfaces import Analysis, AnalysisForm, Result
from ...models import RetrievalTask, RetrievalRun
from ..results import PlotResult
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from django import forms


class RelevanceJudgmentsForMultipleQueriesForm(AnalysisForm):
    prefix = "relevance_judgments_for_multiple_queries"

    number_of_documents_to_display = forms.IntegerField(
        label="Number of Documents to Display", min_value=10, max_value=200, initial=50
    )


class RelevanceJudgmentsForMultipleQueries(Analysis):
    name = "Relevance Judgments for Multiple Queries"
    form_class = RelevanceJudgmentsForMultipleQueriesForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        number_of_documents_to_display = parameters["number_of_documents_to_display"]

        qrels = retrieval_task.qrels_dataframe
        multi_query_docs = self._get_multi_query_docs(qrels).head(
            number_of_documents_to_display
        )

        fig = go.Figure()

        # Get unique relevance labels
        all_relevance = [
            rel
            for doc_rel in multi_query_docs["relevance_judgments"]
            for rel in doc_rel.values()
        ]
        unique_relevance = sorted(set(all_relevance))

        # Generate a color scale
        color_scale = px.colors.qualitative.Plotly
        relevance_colors = {
            rel: color_scale[i % len(color_scale)]
            for i, rel in enumerate(unique_relevance)
        }

        for rel_label in unique_relevance:
            counts = [
                sum(1 for rel in doc_rel.values() if rel == rel_label)
                for doc_rel in multi_query_docs["relevance_judgments"]
            ]

            fig.add_trace(
                go.Bar(
                    x=multi_query_docs["doc_id"],
                    y=counts,
                    name=f"Relevance {rel_label}",
                    marker_color=relevance_colors[rel_label],
                    hovertext=[
                        f"Queries: {', '.join([q for q, r in doc_rel.items() if r == rel_label])}"
                        for doc_rel in multi_query_docs["relevance_judgments"]
                    ],
                    hoverinfo="text+y",
                    hoverlabel=dict(bgcolor="white", font=dict(color="gray")),
                )
            )

        fig.update_layout(
            title="Documents' Relevance Judged across Multiple Queries",
            xaxis_title="Document ID",
            yaxis_title="Number of Queries",
            barmode="stack",
            height=600,
            hoverlabel=dict(bgcolor="white", font_size=12),
            legend_title="Relevance Label",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        return PlotResult(fig)

    def _get_multi_query_docs(self, df: pd.DataFrame) -> pd.DataFrame:
        doc_query_count = df.groupby("doc_id")["query_id"].nunique()
        multi_query_docs = doc_query_count[doc_query_count > 1]
        multi_query_docs = multi_query_docs.sort_values(ascending=False)

        result = pd.DataFrame(
            {"doc_id": multi_query_docs.index, "query_count": multi_query_docs.values}
        )

        relevance_info = df.groupby("doc_id").apply(
            lambda x: x.groupby("query_id")["relevance"].first().to_dict()
        )
        result["relevance_judgments"] = result["doc_id"].map(relevance_info)

        return result
