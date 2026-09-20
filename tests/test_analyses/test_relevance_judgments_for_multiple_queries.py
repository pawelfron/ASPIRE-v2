import pandas as pd

from core.lib.analyses.relevance_judgments_for_multiple_queries import (
    RelevanceJudgmentsForMultipleQueries,
    RelevanceJudgmentsForMultipleQueriesForm,
)
from core.lib.results.plot import PlotResult


def test_form_prefix_and_initial():
    form = RelevanceJudgmentsForMultipleQueriesForm()
    assert form.prefix == "relevance_judgments_for_multiple_queries"
    assert form.fields["number_of_documents_to_display"].initial == 50


def test_multi_query_docs_keeps_docs_judged_for_more_than_one_query():
    qrels = pd.DataFrame(
        {
            "query_id": ["q1", "q2", "q1", "q3"],
            "iteration": ["0"] * 4,
            "doc_id": ["shared", "shared", "solo", "shared"],
            "relevance": [1, 0, 2, 1],
        }
    )
    result = RelevanceJudgmentsForMultipleQueries()._get_multi_query_docs(qrels)
    assert list(result["doc_id"]) == ["shared"]
    assert int(result.loc[0, "query_count"]) == 3
    assert result.loc[0, "relevance_judgments"] == {"q1": 1, "q2": 0, "q3": 1}


def test_execute_plots_stacked_relevance_bars(fake_task, fake_runs):
    result = RelevanceJudgmentsForMultipleQueries().execute(
        fake_task, fake_runs, number_of_documents_to_display=10
    )
    assert isinstance(result, PlotResult)
    assert result.fig.data
    assert result.fig.layout.barmode == "stack"
