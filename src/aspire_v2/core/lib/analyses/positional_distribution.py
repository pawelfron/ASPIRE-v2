from ..interfaces import Analysis, Result, AnalysisForm
from ..results import PlotResult, CompositeResult
from ...models import RetrievalRun, RetrievalTask
import plotly.graph_objects as go
import pandas as pd

from collections import defaultdict


class PositionalDistributionForm(AnalysisForm):
    prefix = "positional_distribution"


class PositionalDistribution(Analysis):
    name = "Positional Distribution of Relevant and Unjudged Retrieved Documents"
    form_class = PositionalDistributionForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        results = {}
        for retrieval_run in retrieval_runs:
            relevant_and_unjedged = self._get_relevant_and_unjudged(
                retrieval_task.qrels_dataframe, retrieval_run.dataframe
            )
            results[retrieval_run.title] = PlotResult(
                self._plot_dist_of_retrieved_docs(relevant_and_unjedged)
            )
        return CompositeResult(results)

    def _get_relevant_and_unjudged(self, qrel: pd.DataFrame, res: pd.DataFrame) -> dict:
        """
        Merge 'res' and 'qrel' DataFrames on 'query_id' and 'doc_id'.
        For each unique 'query_id', determine:
        - The first rank positions for relevance thresholds (0, 1, 2).
        - The rank position where 'relevance' is NaN (first_unjudged).
        Returns a dictionary where keys are 'query_id' and values are dictionaries
        containing these rank positions.
        """
        merged_df = pd.merge(res, qrel, on=["query_id", "doc_id"], how="left")
        ranking_per_relevance = {}
        relevance_thresholds = qrel["relevance"].unique()

        for query_id, group in merged_df.groupby("query_id"):
            group_sorted = group.sort_values(by="score", ascending=False)
            query_result = {}

            for relevance_val in relevance_thresholds:
                relevant_rows = group_sorted[group_sorted["relevance"] == relevance_val]
                first_rank = (
                    relevant_rows["rank"].iloc[0]
                    if not relevant_rows.empty
                    else f"{len(group_sorted)}"
                )

                if not relevance_val == 0:
                    query_result[f"Relevance_Label_{relevance_val}"] = first_rank
                else:
                    query_result["Irrelevant_Document"] = first_rank

            nan_relevance_rows = group_sorted[group_sorted["relevance"].isna()]
            first_rank_nan_relevance = (
                nan_relevance_rows["rank"].iloc[0]
                if not nan_relevance_rows.empty
                else f"{len(group_sorted)}"
            )

            query_result["Unjudged_Document"] = first_rank_nan_relevance
            ranking_per_relevance[query_id] = query_result

        return ranking_per_relevance

    def _plot_dist_of_retrieved_docs(self, relevance_ret_pos: dict) -> None:
        bucket_ranges = {
            "1": (1, 1),
            "2-10": (2, 10),
            "11-20": (11, 20),
            "21-30": (21, 30),
            "31-40": (31, 40),
            "41-50": (41, 50),
            "51-60": (51, 60),
            "61-70": (61, 70),
            "71-80": (71, 80),
            "81-90": (81, 90),
            "91-100": (91, 100),
            "101-200": (101, 200),
            "200+": (201, 999),  # Handle values greater than 200
        }

        thresholds = set(
            key for values in relevance_ret_pos.values() for key in values.keys()
        )
        buckets = {
            threshold: {bucket: 0 for bucket in bucket_ranges.keys()}
            for threshold in thresholds
        }

        for query_id, values in relevance_ret_pos.items():
            for threshold, value in values.items():
                value = int(value)
                for bucket, (start, end) in bucket_ranges.items():
                    if start <= value <= end:
                        buckets[threshold][bucket] += 1
                        break  # Break once the bucket is found

        all_data = []
        for metric, bucket_counts in buckets.items():
            for bucket, count in bucket_counts.items():
                all_data.append((metric, bucket, count))

        all_data.sort(key=lambda x: list(bucket_ranges.keys()).index(x[1]))

        sorted_buckets = defaultdict(lambda: defaultdict(int))
        for metric, bucket, count in all_data:
            sorted_buckets[metric][bucket] = count

        fig = go.Figure()

        x_labels = list(bucket_ranges.keys())
        x_indices = list(range(len(x_labels)))
        num_metrics = len(buckets)
        colors = [
            "skyblue",
            "lightgreen",
            "salmon",
            "gold",
        ]
        width = 0.2

        for index, (metric, bucket_counts) in enumerate(sorted_buckets.items()):
            fig.add_trace(
                go.Bar(
                    x=[i + (index - num_metrics / 2) * width for i in x_indices],
                    y=[bucket_counts[bucket] for bucket in x_labels],
                    width=width,
                    name=metric,
                    marker_color=colors[index % len(colors)],
                    hoverinfo="y",
                )
            )

        fig.update_layout(
            title="Distribution of Document Ranking Positions",
            xaxis_title="Position of the 1st Retrieved Document per Relevance Label",
            yaxis_title="Number of Queries",
            xaxis=dict(tickmode="array", tickvals=x_indices, ticktext=x_labels),
            barmode="group",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )

        return fig
