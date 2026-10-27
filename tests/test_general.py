"""Test suite for dftracer package."""

from typing import List

import pytest
from dftracer.python import (
    AI,
    BLOCK_NAME,
    CTX_SEPARATOR,
    ITER_NAME,
    Checkpoint,
    Communication,
    CommunicationEvent,
    Compute,
    ComputeEvent,
    Data,
    DataEvent,
    DataLoader,
    Device,
    DFTracerAI,
    Pipeline,
    ProfileCategory,
    ai,
    checkpoint,
    comm,
    compute,
    data,
    dataloader,
    device,
    dft_fn,
    dftracer,
    get_iter_block_name,
    get_iter_handle_name,
    pipeline,
)
from dftracer.python.env import DFTRACER_ENABLE


class TestDFTracerLogger:
    def test_dftracer_singleton(self):
        instance1 = dftracer.get_instance()
        instance2 = dftracer.get_instance()

        assert instance1 is instance2
        # Use type name comparison instead of isinstance for parallel test compatibility
        assert type(instance1).__name__ == "dftracer"

    def test_dftracer_initialize_log(self):
        result = dftracer.initialize_log("logfile.log", "/tmp/data", 12345)

        # Use type name comparison instead of isinstance for parallel test compatibility
        assert type(result).__name__ == "dftracer"
        assert result is dftracer.get_instance()

        result.finalize()

    def test_dftracer_methods(self):
        tracer = dftracer.get_instance()

        tracer.enter_event()
        tracer.exit_event()
        tracer.log_event("test", "category", 100, 50)
        tracer.log_event("test", "category", 100, 50, {"arg": "value"})
        tracer.log_metadata_event("key", "value")
        tracer.finalize()

        assert tracer.get_time() == 0


