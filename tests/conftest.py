import os

os.environ.setdefault("DJANGO_SECRET_KEY", "test-secret-key")
os.environ.setdefault("MODE", "DEBUG")

import pytest

from tests.fakes import make_fake_runs, make_fake_task, make_qrels_dataframe


@pytest.fixture
def qrels_df():
    return make_qrels_dataframe()


@pytest.fixture
def fake_task():
    return make_fake_task()


@pytest.fixture
def fake_runs(fake_task):
    return make_fake_runs(fake_task)
