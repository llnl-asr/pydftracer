# pydftracer

[![Documentation Status](https://readthedocs.org/projects/python/badge/?version=latest)](https://dftracer.readthedocs.io/projects/python/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

A lightweight, typed Python interface for [DFTracer](https://github.com/llnl-asr/dftracer). 
Ideal for prototyping, testing, and iterating on code that uses the DFTracer Python API before deploying the complete tracing stack.

## Purposes

- Are prototyping applications that will eventually use full DFTracer
- Maintain DFTracer API compatibility in environments where tracing is not needed (e.g. production apps)

## Installation

```bash
pip install dftracer
```

## Development

```bash
# Install development dependencies
pip install -e .[dev]

# Using Make (recommended)
make test-parallel       # Run all tests with parallel execution
make test-subprocess     # Run only subprocess-based dftracer tests  
make test-ci             # Run comprehensive tests matching CI configuration
make test-ci-quick       # Run quick tests and checks (faster)
make check-all           # Run all quality checks (lint, format, type-check, test)

# Using pytest directly
pytest tests/ -v -n 4    # All tests with parallel execution
pytest tests/ --cov=dftracer --cov-report=term-missing -v -n 4  # Tests with coverage
```

## Documentation

Full documentation is available at [Read the Docs](https://dftracer.readthedocs.io/projects/utils/).

To build documentation locally:

```bash
pip install .
cd docs
pip install -r requirements.txt
make html
```

Furthermore, if you want to enable profiling, please see resources below:

* Building DFTracer: [https://dftracer.readthedocs.io/en/latest/build.html](https://dftracer.readthedocs.io/en/latest/build.html)
* Integrating DFTracer: [https://dftracer.readthedocs.io/en/latest/examples.html](https://dftracer.readthedocs.io/en/latest/examples.html)
* Visualizing DFTracer Traces: [https://dftracer.readthedocs.io/en/latest/perfetto.html](https://dftracer.readthedocs.io/en/latest/perfetto.html)
* Building DFAnalyzer: [https://dftracer.readthedocs.io/en/latest/dfanalyzer_build.html](https://dftracer.readthedocs.io/en/latest/dfanalyzer_build.html)

## Development

### Testing

This project uses a comprehensive test suite with subprocess-based isolation for proper dftracer testing.

#### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Using Make (recommended)
make test-parallel    # Run all tests with parallel execution
make test-subprocess  # Run only subprocess-based dftracer tests  
make test-ci          # Run tests matching CI configuration
make check-all        # Run all quality checks (lint, format, type-check, test)

# Using pytest directly
pytest tests/ -v -n 2                                    # All tests with parallel execution
pytest tests/ --cov=dftracer --cov-report=term-missing -v -n 2  # Tests with coverage
pytest tests/ -m subprocess -v -n 2                      # Only subprocess tests

# Use the provided test script (matches CI)
./scripts/test.sh
```

#### Test Structure

- **Unit Tests**: General functionality tests in `tests/test_general.py`
- **Integration Tests**: Subprocess-based dftracer tests in `tests/test_dftracer.py`
- **Parallel Execution**: Tests run in parallel using `pytest-xdist` for faster execution
- **Process Isolation**: dftracer tests run in separate subprocesses to handle the per-process nature of dftracer

#### CI/CD

The project uses GitHub Actions for continuous integration with:
- Multi-Python version testing (3.9, 3.10, 3.11, 3.12)
- Parallel test execution with coverage reporting
- Code linting with `ruff`
- Type checking with `mypy`
- Package building and installation testing

## Citation and Reference

The original SC'24 paper describes the design and implementation of the DFTracer code. Please cite this paper and the code if you use DFTracer in your research. 

```
@inproceedings{devarajan_dftracer_2024,
    address = {Atlanta, GA},
    title = {{DFTracer}: {An} {Analysis}-{Friendly} {Data} {Flow} {Tracer} for {AI}-{Driven} {Workflows}},
    shorttitle = {{DFTracer}},
    urldate = {2024-07-31},
    booktitle = {{SC24}: {International} {Conference} for {High} {Performance} {Computing}, {Networking}, {Storage} and {Analysis}},
    publisher = {IEEE},
    author = {Devarajan, Hariharan and Pottier, Loic and Velusamy, Kaushik and Zheng, Huihuo and Yildirim, Izzet and Kogiou, Olga and Yu, Weikuan and Kougkas, Anthony and Sun, Xian-He and Yeom, Jae Seung and Mohror, Kathryn},
    month = nov,
    year = {2024},
}

@misc{devarajan_dftracer_code_2024,
    type = {Github},
    title = {Github {DFTracer}},
    shorttitle = {{DFTracer}},
    url = {https://github.com/llnl-asr/dftracer.git},
    urldate = {2024-07-31},
    journal = {DFTracer: A multi-level dataflow tracer for capture I/O calls from worklows.},
    author = {Devarajan, Hariharan and Pottier, Loic and Velusamy, Kaushik and Zheng, Huihuo and Yildirim, Izzet and Kogiou, Olga and Yu, Weikuan and Kougkas, Anthony and Sun, Xian-He and Yeom, Jae Seung and Mohror, Kathryn},
    month = jun,
    year = {2024},
}
```

## Acknowledgments

This work was performed under the auspices of the U.S. Department of Energy by Lawrence Livermore National Laboratory under Contract DE-AC52-07NA27344; and under the auspices of the National Cancer Institute (NCI) by Frederick National Laboratory for Cancer Research (FNLCR) under Contract 75N91019D00024. This research used resources of the Argonne Leadership Computing Facility, a U.S. Department of Energy (DOE) Office of Science user facility at Argonne National Laboratory and is based on research supported by the U.S. DOE Office of Science-Advanced Scientific Computing Research Program, under Contract No. DE-AC02-06CH11357. Office of Advanced Scientific Computing Research under the DOE Early Career Research Program. Also, This material is based upon work partially supported by LLNL LDRD 23-ERD-045 and 24-SI-005. LLNL-CONF-857447.

## License

pydftracer is distributed under the terms of the MIT license.
All new contributions must be made under this license.

See [LICENSE](LICENSE) and [NOTICE](NOTICE) for details.

SPDX-License-Identifier: MIT

LLNL-CODE-2024514 — Applied Storage Research (ASR)
