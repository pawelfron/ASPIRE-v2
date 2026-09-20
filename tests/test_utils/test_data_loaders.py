from types import SimpleNamespace

from tests.fakes import (
    QRELS_TEXT,
    RUN_A_TEXT,
    TOPICS_XML,
    FakeFieldFile,
    make_fake_run,
    make_fake_task,
)

from core.lib.utils.data_loaders_v2 import (
    load_qrel_file,
    load_queries_file,
    load_run_file,
)


def test_load_qrel_file_parses_space_separated_rows():
    task = make_fake_task()
    task.qrels = FakeFieldFile(QRELS_TEXT)
    frame = load_qrel_file(task)

    assert list(frame.columns) == ["query_id", "iteration", "doc_id", "relevance"]
    assert set(frame["query_id"]) == {"q1", "q2"}
    assert frame.loc[frame["doc_id"] == "d3", "relevance"].iloc[0] == 2


def test_load_queries_file_reads_topic_number_and_text():
    task = SimpleNamespace(topics=FakeFieldFile(TOPICS_XML))
    frame = load_queries_file(task)

    assert list(frame["query_id"]) == ["q1", "q2"]
    assert "alpha" in frame.loc[0, "query_text"]
    assert "beta" in frame.loc[1, "query_text"]


def test_load_run_file_parses_tab_separated_rows():
    task = make_fake_task()
    run = make_fake_run(task, title="run-a")
    run.file = FakeFieldFile(RUN_A_TEXT)
    frame = load_run_file(run)

    assert list(frame.columns) == [
        "query_id",
        "iteration",
        "doc_id",
        "rank",
        "score",
        "tag",
    ]
    assert frame.loc[0, "doc_id"] == "d2"
    assert int(frame.loc[0, "rank"]) == 1
    assert frame.loc[0, "tag"] == "run-a"
