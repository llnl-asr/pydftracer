from typing import Any

from dftracer.python.common import (
    _TIME_METRIC_UNITS_PER_SECOND,
    TagDType,
    TagType,
    TagValue,
    get_time_scale,
)

dftracer = None  # type: ignore


# 1. Custom Profiler Plugin (handler)
def trace_handler(profiler_result: Any) -> None:
    global dftracer
    events = profiler_result.events()

    scale = get_time_scale()  # dftracer time units per second
    # NOTE: we need to have start time to align the time properly
    dft_time = dftracer.get_instance().start_time  # type: ignore
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