class TestDftFn:
    def test_dft_fn_initialization(self):
        fn = dft_fn("compute")
        assert fn._cat == "compute"
        # change this if function name changed
        assert fn._name == "test_dft_fn_initialization"
        assert fn._enable is True

        fn = dft_fn(
            cat="data",
            name="preprocess",
            epoch=1,
            step=10,
            image_idx=5,
            image_size=224,
            enable=False,
        )
        assert fn._cat == "data"
        assert fn._name == "preprocess"
        assert fn._enable is False
        if DFTRACER_ENABLE and fn._enable:
            assert fn._arguments_int["epoch"][1] == 1
            assert fn._arguments_int["step"][1] == 10
            assert fn._arguments_int["image_idx"][1] == 5
            assert fn._arguments_float["image_size"][1] == 224.0

    def test_dft_fn_context_manager(self):
        fn = dft_fn("test")

        with fn as ctx:
            assert ctx == fn

    def test_dft_fn_update(self):
        fn = dft_fn("test")

        fn.update(
            epoch=5,
            step=100,
            image_idx=10,
            image_size=128,
            args={"custom": "value"},
        )

        if DFTRACER_ENABLE and fn._enable:
            assert fn._arguments_int["epoch"][1] == 5
            assert fn._arguments_int["step"][1] == 100
            assert fn._arguments_int["image_idx"][1] == 10
            assert fn._arguments_float["image_size"][1] == 128.0
            assert fn._arguments_string["custom"][1] == "value"

    def test_dft_fn_log_decorator(self):
        fn = dft_fn("compute", name="forward")

        @fn.log
        def forward_pass(x):
            return x * 2

        result = forward_pass(5)
        assert result == 10
        assert forward_pass.__name__ == "forward_pass"

    def test_dft_fn_log_decorator_with_args(self):
        fn = dft_fn("compute")

        def test_func(x):
            return x + 1

        decorated = fn.log(test_func)
        assert decorated(5) == 6
        assert decorated.__name__ == "test_func"

    def test_dft_fn_log_decorator_overloads(self):
        fn = dft_fn("compute", name="forward")

        @fn.log
        def method1(x):
            return x * 2

        @fn.log()
        def method2(x):
            return x * 3

        @fn.log(name="custom_name")
        def method3(x):
            return x * 4

        assert method1(5) == 10
        assert method2(5) == 15
        assert method3(5) == 20

        assert method1.__name__ == "method1"
        assert method2.__name__ == "method2"
        assert method3.__name__ == "method3"

    def test_dft_fn_typing_preservation(self):
        fn = dft_fn("test")

        @fn.log
        def typed_function(a: int, b: str) -> str:
            """A function with type annotations."""
            return f"{a}: {b}"

        result = typed_function(42, "hello")
        assert result == "42: hello"

        assert typed_function.__name__ == "typed_function"
        assert typed_function.__doc__ == "A function with type annotations."

        if hasattr(typed_function, "__annotations__"):
            annotations = typed_function.__annotations__
            assert annotations.get("a") is int
            assert annotations.get("b") is str
            assert annotations.get("return") is str

    def test_dft_fn_log_init_decorator(self):
        fn = dft_fn("test")

        class TestClass:
            def __init__(self, value):
                self.value = value

            @fn.log_init
            def custom_init(self, value):
                self.value = value

        obj = TestClass(42)
        assert obj.value == 42

        obj.custom_init(100)
        assert obj.value == 100

    def test_dft_fn_log_init_on_constructor(self):
        """Test log_init decorator on actual __init__ method."""
        fn = dft_fn("test")

        class DecoratedClass:
            @fn.log_init
            def __init__(self, value, name="default"):
                self.value = value
                self.name = name

        obj = DecoratedClass(123, name="test")
        assert obj.value == 123
        assert obj.name == "test"

        # Test with positional arguments only
        obj2 = DecoratedClass(456)
        assert obj2.value == 456
        assert obj2.name == "default"

    def test_dft_fn_log_static_decorator(self):
        fn = dft_fn("test")

        class TestClass:
            @staticmethod
            @fn.log_static
            def static_method(x: int):
                return x * 3

        result = TestClass.static_method(4)
        assert result == 12

    def test_dft_fn_log_static_regular_function(self):
        fn = dft_fn("test")

        @fn.log_static
        def regular_function(x):
            return x * 4

        result = regular_function(3)
        assert result == 12

    def test_dft_fn_log_static_with_parentheses(self):
        fn = dft_fn("test")

        class TestClass:
            @staticmethod
            @fn.log_static()
            def static_method(x: int):
                return x * 5

        result = TestClass.static_method(2)
        assert result == 10

    def test_dft_fn_log_static_with_name(self):
        fn = dft_fn("test")

        class TestClass:
            @staticmethod
            @fn.log_static(name="static_method")
            def static_method(x: int):
                return x * 5

        result = TestClass.static_method(2)
        assert result == 10

    def test_dft_fn_iter_method(self):
        fn = dft_fn("data")

        data = [1, 2, 3, 4, 5]
        result = list(fn.iter(data))

        assert result == data

    def test_dft_fn_no_op_methods(self):
        fn = dft_fn("test")

        fn.flush()
        fn.reset()
        fn.log_metadata("key", "value")
        fn.reset()
        assert not fn._flush


