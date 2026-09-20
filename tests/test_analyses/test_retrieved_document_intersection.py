from core.lib.analyses.retrieved_document_intersection import (
    RetrievedDocumentIntersectionForm,
    RetrievedDocumentInterseciton,
)
from core.lib.results.table import TableResult


def test_form_populates_baseline_choices(fake_task, fake_runs):
    empty = RetrievedDocumentIntersectionForm()
    assert list(dict(empty.fields["baseline_run"].choices)) == [""]
    form = RetrievedDocumentIntersectionForm(
        retrieval_task=fake_task, retrieval_runs=fake_runs
    )
    assert form.prefix == "retrieved_document_intersection"
    assert fake_runs[1].id in dict(form.fields["baseline_run"].choices)


def test_execute_uses_matching_baseline_and_drops_it(fake_task, fake_runs):
    result = RetrievedDocumentInterseciton().execute(
        fake_task,
        fake_runs,
        cutoff=1,
        baseline_run=str(fake_runs[0].id),
    )
    assert isinstance(result, TableResult)
    frame = result.dataframe
    assert list(frame.index) == ["run-b"]
    assert "run-a" not in frame.index
    assert frame.loc["run-b", "Intersected Documents"] == 2
    assert frame.loc["run-b", "Total Documents"] == 2
    assert frame.loc["run-b", "Intersection Percentage"] == 100.0
