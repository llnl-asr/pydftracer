from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Union, overload

from dftracer.python.ai_common import DFTracerAI, dftracer
from dftracer.python.common import DFTRACER_ENABLE, P, R, TagDType, TagType, TagValue

try:
    import torch

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None  # type: ignore

if TORCH_AVAILABLE:
    try:
        from functorch.compile import make_boxed_func

        # Alpha feature from: https://docs.pytorch.org/docs/stable/torch.compiler_custom_backends.html#custom-backends-after-aotautograd
        from torch._dynamo.backends.common import aot_autograd
    except ImportError:
        if DFTRACER_ENABLE:
            raise RuntimeError(
                "DFTracer dynamo requires PyTorch and functorch to be installed"
            )
        else:
            make_boxed_func = None  # type: ignore
            aot_autograd = None  # type: ignore
else:
    make_boxed_func = None  # type: ignore
    aot_autograd = None  # type: ignore

CAT_DYNAMO = "dynamo"


@dataclass
class CallStackRecord:
    op_name: str
    op_type: str
    target: str
    timestamp_us: int
    grad_enabled: bool


def create_detailed_op_name(node: Any, gm: Any) -> str:
    """Create detailed operation name with layer/subfunction info"""
    base_name = str(node.target).replace(".", "_")

    if node.op == "call_module":
        module_path = str(node.target)
        module = gm.get_submodule(node.target)
        module_type = type(module).__name__
        return f"{module_path}.{module_type}_{base_name}"
    elif node.op == "call_function":
        func_name = getattr(node.target, "__name__", str(node.target))
        return f"function.{func_name}"
    elif node.op == "call_method":
        return f"method.{base_name}"
    else:
        return f"{node.op}.{base_name}"


class Dynamo(DFTracerAI):
    def __init__(
        self,
        name: Optional[str] = None,
        epoch: Optional[int] = None,
        step: Optional[int] = None,
        image_idx: Optional[int] = None,
        image_size: Optional[Any] = None,
        enable: bool = True,
    ):
        super().__init__(
            cat=CAT_DYNAMO,
            name=name,
            epoch=epoch,
            step=step,
            image_idx=image_idx,
            image_size=image_size,
            enable=enable,
        )
        if DFTRACER_ENABLE and enable:
            dftracer.get_instance().mark_used("dynamo")
        self.call_stack: List[CallStackRecord] = []

    def reset(self) -> None:
        """Reset the tracer state"""
        super().reset()
        self.call_stack.clear()

    def _record_time_start(self, op_name: str, op_type: str, target: str) -> None:
        timestamp_us = self.get_time()
        grad_enabled = False
        if TORCH_AVAILABLE:
            grad_enabled = torch.is_grad_enabled()
        record = CallStackRecord(
            op_name=op_name,
            op_type=op_type,
            target=target,
            timestamp_us=timestamp_us,
            grad_enabled=grad_enabled,
        )
        self.call_stack.append(record)

    def _record_time_end(self, op_name: str, node: Any) -> None:
        """Record end time for an operation - called from graph execution"""
        if not self.call_stack:
            return None

        # The start_info is at the top of the call stack
        start_info = self.call_stack.pop()
        end_timestamp_us = self.get_time()

        # Calculate duration
        duration_us = end_timestamp_us - start_info.timestamp_us

        # Log the event
        dft = dftracer.get_instance()
        dft.enter_event()
        dft.log_event(
            name=op_name,
            cat=self.cat,
            start_time=start_info.timestamp_us,
            duration=duration_us,
            int_args={
                "grad_enabled": TagValue(
                    int(start_info.grad_enabled), TagDType.INT, TagType.KEY
                ).value(),
                # TODO: Add input and output shapes
            },
        )
        dft.exit_event()
        return None

    def add_enhanced_timing_to_graph(self, gm: Any) -> Any:
        """Add enhanced timing nodes to the FX graph"""
        graph = gm.graph

        # Insert timing calls before and after each operation
        nodes_to_instrument = []
        for node in graph.nodes:
            # We do not want to profile placeholder nodes
            if node.op in ["call_module", "call_function", "call_method"]:
                nodes_to_instrument.append(node)

        for node in reversed(nodes_to_instrument):
            op_name = create_detailed_op_name(node, gm)

            with graph.inserting_before(node):
                graph.call_function(
                    self._record_time_start,
                    args=(op_name, node.op, str(node.target)),
                )

            with graph.inserting_after(node):
                graph.call_function(self._record_time_end, args=(op_name, node))

        gm.recompile()
        # Print graph
        # gm.print_readable()
        return gm

    @overload
    def compile(
        self, f_py: Callable[P, R], autograd: bool = True
    ) -> Callable[P, R]: ...

    @overload
    def compile(
        self, f_py: None = None, *, autograd: bool = True
    ) -> Callable[[Callable[P, R]], Callable[P, R]]: ...

    def compile(
        self, f_py: Optional[Callable[P, R]] = None, autograd: bool = True
    ) -> Union[Callable[P, R], Callable[[Callable[P, R]], Callable[P, R]]]:
        """Used to compile torch.nn.Module and the forward functions
        - Uses PyTorch Dynamo to add nodes before and after each operation
        - The nodes are run before and after each operation -> providing detailed timing information
        """
        if not TORCH_AVAILABLE:
            raise RuntimeError(
                "PyTorch is not available. Install PyTorch to use Dynamo integration."
            )

        if not (DFTRACER_ENABLE and self.enable):  # type: ignore[truthy-function]
            return f_py  # type: ignore

        if autograd and (aot_autograd is None or make_boxed_func is None):
            raise RuntimeError(
                "AOT autograd is not available. Either install required dependencies "
                "or set autograd=False"
            )

        def _decorator(func: Callable[P, R]) -> Callable[P, R]:
            def enhanced_trace_wrapper(gm: Any, example: Any, **kwargs: Any) -> Any:
                """Enhanced custom trace function for Dynamo"""
                instrumented_gm = self.add_enhanced_timing_to_graph(gm)
                if autograd and make_boxed_func is not None:
                    return make_boxed_func(instrumented_gm.forward)
                else:
                    return instrumented_gm.forward

            if autograd and aot_autograd is not None:
                return torch.compile(  # type: ignore
                    func, backend=aot_autograd(fw_compiler=enhanced_trace_wrapper)
                )
            else:
                return torch.compile(func, backend=enhanced_trace_wrapper)  # type: ignore

        return _decorator(f_py) if callable(f_py) else _decorator

    def count_parameters(self, module: Any) -> Optional[int]:
        """Count parameters in a module"""
        if hasattr(module, "parameters"):
            return int(sum(p.numel() for p in module.parameters()))
        return None


