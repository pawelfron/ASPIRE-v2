import pandas as pd

from core.lib.analyses.relevance_judgments_per_query import (
    RelevanceJudgmentsPerQuery,
    RelevanceJudgmentsPerQueryForm,
)
from core.lib.results.composite import CompositeResult
from core.lib.results.plot import PlotResult
from core.lib.results.table import TableResult
from tests.fakes import make_binary_qrels_dataframe, make_fake_task


def test_form_prefix():
    assert RelevanceJudgmentsPerQueryForm.prefix == "relevance_judgments_per_query"


def test_label_judgements_and_classification():
    analysis = RelevanceJudgmentsPerQuery()
    data = {
        "q1": {"irrelevant": 5, "relevant": {"Relevance_Label_1": 1}},
        "q2": {"irrelevant": 1, "relevant": {"Relevance_Label_1": 4}},
        "q3": {"irrelevant": 2, "relevant": {"Relevance_Label_1": 2}},
    }
    queries = ["q1", "q2", "q3"]
    assert analysis._get_label_judgements(data, queries, "Relevance_Label_0")["q1"] == 5
    assert analysis._get_label_judgements(data, queries, "Relevance_Label_1")["q2"] == 4

    classified = analysis._classify_queries(
        {"q1": 1, "q2": 2, "q3": 3, "q4": 4, "q5": 5, "q6": 6},
        n_hard=2,
        n_easy=2,
    )
    assert classified["hard"] == ["q1", "q2"]
    assert classified["easy"] == ["q5", "q6"]

    compared = analysis._compare_relevance_labels(
        data, queries, ["Relevance_Label_0", "Relevance_Label_1"]
    )
    assert compared["Relevance_Label_1"]["easy_queries"] == ["q2", "q3"]
    assert compared["Relevance_Label_1"]["hard_queries"] == ["q1"]
    assert compared["Relevance_Label_1"]["min_query"] == "q1"
    assert compared["Relevance_Label_1"]["max_query"] == "q2"
    assert "Combined" in compared


def test_execute_single_relevance_label_uses_solid_blue():
    task = make_fake_task(qrels=make_binary_qrels_dataframe())
    result = RelevanceJudgmentsPerQuery().execute(task, [])
    plot = result.children["Query Relevance Judgments Plot"]
    colors = [trace.marker.color for trace in plot.fig.data]
    assert "blue" in colors
    assert "red" in colors


def test_execute_returns_plot_and_table(fake_task, fake_runs):
    result = RelevanceJudgmentsPerQuery().execute(fake_task, fake_runs)
    assert isinstance(result, CompositeResult)
    assert isinstance(result.children["Query Relevance Judgments Plot"], PlotResult)
    table = result.children["Easy and Hard Queries"]
    assert isinstance(table, TableResult)
    assert isinstance(table.dataframe, pd.DataFrame)
    assert "Relevance Label 1" in table.dataframe.columns
