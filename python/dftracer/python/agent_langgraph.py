import uuid
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional

from dftracer.python.agent_common import (
    AGENT_ID_KEY,
    AGENT_ROLE_KEY,
    FRAMEWORK_KEY,
    OPERATION_KIND_KEY,
    PARENT_SPAN_ID_KEY,
    RUN_ID_KEY,
    SPAN_ID_KEY,
    STEP_ID_KEY,
    TRACE_ID_KEY,
    WORKFLOW_ID_KEY,
)
from dftracer.python.agent_init import agent_step, workflow
from dftracer.python.ai_common import DFTracerAI
from dftracer.python.common import P, R

DEFAULT_FRAMEWORK_NAME = "langgraph"
DEFAULT_WORKFLOW_EVENT_NAME = "langgraph.invoke"
DEFAULT_NODE_OPERATION_KIND = "node"
DEFAULT_WORKFLOW_OPERATION_KIND = "workflow"


def _new_id() -> str:
    return uuid.uuid4().hex


def _extract_thread_id(config: Optional[Mapping[str, Any]]) -> Optional[str]:
    if not config:
        return None
    configurable = config.get("configurable")
    if not isinstance(configurable, Mapping):
        return None
    thread_id = configurable.get("thread_id")
    if thread_id is None:
        return None
    return str(thread_id)


def _prune_none_values(args: Dict[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in args.items() if v is not None}


def _get_step_event_tracer(step_event: str) -> DFTracerAI:
    tracer: Optional[DFTracerAI] = getattr(agent_step, step_event, None)
    if tracer is None:
        valid_events = ", ".join(sorted(agent_step._children.keys()))
        raise ValueError(
            f"Unknown step_event '{step_event}'. Valid values: {valid_events}"
        )
    return tracer


def get_or_init_trace_context(
    state: Optional[Mapping[str, Any]] = None,
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Optional[str]]:
    state = state or {}

    trace_id = state.get(TRACE_ID_KEY)
    if trace_id is not None:
        trace_id = str(trace_id)
    if not trace_id:
        trace_id = _new_id()

    workflow_id = state.get(WORKFLOW_ID_KEY)
    if workflow_id is not None:
        workflow_id = str(workflow_id)
    if not workflow_id:
        workflow_id = _extract_thread_id(config) or _new_id()

    parent_span_id = state.get(PARENT_SPAN_ID_KEY)
    if parent_span_id is not None:
        parent_span_id = str(parent_span_id)

    return {
        TRACE_ID_KEY: trace_id,
        WORKFLOW_ID_KEY: workflow_id,
        PARENT_SPAN_ID_KEY: parent_span_id,
    }


def _merge_trace_updates(
    updates: MutableMapping[str, Any], trace_id: str, workflow_id: str, span_id: str
) -> MutableMapping[str, Any]:
    updates.setdefault(TRACE_ID_KEY, trace_id)
    updates.setdefault(WORKFLOW_ID_KEY, workflow_id)
    updates.setdefault(PARENT_SPAN_ID_KEY, span_id)
    return updates


def traced_node(
    node_name: str,
    *,
    agent_role: str = "",
    step_event: str = "act",
    framework: str = DEFAULT_FRAMEWORK_NAME,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    tracer = _get_step_event_tracer(step_event)

    def _decorator(fn: Callable[P, R]) -> Callable[P, R]:
        def _wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            state: Optional[Mapping[str, Any]] = None
            kw_state = kwargs.get("state")
            if len(args) > 0 and isinstance(args[0], Mapping):
                state = args[0]
            elif isinstance(kw_state, Mapping):
                state = kw_state

            config: Optional[Mapping[str, Any]] = None
            kw_config = kwargs.get("config")
            if len(args) > 1 and isinstance(args[1], Mapping):
                config = args[1]
            elif isinstance(kw_config, Mapping):
                config = kw_config

            ctx = get_or_init_trace_context(state=state, config=config)
            span_id = _new_id()
            event_args = _prune_none_values(
                {
                    TRACE_ID_KEY: ctx[TRACE_ID_KEY],
                    WORKFLOW_ID_KEY: ctx[WORKFLOW_ID_KEY],
                    SPAN_ID_KEY: span_id,
                    STEP_ID_KEY: span_id,
                    PARENT_SPAN_ID_KEY: ctx[PARENT_SPAN_ID_KEY],
                    AGENT_ID_KEY: node_name,
                    AGENT_ROLE_KEY: agent_role or None,
                    FRAMEWORK_KEY: framework,
                    OPERATION_KIND_KEY: DEFAULT_NODE_OPERATION_KIND,
                }
            )

            with tracer(args=event_args):
                result = fn(*args, **kwargs)

            if result is None:
                updates: MutableMapping[str, Any] = {}
                merged = _merge_trace_updates(
                    updates=updates,
                    trace_id=str(ctx[TRACE_ID_KEY]),
                    workflow_id=str(ctx[WORKFLOW_ID_KEY]),
                    span_id=span_id,
                )
                return merged  # type: ignore[return-value]

            if isinstance(result, Mapping):
                updates = dict(result)
                merged = _merge_trace_updates(
                    updates=updates,
                    trace_id=str(ctx[TRACE_ID_KEY]),
                    workflow_id=str(ctx[WORKFLOW_ID_KEY]),
                    span_id=span_id,
                )
                return merged  # type: ignore[return-value]

            return result

        return _wrapped

    return _decorator


def trace_invoke(
    app: Any,
    state: Any,
    config: Optional[Mapping[str, Any]] = None,
    *,
    workflow_name: str = DEFAULT_WORKFLOW_EVENT_NAME,
    framework: str = DEFAULT_FRAMEWORK_NAME,
    run_id: Optional[str] = None,
) -> Any:
    if not hasattr(app, "invoke"):
        raise AttributeError("Expected app to have an 'invoke' method")

    state_mapping = state if isinstance(state, Mapping) else None
    ctx = get_or_init_trace_context(state=state_mapping, config=config)
    run_id = run_id or _new_id()
    span_id = _new_id()

    event_args = _prune_none_values(
        {
            TRACE_ID_KEY: ctx[TRACE_ID_KEY],
            WORKFLOW_ID_KEY: ctx[WORKFLOW_ID_KEY],
            RUN_ID_KEY: run_id,
            SPAN_ID_KEY: span_id,
            PARENT_SPAN_ID_KEY: ctx[PARENT_SPAN_ID_KEY],
            FRAMEWORK_KEY: framework,
            OPERATION_KIND_KEY: DEFAULT_WORKFLOW_OPERATION_KIND,
        }
    )

    workflow_tracer = (
        workflow.run.derive(workflow_name) if workflow_name else workflow.run
    )
    with workflow_tracer(args=event_args):
        if config is None:
            return app.invoke(state)
        return app.invoke(state, config=config)


__all__ = [
    "DEFAULT_FRAMEWORK_NAME",
    "DEFAULT_WORKFLOW_EVENT_NAME",
    "DEFAULT_NODE_OPERATION_KIND",
    "DEFAULT_WORKFLOW_OPERATION_KIND",
    "get_or_init_trace_context",
    "traced_node",
    "trace_invoke",
]
