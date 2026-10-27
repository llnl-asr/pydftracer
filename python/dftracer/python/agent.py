import dftracer.python.ai_common as ai_common
from dftracer.python.logger import dft_fn as dft_fn_orig
from dftracer.python.logger import dftracer as dftracer_orig

ai_common.dft_fn = dft_fn_orig  # type: ignore[misc]
ai_common.dftracer = dftracer_orig  # type: ignore[misc]

from dftracer.python.agent_common import *
from dftracer.python.agent_init import *
