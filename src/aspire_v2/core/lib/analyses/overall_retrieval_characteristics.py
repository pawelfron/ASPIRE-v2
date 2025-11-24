from ..interfaces import Analysis, Result, AnalysisForm
from ..results import TableResult
import pandas as pd
from ir_measures import parse_measure, calc_aggregate

from django import forms


class OverallRetrievalCharacteristicsForm(forms.Form):
    prefix = "overall_retrieval_characteristics"


class OverallRetrievalCharacteristics(Analysis):
    name = "Overall Retrieval Characteristics"
    form_class = OverallRetrievalCharacteristicsForm

    def execute(
        self,
        qrels: pd.DataFrame,
        queries: pd.DataFrame,
        retrieval_runs: dict[str, pd.DataFrame],
        **parameters: dict,
    ) -> Result:
        measure_names = {
            "NumQ": "Total Queries",
            "NumRet": "Retrieved Documents",
            "NumRel": "Relevant Documents",
            "NumRelRet": "Relevant Retrieved Documents",
        }
        measures = [parse_measure(measure_name) for measure_name in measure_names]

        agg_result = [
            calc_aggregate(measures, qrels, retrieval_run)
            for retrieval_run in retrieval_runs.values()
        ]

        clean_results = []
        for res in agg_result:
            clean_result = {}
            for measure in measures:
                clean_result[str(measure)] = res[measure]
            clean_results.append(clean_result)

        result = pd.DataFrame(clean_results, index=retrieval_runs.keys())

        return TableResult(result)
