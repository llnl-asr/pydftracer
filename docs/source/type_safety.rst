Type Safety
===========

pydftracer is fully type-checked and preserves function signatures when using decorators.
This means you get full IDE autocomplete, type checking with mypy, and no loss of type information.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

All pydftracer decorators are **type-safe** and **signature-preserving**:

- ✅ Full mypy compatibility
- ✅ IDE autocomplete works perfectly
- ✅ Type hints are preserved
- ✅ No ``# type: ignore`` needed
- ✅ Generic types supported
- ✅ ParamSpec for perfect signature preservation

Type-Preserving Decorators
---------------------------

Basic Example
~~~~~~~~~~~~~

The decorators **do not change** the type signature of your functions:

.. code-block:: python

   from dftracer.python import ai
   import torch
   from torch import Tensor

   @ai.compute.forward
   def forward(data: Tensor) -> Tensor:
       return data

   # Type is preserved! forward is still (Tensor) -> Tensor
   result: Tensor = forward(torch.randn(10))  # ✅ Type checks correctly

   # IDE autocomplete works perfectly
   result.shape  # ✅ IDE knows this is a Tensor

Without type preservation, you would lose this information and need:

.. code-block:: python

   # ❌ What happens with poorly-typed decorators
   result = forward(torch.randn(10))  # type: ignore
   # IDE doesn't know what type 'result' is

Complex Type Signatures
~~~~~~~~~~~~~~~~~~~~~~~~

Even complex signatures are preserved:

.. code-block:: python

   from typing import List, Tuple, Optional, Dict
   from dftracer.python import ai, dft_fn

   @ai.data.preprocess
   def process_batch(
       images: List[Tensor],
       labels: List[int],
       augment: bool = True,
       config: Optional[Dict[str, float]] = None
   ) -> Tuple[Tensor, Tensor]:
       """Process a batch of images and labels."""
       # Implementation
       batch_images = torch.stack(images)
       batch_labels = torch.tensor(labels)
       return batch_images, batch_labels

   # Type signature is completely preserved
   imgs, lbls = process_batch(
       images=[torch.randn(3, 224, 224)],
       labels=[1],
       augment=True
   )
   # ✅ mypy knows: imgs is Tensor, lbls is Tensor

Generic Types
~~~~~~~~~~~~~

Generic types work perfectly:

.. code-block:: python

   from typing import TypeVar, List
   from dftracer.python import ai

   T = TypeVar('T')

   @ai.data.item
   def transform(item: T) -> T:
       """Identity transformation - preserves type."""
       return item

   # Works with any type
   x: int = transform(5)        # ✅ Returns int
   y: str = transform("hello")  # ✅ Returns str
   z: Tensor = transform(torch.randn(10))  # ✅ Returns Tensor

Method Decorators
~~~~~~~~~~~~~~~~~

Class methods work perfectly too:

.. code-block:: python

   from dftracer.python import ai
   import torch.nn as nn

   class MyModel(nn.Module):
       @ai.compute.forward
       def forward(self, x: Tensor) -> Tensor:
           # Type of 'self' is preserved
           # Type of 'x' is preserved
           # Return type is preserved
           return self.layers(x)

   model = MyModel()
   # ✅ IDE autocomplete shows correct signature
   output: Tensor = model.forward(torch.randn(10))

MyPy Integration
----------------

Configuration
~~~~~~~~~~~~~

pydftracer works out of the box with mypy. Add to your ``pyproject.toml``:

.. code-block:: toml

   [tool.mypy]
   python_version = "3.9"
   warn_return_any = true
   disallow_untyped_defs = true
   disallow_incomplete_defs = true

   # No special configuration needed for pydftracer!

Running MyPy
~~~~~~~~~~~~

.. code-block:: bash

   # Type check your code
   mypy your_script.py

   # Should pass without errors or type: ignore comments
   ✅ Success: no issues found in 1 source file

