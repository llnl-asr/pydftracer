import glob
import gzip
import json
import os
import shutil
from typing import List

import dftracer.python.ai_common as ai_common
import pytest
from dftracer.python import (
    AGENT_ID_KEY,
    AGENT_ROLE_KEY,
    COMPLETION_TOKENS_KEY,
    ERROR_TYPE_KEY,
    FORMAT_KEY,
    FRAMEWORK_KEY,
    LLM,
    LLM_CALL_ID_KEY,
    LOGICAL_PATH_KEY,
    MESSAGE_TYPE_KEY,
    MODEL_NAME_KEY,
    OPERATION_KIND_KEY,
    PARENT_SPAN_ID_KEY,
    PHYSICAL_PATH_KEY,
    PROMPT_TOKENS_KEY,
    RUN_ID_KEY,
    SPAN_ID_KEY,
    STEP_ID_KEY,
    SUCCESS_KEY,
    TOOL_CALL_ID_KEY,
    TOTAL_TOKENS_KEY,
    TRACE_ID_KEY,
    WORKFLOW_ID_KEY,
    Agent,
    AgentCategory,
    AgentData,
    AgentDataEvent,
    AgentStep,
    AgentStepEvent,
    Judge,
    JudgeEvent,
    LLMEvent,
    Message,
    MessageEvent,
    Tool,
    ToolEvent,
    Workflow,
    WorkflowEvent,
    agent,
    agent_data,
    agent_step,
    dftracer,
    judge,
    llm,
    message,
    tool,
    workflow,
)
from dftracer.python import (
    data as ai_data,
)

from .utils import run_test_in_spawn_process


def run_agent_trace_args_test(test_config):
    base_dir = os.path.join(os.path.dirname(__file__), "test_agent_output")
    test_base_dir = os.path.join(base_dir, test_config["name"])
    os.makedirs(test_base_dir, exist_ok=True)
    log_file = os.path.join(test_base_dir, "agent_trace.pfw")

    try:
        df_logger = dftracer.initialize_log(log_file, None, -1)
        with workflow.run(
            args={
                TRACE_ID_KEY: "trace-1",
                WORKFLOW_ID_KEY: "workflow-1",
                OPERATION_KIND_KEY: "workflow",
            }
        ):
            with tool.call(
                args={
                    TRACE_ID_KEY: "trace-1",
                    WORKFLOW_ID_KEY: "workflow-1",
                    OPERATION_KIND_KEY: "tool_call",
                    "tool_name": "list_dir",
                }
            ):
                pass
            with llm.call(
                args={
                    TRACE_ID_KEY: "trace-1",
                    WORKFLOW_ID_KEY: "workflow-1",
                    MODEL_NAME_KEY: "test-model",
                    OPERATION_KIND_KEY: "generate",
                }
            ) as span:
                span.update_args(
                    {
                        PROMPT_TOKENS_KEY: 11,
                        COMPLETION_TOKENS_KEY: 7,
                        TOTAL_TOKENS_KEY: 18,
                    }
                )
        df_logger.finalize()

        trace_files = glob.glob(log_file.replace(".pfw", "*.pfw")) + glob.glob(
            log_file.replace(".pfw", "*.pfw.gz")
        )
        assert trace_files, f"No trace files found for {log_file}"

        events = {}
        for trace_file in trace_files:
            opener = gzip.open if trace_file.endswith(".gz") else open
            with opener(trace_file, "rt", errors="ignore") as handle:
                for line in handle:
                    line = line.strip()
                    if not line or line[0] in "[]":
                        continue
                    event = json.loads(line)
                    if event.get("cat") in {"workflow", "tool", "llm"}:
                        events[event["cat"]] = event

        assert events["workflow"]["args"][WORKFLOW_ID_KEY] == "workflow-1"
        assert events["workflow"]["args"][OPERATION_KIND_KEY] == "workflow"
        assert events["tool"]["args"]["tool_name"] == "list_dir"
        assert events["tool"]["args"][TRACE_ID_KEY] == "trace-1"
        assert events["llm"]["args"][MODEL_NAME_KEY] == "test-model"
        assert events["llm"]["args"][PROMPT_TOKENS_KEY] == 11
        assert events["llm"]["args"][COMPLETION_TOKENS_KEY] == 7
        assert events["llm"]["args"][TOTAL_TOKENS_KEY] == 18
        return True
    finally:
        shutil.rmtree(test_base_dir, ignore_errors=True)


