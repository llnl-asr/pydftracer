from typing import Any

from dftracer.python.common import (
    _TIME_METRIC_UNITS_PER_SECOND,
    TagDType,
    TagType,
    TagValue,
    get_time_scale,
)

dftracer = None  # type: ignore


def _trace_start_in_dft_units(profiler_result: Any, scale: float) -> "int | None":
    """dftracer-clock timestamp of the PyTorch profiler's trace start.

    ``FunctionEvent.time_range.start`` is measured in microseconds RELATIVE TO
    THE PROFILER'S TRACE START, not to process start and not to the epoch. To
    place those events on dftracer's timeline we therefore need the absolute
    epoch time at which kineto began tracing.

    kineto exposes that as ``trace_start_ns()`` (epoch nanoseconds; named
    ``trace_start_us()`` on torch < 2.4). Both are the same clock dftracer's
    own ``get_time()`` uses, so a plain unit conversion is all that is needed.

    Returns ``None`` when the profiler does not expose a trace start at all, so
    the caller can fall back rather than crash.
    """
    profiler = getattr(profiler_result, "profiler", None)
    kineto_results = getattr(profiler, "kineto_results", None)
    if kineto_results is None:
        return None
    for method, units_per_second in (
        ("trace_start_ns", _TIME_METRIC_UNITS_PER_SECOND["NS"]),
        ("trace_start_us", _TIME_METRIC_UNITS_PER_SECOND["US"]),
    ):
        fn = getattr(kineto_results, method, None)
        if fn is None:
            continue
        try:
            trace_start = fn()
        except Exception:  # pragma: no cover - defensive, torch version drift
            continue
        if trace_start:
            return int(trace_start * scale / units_per_second)
    return None


# 1. Custom Profiler Plugin (handler)
def trace_handler(profiler_result: Any) -> None:
    global dftracer
    # This is the function the app must pass as
    # torch.profiler.profile(on_trace_ready=trace_handler): it only actually
    # runs when torch's profiler invokes it with a real result, so marking
    # here (unlike marking at module-import time) reflects genuine use. Called
    # once per profiling step, but mark_used() is a cheap no-op after the
    # first call.
    dftracer.get_instance().mark_used("torch_profiler")  # type: ignore
    events = profiler_result.events()

    scale = get_time_scale()  # dftracer time units per second
    # Anchor for the profiler's relative event offsets. This MUST be the
    # profiler's trace start, NOT dftracer's start_time: start_time is stamped
    # at initialize_log() (process init), whereas the profiler typically opens
    # much later -- after dataset construction, warmup steps, etc. Anchoring at
    # process init shifts every PP event earlier by that entire gap (~150s in a
    # real training run), so kernels land before the forward/backward regions
    # they belong to instead of inside them.
    dft_time = _trace_start_in_dft_units(profiler_result, scale)
    if dft_time is None:
        # Older/unknown torch that exposes no trace start: fall back to process
        # init so events are still emitted, but say so -- they will be shifted.
        dft_time = dftracer.get_instance().start_time  # type: ignore
        dbg = dftracer.get_instance().dbg_logging  # type: ignore
        if dbg:
            dbg.debug(
                "torch profiler exposes no trace_start_ns/trace_start_us; "
                "falling back to dftracer start_time -- PP events will be "
                "shifted earlier by the init-to-profiler-start gap"
            )
    us_to_dft = (
        scale / _TIME_METRIC_UNITS_PER_SECOND["US"]
    )  # dftracer time units per PyTorch-profiler microsecond

    # Print attributes for each event
    dftracer.get_instance().enter_event()  # type: ignore
    for _i, event in enumerate(events):
        # Extract kernel name from event.key
        key = event.key
        # NOTE: event.time_range.start is in microseconds, so we need to convert it to dftracer time units
        #       event.time_range.start is relative to pytorch profiler trace start time
        #       event.time docs: https://docs.pytorch.org/docs/2.13/generated/torch.autograd.profiler_util.FunctionEvent.html#torch.autograd.profiler_util.FunctionEvent
        start_time = int(event.time_range.start * us_to_dft + dft_time)
        duration = int(event.time_range.elapsed_us() * us_to_dft)
        int_args = {}
        int_args["device"] = TagValue(
            event.device_type, TagDType.INT, TagType.KEY
        ).value()
        int_args["cpu_memory"] = TagValue(
            event.cpu_memory_usage, TagDType.INT, TagType.KEY
        ).value()
        int_args["is_remote"] = TagValue(
            event.is_remote, TagDType.INT, TagType.KEY
        ).value()
        int_args["device_memory_usage"] = TagValue(
            event.device_memory_usage, TagDType.INT, TagType.KEY
        ).value()
        int_args["input_size"] = TagValue(
            sum(len(s) for s in event.input_shapes) if event.input_shapes else 0,
            TagDType.INT,
            TagType.KEY,
        ).value()
        float_args = {}
        float_args["total_cpu_percent"] = TagValue(
            event.total_cpu_percent, TagDType.FLOAT, TagType.KEY
        ).value()
        float_args["total_device_percent"] = TagValue(
            event.total_device_percent, TagDType.FLOAT, TagType.KEY
        ).value()

        dftracer.get_instance().log_event(  # type: ignore
            name=key,
            cat="PP",
            start_time=start_time,
            duration=duration,
            int_args=int_args,
            float_args=float_args,
            string_args={},
        )
    dftracer.get_instance().exit_event()  # type: ignore
