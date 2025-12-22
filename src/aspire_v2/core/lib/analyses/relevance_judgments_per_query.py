from ..interfaces import Analysis, AnalysisForm, Result
from ...models import RetrievalTask, RetrievalRun
from ..results import CompositeResult, TableResult, PlotResult
from ..utils.common import get_query_rel_judgements, sort_query_ids
import numpy as np
import pandas as pd
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import matplotlib.colors as mcolors


class RelevanceJudgmentsPerQueryForm(AnalysisForm):
    prefix = "relevance_judgments_per_query"


class RelevanceJudgmentsPerQuery(Analysis):
    name = "Relevance Judgments per Query"
    form_class = RelevanceJudgmentsPerQueryForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        qrel_df = retrieval_task.qrels_dataframe
        relevance_counts, results = get_query_rel_judgements(qrel_df)

        sorted_query_ids = sort_query_ids(relevance_counts.index)
        relevance_counts = relevance_counts.loc[sorted_query_ids]

        fig = make_subplots(
            rows=1, cols=1, subplot_titles=["Relevance Judgements per Query"]
        )

        relevant_columns = [
            col for col in relevance_counts.columns if col != "Irrelevant"
        ]
        num_relevant_labels = len(relevant_columns)

        if num_relevant_labels > 1:
            blue_scale = mcolors.LinearSegmentedColormap.from_list(
                "", ["lightblue", "darkblue"]
            )
            blue_colors = [
                mcolors.rgb2hex(blue_scale(i / (num_relevant_labels - 1)))
                for i in range(num_relevant_labels)
            ]
        elif num_relevant_labels == 1:
            blue_colors = ["blue"]
        else:
            blue_colors = []

        for i, column in enumerate(relevance_counts.columns):
            if column == "Irrelevant":
                color = "red"
            else:
                color = blue_colors[relevant_columns.index(column)]

            fig.add_trace(
                go.Bar(
                    name=column,
                    x=relevance_counts.index,
                    y=relevance_counts[column],
                    text=relevance_counts[column],
                    textposition="auto",
                    marker_color=color,
                    hovertemplate="Query: %{x}<br>"
                    + f"{column}: "
                    + "%{y}<extra></extra>",
                ),
                row=1,
                col=1,
            )

        fig.update_layout(
            height=550,
            title={
                "text": "Query Relevance Judgements Analysis",
                "x": 0.01,
                "xanchor": "left",
                "yanchor": "top",
            },
            barmode="stack",
            xaxis_title="Query ID",
            yaxis_title="Number of Documents",
            legend_title="Relevance Labels",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        fig.update_xaxes(
            tickmode="array",
            tickvals=relevance_counts.index,
            ticktext=relevance_counts.index,
            tickangle=45,
        )

        analysis_results = {}
        queries = sort_query_ids(list(results.keys()))
        relevance_labels = ["Relevance_Label_0"] + list(
            results[queries[0]]["relevant"].keys()
        )

        sorted_queries = {}
        for label in relevance_labels:
            label_judgements = self._get_label_judgements(results, queries, label)
            sorted_queries[label] = sorted(
                label_judgements.items(), key=lambda x: (-x[1], queries.index(x[0]))
            )
        analysis_results["sorted_queries"] = sorted_queries

        for label in relevance_labels:
            values = [
                self._get_label_judgements(results, queries, label)[q] for q in queries
            ]
            analysis_results[f"{label}_stats"] = {
                "mean": np.mean(values),
                "median": np.median(values),
                "std": np.std(values),
                "min": min(values),
                "max": max(values),
            }

        analysis_results["query_difficulty"] = {}
        for label in relevance_labels:
            values = {
                q: self._get_label_judgements(results, queries, label)[q]
                for q in queries
            }
            difficulty_classification = self._classify_queries(values)
            analysis_results["query_difficulty"][label] = difficulty_classification

        analysis_results["overall_stats"] = {}
        for label in relevance_labels:
            total = sum(self._get_label_judgements(results, queries, label).values())
            analysis_results["overall_stats"][label] = total

        total_judgements = sum(analysis_results["overall_stats"].values())
        for label in relevance_labels:
            analysis_results["overall_stats"][f"{label}_percentage"] = (
                analysis_results["overall_stats"][label] / total_judgements
            ) * 100

        label_comparison = self._compare_relevance_labels(
            results, queries, relevance_labels
        )

        analysis_results_df = pd.DataFrame(
            index=[
                "Easy Queries (top 5)",
                "Hard Queries (top 5)",
                "Min Query",
                "Max Query",
            ]
        )

        for label, stats in label_comparison.items():
            top5_easy = ", ".join(
                stats["easy_queries"][:5]
                if len(stats["easy_queries"]) > 5
                else stats["easy_queries"]
            )
            top5_hard = ", ".join(
                stats["hard_queries"][:5]
                if len(stats["hard_queries"]) > 5
                else stats["hard_queries"]
            )
            analysis_results_df[label.replace("_", " ")] = [
                top5_easy,
                top5_hard,
                stats["min_query"],
                stats["max_query"],
            ]

        return CompositeResult(
            {
                "Query Relevance Judgments Plot": PlotResult(fig),
                "Easy and Hard Queries": TableResult(analysis_results_df),
            }
        )

    def _get_label_judgements(self, data, queries, label):
        if label == "Relevance_Label_0":
            return {q: data[q]["irrelevant"] for q in queries}
        else:
            return {q: data[q]["relevant"][label] for q in queries}

    def _classify_queries(self, values, n_hard=5, n_easy=5):
        sorted_queries = sorted(values.items(), key=lambda x: x[1])
        hard_queries = [q for q, _ in sorted_queries[:n_hard]]
        easy_queries = [q for q, _ in sorted_queries[-n_easy:]]
        values_list = list(values.values())
        return {
            "hard": hard_queries,
            "easy": easy_queries,
            "median": np.median(values_list),
            "mean": np.mean(values_list),
            "min": min(values_list),
            "max": max(values_list),
        }

    def _compare_relevance_labels(self, data, queries, relevance_labels):
        results = {}
        irrelevant_label = "Relevance_Label_0"

        for label in relevance_labels:
            if label == irrelevant_label:
                continue

            label_judgements = self._get_label_judgements(data, queries, label)
            irrelevant_judgements = self._get_label_judgements(
                data, queries, irrelevant_label
            )

            easy_queries = []
            hard_queries = []
            min_query = max_query = queries[0]
            min_count = max_count = label_judgements[queries[0]]

            for query in queries:
                label_count = label_judgements[query]
                irrelevant_count = irrelevant_judgements[query]

                if label_count >= irrelevant_count:
                    easy_queries.append(query)
                elif (
                    label_count < irrelevant_count / 2
                ):  # Arbitrary threshold for "very few"
                    hard_queries.append(query)

                if label_count < min_count:
                    min_count = label_count
                    min_query = query
                if label_count > max_count:
                    max_count = label_count
                    max_query = query

            results[label] = {
                "easy_queries": easy_queries,
                "hard_queries": hard_queries,
                "min_query": min_query,
                "max_query": max_query,
            }

        # Combine all relevant labels
        combined_judgements = {
            q: sum(
                self._get_label_judgements(data, [q], label)[q]
                for label in relevance_labels
                if label != irrelevant_label
            )
            for q in queries
        }
        irrelevant_judgements = self._get_label_judgements(
            data, queries, irrelevant_label
        )

        easy_queries = []
        hard_queries = []
        min_query = max_query = queries[0]
        min_count = max_count = combined_judgements[queries[0]]

        for query in queries:
            combined_count = combined_judgements[query]
            irrelevant_count = irrelevant_judgements[query]

            if combined_count >= irrelevant_count:
                easy_queries.append(query)
            elif combined_count < irrelevant_count / 2:
                hard_queries.append(query)

            if combined_count < min_count:
                min_count = combined_count
                min_query = query
            if combined_count > max_count:
                max_count = combined_count
                max_query = query

        results["Combined"] = {
            "easy_queries": easy_queries,
            "hard_queries": hard_queries,
            "min_query": min_query,
            "max_query": max_query,
        }

        return results
