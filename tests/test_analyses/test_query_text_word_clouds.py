from unittest.mock import MagicMock, patch

import pandas as pd

from core.lib.analyses.query_text_word_clouds import (
    MAX_MIN_MEDIAN,
    MEDIAN_ABSOLUTE_DEVIATION,
    MODIFIED_Z_SCORE,
    PERCENTILE,
    QueryTextWordClouds,
    QueryTextWordCloudsForm,
)
from core.lib.results.composite import CompositeResult
from core.lib.results.image import ImageResult
from core.lib.results.value import ValueResult


def test_form_prefix():
    form = QueryTextWordCloudsForm()
    assert form.prefix == "query_text_word_clouds"
    assert form.fields["method"].initial == MAX_MIN_MEDIAN


def _judgements():
    return {
        "q1": {"irrelevant": 1, "relevant": {"Relevance_Label_1": 10}},
        "q2": {"irrelevant": 2, "relevant": {"Relevance_Label_1": 9}},
        "q3": {"irrelevant": 3, "relevant": {"Relevance_Label_1": 8}},
        "q4": {"irrelevant": 4, "relevant": {"Relevance_Label_1": 2}},
        "q5": {"irrelevant": 5, "relevant": {"Relevance_Label_1": 1}},
        "q6": {"irrelevant": 20, "relevant": {"Relevance_Label_1": 0}},
    }


def test_classify_max_min_median():
    buckets = QueryTextWordClouds()._classify_queries(
        _judgements(), MAX_MIN_MEDIAN, 1.5
    )
    assert "irrelevant" in buckets
    assert "Relevance_Label_1" in buckets
    assert len(buckets["irrelevant"]["5_queries_most_assessments"]) == 5
    assert buckets["irrelevant"]["5_queries_least_assessments"][0] in {"q1"}


def test_classify_percentile_and_deviation_methods():
    analysis = QueryTextWordClouds()
    percentile = analysis._classify_queries(_judgements(), PERCENTILE, 1.5)
    assert "queries_above_95th_percentile" in percentile["irrelevant"]
    mad = analysis._classify_queries(_judgements(), MEDIAN_ABSOLUTE_DEVIATION, 1.0)
    assert "queries_above_threshold" in mad["irrelevant"]
    zscore = analysis._classify_queries(_judgements(), MODIFIED_Z_SCORE, 1.0)
    assert "queries_within_normal_range" in zscore["Relevance_Label_1"]


def test_classify_empty_judgements():
    assert QueryTextWordClouds()._classify_queries({}, MAX_MIN_MEDIAN, 1.5) == {}


def test_render_bucket_messages_and_image():
    analysis = QueryTextWordClouds()
    texts = {"q1": "alpha ranking retrieval", "q2": "beta search evaluation"}
    empty = analysis._render_bucket([], texts)
    assert isinstance(empty, ValueResult)
    assert "No queries" in empty.value

    single = analysis._render_bucket(["q1"], texts)
    assert isinstance(single, ValueResult)
    assert "Only query q1" in single.value

    with patch.object(analysis, "_build_word_cloud", return_value=None):
        missing = analysis._render_bucket(["q1", "q2"], texts)
        assert "Not enough distinct words" in missing.value

    with patch.object(analysis, "_build_word_cloud", return_value=b"png-bytes"):
        image = analysis._render_bucket(["q1", "q2"], texts)
        assert isinstance(image, ImageResult)
        assert image.image == b"png-bytes"


def test_clean_strips_stopwords_and_non_letters():
    cleaned = QueryTextWordClouds()._clean(
        "The RANKING of 12 documents, and retrieval!"
    )
    assert "the" not in cleaned.split()
    assert "ranking" in cleaned
    assert "12" not in cleaned


def test_build_word_cloud_handles_empty_and_value_error():
    analysis = QueryTextWordClouds()
    assert analysis._build_word_cloud("   ") is None

    with patch("core.lib.analyses.query_text_word_clouds.WordCloud") as mock_cls:
        mock_cls.return_value.generate.side_effect = ValueError("empty")
        assert analysis._build_word_cloud("ranking retrieval evaluation") is None

    with patch("core.lib.analyses.query_text_word_clouds.WordCloud") as mock_cls:
        image = MagicMock()

        def save(buffer, format):
            buffer.write(b"PNGDATA")

        image.save.side_effect = save
        mock_cls.return_value.generate.return_value.to_image.return_value = image
        assert analysis._build_word_cloud("ranking retrieval evaluation") == b"PNGDATA"


@patch("core.lib.analyses.query_text_word_clouds.load_queries_file")
def test_execute_returns_composite_of_buckets(mock_load, fake_task, fake_runs):
    mock_load.return_value = pd.DataFrame(
        {
            "query_id": ["q1", "q2"],
            "query_text": ["alpha ranking retrieval", "beta search evaluation"],
        }
    )
    with patch.object(
        QueryTextWordClouds, "_build_word_cloud", return_value=None
    ):
        result = QueryTextWordClouds().execute(
            fake_task,
            fake_runs,
            method=MAX_MIN_MEDIAN,
            threshold=1.5,
        )
    assert isinstance(result, CompositeResult)
    assert result.children
    assert all(
        isinstance(child, (ValueResult, ImageResult))
        for child in result.children.values()
    )