Example: Full Type Checking
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from typing import List, Tuple
   from dftracer.python import dftracer, ai, dft_fn
   import torch
   from torch import Tensor, nn, optim

   class Model(nn.Module):
       def __init__(self, input_size: int, hidden_size: int, output_size: int):
           super().__init__()
           self.fc1 = nn.Linear(input_size, hidden_size)
           self.fc2 = nn.Linear(hidden_size, output_size)

       @ai.compute.forward
       def forward(self, x: Tensor) -> Tensor:
           x = torch.relu(self.fc1(x))
           return self.fc2(x)

   @ai.device.transfer
   def to_device(data: Tensor, device: str) -> Tensor:
       return data.to(device)

   @ai.pipeline.train
   def train(
       model: Model,
       data: List[Tuple[Tensor, Tensor]],
       optimizer: optim.Optimizer,
       device: str,
       epochs: int
   ) -> None:
       for epoch in ai.pipeline.epoch.iter(range(epochs)):
           for batch_idx, (images, labels) in ai.dataloader.fetch.iter(enumerate(data)):
               # All types are preserved and checked
               images = to_device(images, device)
               labels = to_device(labels, device)

               with ai.compute.forward:
                   output: Tensor = model(images)

               with ai.compute.backward:
                   loss: Tensor = nn.functional.cross_entropy(output, labels)
                   loss.backward()

               optimizer.step()
               optimizer.zero_grad()

   # ✅ This entire file type-checks with mypy with strict settings!

Common Patterns
---------------

Pattern 1: Preserving Generic Return Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from typing import TypeVar, Callable
   from dftracer.python import ai

   T = TypeVar('T')

   @ai.data.preprocess
   def apply_transform(
       data: T,
       transform: Callable[[T], T]
   ) -> T:
       return transform(data)

   # ✅ Type is preserved through the generic
   result: int = apply_transform(5, lambda x: x * 2)

Pattern 2: Multiple Return Values
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from typing import Tuple
   from dftracer.python import ai

   @ai.data.preprocess
   def split_batch(
       batch: Tensor,
       ratio: float = 0.8
   ) -> Tuple[Tensor, Tensor]:
       split_point = int(len(batch) * ratio)
       return batch[:split_point], batch[split_point:]

   # ✅ Tuple unpacking is type-safe
   train_data, val_data = split_batch(data)
   # Both train_data and val_data are known to be Tensor

Pattern 3: Optional Parameters
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from typing import Optional
   from dftracer.python import ai

   @ai.checkpoint.capture
   def save_checkpoint(
       model: nn.Module,
       path: str,
       metadata: Optional[Dict[str, str]] = None
   ) -> bool:
       # Implementation
       return True

   # ✅ All these calls type-check correctly
   save_checkpoint(model, "checkpoint.pt")
   save_checkpoint(model, "checkpoint.pt", {"epoch": "10"})
   save_checkpoint(model, "checkpoint.pt", None)

Benefits
--------

1. **Catch Errors Early**

   Type errors are caught before runtime:

   .. code-block:: python

      @ai.compute.forward
      def forward(x: Tensor) -> Tensor:
          return x

      # ❌ mypy catches this error
      result: str = forward(torch.randn(10))
      # error: Incompatible types in assignment

2. **Better Documentation**

   Type hints serve as documentation:

   .. code-block:: python

      @ai.data.preprocess
      def augment(
          image: Tensor,
          flip: bool = True,
          rotation: float = 0.0
      ) -> Tensor:
          """
          Type hints make it clear what this function expects
          and returns, even without reading the docstring!
          """
          pass

3. **Refactoring Confidence**

   Change function signatures with confidence:

   .. code-block:: python

      # Change return type
      @ai.compute.forward
      def forward(x: Tensor) -> Tuple[Tensor, Tensor]:  # Changed!
          return x, x

      # ✅ mypy will find all places that need updating
      result = forward(data)  # error: Need to unpack tuple

4. **IDE Productivity**

   - Autocomplete knows exact types
   - Jump to definition works
   - Find usages is accurate
   - Refactoring is safe

