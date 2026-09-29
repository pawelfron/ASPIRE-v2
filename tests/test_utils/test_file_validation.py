import pandas as pd
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from core.forms import RetrievalRunUploadForm, RetrievalTaskUploadForm
from core.lib.utils.file_validation import (
    validate_qrels_file,
    validate_run_file,
    validate_topics_file,
)
from tests.fakes import QRELS_TEXT, RUN_A_TEXT, TOPICS_XML


def _upload(name: str, content: str | bytes) -> SimpleUploadedFile:
    data = content.encode() if isinstance(content, str) else content
    return SimpleUploadedFile(name, data)


def test_valid_qrels_round_trips_for_the_loader():
    uploaded = _upload("qrels.txt", QRELS_TEXT)
    validate_qrels_file(uploaded)

    frame = pd.read_csv(
        uploaded,
        sep=" ",
        names=["query_id", "iteration", "doc_id", "relevance"],
    )
    assert len(frame) == 6
    assert frame.loc[0, "doc_id"] == "d1"


def test_qrels_allows_blank_lines_and_negative_relevance():
    validate_qrels_file(_upload("qrels.txt", "\nq1 0 d1 -1\n\n"))


def test_qrels_rejects_empty_missing_extra_and_non_integer_rows():
    with pytest.raises(ValidationError, match="empty"):
        validate_qrels_file(_upload("qrels.txt", "\n\n"))

    with pytest.raises(ValidationError, match="Line 1"):
        validate_qrels_file(_upload("qrels.txt", "q1 0 d1"))

    with pytest.raises(ValidationError, match="Line 1"):
        validate_qrels_file(_upload("qrels.txt", "q1 0 d1 0 extra"))

    with pytest.raises(ValidationError, match="relevance"):
        validate_qrels_file(_upload("qrels.txt", "q1 0 d1 x"))

    with pytest.raises(ValidationError, match="Line 1"):
        validate_qrels_file(_upload("qrels.txt", "q1  0  d1  0"))

    with pytest.raises(ValidationError, match="Line 1"):
        validate_qrels_file(_upload("qrels.txt", "q1\t0\td1\t0"))


def test_qrels_rejects_relevance_outside_int32_and_non_utf8():
    with pytest.raises(ValidationError, match="32-bit"):
        validate_qrels_file(_upload("qrels.txt", "q1 0 d1 2147483648"))

    uploaded = _upload("qrels.txt", b"\xff")
    with pytest.raises(ValidationError, match="UTF-8"):
        validate_qrels_file(uploaded)
    assert uploaded.read() == b"\xff"


def test_valid_topics_and_structural_failures():
    uploaded = _upload("topics.xml", TOPICS_XML)
    validate_topics_file(uploaded)
    assert uploaded.read().decode().startswith("<?xml")

    validate_topics_file(
        _upload(
            "topics.xml",
            '<topics><topic number="q1"><query>alpha</query></topic></topics>',
        )
    )
    validate_topics_file(_upload("topics.xml", '<topic number="q1"/>'))

    with pytest.raises(ValidationError, match="empty"):
        validate_topics_file(_upload("topics.xml", b""))

    with pytest.raises(ValidationError, match="empty"):
        validate_topics_file(_upload("topics.xml", "   "))

    with pytest.raises(ValidationError, match="not valid XML"):
        validate_topics_file(_upload("topics.xml", "<topics>"))

    with pytest.raises(ValidationError, match="at least one"):
        validate_topics_file(_upload("topics.xml", "<topics></topics>"))

    with pytest.raises(ValidationError, match="Topic 1"):
        validate_topics_file(_upload("topics.xml", "<topic>alpha</topic>"))

    with pytest.raises(ValidationError, match="Topic 2"):
        validate_topics_file(
            _upload(
                "topics.xml",
                "<topics>"
                '<topic number="q1">a</topic>'
                '<topic number=" ">b</topic>'
                "</topics>",
            )
        )


def test_valid_run_round_trips_and_rejects_bad_rows():
    uploaded = _upload("run.txt", RUN_A_TEXT)
    validate_run_file(uploaded)
    frame = pd.read_csv(
        uploaded,
        sep="\t",
        names=["query_id", "iteration", "doc_id", "rank", "score", "tag"],
    )
    assert frame.loc[0, "tag"] == "run-a"

    validate_run_file(_upload("run.txt", "q1\tQ0\td2\t1\t10\trun-a\n\n"))
    validate_run_file(_upload("run.txt", "q1\tQ0\td2\t1\t1e-3\trun-a\n"))

    with pytest.raises(ValidationError, match="empty"):
        validate_run_file(_upload("run.txt", ""))

    with pytest.raises(ValidationError, match="Line 1"):
        validate_run_file(_upload("run.txt", "q1 Q0 d2 1 10.0 run-a"))

    with pytest.raises(ValidationError, match="Line 2"):
        validate_run_file(
            _upload("run.txt", "q1\tQ0\td2\t1\t10.0\trun-a\nq2\tQ0\td1\t1\t9\n")
        )

    with pytest.raises(ValidationError, match="rank"):
        validate_run_file(_upload("run.txt", "q1\tQ0\td2\tx\t10.0\trun-a"))

    with pytest.raises(ValidationError, match="score"):
        validate_run_file(_upload("run.txt", "q1\tQ0\td2\t1\tfoo\trun-a"))

    with pytest.raises(ValidationError, match="finite"):
        validate_run_file(_upload("run.txt", "q1\tQ0\td2\t1\tnan\trun-a"))


def _validate_without_saving(form):
    # ModelForm._post_clean checks uniqueness against the database. These tests
    # only need the field cleaners.
    form._post_clean = lambda: None
    return form.is_valid()


def test_task_upload_form_reports_field_errors_and_keeps_valid_files():
    bad = RetrievalTaskUploadForm(
        data={"title": "Task", "description": ""},
        files={
            "qrels": _upload("qrels.txt", "nope"),
            "topics": _upload("topics.xml", "<nope"),
        },
    )
    assert _validate_without_saving(bad) is False
    assert "four" in bad.errors["qrels"][0]
    assert "not valid XML" in bad.errors["topics"][0]

    good = RetrievalTaskUploadForm(
        data={"title": "Task", "description": ""},
        files={
            "qrels": _upload("qrels.txt", QRELS_TEXT),
            "topics": _upload("topics.xml", TOPICS_XML),
        },
    )
    assert _validate_without_saving(good) is True
    assert good.cleaned_data["qrels"].read() == QRELS_TEXT.encode()
    assert good.cleaned_data["topics"].read().startswith(b"<?xml")


def test_run_upload_form_validates_the_run_file():
    bad = RetrievalRunUploadForm(
        user=1,
        data={"title": "Run", "description": "", "ir_task": ""},
        files={"file": _upload("run.txt", "not\ta\trun")},
    )
    assert _validate_without_saving(bad) is False
    assert "six" in bad.errors["file"][0]

    good = RetrievalRunUploadForm(
        user=1,
        data={"title": "Run", "description": "", "ir_task": ""},
        files={"file": _upload("run.txt", RUN_A_TEXT)},
    )
    assert _validate_without_saving(good) is False
    assert "file" not in good.errors
    assert good.files["file"].read() == RUN_A_TEXT.encode()
