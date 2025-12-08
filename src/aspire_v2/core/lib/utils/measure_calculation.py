from ir_measures import parse_measure, calc_aggregate

from ..interfaces import Measure
from ...models import MeasureValue, RetrievalRun


def get_measure_value(retrieval_run: RetrievalRun, measure: Measure) -> float:
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
