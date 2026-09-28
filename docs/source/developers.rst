Developer Guide
===============

This guide is for developers who want to contribute to pydftracer or understand its internals.

.. contents:: Table of Contents
   :local:
   :depth: 2

Development Setup
-----------------

Prerequisites
~~~~~~~~~~~~~

- Python 3.9 or higher
- Git
- C++ compiler (for building the core DFTracer library)
- pip and virtualenv

Clone the Repository
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install git+https://github.com/llnl-asr/dftracer.git --no-deps
   pip install ".[dev]"

Create Development Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Create virtual environment
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate

   # Install in development mode with all dependencies
   pip install ".[dev,docs,dynamo]"

This installs:

- **dev**: Testing and development tools (pytest, ruff, mypy)
- **docs**: Documentation building tools (Sphinx, themes)
- **dynamo**: PyTorch integration for Dynamo tracing

Project Structure
-----------------

Repository Layout
~~~~~~~~~~~~~~~~~

.. code-block:: text

   pydftracer/
   ├── python/
   │   └── dftracer/
   │       └── python/          # Main Python package
   │           ├── __init__.py
   │           ├── logger.py    # Core logger implementation
   │           ├── common.py    # Common utilities
   │           ├── env.py       # Environment configuration
   │           ├── ai.py        # AI/ML tracing API
   │           ├── ai_common.py # AI common utilities
   │           ├── ai_init.py   # AI initialization
   │           ├── dynamo.py    # PyTorch Dynamo integration
   │           └── dbg/         # Debug utilities
   │               ├── __init__.py
   │               ├── logger.py
   │               └── ai.py
   ├── tests/                   # Test suite
   │   ├── test_dftracer.py
   │   ├── test_ai_logging.py
   │   ├── test_dynamo.py
   │   └── utils.py
   ├── docs/                    # Documentation
   │   ├── source/
   │   └── Makefile
   ├── pyproject.toml           # Project configuration
   └── README.md

Key Modules
~~~~~~~~~~~

**dftracer.python.logger**
   Core logging functionality, ``dftracer`` class, and ``dft_fn`` decorator

**dftracer.python.common**
   Common utilities, type definitions, and the profiler protocol

**dftracer.python.env**
   Environment variable handling and logger setup

**dftracer.python.ai**
   AI/ML specific tracing decorators and utilities

**dftracer.python.dynamo**
   PyTorch Dynamo integration for model tracing

Running Tests
-------------

Run All Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   pytest

   # Run with coverage
   pytest --cov=python/dftracer --cov-report=html

   # Run in parallel
   pytest -n auto

Run Specific Tests
~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Run specific test file
   pytest tests/test_dftracer.py

   # Run specific test function
   pytest tests/test_dftracer.py::TestDFTracerLogger::test_dftracer_singleton

   # Run tests matching a pattern
   pytest -k "test_ai"

Test with Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Enable DFTracer for tests
   DFTRACER_ENABLE=1 pytest tests/test_dftracer.py

   # Set log level for debugging
   DFTRACER_LOG_LEVEL=DEBUG pytest tests/test_ai_logging.py

Code Quality
------------

Linting
~~~~~~~

The project uses **ruff** for linting:

.. code-block:: bash

   # Run ruff linter
   ruff check python/dftracer

   # Auto-fix issues
   ruff check --fix python/dftracer

Type Checking
~~~~~~~~~~~~~

The project uses **mypy** for type checking:

.. code-block:: bash

   # Run mypy
   mypy python/dftracer/python/

   # Check specific file
   mypy python/dftracer/python/logger.py

Formatting
~~~~~~~~~~

Follow the project's coding style:

- Line length: 88 characters (Black default)
- Use type hints where possible
- Follow Google/NumPy docstring conventions

Configuration
~~~~~~~~~~~~~

Linting and type checking rules are defined in ``pyproject.toml``:

.. code-block:: toml

   [tool.ruff]
   line-length = 88
   target-version = "py39"

   [tool.ruff.lint]
   select = ["E", "F", "W", "B", "I", "UP"]
   ignore = ["E501", "B006", "B008", ...]

   [tool.mypy]
   python_version = "3.9"
   warn_return_any = true
   disallow_untyped_defs = true

Building Documentation
----------------------

Build HTML Docs
~~~~~~~~~~~~~~~

.. code-block:: bash

   cd docs
   make html

   # View the docs
   open build/html/index.html  # macOS
   # or
   xdg-open build/html/index.html  # Linux

Clean Build
~~~~~~~~~~~

.. code-block:: bash

   make clean
   make html

Check for Broken Links
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   make linkcheck

Build Other Formats
~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   make latexpdf  # PDF (requires LaTeX)
   make epub      # EPUB
   make man       # Man pages

Contributing
------------

Development Workflow
~~~~~~~~~~~~~~~~~~~~

1. **Fork and Clone**

   .. code-block:: bash

      git clone https://github.com/YOUR_USERNAME/dftracer.git
      cd dftracer/pydftracer

2. **Create a Branch**

   .. code-block:: bash

      git checkout -b feature/my-feature
      # or
      git checkout -b fix/issue-123

3. **Make Changes**

   - Write code following the style guide
   - Add tests for new functionality
   - Update documentation

4. **Run Tests**

   .. code-block:: bash

      pytest
      ruff check python/dftracer
      mypy python/dftracer/python/

5. **Commit Changes**

   .. code-block:: bash

      git add .
      git commit -m "Add feature: description"

