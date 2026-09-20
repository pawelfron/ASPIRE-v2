from core.lib.analyses.relevance_ranking_positions import (
    RelevanceRankingPositions,
    RelevanceRankingPositionsForm,
)
from core.lib.results.plot import PlotResult


def test_form_prefix():
    form = RelevanceRankingPositionsForm()
    assert form.prefix == "relevance_ranking_positions"
    assert form.fields["ranking_depth"].initial == 25


def test_color_scale_for_one_and_many_labels():
    analysis = RelevanceRankingPositions()
    single = analysis._generate_color_scale(1)
    assert single[0] == "lightgray"
    assert single[1] == "red"
    many = analysis._generate_color_scale(3)
    assert many[0] == "lightgray"
    assert len(many) == 4


def test_execute_builds_heatmap_per_run(fake_task, fake_runs):
    result = RelevanceRankingPositions().execute(
        fake_task, fake_runs, ranking_depth=2
    )
    assert isinstance(result, PlotResult)
    heatmap_traces = [trace for trace in result.fig.data if trace.type == "heatmap"]
    assert len(heatmap_traces) == 2
    assert "Top 2 Rank Positions" in result.fig.layout.title.text
