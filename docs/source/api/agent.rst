Agent API
=========

This section documents the agent tracing namespace and its event model.

Agent Module
------------

The ``agent`` module provides decorators and utilities for tracing agentic workflows.

.. automodule:: dftracer.python.agent
   :members:
   :undoc-members:

Agent Categories
----------------

.. autoclass:: dftracer.python.AgentCategory
   :members:
   :undoc-members:

Agent Components
----------------

.. autoclass:: dftracer.python.Workflow
   :members:
   :undoc-members:

.. autoclass:: dftracer.python.AgentStep
   :members:
   :undoc-members:

.. autoclass:: dftracer.python.LLM
   :members:
   :undoc-members:

.. autoclass:: dftracer.python.Tool
   :members:
   :undoc-members:

.. autoclass:: dftracer.python.AgentData
   :members:
   :undoc-members:

.. autoclass:: dftracer.python.Message
   :members:
   :undoc-members:

.. autoclass:: dftracer.python.Judge
   :members:
   :undoc-members:

Agent Instance
--------------

.. autoclass:: dftracer.python.Agent
   :members:
   :undoc-members:

Convenience aliases:

- ``agent`` - Main agent tracing instance
- ``workflow`` - Workflow tracing category
- ``agent_step`` - Agent step tracing category
- ``llm`` - LLM tracing category
- ``tool`` - Tool tracing category
- ``agent_data`` - Data operation tracing category
- ``message`` - Message/event tracing category
- ``judge`` - Evaluation/retry tracing category

Span Arguments and Aggregation
------------------------------

Spans carry their ``args`` (``trace_id``, ``step``, token counts, and so on) in the
trace, and ``span.update_args({...})`` adds values after the work finishes, such as
token usage from an LLM response.

DFTracer can aggregate short events into counters to keep traces small. An
aggregated event no longer carries its ``args``, so with the default aggregation a
short ``llm.call`` or ``tool.call`` loses its arguments, token counts included. To
keep agent spans intact, either turn aggregation off:

.. code-block:: bash

   DFTRACER_ENABLE_AGGREGATION=0

or aggregate only the I/O events, with the ``SELECTIVE`` type and a rules file that
includes only POSIX and STDIO:

.. code-block:: bash

   DFTRACER_ENABLE_AGGREGATION=1
   DFTRACER_AGGREGATION_TYPE=SELECTIVE
   DFTRACER_AGGREGATION_FILE=aggregation_rules.yaml

.. code-block:: yaml

   inclusion:
     - cat IN {POSIX,STDIO}
   exclusion:

LangGraph Adapter
-----------------

Utilities for tracing LangGraph-style node and workflow invocation boundaries:

.. autofunction:: dftracer.python.get_or_init_trace_context
.. autofunction:: dftracer.python.traced_node
.. autofunction:: dftracer.python.trace_invoke
