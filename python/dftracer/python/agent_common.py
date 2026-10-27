from typing import Any, Optional

from dftracer.python.ai_common import DFTracerAI
from dftracer.python.common import StringEnum, auto

ROOT_NAME = "agent_root"
ROOT_CAT = "agent_root"

TRACE_ID_KEY = "trace_id"
WORKFLOW_ID_KEY = "workflow_id"
RUN_ID_KEY = "run_id"
STEP_ID_KEY = "step_id"
AGENT_ID_KEY = "agent_id"
AGENT_ROLE_KEY = "agent_role"
SPAN_ID_KEY = "span_id"
PARENT_SPAN_ID_KEY = "parent_span_id"
TOOL_CALL_ID_KEY = "tool_call_id"
LLM_CALL_ID_KEY = "llm_call_id"
FRAMEWORK_KEY = "framework"
MODEL_NAME_KEY = "model_name"
MESSAGE_TYPE_KEY = "message_type"
LOGICAL_PATH_KEY = "logical_path"
PHYSICAL_PATH_KEY = "physical_path"
FORMAT_KEY = "format"
OPERATION_KIND_KEY = "operation_kind"
SUCCESS_KEY = "success"
ERROR_TYPE_KEY = "error_type"

# Token usage tracking keys for LLM calls
PROMPT_TOKENS_KEY = "prompt_tokens"
COMPLETION_TOKENS_KEY = "completion_tokens"
TOTAL_TOKENS_KEY = "total_tokens"
CONTEXT_SIZE_KEY = "context_size"
CONTEXT_WINDOW_KEY = "context_window"
CONTEXT_UTILIZATION_KEY = "context_utilization"


class AgentCategory(StringEnum):
    WORKFLOW = auto()
    STEP = auto()
    LLM = auto()
    TOOL = auto()
    DATA = auto()
    MESSAGE = auto()
    JUDGE = auto()


class WorkflowEvent(StringEnum):
    RUN = auto()
    RESUME = auto()


class AgentStepEvent(StringEnum):
    PLAN = auto()
    ACT = auto()
    OBSERVE = auto()
    REFLECT = auto()


class LLMEvent(StringEnum):
    CALL = auto()
    STREAM = auto()
    PARSE = auto()


class ToolEvent(StringEnum):
    CALL = auto()
    RESULT = auto()


class AgentDataEvent(StringEnum):
    LOAD = auto()
    SAVE = auto()


class MessageEvent(StringEnum):
    SEND = auto()
    RECEIVE = auto()
    STREAM = auto()


class JudgeEvent(StringEnum):
    EVALUATE = auto()
    RETRY = auto()


class Workflow(DFTracerAI):
    run: DFTracerAI
    resume: DFTracerAI

    def __init__(
        self,
        epoch: Optional[int] = None,
        step: Optional[int] = None,
        image_idx: Optional[int] = None,
        image_size: Optional[Any] = None,
        enable: bool = True,
    ):
        super().__init__(
            cat=AgentCategory.WORKFLOW,
            name=AgentCategory.WORKFLOW,
            epoch=epoch,
            step=step,
            image_idx=image_idx,
            image_size=image_size,
            enable=enable,
        )
        self.create_children(
            {
                "run": WorkflowEvent.RUN,
                "resume": WorkflowEvent.RESUME,
            }
        )


class AgentStep(DFTracerAI):
    plan: DFTracerAI
    act: DFTracerAI
    observe: DFTracerAI
    reflect: DFTracerAI

    def __init__(
        self,
        epoch: Optional[int] = None,
        step: Optional[int] = None,
        image_idx: Optional[int] = None,
        image_size: Optional[Any] = None,
        enable: bool = True,
    ):
        super().__init__(
            cat=AgentCategory.STEP,
            name=AgentCategory.STEP,
            epoch=epoch,
            step=step,
            image_idx=image_idx,
            image_size=image_size,
            enable=enable,
        )
        self.create_children(
            {
                "plan": AgentStepEvent.PLAN,
                "act": AgentStepEvent.ACT,
                "observe": AgentStepEvent.OBSERVE,
                "reflect": AgentStepEvent.REFLECT,
            }
        )


class LLM(DFTracerAI):
    call: DFTracerAI
    stream: DFTracerAI
    parse: DFTracerAI

    def __init__(
        self,
        epoch: Optional[int] = None,
        step: Optional[int] = None,
        image_idx: Optional[int] = None,
        image_size: Optional[Any] = None,
        enable: bool = True,
    ):
        super().__init__(
            cat=AgentCategory.LLM,
            name=AgentCategory.LLM,
            epoch=epoch,
            step=step,
            image_idx=image_idx,
            image_size=image_size,
            enable=enable,
        )
        self.create_children(
            {
                "call": LLMEvent.CALL,
                "stream": LLMEvent.STREAM,
                "parse": LLMEvent.PARSE,
            }
        )


class Tool(DFTracerAI):
    call: DFTracerAI
    result: DFTracerAI

    def __init__(
        self,
        epoch: Optional[int] = None,
        step: Optional[int] = None,
        image_idx: Optional[int] = None,
        image_size: Optional[Any] = None,
        enable: bool = True,
    ):
        super().__init__(
            cat=AgentCategory.TOOL,
            name=AgentCategory.TOOL,
            epoch=epoch,
            step=step,
            image_idx=image_idx,
            image_size=image_size,
            enable=enable,
        )
        self.create_children(
            {
                "call": ToolEvent.CALL,
                "result": ToolEvent.RESULT,
            }
        )


