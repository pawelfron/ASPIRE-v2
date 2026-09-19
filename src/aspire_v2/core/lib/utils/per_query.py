from collections.abc import Sequence

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ...models import RetrievalRun
from ..interfaces import Measure
from .common import sort_query_ids
from .measure_calculation import get_per_query_measure

# Values keyed by run title, then measure name, then query id.
PerQueryValues = dict[str, dict[str, dict[str, float]]]

# The colour-blind safe palette the original uses, without its random shuffle so
# that regenerating a report produces identical figures.
RUN_COLORS = [
    "#E69F00",
    "#56B4E9",
    "#009E73",
    "#0072B2",
    "#D55E00",
    "#CC79A7",
    "#000000",
]
RUN_PATTERNS = ["", "/", "x", "-", "|", "+", "."]


def run_style(index: int) -> tuple[str, str]:
    """Colour and bar pattern for the nth run, so runs stay distinguishable."""
    return (
        RUN_COLORS[index % len(RUN_COLORS)],
        RUN_PATTERNS[index % len(RUN_PATTERNS)],
    )


def get_per_query_measures(
    retrieval_runs: list[RetrievalRun],
    measures: list[Measure],
) -> tuple[PerQueryValues, list[str]]:
    """Evaluate every measure per query for every run.

    Only the queries that every run scored are kept, so the runs stay directly
    comparable. The difference-based analyses subtract one run's values from
    another's positionally and would otherwise silently misalign.
    """
    values: PerQueryValues = {}
    common_query_ids: set[str] | None = None

    for retrieval_run in retrieval_runs:
        per_measure = {
            measure.measure_name: get_per_query_measure(retrieval_run, measure)
            for measure in measures
        }
        values[retrieval_run.title] = per_measure

        for per_query in per_measure.values():
            query_ids = set(per_query)
            common_query_ids = (
                query_ids if common_query_ids is None else common_query_ids & query_ids
            )

    query_ids = sort_query_ids(list(common_query_ids or set()))

    aligned = {
        title: {
            measure_name: {query_id: per_query[query_id] for query_id in query_ids}
            for measure_name, per_query in per_measure.items()
        }
        for title, per_measure in values.items()
    }

    return aligned, query_ids


def summarize_differences(
    actual: Sequence[float],
    reference: Sequence[float],
    query_ids: Sequence[str],
) -> dict:
    """Describe how a run's per-query scores differ from a set of reference scores.

    `reference` may be a baseline run, the median of the other runs, or a constant
    threshold repeated per query.
    """
    actual_values = np.asarray(actual, dtype=float)
    reference_values = np.asarray(reference, dtype=float)
    differences = actual_values - reference_values
    total = len(differences)

    improved = [qid for qid, diff in zip(query_ids, differences) if diff > 0]
    degraded = [qid for qid, diff in zip(query_ids, differences) if diff < 0]
    unchanged = [qid for qid, diff in zip(query_ids, differences) if diff == 0]

    reference_sum = float(reference_values.sum())
    spread = float(differences.std()) if total else 0.0

    return {
        "improved": improved,
        "degraded": degraded,
        "unchanged": unchanged,
        "total": total,
        "pct_improved": len(improved) / total * 100 if total else 0.0,
        "pct_degraded": len(degraded) / total * 100 if total else 0.0,
        "pct_unchanged": len(unchanged) / total * 100 if total else 0.0,
        "mean": float(differences.mean()) if total else 0.0,
        "median": float(np.median(differences)) if total else 0.0,
        "std": spread,
        "relative_improvement": (
            (float(actual_values.sum()) - reference_sum) / reference_sum * 100
            if reference_sum
            else None
        ),
        # Cohen's d for paired samples.
        "effect_size": (
            float(differences.mean()) / spread if total and spread else None
        ),
    }


def format_query_ids(query_ids: Sequence[str]) -> str:
    return ", ".join(str(query_id) for query_id in query_ids) if query_ids else "-"


def format_number(value: float | None, precision: int = 3) -> str:
    return "-" if value is None else f"{value:.{precision}f}"


DIFFERENCE_SUMMARY_ROWS = [
    "Improved queries",
    "Improved queries (%)",
    "Degraded queries",
    "Degraded queries (%)",
    "Unchanged queries",
    "Unchanged queries (%)",
    "Mean difference",
    "Median difference",
    "Std. dev. of difference",
    "Relative improvement (%)",
    "Effect size (Cohen's d)",
    "Improved query IDs",
    "Degraded query IDs",
    "Unchanged query IDs",
]


def difference_summary_column(summary: dict) -> list:
    """Render `summarize_differences` output in `DIFFERENCE_SUMMARY_ROWS` order."""
    return [
        len(summary["improved"]),
        format_number(summary["pct_improved"], 2),
        len(summary["degraded"]),
        format_number(summary["pct_degraded"], 2),
        len(summary["unchanged"]),
        format_number(summary["pct_unchanged"], 2),
        format_number(summary["mean"]),
        format_number(summary["median"]),
        format_number(summary["std"]),
        format_number(summary["relative_improvement"], 2),
        format_number(summary["effect_size"]),
        format_query_ids(summary["improved"]),
        format_query_ids(summary["degraded"]),
        format_query_ids(summary["unchanged"]),
    ]


def per_measure_bar_figure(
    data: dict[str, dict[str, list[float]]],
    query_ids: list[str],
    title: str,
    yaxis_suffix: str = "",
    zero_line: bool = False,
    row_height: int = 550,
) -> go.Figure:
    """Grouped per-query bars, one subplot row per measure and one series per run.

    `data` is keyed by measure name, then run title, with values ordered to match
    `query_ids`.
    """
    measure_names = list(data)

    fig = make_subplots(
        rows=len(measure_names),
        cols=1,
        subplot_titles=measure_names,
        vertical_spacing=0.15,
    )

    for row, measure_name in enumerate(measure_names, start=1):
        for index, (run_title, values) in enumerate(data[measure_name].items()):
            color, pattern = run_style(index)
            fig.add_trace(
                go.Bar(
                    x=query_ids,
                    y=values,
                    name=run_title,
                    marker_color=color,
                    marker_pattern_shape=pattern,
                    opacity=0.8,
                    showlegend=row == 1,
                    hovertemplate=(
                        "Query: %{x}<br>"
                        f"{measure_name}{yaxis_suffix}: "
                        "%{y:.3f}<br>"
                        f"Run: {run_title}<extra></extra>"
                    ),
                ),
                row=row,
                col=1,
            )

        if zero_line and query_ids:
            fig.add_shape(
                type="line",
                x0=query_ids[0],
                x1=query_ids[-1],
                y0=0,
                y1=0,
                line=dict(color="black", width=1, dash="dash"),
                row=row,
                col=1,
            )

        fig.update_yaxes(title_text=f"{measure_name}{yaxis_suffix}", row=row, col=1)
        fig.update_xaxes(
            title_text="Query ID",
            tickmode="array",
            tickvals=query_ids,
            ticktext=query_ids,
            tickangle=45,
            row=row,
            col=1,
        )

    fig.update_layout(
        height=row_height * len(measure_names),
        title={"text": title, "x": 0.5, "xanchor": "center", "yanchor": "top"},
        barmode="group",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=50, r=50, t=100, b=50),
    )

    return fig