dynamo = Dynamo()


def create_backend(
    name: Optional[str] = None,
    epoch: Optional[int] = None,
    step: Optional[int] = None,
    image_idx: Optional[int] = None,
    image_size: Optional[Any] = None,
    enable: bool = True,
    autograd: bool = True,
) -> Any:
    """Create a torch.compile backend with DFTracer instrumentation.

    Args:
        name: Optional name for the tracer
        epoch: Optional epoch number
        step: Optional step number
        image_idx: Optional image index
        image_size: Optional image size
        enable: Whether to enable tracing (default: True)
        autograd: Whether to use autograd (default: True)

    Returns:
        A backend function that can be used with torch.compile

    Example:
        >>> import torch
        >>> from dftracer.python.dynamo import create_backend
        >>>
        >>> # Create a custom backend
        >>> backend = create_backend(name="my_model", epoch=0, step=0)
        >>>
        >>> # Use it with torch.compile
        >>> model = torch.nn.Linear(10, 10)
        >>> compiled_model = torch.compile(model, backend=backend)
    """
    if not TORCH_AVAILABLE:
        raise RuntimeError("PyTorch is not available")

    if autograd and (aot_autograd is None or make_boxed_func is None):
        raise RuntimeError(
            "AOT autograd is not available. Either install required dependencies "
            "or set autograd=False"
        )

    tracer = Dynamo(
        name=name,
        epoch=epoch,
        step=step,
        image_idx=image_idx,
        image_size=image_size,
        enable=enable,
    )

    def backend(gm: Any, _example_inputs: Any, **_kwargs: Any) -> Any:
        """Backend function for torch.compile"""
        instrumented_gm = tracer.add_enhanced_timing_to_graph(gm)
        if autograd and make_boxed_func is not None:
            return make_boxed_func(instrumented_gm.forward)
        else:
            return instrumented_gm.forward

    if autograd and aot_autograd is not None:
        return aot_autograd(fw_compiler=backend)
    else:
        return backend


__all__ = ["Dynamo", "dynamo", "create_backend"]
