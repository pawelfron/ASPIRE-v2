from ir_measures import parse_measure, calc_aggregate, iter_calc

from ..interfaces import Measure
from ...models import MeasureValue, RetrievalRun


def get_aggregate_measure(retrieval_run: RetrievalRun, measure: Measure) -> float:
    try:
        measure_value = MeasureValue.objects.get(
            pk=(retrieval_run.id, measure.measure_name)
        )
        return measure_value.value
    except MeasureValue.DoesNotExist:
        run_df = retrieval_run.dataframe
        qrels_df = retrieval_run.ir_task.qrels_dataframe
        ir_measure = parse_measure(measure.measure_name)

        agg = calc_aggregate([ir_measure], qrels_df, run_df)
        value = agg[ir_measure]
        MeasureValue.objects.create(
            retrieval_run=retrieval_run,
            measure_name=measure.measure_name,
            value=value,
        )
        return value


def get_per_query_measure(
    retrieval_run: RetrievalRun, measure: Measure
) -> dict[str, float]:
    run_df = retrieval_run.dataframe
    qrels_df = retrieval_run.ir_task.qrels_dataframe
    ir_measure = parse_measure(measure.measure_name)

    result = {}
    for query_result in iter_calc([ir_measure], qrels_df, run_df):
        result[query_result.query_id] = query_result.value

    return result
