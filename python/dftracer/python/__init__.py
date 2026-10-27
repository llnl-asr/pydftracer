from importlib.metadata import PackageNotFoundError, version

from dftracer.python.agent import *
from dftracer.python.agent_langgraph import *
from dftracer.python.ai import *
from dftracer.python.dynamo import *
from dftracer.python.logger import *

try:
    __version__ = version("pydftracer")
except PackageNotFoundError:
    # package is not installed
    pass
