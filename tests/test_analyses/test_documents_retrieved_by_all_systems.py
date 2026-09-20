from core.lib.analyses.documents_retrieved_by_all_systems import (
    DocumentsRetrievedByAllSystems,
    DocumentsRetrievedByAllSystemsForm,
)
from core.lib.results.composite import CompositeResult
from core.lib.results.value import ValueResult


def test_form_prefix_and_defaults():
    form = DocumentsRetrievedByAllSystemsForm()
    assert form.prefix == "documents_retrieved_by_all_systems"
    assert form.fields["cutoff"].initial == 1
    assert form.fields["sample_size"].initial == 10


def test_execute_finds_docs_retrieved_by_every_run(fake_task, fake_runs):
    result = DocumentsRetrievedByAllSystems().execute(
        fake_task, fake_runs, cutoff=1, sample_size=10
    )
    assert isinstance(result, CompositeResult)
    common_queries = result.children["Number of common queries"]
    query_ids = result.children["Queries with documents retrieved by all systems"]
    sample = result.children["Sample of documents retrieved by all systems"]
    assert isinstance(common_queries, ValueResult)
    assert common_queries.value == 2
    assert set(query_ids.value.split(", ")) == {"q1", "q2"}
    assert set(sample.value.split(", ")) == {"d1", "d2"}
