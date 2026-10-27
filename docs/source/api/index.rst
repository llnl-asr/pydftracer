API Reference
=============

This section contains the complete API reference for pydftracer.

.. toctree::
   :maxdepth: 2

   core
   ai
   agent
   dynamo
   env

Main Package
------------

.. autosummary::
   :toctree: _autosummary
   :recursive:

   dftracer.python

The main package exports all key functions and classes:

Core Tracing
~~~~~~~~~~~~

- ``dftracer`` - Main tracer class for logging events
- ``dft_fn`` - Decorator for tracing functions
- ``initialize`` - Initialize the DFTracer profiler
- ``finalize`` - Finalize and cleanup the profiler
- ``get_time`` - Get current timestamp for profiling

AI/ML Support
~~~~~~~~~~~~~

- ``DFTracerAI`` - Base class for AI/ML tracing
- ``Agent`` - Base class for agent/workflow tracing
- ``Dynamo`` - PyTorch Dynamo integration class
- ``dynamo`` - Pre-configured Dynamo instance for tracing
- ``create_backend`` - Create a custom torch.compile backend with DFTracer

Configuration
~~~~~~~~~~~~~

- ``DFTRACER_ENABLE`` - Check if DFTracer is enabled
- ``DFTRACER_INIT_PRELOAD`` - Check initialization mode
- ``DFTRACER_LOG_LEVEL`` - Current log level

Utilities
~~~~~~~~~

- ``TagValue`` - Represent tagged values for events
- ``TagType`` - Enum for tag types (KEY, VALUE, IGNORE)
- ``TagDType`` - Enum for data types (INT, FLOAT, STRING)

Modules
-------

- :doc:`core` - Core tracing functionality (logger, common utilities)
- :doc:`ai` - AI/ML specific tracing features
- :doc:`agent` - Agent/workflow tracing features
- :doc:`dynamo` - PyTorch Dynamo integration
- :doc:`env` - Environment configuration and setup