class _FakeTracer:
    """Stands in for the core tracer, so spans can be built in-process."""

    def get_instance(self):
        return self

    def mark_used(self, *_args):
        pass


@pytest.fixture
def tracing_on(monkeypatch):
    """Record span args in-process, on spans that start clean.

    Args are only stored when DFTRACER_ENABLE is on, and the module-level
    spans are shared, so give the two spans these tests use empty arg tables.
    """
    monkeypatch.setattr(ai_common, "dftracer", _FakeTracer())
    monkeypatch.setattr(ai_common, "DFTRACER_ENABLE", True)
    for span in (tool.call, llm.call):
        for table in ("_arguments_int", "_arguments_float", "_arguments_string"):
            monkeypatch.setattr(span.profiler, table, {})


class TestAgentModule:
    def test_agent_categories_exist(self):
        assert isinstance(agent, Agent)
        assert isinstance(workflow, Workflow)
        assert isinstance(agent_step, AgentStep)
        assert isinstance(llm, LLM)
        assert isinstance(tool, Tool)
        assert isinstance(agent_data, AgentData)
        assert isinstance(message, Message)
        assert isinstance(judge, Judge)

    def test_agent_category_children(self):
        assert hasattr(workflow, "run")
        assert hasattr(workflow, "resume")

        assert hasattr(agent_step, "plan")
        assert hasattr(agent_step, "act")
        assert hasattr(agent_step, "observe")
        assert hasattr(agent_step, "reflect")

        assert hasattr(llm, "call")
        assert hasattr(llm, "stream")
        assert hasattr(llm, "parse")

        assert hasattr(tool, "call")
        assert hasattr(tool, "result")

        assert hasattr(agent_data, "load")
        assert hasattr(agent_data, "save")

        assert hasattr(message, "send")
        assert hasattr(message, "receive")
        assert hasattr(message, "stream")

        assert hasattr(judge, "evaluate")
        assert hasattr(judge, "retry")

    def test_agent_decorator_usage(self):
        @workflow.run
        def run_workflow(x: int) -> int:
            return x + 1

        @agent_step.plan
        def plan_step(x: int) -> int:
            return x * 2

        @tool.call
        def call_tool(x: int) -> int:
            return x - 3

        @llm.call
        def call_llm(x: int) -> int:
            return x

        assert run_workflow(3) == 4
        assert plan_step(4) == 8
        assert call_tool(10) == 7
        assert call_llm(5) == 5

    def test_agent_context_manager_usage(self):
        events: List[str] = []

        with workflow.run:
            events.append("workflow")
            with agent_step.act:
                events.append("step")
            with tool.call:
                events.append("tool")
            with judge.evaluate:
                events.append("judge")

        assert events == ["workflow", "step", "tool", "judge"]

    def test_agent_enable_disable_propagation(self):
        agent.enable()
        assert agent.profiler._enable
        assert workflow.profiler._enable
        assert llm.profiler._enable

        agent.disable()
        assert not agent.profiler._enable
        assert not workflow.profiler._enable
        assert not llm.profiler._enable

        agent.enable()
        assert agent.profiler._enable
        assert workflow.profiler._enable
        assert llm.profiler._enable

    def test_agent_derive_cached_children(self):
        child1 = tool.call.derive("weather")
        child2 = tool.call.derive("weather")
        child3 = tool.call.derive("search")

        assert child1 is child2
        assert child1 is not child3

    def test_agent_iter_method(self):
        data_list = [1, 2, 3]
        result = list(agent_step.act.iter(iter(data_list)))
        assert result == data_list

    def test_agent_init_method(self):
        @tool.init
        def setup_tooling() -> str:
            return "ok"

        assert setup_tooling() == "ok"

    def test_agent_update(self):
        # Ensure the API accepts canonical metadata keys via generic args.
        agent.update(
            args={
                TRACE_ID_KEY: "trace-1",
                WORKFLOW_ID_KEY: "wf-1",
                RUN_ID_KEY: "run-1",
                STEP_ID_KEY: "step-1",
                AGENT_ID_KEY: "planner",
                AGENT_ROLE_KEY: "planner",
                SPAN_ID_KEY: "span-1",
                PARENT_SPAN_ID_KEY: "span-0",
                TOOL_CALL_ID_KEY: "tool-1",
                LLM_CALL_ID_KEY: "llm-1",
                FRAMEWORK_KEY: "plain_python",
                MODEL_NAME_KEY: "test-model",
                MESSAGE_TYPE_KEY: "ToolCallRequestEvent",
                LOGICAL_PATH_KEY: "dataset.input",
                PHYSICAL_PATH_KEY: "/tmp/input.npy",
                FORMAT_KEY: "npy",
                OPERATION_KIND_KEY: "tool_call",
                SUCCESS_KEY: 1,
                ERROR_TYPE_KEY: "",
            }
        )

    def test_agent_context_manager_args_stay_on_returned_span(self, tracing_on):
        span = tool.call(
            args={
                TRACE_ID_KEY: "trace-ctx",
                WORKFLOW_ID_KEY: "workflow-ctx",
                OPERATION_KIND_KEY: "tool_call",
                "tool_name": "list_dir",
            }
        )

        if span.profiler._enable:
            assert span.profiler._arguments_string[TRACE_ID_KEY][1] == "trace-ctx"
            assert span.profiler._arguments_string[WORKFLOW_ID_KEY][1] == "workflow-ctx"
            assert span.profiler._arguments_string[OPERATION_KIND_KEY][1] == "tool_call"
            assert span.profiler._arguments_string["tool_name"][1] == "list_dir"
            assert TRACE_ID_KEY not in tool.call.profiler._arguments_string

    def test_agent_update_args_mutates_active_span(self, tracing_on):
        span = llm.call(
            args={
                TRACE_ID_KEY: "trace-llm",
                WORKFLOW_ID_KEY: "workflow-llm",
                MODEL_NAME_KEY: "test-model",
            }
        )
        span.update_args(
            {
                PROMPT_TOKENS_KEY: 11,
                COMPLETION_TOKENS_KEY: 7,
                TOTAL_TOKENS_KEY: 18,
            }
        )

        if span.profiler._enable:
            assert span.profiler._arguments_string[TRACE_ID_KEY][1] == "trace-llm"
            assert span.profiler._arguments_string[WORKFLOW_ID_KEY][1] == "workflow-llm"
            assert span.profiler._arguments_string[MODEL_NAME_KEY][1] == "test-model"
            assert span.profiler._arguments_int[PROMPT_TOKENS_KEY][1] == 11
            assert span.profiler._arguments_int[COMPLETION_TOKENS_KEY][1] == 7
            assert span.profiler._arguments_int[TOTAL_TOKENS_KEY][1] == 18

    def test_names_do_not_collide_with_ai_aliases(self):
        assert ai_data is not agent_data

    def test_agent_trace_emits_context_manager_args(self):
        run_test_in_spawn_process(
            run_agent_trace_args_test,
            {
                "name": "agent_trace_args",
                "env": {
                    "DFTRACER_ENABLE": "1",
                    "DFTRACER_INC_METADATA": "1",
                    "DFTRACER_TRACE_COMPRESSION": "1",
                    "DFTRACER_DISABLE_IO": "1",
                    # Aggregation turns short spans into counters without args.
                    "DFTRACER_ENABLE_AGGREGATION": "0",
                },
            },
        )


class TestAgentEnumerations:
    def test_agent_category_values(self):
        assert AgentCategory.WORKFLOW == "workflow"
        assert AgentCategory.STEP == "step"
        assert AgentCategory.LLM == "llm"
        assert AgentCategory.TOOL == "tool"
        assert AgentCategory.DATA == "data"
        assert AgentCategory.MESSAGE == "message"
        assert AgentCategory.JUDGE == "judge"

    def test_agent_event_values(self):
        assert WorkflowEvent.RUN == "run"
        assert WorkflowEvent.RESUME == "resume"

        assert AgentStepEvent.PLAN == "plan"
        assert AgentStepEvent.ACT == "act"

        assert LLMEvent.CALL == "call"
        assert LLMEvent.STREAM == "stream"

        assert ToolEvent.CALL == "call"
        assert ToolEvent.RESULT == "result"

        assert AgentDataEvent.LOAD == "load"
        assert AgentDataEvent.SAVE == "save"

        assert MessageEvent.SEND == "send"
        assert MessageEvent.RECEIVE == "receive"

        assert JudgeEvent.EVALUATE == "evaluate"
        assert JudgeEvent.RETRY == "retry"
