AI/ML API
=========

This section documents the AI/ML specific tracing features.

DFTracerAI Class
----------------

.. autoclass:: dftracer.python.DFTracerAI
   :members:
   :undoc-members:
   :show-inheritance:

AI Module
---------

The ``ai`` module provides decorators and utilities for tracing AI/ML workflows.
It re-exports everything documented below, and the same names are available from
``dftracer.python``.

AI Categories
-------------

ProfileCategory
~~~~~~~~~~~~~~~

.. autoclass:: dftracer.python.ProfileCategory
   :members:
   :undoc-members:

AI Components
~~~~~~~~~~~~~

Data Operations
^^^^^^^^^^^^^^^

.. autoclass:: dftracer.python.Data
   :members:
   :undoc-members:

.. autoclass:: dftracer.python.DataEvent
   :members:
   :undoc-members:

Dataloader Operations
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: dftracer.python.DataLoader
   :members:
   :undoc-members:

Device Operations
^^^^^^^^^^^^^^^^^

.. autoclass:: dftracer.python.Device
   :members:
   :undoc-members:

Compute Operations
^^^^^^^^^^^^^^^^^^

.. autoclass:: dftracer.python.Compute
   :members:
   :undoc-members:

.. autoclass:: dftracer.python.ComputeEvent
   :members:
   :undoc-members:

Communication Operations
^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: dftracer.python.Communication
   :members:
   :undoc-members:

.. autoclass:: dftracer.python.CommunicationEvent
   :members:
   :undoc-members:

Checkpoint Operations
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: dftracer.python.Checkpoint
   :members:
   :undoc-members:

Pipeline Operations
^^^^^^^^^^^^^^^^^^^

.. autoclass:: dftracer.python.Pipeline
   :members:
   :undoc-members:

AI Instance
^^^^^^^^^^^

.. autoclass:: dftracer.python.AI
   :members:
   :undoc-members:

Utility Functions
-----------------

.. autofunction:: dftracer.python.get_iter_block_name
.. autofunction:: dftracer.python.get_iter_handle_name

Constants
---------

.. autodata:: dftracer.python.BLOCK_NAME
.. autodata:: dftracer.python.ITER_NAME
.. autodata:: dftracer.python.CTX_SEPARATOR

Module Instances
----------------

Convenience instances for common operations:

- ``ai`` - Main AI tracing instance
- ``data`` - Data operations
- ``dataloader`` - Dataloader operations
- ``device`` - Device transfer operations
- ``compute`` - Compute operations
- ``comm`` - Communication operations
- ``checkpoint`` - Checkpoint operations
- ``pipeline`` - Pipeline operations