class TestAIModule:
    def test_ai_categories_exist(self):
        assert isinstance(ai, AI)
        assert isinstance(compute, Compute)
        assert isinstance(data, Data)
        assert isinstance(dataloader, DataLoader)
        assert isinstance(comm, Communication)
        assert isinstance(device, Device)
        assert isinstance(checkpoint, Checkpoint)
        assert isinstance(pipeline, Pipeline)

    def test_ai_category_children(self):
        assert hasattr(compute, "forward")
        assert hasattr(compute, "backward")
        assert hasattr(compute, "step")

        assert hasattr(data, "preprocess")
        assert hasattr(data, "item")

        assert hasattr(comm, "all_reduce")
        assert hasattr(comm, "send")
        assert hasattr(comm, "receive")
        assert hasattr(comm, "barrier")

    def test_ai_decorator_usage(self):
        @compute.forward
        def forward_pass(x: int) -> int:
            return x**2

        @data.preprocess
        def preprocess(batch: List[int]) -> List[int]:
            return [item * 2 for item in batch]

        assert forward_pass(3) == 9
        assert preprocess([1, 2, 3]) == [2, 4, 6]

    def test_ai_context_manager_usage(self):
        results: List[str] = []

        with pipeline.train:
            results.append("train_start")
            with compute.forward:
                results.append("forward")
            with data.preprocess:
                results.append("preprocess")
            results.append("train_end")

        expected: List[str] = ["train_start", "forward", "preprocess", "train_end"]
        assert results == expected

    def test_ai_update_propagation(self):
        ai.update(epoch=5, step=100)

    def test_ai_enable_disable(self):
        ai.enable()
        ai.disable()

        compute.enable()
        compute.disable()

    def test_ai_derive_method(self):
        child = ai.derive("custom_operation")
        assert isinstance(child, DFTracerAI)

        child1 = ai.derive("test_child")
        child2 = ai.derive("test_child")
        assert child1 is child2

    def test_ai_iter_method(self):
        data_list: List[int] = [1, 2, 3, 4, 5]

        results: List[int] = []
        for item in ai.iter(iter(data_list)):
            results.append(item)

        assert results == data_list

    def test_ai_empty_name_initialization(self):
        ai_instance = DFTracerAI(cat="test_cat", name="")
        assert ai_instance.profiler._name == "test_cat"

    def test_ai_all_optional_parameters(self):
        @compute.forward(
            enable=True,
            epoch=10,
            step=100,
            image_idx=5,
            image_size=224,
            args={"custom_param": "value"},
        )
        def test_function(x: int) -> int:
            return x * 2

        result = test_function(5)
        assert result == 10
        assert test_function.__name__ == "test_function"

    def test_ai_no_optional_parameters(self):
        """Test AI decorators with no optional parameters (all None)."""

        @data.preprocess(
            enable=None,
            epoch=None,
            step=None,
            image_idx=None,
            image_size=None,
            args=None,
        )
        def test_function(x: int) -> int:
            return x * 3

        result = test_function(7)
        assert result == 21

    def test_ai_init_method_with_function(self):
        """Test the init method when called with a function."""

        def sample_function():
            return "init_test"

        # Test init with function
        result = compute.init(sample_function)
        assert callable(result)
        assert result() == "init_test"

    def test_ai_init_method_without_function(self):
        """Test the init method when called without a function (returns decorator)."""

        # Test init without function - should return a decorator
        decorator = compute.init(enable=True, epoch=5)
        assert callable(decorator)

        # Use the decorator
        @decorator
        def sample_function():
            return "decorated_init"

        assert sample_function() == "decorated_init"

    def test_ai_init_method_with_cached_child(self):
        """Test that init method reuses cached children."""

        # First call creates the child
        def func1():
            return "first"

        result1 = compute.init(func1)

        # Second call should reuse the same child
        def func2():
            return "second"

        result2 = compute.init(func2)

        # Both should work
        assert result1() == "first"
        assert result2() == "second"

    def test_ai_init_cached_child_without_function(self):
        """Test init method cached child path without function."""
        # First call to create a cached child
        ai.init(enable=False, epoch=1)

        # Second call without function should use cached child and return decorator
        decorator_result = ai.init(enable=True, epoch=2)
        assert isinstance(decorator_result, DFTracerAI)

    def test_ai_iter_with_conditional_parameters(self):
        """Test iter method with different parameter combinations."""

        data_list = [1, 2, 3]

        # Test with include_block=False
        results1 = list(compute.iter(iter(data_list), include_block=False))
        assert results1 == data_list

        # Test with include_iter=False
        results2 = list(compute.iter(iter(data_list), include_iter=False))
        assert results2 == data_list

        # Test with custom names
        results3 = list(
            compute.iter(
                iter(data_list), iter_name="custom_iter", block_name="custom_block"
            )
        )
        assert results3 == data_list

        # Test with both include options False
        results4 = list(
            compute.iter(iter(data_list), include_block=False, include_iter=False)
        )
        assert results4 == data_list

    def test_ai_iter_with_empty_arguments(self):
        """Test iter when profiler arguments are empty."""

        # Create AI instance with no arguments
        ai_instance = DFTracerAI(cat=ProfileCategory.COMPUTE, name="test")

        # Clear arguments to test empty args condition
        ai_instance.profiler._arguments = {}

        data_list = [10, 20]
        results = list(ai_instance.iter(iter(data_list)))
        assert results == data_list

    def test_ai_update_with_custom_args(self):
        """Test update method with custom args dictionary."""

        custom_args = {"learning_rate": 0.001, "batch_size": 32, "optimizer": "adam"}

        compute.update(
            epoch=15, step=500, image_idx=100, image_size=512, args=custom_args
        )

        # Verify the update worked (no exceptions thrown)
        assert True

    def test_ai_context_manager_with_parameters(self):
        """Test AI context managers with various parameters."""

        # Test with all parameters
        with compute.forward(epoch=1, step=10, image_idx=5):
            result = "context_test"

        assert result == "context_test"

        # Test with enable=False
        with data.preprocess(enable=False):
            result2 = "disabled_context"

        assert result2 == "disabled_context"

    def test_string_enum(self):
        """Test StringEnum implementation"""

        # Test enum values
        assert str(ProfileCategory.COMPUTE) == "compute"
        assert str(ProfileCategory.DATA) == "data"
        assert str(ProfileCategory.COMM) == "comm"

        # Test enum comparison
        assert ProfileCategory.COMPUTE == "compute"
        assert ProfileCategory.DATA == "data"

    def test_string_enum_has_one_definition(self):
        """ai and agent share one StringEnum, defined in common."""
        import dftracer.python.agent_common as agent_common
        import dftracer.python.ai_common as ai_common
        import dftracer.python.common as common

        assert ai_common.StringEnum is common.StringEnum
        assert agent_common.StringEnum is common.StringEnum

    def test_ai_start_stop_with_metadata(self):
        """Test start/stop methods with metadata enabled."""

        # Test start with metadata
        compute.start(metadata=True)

        # Test stop with metadata
        compute.stop(metadata=True)

        # Test start/stop without metadata
        compute.start(metadata=False)
        compute.stop(metadata=False)

        # Test default behavior
        compute.start()
        compute.stop()

    def test_ai_properties(self):
        """Test AI category and name properties."""

        assert compute.cat == "compute"
        assert compute.name == "compute"

        assert data.cat == "data"
        assert data.name == "data"

        assert comm.cat == "comm"
        assert comm.name == "comm"

    def test_ai_decorator_overloads_comprehensive(self):
        """Test comprehensive decorator overloads with various parameter combinations."""

        # Test decorator without any parameters
        @compute.forward
        def simple_func() -> str:
            return "simple"

        # Test decorator with parentheses but no parameters
        @compute.forward()
        def empty_params_func() -> str:
            return "empty_params"

        # Test decorator with epoch parameter
        @compute.forward(epoch=1)
        def epoch_func() -> str:
            return "epoch"

        # Test decorator with step parameter
        @compute.forward(step=10)
        def step_func() -> str:
            return "step"

        # Test decorator with image_idx parameter
        @compute.forward(image_idx=5)
        def image_idx_func() -> str:
            return "image_idx"

        # Test decorator with image_size parameter
        @compute.forward(image_size=224)
        def image_size_func() -> str:
            return "image_size"

        # Test decorator with enable parameter
        @compute.forward(enable=True)
        def enable_func() -> str:
            return "enable"

        # Test decorator with args parameter
        @compute.forward(args={"custom": "value"})
        def args_func() -> str:
            return "args"

        # Test decorator with multiple parameters
        @compute.forward(epoch=2, step=20, enable=False)
        def multi_param_func() -> str:
            return "multi_param"

        # Verify all functions work correctly
        assert simple_func() == "simple"
        assert empty_params_func() == "empty_params"
        assert epoch_func() == "epoch"
        assert step_func() == "step"
        assert image_idx_func() == "image_idx"
        assert image_size_func() == "image_size"
        assert enable_func() == "enable"
        assert args_func() == "args"
        assert multi_param_func() == "multi_param"

        # Verify function names are preserved
        assert simple_func.__name__ == "simple_func"
        assert empty_params_func.__name__ == "empty_params_func"
        assert epoch_func.__name__ == "epoch_func"

    def test_ai_helper_functions_edge_cases(self):
        # Test when name already ends with the separator and name
        block_name_with_suffix = f"test{CTX_SEPARATOR}{BLOCK_NAME}"
        result = get_iter_block_name(block_name_with_suffix)
        assert result == block_name_with_suffix

        iter_name_with_suffix = f"test{CTX_SEPARATOR}{ITER_NAME}"
        result = get_iter_handle_name(iter_name_with_suffix)
        assert result == iter_name_with_suffix

        # Test when name doesn't end with the separator and name
        simple_name = "test"
        result = get_iter_block_name(simple_name)
        assert result == f"test{CTX_SEPARATOR}{BLOCK_NAME}"

        result = get_iter_handle_name(simple_name)
        assert result == f"test{CTX_SEPARATOR}{ITER_NAME}"

    def test_ai_derive_cached_children(self):
        """Test that derive method returns cached children instead of creating new ones."""
        # First call to derive should create a new child
        child1 = ai.derive("test_operation")
        assert isinstance(child1, DFTracerAI)

        # Second call to derive with same name should return cached child
        child2 = ai.derive("test_operation")
        assert child1 is child2

        # Different name should create a different child
        child3 = ai.derive("different_operation")
        assert child3 is not child1
        assert child3 is not child2


