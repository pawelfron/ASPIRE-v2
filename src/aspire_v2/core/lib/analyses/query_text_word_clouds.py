from ..interfaces import Analysis, AnalysisForm, Result
from ...models import RetrievalRun, RetrievalTask
from ..results import CompositeResult, ImageResult, ValueResult
from ..utils.common import get_query_rel_judgements
from ..utils.data_loaders_v2 import load_queries_file
import io
import re

import numpy as np
from wordcloud import STOPWORDS, WordCloud

from django import forms

MAX_MIN_MEDIAN = "Max-Min-Median"
MEDIAN_ABSOLUTE_DEVIATION = "Median Absolute Deviation"
PERCENTILE = "Percentile-based method"
MODIFIED_Z_SCORE = "Modified Z-score"

# Only the deviation-based methods consult the threshold.
THRESHOLD_METHODS = (MEDIAN_ABSOLUTE_DEVIATION, MODIFIED_Z_SCORE)

BUCKET_LABELS = {
    "5_queries_most_assessments": "5 queries with the most assessments",
    "5_queries_around_median_assessments": "5 queries around the median",
    "5_queries_least_assessments": "5 queries with the fewest assessments",
    "queries_above_95th_percentile": "Queries above the 95th percentile",
    "queries_between_5th_95th_percentiles": (
        "Queries between the 5th and 95th percentiles"
    ),
    "queries_below_5th_percentile": "Queries below the 5th percentile",
    "queries_above_threshold": "Queries above the threshold",
    "queries_within_normal_range": "Queries within the normal range",
    "queries_below_threshold": "Queries below the threshold",
}

WORD_PATTERN = re.compile(r"\b[a-zA-Z]+\b")


class QueryTextWordCloudsForm(AnalysisForm):
    prefix = "query_text_word_clouds"

    method = forms.ChoiceField(
        label="Query sampling method",
        choices=[
            (MAX_MIN_MEDIAN, MAX_MIN_MEDIAN),
            (MEDIAN_ABSOLUTE_DEVIATION, MEDIAN_ABSOLUTE_DEVIATION),
            (PERCENTILE, PERCENTILE),
            (MODIFIED_Z_SCORE, MODIFIED_Z_SCORE),
        ],
        initial=MAX_MIN_MEDIAN,
    )
    threshold = forms.FloatField(
        label="Outlier threshold (used by the deviation-based methods only)",
        min_value=1.0,
        max_value=10.0,
        initial=1.5,
        widget=forms.NumberInput(attrs={"step": "0.1", "min": "1", "max": "10"}),
    )


class QueryTextWordClouds(Analysis):
    name = "Query Text Analysis based on Relevance Judgments"
    form_class = QueryTextWordCloudsForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        method = parameters["method"]
        threshold = float(parameters["threshold"])

        _, judgements = get_query_rel_judgements(retrieval_task.qrels_dataframe)
        queries = load_queries_file(retrieval_task)
        query_texts = dict(zip(queries["query_id"].astype(str), queries["query_text"]))

        buckets = self._classify_queries(judgements, method, threshold)

        results = {}
        for relevance_label, label_buckets in buckets.items():
            display_label = (
                "Relevance_Label_0 (Irrelevant)"
                if relevance_label == "irrelevant"
                else relevance_label
            )

            for bucket, query_ids in label_buckets.items():
                key = f"{display_label} - {BUCKET_LABELS.get(bucket, bucket)}"
                results[key] = self._render_bucket(query_ids, query_texts)

        return CompositeResult(results)

    def _classify_queries(
        self, judgements: dict, method: str, threshold: float
    ) -> dict[str, dict[str, list[str]]]:
        """Group queries into buckets by how many judgments each relevance label has."""
        query_ids = list(judgements)
        if not query_ids:
            return {}

        labels = ["irrelevant"] + list(judgements[query_ids[0]]["relevant"])

        counts = np.zeros((len(query_ids), len(labels)))
        for row, query_id in enumerate(query_ids):
            counts[row, 0] = judgements[query_id]["irrelevant"]
            for column, label in enumerate(labels[1:], start=1):
                counts[row, column] = judgements[query_id]["relevant"][label]

        buckets = {}
        for column, label in enumerate(labels):
            values = counts[:, column]

            if method == MAX_MIN_MEDIAN:
                ranked = np.argsort(values)
                closest_to_median = np.abs(values - np.median(values)).argsort()[:5]
                buckets[label] = {
                    "5_queries_most_assessments": [query_ids[i] for i in ranked[-5:]],
                    "5_queries_around_median_assessments": [
                        query_ids[i] for i in closest_to_median
                    ],
                    "5_queries_least_assessments": [query_ids[i] for i in ranked[:5]],
                }
                continue

            if method == PERCENTILE:
                lower, upper = np.percentile(values, [5, 95])
                bucket_names = (
                    "queries_above_95th_percentile",
                    "queries_between_5th_95th_percentiles",
                    "queries_below_5th_percentile",
                )
            else:
                median = np.median(values)
                deviation = np.median(np.abs(values - median))
                lower = median - threshold * deviation
                upper = median + threshold * deviation
                bucket_names = (
                    "queries_above_threshold",
                    "queries_within_normal_range",
                    "queries_below_threshold",
                )

            above = np.where(values > upper)[0]
            within = np.where((values >= lower) & (values <= upper))[0]
            below = np.where(values < lower)[0]

            buckets[label] = {
                bucket_names[0]: [query_ids[i] for i in above],
                bucket_names[1]: [query_ids[i] for i in within],
                bucket_names[2]: [query_ids[i] for i in below],
            }

        return buckets

    def _render_bucket(
        self, query_ids: list[str], query_texts: dict[str, str]
    ) -> Result:
        texts = [
            query_texts[str(query_id)]
            for query_id in query_ids
            if str(query_id) in query_texts
        ]

        if not texts:
            return ValueResult("No queries fall into this group.")

        if len(texts) == 1:
            return ValueResult(f"Only query {query_ids[0]}: {texts[0].strip()}")

        words = " ".join(self._clean(text) for text in texts)
        image = self._build_word_cloud(words)

        if image is None:
            return ValueResult(
                f"Not enough distinct words to build a word cloud for the "
                f"{len(texts)} queries in this group."
            )

        return ImageResult(image)

    def _clean(self, text: str) -> str:
        """Keep alphabetic words only, matching the original's preprocessing."""
        return " ".join(
            word for word in WORD_PATTERN.findall(text.lower()) if word not in STOPWORDS
        )

    def _build_word_cloud(self, words: str) -> bytes | None:
        if not words.strip():
            return None

        try:
            word_cloud = WordCloud(
                width=800,
                height=400,
                background_color="white",
                max_words=50,
                min_font_size=10,
                collocations=False,
                min_word_length=3,
            ).generate(words)
        except ValueError:
            return None

        buffer = io.BytesIO()
        word_cloud.to_image().save(buffer, format="PNG")

        return buffer.getvalue()
