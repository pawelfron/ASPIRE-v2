from ..interfaces import Analysis, AnalysisForm, Measure, Result
from ...models import RetrievalRun, RetrievalTask
from ..measures import nDCG
from ..results import CompositeResult, PlotResult, TableResult, ValueResult
from ..utils.data_loaders_v2 import load_queries_file
from ..utils.per_query import get_per_query_measures
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from django import forms

# Below this many queries the bucket means are too noisy for the test to say
# anything, so the original skips it too.
MINIMUM_QUERIES_FOR_ANOVA = 20
BUCKET_COUNT = 10


class QueryPerformanceVsQueryLengthForm(AnalysisForm):
    prefix = "query_performance_vs_query_length"

    rolling_window = forms.IntegerField(
        label="Rolling mean window (queries)",
        min_value=2,
        max_value=100,
        initial=20,
    )


class QueryPerformanceVsQueryLength(Analysis):
    name = "Query Performance vs Query Length"
    form_class = QueryPerformanceVsQueryLengthForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        rolling_window = int(parameters["rolling_window"])

        measures: list[Measure] = [nDCG(cutoff=10, judged_only=False, dcg="log2")]
        measure_name = measures[0].measure_name

        queries = load_queries_file(retrieval_task)
        lengths = {
            str(query_id): len(str(query_text).split())
            for query_id, query_text in zip(queries["query_id"], queries["query_text"])
        }

        values, query_ids = get_per_query_measures(retrieval_runs, measures)

        results = {}
        for run_title, per_measure in values.items():
            frame = pd.DataFrame(
                [
                    {
                        "query_id": query_id,
                        "length": lengths[str(query_id)],
                        "performance": per_measure[measure_name][query_id],
                    }
                    for query_id in query_ids
                    if str(query_id) in lengths
                ]
            )

            if frame.empty:
                results[f"{run_title} - query length"] = ValueResult(
                    "No query in the topics file matches the evaluated queries."
                )
                continue

            frame = frame.sort_values("length").reset_index(drop=True)

            results[f"{run_title} - performance vs query length"] = PlotResult(
                self._scatter(frame, run_title, measure_name, rolling_window)
            )
            results[f"{run_title} - performance by length range"] = PlotResult(
                self._buckets(frame, run_title, measure_name)
            )
            results[f"{run_title} - query length distribution"] = TableResult(
                self._distribution(frame)
            )

            anova = self._anova(frame)
            if anova is not None:
                results[f"{run_title} - one-way ANOVA across length ranges"] = (
                    ValueResult(anova)
                )

        return CompositeResult(results)

    def _scatter(
        self,
        frame: pd.DataFrame,
        run_title: str,
        measure_name: str,
        rolling_window: int,
    ) -> go.Figure:
        rolling = (
            frame["performance"]
            .rolling(window=rolling_window, center=True, min_periods=1)
            .mean()
        )

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=frame["length"],
                y=frame["performance"],
                mode="markers",
                name="Queries",
                text=frame["query_id"],
                marker=dict(
                    size=8,
                    color=frame["performance"],
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title=measure_name),
                ),
                hovertemplate=(
                    "Query: %{text}<br>Length: %{x} tokens<br>"
                    f"{measure_name}: " + "%{y:.3f}<extra></extra>"
                ),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=frame["length"],
                y=rolling,
                mode="lines",
                name=f"Rolling mean ({rolling_window} queries)",
                line=dict(color="crimson", width=2),
            )
        )
        fig.update_layout(
            title=f"{measure_name} against query length - {run_title}",
            xaxis_title="Query length (tokens)",
            yaxis_title=measure_name,
            height=500,
            hovermode="closest",
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        return fig

    def _buckets(
        self, frame: pd.DataFrame, run_title: str, measure_name: str
    ) -> go.Figure:
        fig = make_subplots(
            rows=1,
            cols=2,
            subplot_titles=[
                "Equal-width length ranges",
                "Equal-frequency length ranges",
            ],
        )

        panels = [
            (self._equal_width_buckets(frame), "#0072B2"),
            (self._equal_frequency_buckets(frame), "#E69F00"),
        ]

        for col, (buckets, color) in enumerate(panels, start=1):
            grouped = frame.groupby(buckets, observed=True)["performance"].agg(
                ["mean", "count"]
            )
            fig.add_trace(
                go.Bar(
                    x=[str(bucket) for bucket in grouped.index],
                    y=grouped["mean"],
                    text=[f"n={count}" for count in grouped["count"]],
                    textposition="outside",
                    marker_color=color,
                    showlegend=False,
                    hovertemplate=(
                        "Length range: %{x}<br>"
                        f"Mean {measure_name}: " + "%{y:.3f}<extra></extra>"
                    ),
                ),
                row=1,
                col=col,
            )
            fig.update_xaxes(
                title_text="Query length (tokens)", tickangle=45, row=1, col=col
            )
            fig.update_yaxes(title_text=f"Mean {measure_name}", row=1, col=col)

        fig.update_layout(
            title=f"{measure_name} by query length range - {run_title}",
            height=550,
        )

        return fig

    def _distribution(self, frame: pd.DataFrame) -> pd.DataFrame:
        lengths = frame["length"]
        correlation = (
            f"{frame['performance'].corr(lengths):.4f}"
            if lengths.nunique() > 1
            else "-"
        )
        return pd.DataFrame(
            {
                "Value": [
                    str(len(frame)),
                    str(int(lengths.min())),
                    str(int(lengths.max())),
                    f"{lengths.mean():.2f}",
                    f"{lengths.median():.1f}",
                    correlation,
                ]
            },
            index=[
                "Queries",
                "Shortest query (tokens)",
                "Longest query (tokens)",
                "Mean length (tokens)",
                "Median length (tokens)",
                "Correlation between length and performance",
            ],
        )

    def _anova(self, frame: pd.DataFrame) -> str | None:
        """Test whether mean performance differs across the length ranges."""
        if len(frame) < MINIMUM_QUERIES_FOR_ANOVA:
            return None

        groups = [
            group["performance"].to_numpy()
            for _, group in frame.groupby(
                self._equal_frequency_buckets(frame), observed=True
            )
            if len(group) > 1
        ]

        if len(groups) < 2:
            return None

        statistic, p_value = stats.f_oneway(*groups)

        verdict = (
            "query length is associated with a difference in performance"
            if p_value < 0.05
            else "no significant association between query length and performance"
        )

        return (
            f"F = {statistic:.3f}, p = {p_value:.4f} across {len(groups)} length "
            f"ranges: {verdict} at alpha = 0.05."
        )

    def _equal_width_buckets(self, frame: pd.DataFrame) -> pd.Series:
        return pd.cut(frame["length"], bins=BUCKET_COUNT)

    def _equal_frequency_buckets(self, frame: pd.DataFrame) -> pd.Series:
        return pd.qcut(frame["length"], q=BUCKET_COUNT, duplicates="drop")
