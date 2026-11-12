Environment Configuration
=========================

This section documents environment variables and configuration options.

Environment Variables
---------------------

.. autodata:: dftracer.python.DFTRACER_ENABLE
   :annotation: = True if DFTRACER_ENABLE=1

.. autodata:: dftracer.python.DFTRACER_INIT_PRELOAD
   :annotation: = True if DFTRACER_INIT=PRELOAD

.. autodata:: dftracer.python.DFTRACER_LOG_LEVEL
   :annotation: = "ERROR" | "WARN" | "INFO" | "DEBUG"

``DFTRACER_ATTACH``
~~~~~~~~~~~~~~~~~~~

``DFTRACER_ATTACH=1`` tells ``dftracer.initialize_log`` that another owner already runs
the tracing core of the process (moirai sets it when it is imported). ``initialize_log``
then attaches to the running core instead of initializing it a second time, and
``finalize`` leaves the core to its owner. Without the variable, or with
``DFTRACER_ATTACH=0``, ``initialize_log`` and ``finalize`` behave as before. pydftracer
reads only this variable; it does not look for the owner.

Environment Variable Names
--------------------------

.. autodata:: dftracer.python.env.DFTRACER_ENABLE_ENV
   :annotation: = "DFTRACER_ENABLE"

.. autodata:: dftracer.python.env.DFTRACER_INIT_ENV
   :annotation: = "DFTRACER_INIT"

.. autodata:: dftracer.python.env.DFTRACER_LOG_LEVEL_ENV
   :annotation: = "DFTRACER_LOG_LEVEL"

Logger Setup
------------

.. autofunction:: dftracer.python.env.setup_stream_logger

Configuration Examples
----------------------

Enable DFTracer
~~~~~~~~~~~~~~~

.. code-block:: bash

   export DFTRACER_ENABLE=1

Set Log Level
~~~~~~~~~~~~~

.. code-block:: bash

   export DFTRACER_LOG_LEVEL=INFO

Set Initialization Mode
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   export DFTRACER_INIT=PRELOAD

Checking Configuration
----------------------

In Python code:

.. code-block:: python

   from dftracer.python import (
       DFTRACER_ENABLE,
       DFTRACER_INIT_PRELOAD,
       DFTRACER_LOG_LEVEL
   )

   if DFTRACER_ENABLE:
       print("DFTracer is enabled")
       print(f"Log level: {DFTRACER_LOG_LEVEL}")
       print(f"Preload mode: {DFTRACER_INIT_PRELOAD}")