class TestEnumerations:
    def test_profile_category_values(self):
        assert ProfileCategory.COMPUTE == "compute"
        assert ProfileCategory.DATA == "data"
        assert ProfileCategory.COMM == "comm"
        assert ProfileCategory.DEVICE == "device"

    def test_event_enums(self):
        assert ComputeEvent.FORWARD == "forward"
        assert ComputeEvent.BACKWARD == "backward"
        assert ComputeEvent.STEP == "step"

        assert DataEvent.PREPROCESS == "preprocess"
        assert DataEvent.ITEM == "item"

        assert CommunicationEvent.ALL_REDUCE == "all_reduce"
        assert CommunicationEvent.SEND == "send"


class TestIntegration:
    def test_realistic_ml_workflow(self):
        results: List[str] = []

        with pipeline.train:
            for epoch in range(2):
                with pipeline.epoch(epoch=epoch):
                    with dataloader.fetch:
                        batch: List[int] = list(range(5))

                    @data.preprocess
                    def preprocess_batch(batch: List[int]) -> List[int]:
                        results.append(f"preprocess_epoch_{epoch}")
                        return [x * 2 for x in batch]

                    processed: List[int] = preprocess_batch(batch)

                    @compute.forward
                    def forward(x: List[int]) -> int:
                        results.append(f"forward_epoch_{epoch}")
                        return sum(x)

                    forward(processed)

                    with compute.backward:
                        results.append(f"backward_epoch_{epoch}")

                    with comm.all_reduce:
                        results.append(f"comm_epoch_{epoch}")

        expected: List[str] = [
            "preprocess_epoch_0",
            "forward_epoch_0",
            "backward_epoch_0",
            "comm_epoch_0",
            "preprocess_epoch_1",
            "forward_epoch_1",
            "backward_epoch_1",
            "comm_epoch_1",
        ]
        assert results == expected

    def test_nested_context_managers(self):
        result: str
        with ai:
            with pipeline.train:
                with compute.forward:
                    with data.preprocess:
                        result = "deeply_nested"

        assert result == "deeply_nested"

    def test_mixed_decorator_and_context_usage(self):
        @pipeline.train
        def training_step() -> str:
            with compute.forward:
                with data.preprocess:
                    return "mixed_usage"

        result: str = training_step()
        assert result == "mixed_usage"


class TestErrorHandling:
    def test_decorator_with_exception(self):
        fn = dft_fn("test")

        @fn.log
        def failing_function():
            raise ValueError("Test exception")

        with pytest.raises(ValueError, match="Test exception"):
            failing_function()

    def test_context_manager_with_exception(self):
        with pytest.raises(ValueError, match="Test exception"):
            with compute.forward:
                raise ValueError("Test exception")

    def test_iterator_with_exception(self):
        def failing_generator():
            yield 1
            yield 2
            raise ValueError("Iterator failed")
            yield 3

        fn = dft_fn("test")
        results = []

        with pytest.raises(ValueError, match="Iterator failed"):
            for item in fn.iter(failing_generator()):
                results.append(item)

        assert results == [1, 2]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