6. **Push and Create PR**

   .. code-block:: bash

      git push origin feature/my-feature

   Then create a Pull Request on GitHub.

Commit Message Guidelines
~~~~~~~~~~~~~~~~~~~~~~~~~~

Follow conventional commit format:

.. code-block:: text

   <type>: <description>

   [optional body]

   [optional footer]

Types:

- ``feat``: New feature
- ``fix``: Bug fix
- ``docs``: Documentation changes
- ``test``: Adding or updating tests
- ``refactor``: Code refactoring
- ``perf``: Performance improvements
- ``chore``: Maintenance tasks

Example:

.. code-block:: text

   feat: add support for custom trace categories

   - Implement custom category registration
   - Add tests for category validation
   - Update documentation

   Closes #123

Adding New Features
-------------------

Adding a New Tracer Category
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To add a new AI/ML tracer category:

1. **Define the category in ai_common.py**

   .. code-block:: python

      class MyCategory(DFTracerAI):
          def __init__(self, ...):
              super().__init__(cat="my_category", ...)

2. **Add to AI class hierarchy**

   .. code-block:: python

      class AI(DFTracerAI):
          def __init__(self):
              super().__init__(cat="ai", ...)
              self.my_category = MyCategory()

3. **Export in __init__.py**

   .. code-block:: python

      from dftracer.python.ai_common import MyCategory
      __all__ = [..., "MyCategory"]

4. **Add tests**

   .. code-block:: python

      def test_my_category():
          @ai.my_category
          def my_function():
              pass

5. **Update documentation**

   Add examples to :doc:`ai_ml_guide`

Adding New Environment Variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. **Define in env.py**

   .. code-block:: python

      MY_NEW_VAR_ENV = "DFTRACER_MY_VAR"
      MY_NEW_VAR = os.getenv(MY_NEW_VAR_ENV, "default_value")

2. **Export in __init__.py**

   .. code-block:: python

      from dftracer.python.env import MY_NEW_VAR
      __all__ = [..., "MY_NEW_VAR"]

3. **Document in env.rst**

   Add to API reference

Debugging
---------

Enable Debug Logging
~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   export DFTRACER_LOG_LEVEL=DEBUG
   python your_script.py

Use Debug Logger
~~~~~~~~~~~~~~~~

.. code-block:: python

   from dftracer.python.dbg import logger as dbg_logger

   # This provides more verbose output
   log = dbg_logger()

Common Issues
~~~~~~~~~~~~~

**Issue**: Tests fail with "DFTracer not available"

**Solution**: Ensure the C++ DFTracer library is installed:

.. code-block:: bash

   pip install dftracer
   pip install . # rewrite to install local changes

   # OR

   pip install dftracer --no-deps # since dftracer depends on this package

**Issue**: Import errors in tests

**Solution**: Install in development mode:

.. code-block:: bash

   pip install .

**Issue**: Type checking fails

**Solution**: Update type stubs or add to mypy overrides in pyproject.toml

Performance Considerations
--------------------------

Profiling Overhead
~~~~~~~~~~~~~~~~~~

DFTracer is designed for minimal overhead, but consider:

- **Decorator overhead**: ~1-5% for most functions
- **I/O tracing**: Depends on I/O frequency
- **Event logging**: Buffered writes, minimal impact

Reducing Overhead
~~~~~~~~~~~~~~~~~

1. **Selective tracing**: Only trace critical paths
2. **Disable categories**: Turn off unused categories
3. **Batch logging**: Use streaming mode for high-frequency events

.. code-block:: python

   # Disable unused categories
   ai.comm.disable()
   ai.checkpoint.disable()

   # Use metadata mode for high-frequency events
   for epoch in range(num_epochs):
       ai.pipeline.epoch.start(metadata=True)
       # Training code
       ai.pipeline.epoch.stop(metadata=True)

Release Process
---------------

Versioning
~~~~~~~~~~

pydftracer follows `Semantic Versioning <https://semver.org/>`_:

- **MAJOR**: Incompatible API changes
- **MINOR**: New features, backward compatible
- **PATCH**: Bug fixes, backward compatible

The version is managed by ``setuptools-scm`` from git tags.

Creating a Release
~~~~~~~~~~~~~~~~~~

1. **Update CHANGELOG**

   Document all changes since last release

2. **Create Git Tag**

   .. code-block:: bash

      git tag -a v0.2.0 -m "Release version 0.2.0"
      git push origin v0.2.0

3. **Build**

   .. code-block:: bash

      python -m build

4. **Update Documentation**

   Documentation is auto-deployed from tags

Resources
---------

- **Main Repository**: https://github.com/llnl-asr/dftracer
- **Issues**: https://github.com/llnl-asr/dftracer/issues
- **DFAnalyzer**: https://github.com/llnl-asr/dfanalyzer

Getting Help
------------

If you need help:

1. Check the :doc:`quickstart` and :doc:`api/index`
2. Search existing `GitHub Issues <https://github.com/llnl-asr/dftracer/issues>`_
3. Contact the maintainers

License
-------

pydftracer is released under the MIT License. See the LICENSE file in the repository for details.

Contributing to Documentation
-----------------------------

The documentation is built with Sphinx. See ``docs/README.md`` for details.

Key files:

- ``docs/source/conf.py`` - Sphinx configuration
- ``docs/source/*.rst`` - ReStructuredText source files
- ``docs/source/api/`` - API reference

To contribute:

1. Edit the appropriate ``.rst`` files
2. Build locally to preview: ``make html``
3. Check for warnings and broken links
4. Submit PR with documentation changes
