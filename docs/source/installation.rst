Installation
============

Basic Installation
------------------

The easiest way to install pydftracer is via pip:

.. code-block:: bash

   pip install pydftracer

Development Installation
------------------------

To install pydftracer for development:

.. code-block:: bash

   git clone https://github.com/llnl-asr/pydftracer.git
   cd pydftracer
   pip install -e ".[dev]"

Optional Dependencies
---------------------

PyTorch/Dynamo Support
~~~~~~~~~~~~~~~~~~~~~~

To use pydftracer with PyTorch and Dynamo tracing features:

.. code-block:: bash

   pip install pydftracer[dynamo]

Or manually install PyTorch:

.. code-block:: bash

   pip install torch>=2.5.1

Development Tools
~~~~~~~~~~~~~~~~~

To install all development dependencies (testing, linting, type checking):

.. code-block:: bash

   pip install pydftracer[dev]

This includes:
- pytest and pytest plugins
- ruff (linting)
- mypy (type checking)
- h5py, numpy, pillow (for testing)

Requirements
------------

- Python 3.9 or higher
- Operating System: Linux or Unix-like systems

Verifying Installation
----------------------

You can verify the installation by importing the package:

.. code-block:: python

   import dftracer.python
   print("pydftracer installed successfully!")