Implementation Details
----------------------

How It Works
~~~~~~~~~~~~

pydftracer uses Python's ``ParamSpec`` and ``TypeVar`` to preserve signatures:

.. code-block:: python

   from typing import TypeVar, ParamSpec, Callable

   P = ParamSpec("P")  # Captures parameters
   R = TypeVar("R")    # Captures return type

   def decorator(func: Callable[P, R]) -> Callable[P, R]:
       """This decorator preserves the exact signature."""
       def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
           # Tracing logic here
           return func(*args, **kwargs)
       return wrapper


Comparison
~~~~~~~~~~

**Without type preservation:**

.. code-block:: python

   # ❌ Poor decorator
   def bad_decorator(func):
       def wrapper(*args, **kwargs):
           return func(*args, **kwargs)
       return wrapper

   @bad_decorator
   def forward(x: Tensor) -> Tensor:
       return x

   # Type checker doesn't know the signature anymore
   result = forward(torch.randn(10))  # Unknown type

**With type preservation (pydftracer):**

.. code-block:: python

   # ✅ Good decorator (what pydftracer does)
   from typing import ParamSpec, TypeVar, Callable

   P = ParamSpec("P")
   R = TypeVar("R")

   def good_decorator(func: Callable[P, R]) -> Callable[P, R]:
       def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
           return func(*args, **kwargs)
       return wrapper

   @good_decorator
   def forward(x: Tensor) -> Tensor:
       return x

   # ✅ Type checker knows exact signature
   result: Tensor = forward(torch.randn(10))

Best Practices
--------------

1. **Always Use Type Hints**

   .. code-block:: python

      # ✅ Good
      @ai.compute.forward
      def forward(x: Tensor) -> Tensor:
          return x

      # ❌ Missing type hints
      @ai.compute.forward
      def forward(x):
          return x

2. **Use Strict MyPy Settings**

   .. code-block:: toml

      [tool.mypy]
      disallow_untyped_defs = true
      disallow_incomplete_defs = true
      warn_return_any = true

3. **Type Your Data Structures**

   .. code-block:: python

      from typing import List, Dict, NamedTuple

      class Sample(NamedTuple):
          image: Tensor
          label: int

      @ai.dataloader.fetch
      def load_batch(indices: List[int]) -> List[Sample]:
          return [Sample(load_image(i), get_label(i)) for i in indices]

4. **Leverage Protocol Types**

   .. code-block:: python

      from typing import Protocol

      class Optimizer(Protocol):
          def step(self) -> None: ...
          def zero_grad(self) -> None: ...

      @ai.compute.step
      def optimizer_step(optimizer: Optimizer) -> None:
          optimizer.step()
          optimizer.zero_grad()

Summary
-------

pydftracer is designed with type safety as a first-class feature:

- **Zero type information loss** when using decorators
- **Full mypy compatibility** with strict settings
- **IDE autocomplete** works perfectly
- **Type stubs included** for all modules
- **No ``# type: ignore`` needed** in your code
- **ParamSpec-based** implementation for perfect preservation

This means you can use pydftracer in production codebases with strict type checking
requirements without any compromises!

.. note::

   **A Note on Internal Implementation**

   We've worked hard to make pydftracer's public API fully type-safe for users. However,
   internally, the implementation does use some ``# type: ignore`` comments and relaxed
   mypy rules where necessary to handle the complexity of decorator internals, dynamic
   profiler initialization, and Python's type system limitations.

   **From your perspective as a user**, your code will type-check perfectly without
   any workarounds. The internal complexity is hidden behind a clean, type-safe interface.

   If you have ideas for improving pydftracer's type safety—either in the public API or
   internal implementation—we'd love to hear from you! Please open an issue or discussion
   on `GitHub <https://github.com/llnl-asr/pydftracer/issues>`_.

For more examples, see :doc:`examples` and :doc:`ai_ml_guide`.
