"""With DFTRACER_ATTACH=1 (set by the owner of the core, moirai), initialize_log attaches and never initializes or finalizes the core."""

import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "python"

CODE = textwrap.dedent(
    """
    import sys, types
    {moirai}
    import dftracer.python.common as C

    class Profiler(C.NoOpProfiler):
        calls = []
        def initialize(self, *a, **k): Profiler.calls.append("initialize")
        def finalize(self): Profiler.calls.append("finalize")
        def get_time(self): return 1

    C.profiler = Profiler()
    log = C.dftracer.initialize_log(logfile=None, data_dir=None, process_id=-1)
    log.finalize()
    print(log._attached, Profiler.calls)
    """
)


def run(moirai: str, env_extra: dict) -> str:
    env = {
        "PATH": "/usr/bin:/bin",
        "DFTRACER_ENABLE": "1",
        "PYTHONPATH": str(ROOT),
        **env_extra,
    }
    out = subprocess.run(
        [sys.executable, "-c", CODE.format(moirai=moirai)],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert out.returncode == 0, out.stderr
    return out.stdout.strip().splitlines()[-1]


def test_attaches_when_the_owner_sets_dftracer_attach():
    assert run("", {"DFTRACER_ATTACH": "1"}) == "True []"


def test_initializes_and_finalizes_without_the_variable():
    assert run("", {}) == "False ['initialize', 'finalize']"


def test_a_loaded_moirai_module_is_not_looked_up():
    """The variable is the whole contract: pydftracer never inspects sys.modules for the owner."""
    assert (
        run('sys.modules["moirai"] = types.ModuleType("moirai")', {})
        == "False ['initialize', 'finalize']"
    )
    assert run("", {"DFTRACER_ATTACH": "0"}) == "False ['initialize', 'finalize']"


def test_log_decorator_accepts_a_cached_function():
    code = (
        "import functools\n"
        "import dftracer.python.common as C\n"
        "d = C.dft_fn('t')\n"
        "@d.log\n"
        "@functools.lru_cache(maxsize=None)\n"
        "def f(x, y=1):\n"
        "    return x + y\n"
        "print(f(1), f(1))\n"
    )
    env = {"PATH": "/usr/bin:/bin", "DFTRACER_ENABLE": "1", "PYTHONPATH": str(ROOT)}
    out = subprocess.run(
        [sys.executable, "-c", code],
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert out.returncode == 0, out.stderr
    assert out.stdout.strip() == "2 2"
