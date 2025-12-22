from ..interfaces import Analysis, AnalysisForm, Result
from ...models import RetrievalTask, RetrievalRun
from ..results import PlotResult
import pandas as pd
import matplotlib.colors as mcolors
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import math

from django import forms


class RelevanceRankingPositionsForm(AnalysisForm):
    prefix = "relevance_ranking_positions"

    ranking_depth = forms.IntegerField(
        label="Ranking depth", min_value=1, max_value=100, initial=25
    )


class RelevanceRankingPositions(Analysis):
    name = "Retrieved Documents, Relevance, Ranking Position"
    form_class = RelevanceRankingPositionsForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        ranking_depth = parameters["ranking_depth"]
        qrel = retrieval_task.qrels_dataframe

        unique_relevance = sorted(qrel["relevance"].unique())
        color_scale = self._generate_color_scale(len(unique_relevance))

        min_val, max_val = -100, max(unique_relevance)
        range_val = max_val - min_val
        colorscale = [
            [(val - min_val) / range_val, color]
            for val, color in zip([-100] + unique_relevance, color_scale)
        ]

        num_runs = len(retrieval_runs)
        num_cols = 2
        num_rows = math.ceil(num_runs / num_cols)

        fig = make_subplots(
            rows=num_rows,
            cols=num_cols,
            subplot_titles=[run.title for run in retrieval_runs],
            # vertical_spacing=0.15,
            horizontal_spacing=0.05,
        )

        for i, run in enumerate(retrieval_runs, start=1):
            run_name = run.title
            run_df = run.dataframe
            # Merge run data with qrel data to get relevance information
            merged_df = pd.merge(run_df, qrel, on=["query_id", "doc_id"], how="left")
            merged_df["relevance"] = merged_df["relevance"].fillna(
                -100
            )  # Mark unjudged as -100

            # Filter for the specified ranking depth
            merged_df = merged_df[merged_df["rank"] <= ranking_depth]

            # Create heatmap data and hover text
            heatmap_data = []
            hover_text = []

            for rank in range(1, ranking_depth + 1):
                rank_data = merged_df[merged_df["rank"] == rank]
                row_data = rank_data["relevance"].tolist()
                row_data += [None] * (
                    len(merged_df["query_id"].unique()) - len(row_data)
                )  # Pad with None
                heatmap_data.append(row_data)

                hover_row = [
                    f"Query: {query_id}<br>Rank: {rank}<br>Doc ID: {doc_id}<br>Relevance: {'Unjudged' if rel == -100 else rel}"
                    for query_id, doc_id, rel in zip(
                        rank_data["query_id"],
                        rank_data["doc_id"],
                        rank_data["relevance"],
                    )
                ]
                hover_row += [None] * (
                    len(merged_df["query_id"].unique()) - len(hover_row)
                )
                hover_text.append(hover_row)

            row = (i - 1) // num_cols + 1
            col = (i - 1) % num_cols + 1

            fig.add_trace(
                go.Heatmap(
                    z=heatmap_data,
                    y=list(range(1, ranking_depth + 1)),
                    x=merged_df["query_id"].unique(),
                    colorscale=colorscale,
                    showscale=False,
                    hoverinfo="text",
                    text=hover_text,
                    xgap=1,
                    ygap=1,
                    zmin=min_val,
                    zmax=max_val,
                ),
                row=row,
                col=col,
            )

            fig.update_xaxes(title_text="Query ID", row=row, col=col, tickangle=45)
            fig.update_yaxes(
                title_text="Ranking Position" if col == 1 else "", row=row, col=col
            )

            # Add legend only once
            if i == 1:
                for val, color in zip([-100] + unique_relevance, color_scale):
                    label = (
                        "Unjudged Relevance"
                        if val == -100
                        else f"Relevance_Label_{val}"
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=[None],
                            y=[None],
                            mode="markers",
                            marker=dict(size=10, color=color),
                            name=label,
                            legendgroup=f"relevance {val}",
                            showlegend=True,
                        ),
                        row=row,
                        col=col,
                    )

        fig.update_layout(
            height=700 * num_rows,
            width=1400,
            title_text=f"Document Ranking and Relevance for the Top {ranking_depth} Rank Positions per Experiment",
            font=dict(size=14),
            legend=dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
            ),
        )

        return PlotResult(fig)

    def _generate_color_scale(self, num_colors):
        colors = ["lightgray"]
        if num_colors > 1:
            cmap = mcolors.LinearSegmentedColormap.from_list(
                "custom", ["red", "orange", "green"]
            )
            colors.extend(
                [mcolors.rgb2hex(cmap(i / (num_colors - 1))) for i in range(num_colors)]
            )
        else:
            colors.append("red")
        return colors
