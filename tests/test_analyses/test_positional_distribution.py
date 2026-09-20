from core.lib.analyses.positional_distribution import (
    PositionalDistribution,
    PositionalDistributionForm,
)
from core.lib.results.composite import CompositeResult
from core.lib.results.plot import PlotResult
from tests.fakes import make_qrels_dataframe, make_run_dataframe


def test_form_prefix():
    assert PositionalDistributionForm.prefix == "positional_distribution"


def test_first_ranks_for_relevance_and_unjudged():
    analysis = PositionalDistribution()
    ranks = analysis._get_relevant_and_unjudged(
        make_qrels_dataframe(), make_run_dataframe("run-a")
    )
    assert ranks["q1"]["Relevance_Label_1"] == 1
    assert ranks["q1"]["Relevance_Label_2"] == 2
    assert ranks["q1"]["Irrelevant_Document"] == 3
    assert ranks["q1"]["Unjudged_Document"] == 4


def test_plot_buckets_first_ranks():
    analysis = PositionalDistribution()
    figure = analysis._plot_dist_of_retrieved_docs(
        {
            "q1": {"Relevance_Label_1": 1, "Unjudged_Document": 15},
            "q2": {"Relevance_Label_1": 5, "Unjudged_Document": 250},
        }
    )
    names = [trace.name for trace in figure.data]
    assert "Relevance_Label_1" in names
    assert "Unjudged_Document" in names
    assert figure.layout.title.text == "Distribution of Document Ranking Positions"


def test_execute_one_plot_per_run(fake_task, fake_runs):
    result = PositionalDistribution().execute(fake_task, fake_runs)
    assert isinstance(result, CompositeResult)
    assert set(result.children) == {"run-a", "run-b"}
    assert all(isinstance(child, PlotResult) for child in result.children.values())