class AgentData(DFTracerAI):
    load: DFTracerAI
    save: DFTracerAI

    def __init__(
        self,
        epoch: Optional[int] = None,
        step: Optional[int] = None,
        image_idx: Optional[int] = None,
        image_size: Optional[Any] = None,
        enable: bool = True,
    ):
        super().__init__(
            cat=AgentCategory.DATA,
            name=AgentCategory.DATA,
            epoch=epoch,
            step=step,
            image_idx=image_idx,
            image_size=image_size,
            enable=enable,
        )
        self.create_children(
            {
                "load": AgentDataEvent.LOAD,
                "save": AgentDataEvent.SAVE,
            }
        )


class Message(DFTracerAI):
    send: DFTracerAI
    receive: DFTracerAI
    stream: DFTracerAI

    def __init__(
        self,
        epoch: Optional[int] = None,
        step: Optional[int] = None,
        image_idx: Optional[int] = None,
        image_size: Optional[Any] = None,
        enable: bool = True,
    ):
        super().__init__(
            cat=AgentCategory.MESSAGE,
            name=AgentCategory.MESSAGE,
            epoch=epoch,
            step=step,
            image_idx=image_idx,
            image_size=image_size,
            enable=enable,
        )
        self.create_children(
            {
                "send": MessageEvent.SEND,
                "receive": MessageEvent.RECEIVE,
                "stream": MessageEvent.STREAM,
            }
        )


class Judge(DFTracerAI):
    evaluate: DFTracerAI
    retry: DFTracerAI

    def __init__(
        self,
        epoch: Optional[int] = None,
        step: Optional[int] = None,
        image_idx: Optional[int] = None,
        image_size: Optional[Any] = None,
        enable: bool = True,
    ):
        super().__init__(
            cat=AgentCategory.JUDGE,
            name=AgentCategory.JUDGE,
            epoch=epoch,
            step=step,
            image_idx=image_idx,
            image_size=image_size,
            enable=enable,
        )
        self.create_children(
            {
                "evaluate": JudgeEvent.EVALUATE,
                "retry": JudgeEvent.RETRY,
            }
        )


# fmt: off
class Agent(DFTracerAI):
    workflow: Workflow
    step: AgentStep
    llm: LLM
    tool: Tool
    data: AgentData
    message: Message
    judge: Judge

    def __init__(
        self,
        epoch: Optional[int] = None,
        step: Optional[int] = None,
        image_idx: Optional[int] = None,
        image_size: Optional[Any] = None,
        enable: bool = True,
    ):
        super().__init__(cat=ROOT_CAT, name=ROOT_NAME, epoch=epoch, step=step, image_idx=image_idx, image_size=image_size, enable=enable)
        self.workflow = Workflow(epoch=epoch, step=step, image_idx=image_idx, image_size=image_size, enable=enable)
        self.step = AgentStep(epoch=epoch, step=step, image_idx=image_idx, image_size=image_size, enable=enable)
        self.llm = LLM(epoch=epoch, step=step, image_idx=image_idx, image_size=image_size, enable=enable)
        self.tool = Tool(epoch=epoch, step=step, image_idx=image_idx, image_size=image_size, enable=enable)
        self.data = AgentData(epoch=epoch, step=step, image_idx=image_idx, image_size=image_size, enable=enable)
        self.message = Message(epoch=epoch, step=step, image_idx=image_idx, image_size=image_size, enable=enable)
        self.judge = Judge(epoch=epoch, step=step, image_idx=image_idx, image_size=image_size, enable=enable)

        self._children = {
            "workflow": self.workflow,
            "step": self.step,
            "llm": self.llm,
            "tool": self.tool,
            "data": self.data,
            "message": self.message,
            "judge": self.judge,
        }
# fmt: on


__all__ = [
    "ROOT_NAME",
    "ROOT_CAT",
    "TRACE_ID_KEY",
    "WORKFLOW_ID_KEY",
    "RUN_ID_KEY",
    "STEP_ID_KEY",
    "AGENT_ID_KEY",
    "AGENT_ROLE_KEY",
    "SPAN_ID_KEY",
    "PARENT_SPAN_ID_KEY",
    "TOOL_CALL_ID_KEY",
    "LLM_CALL_ID_KEY",
    "FRAMEWORK_KEY",
    "MODEL_NAME_KEY",
    "MESSAGE_TYPE_KEY",
    "LOGICAL_PATH_KEY",
    "PHYSICAL_PATH_KEY",
    "FORMAT_KEY",
    "OPERATION_KIND_KEY",
    "SUCCESS_KEY",
    "ERROR_TYPE_KEY",
    "PROMPT_TOKENS_KEY",
    "COMPLETION_TOKENS_KEY",
    "TOTAL_TOKENS_KEY",
    "CONTEXT_SIZE_KEY",
    "CONTEXT_WINDOW_KEY",
    "CONTEXT_UTILIZATION_KEY",
    "AgentCategory",
    "WorkflowEvent",
    "AgentStepEvent",
    "LLMEvent",
    "ToolEvent",
    "AgentDataEvent",
    "MessageEvent",
    "JudgeEvent",
    "Workflow",
    "AgentStep",
    "LLM",
    "Tool",
    "AgentData",
    "Message",
    "Judge",
    "Agent",
]
