from typing import Any, Dict, Mapping, Optional

import pytest
from dftracer.python import PARENT_SPAN_ID_KEY, TRACE_ID_KEY, WORKFLOW_ID_KEY
from dftracer.python.agent_langgraph import (
    get_or_init_trace_context,
    trace_invoke,
    traced_node,
)


class FakeApp:
    def __init__(self) -> None:
        self.last_state: Optional[Any] = None
        self.last_config: Optional[Mapping[str, Any]] = None

    def invoke(self, state: Any, config: Optional[Mapping[str, Any]] = None) -> Any:
        self.last_state = state
        self.last_config = config
        return {"ok": True, "state": state}


class TestAgentLangGraph:
    def test_get_or_init_trace_context_prefers_state(self):
        state = {
            TRACE_ID_KEY: "trace-a",
            WORKFLOW_ID_KEY: "wf-a",
            PARENT_SPAN_ID_KEY: "span-a",
        }
        config = {"configurable": {"thread_id": "thread-b"}}

        ctx = get_or_init_trace_context(state=state, config=config)
        assert ctx[TRACE_ID_KEY] == "trace-a"
        assert ctx[WORKFLOW_ID_KEY] == "wf-a"
        assert ctx[PARENT_SPAN_ID_KEY] == "span-a"

    def test_get_or_init_trace_context_uses_thread_id_when_missing(self):
        config = {"configurable": {"thread_id": "thread-1"}}
        ctx = get_or_init_trace_context(state={}, config=config)

        assert ctx[WORKFLOW_ID_KEY] == "thread-1"
        assert ctx[TRACE_ID_KEY] is not None

    def test_traced_node_adds_context_to_mapping_result(self):
        @traced_node("planner", agent_role="planner", step_event="plan")
        def planner(state: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
            return {"plan": "do_something"}

        result = planner({}, {"configurable": {"thread_id": "wf-1"}})
        assert result["plan"] == "do_something"
        assert result[WORKFLOW_ID_KEY] == "wf-1"
        assert TRACE_ID_KEY in result
        assert PARENT_SPAN_ID_KEY in result

    def test_traced_node_none_result_becomes_context_update(self):
        @traced_node("executor", step_event="act")
        def executor(state: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
            return None

        result = executor({}, {"configurable": {"thread_id": "wf-2"}})
        assert isinstance(result, dict)
        assert result[WORKFLOW_ID_KEY] == "wf-2"
        assert TRACE_ID_KEY in result
        assert PARENT_SPAN_ID_KEY in result

    def test_traced_node_passes_through_non_mapping_result(self):
        @traced_node("judge", step_event="reflect")
        def judge(state: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
            return 42

        result = judge({}, {"configurable": {"thread_id": "wf-3"}})
        assert result == 42

    def test_traced_node_rejects_unknown_step_event(self):
        with pytest.raises(ValueError, match="Unknown step_event"):
            traced_node("x", step_event="unknown")

    def test_trace_invoke_calls_app_and_returns_result(self):
        app = FakeApp()
        state = {"input": 1}
        config = {"configurable": {"thread_id": "wf-10"}}

        result = trace_invoke(app, state, config)
        assert result["ok"] is True
        assert app.last_state == state
        assert app.last_config == config

    def test_trace_invoke_without_config(self):
        app = FakeApp()
        state = {"input": 2}

        result = trace_invoke(app, state)
        assert result["ok"] is True
        assert app.last_state == state
        assert app.last_config is None

    def test_trace_invoke_requires_invoke_method(self):
        class NoInvoke:
            pass

        with pytest.raises(AttributeError, match="invoke"):
            trace_invoke(NoInvoke(), {})
