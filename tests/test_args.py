"""List args on events (dft_fn.append, log_event list_args) and metadata
records with fields (log_metadata_event fields), as sent to the native
module. The native module's output is tested in dftracer (test/py/test_args.py,
test/check_args_trace.py)."""

from unittest.mock import MagicMock

import pytest
from dftracer.python import dft_fn, dftracer
from dftracer.python.env import DFTRACER_ENABLE

pytestmark = pytest.mark.skipif(
    not DFTRACER_ENABLE, reason="DFTRACER_ENABLE=0 makes every call a no-op"
)


@pytest.fixture
def logger():
    tracer = dftracer.get_instance()
    original = tracer.logger
    tracer.logger = MagicMock(
        spec=["get_time", "enter_event", "exit_event", "log_event", "log_metadata_event"]
    )
    tracer.logger.get_time.return_value = 0
    try:
        yield tracer.logger
    finally:
        tracer.logger = original


def test_append_builds_lists_in_order(logger):
    fn = dft_fn("PY_APP", name="read")
    fn.append("files", "a.h5").append("files", "b.h5")
    fn.append("links", "x", sub="in").append("links", "y", sub="out")
    fn.flush()
    assert logger.log_event.call_args[1]["list_args"] == {
        "files": ["a.h5", "b.h5"],
        "links": {"in": ["x"], "out": ["y"]},
    }


def test_no_lists_no_list_args(logger):
    dft_fn("PY_APP", name="read").flush()
    assert "list_args" not in logger.log_event.call_args[1]


def test_reset_clears_lists(logger):
    fn = dft_fn("PY_APP", name="read")
    fn.append("files", "a.h5")
    fn.reset()
    assert fn._lists == {}


def test_metadata_fields_reach_the_logger(logger):
    fields = {"id": "s1", "n": 4, "tags": ["x"]}
    dftracer.get_instance().log_metadata_event("SAMPLE", fields=fields)
    assert logger.log_metadata_event.call_args[1] == {
        "key": "SAMPLE",
        "value": "",
        "fields": fields,
    }


def test_metadata_without_fields_is_unchanged(logger):
    dftracer.get_instance().log_metadata_event("epoch", "1")
    assert logger.log_metadata_event.call_args[1] == {"key": "epoch", "value": "1"}
