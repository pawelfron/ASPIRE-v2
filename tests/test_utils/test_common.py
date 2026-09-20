import pandas as pd

from core.lib.utils.common import get_query_rel_judgements, sort_query_ids


def test_get_query_rel_judgements_splits_irrelevant_and_relevant(qrels_df):
    counts, results = get_query_rel_judgements(qrels_df)

    assert "Irrelevant" in counts.columns
    assert "Relevance_Label_1" in counts.columns
    assert "Relevance_Label_2" in counts.columns
    assert results["q1"]["irrelevant"] == 1
    assert results["q1"]["relevant"]["Relevance_Label_1"] == 1
    assert results["q1"]["relevant"]["Relevance_Label_2"] == 1
    assert results["q2"]["irrelevant"] == 1
    assert 0 not in results["q2"]["relevant"]


def test_get_query_rel_judgements_adds_missing_irrelevant_column():
    qrels = pd.DataFrame(
        {
            "query_id": ["q1", "q1"],
            "iteration": ["0", "0"],
            "doc_id": ["d1", "d2"],
            "relevance": [1, 2],
        }
    )
    counts, results = get_query_rel_judgements(qrels)

    assert "Irrelevant" in counts.columns
    assert int(counts.loc["q1", "Irrelevant"]) == 0
    assert results["q1"]["irrelevant"] == 0
    assert results["q1"]["relevant"]["Relevance_Label_1"] == 1


def test_sort_query_ids_orders_by_embedded_number():
    assert sort_query_ids(["q10", "q2", "q1"]) == ["q1", "q2", "q10"]


def test_sort_query_ids_puts_ids_without_digits_last():
    assert sort_query_ids(["topic", "q2", "q1"]) == ["q1", "q2", "topic"]
