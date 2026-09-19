from ..interfaces import Analysis, Measure, RelevanceThresholdForm, Result
from ...models import RetrievalRun, RetrievalTask
from ..measures import PercentageOfRelevantDocsInCutoff, nDCG
from ..results import CompositeResult, PlotResult, TableResult
from ..utils.per_query import (
    format_number,
    format_query_ids,
    get_per_query_measures,
    per_measure_bar_figure,
)
import numpy as np
import pandas as pd


class PerQueryPerformanceForm(RelevanceThresholdForm):
    prefix = "per_query_performance"


class PerQueryPerformance(Analysis):
    name = "Experimental Evaluation per Query"
    form_class = PerQueryPerformanceForm

    def execute(
        self,
        retrieval_task: RetrievalTask,
        retrieval_runs: list[RetrievalRun],
        **parameters: dict,
    ) -> Result:
        relevance_threshold = int(parameters["relevance_threshold"])

        measures: list[Measure] = [
            nDCG(cutoff=10, judged_only=False, dcg="log2"),
            PercentageOfRelevantDocsInCutoff(
                rel=relevance_threshold, cutoff=10, judged_only=False
            ),
        ]
        measure_names = [measure.measure_name for measure in measures]

        values, query_ids = get_per_query_measures(retrieval_runs, measures)
        data = {
            measure_name: {
                run_title: list(values[run_title][measure_name].values())
                for run_title in values
            }
            for measure_name in measure_names
        }

        results = {
            "Per-query performance": PlotResult(
                per_measure_bar_figure(
                    data,
                    query_ids,
                    "Performance measures across queries",
                    row_height=450,
                )
            )
        }

        if len(retrieval_runs) > 1:
            consistency = pd.DataFrame(
                index=[
                    "Queries with equal performance across experiments",
                    "Large-gap threshold (1.5 x IQR)",
                    "Queries with large performance gaps",
                ]
            )

            for measure_name in measure_names:
                equal, gaps, threshold = self._compare_runs(
                    data[measure_name], query_ids
                )
                consistency[measure_name] = [
                    format_query_ids(equal),
                    format_number(threshold),
                    format_query_ids([query_id for query_id, _, _ in gaps]),
                ]

                if gaps:
                    results[f"Large performance gaps - {measure_name}"] = TableResult(
                        pd.DataFrame(
                            [
                                [lowest, highest, highest - lowest]
                                for _, lowest, highest in gaps
                            ],
                            index=[query_id for query_id, _, _ in gaps],
                            columns=["Minimum", "Maximum", "Gap"],
                        ).round(3)
                    )

            results["Cross-experiment consistency"] = TableResult(consistency)

        return CompositeResult(results)

    def _compare_runs(
        self, per_run: dict[str, list[float]], query_ids: list[str]
    ) -> tuple[list[str], list[tuple[str, float, float]], float]:
        """Find queries every run scores alike, and queries whose spread is unusual.

        A spread counts as unusual when it exceeds 1.5 times the interquartile range
        of the measure across all runs and queries, so the cutoff adapts to each
        measure's own scale.
        """
        all_values = [value for values in per_run.values() for value in values]
        if not all_values:
            return [], [], 0.0

        first_quartile, third_quartile = np.percentile(all_values, [25, 75])
        threshold = float(1.5 * (third_quartile - first_quartile))

        equal = []
        gaps = []
        for index, query_id in enumerate(query_ids):
            across_runs = [values[index] for values in per_run.values()]
            lowest, highest = min(across_runs), max(across_runs)

            if highest - lowest < 1e-6:
                equal.append(query_id)
            elif highest - lowest > threshold:
                gaps.append((query_id, lowest, highest))

        return equal, gaps, threshold
