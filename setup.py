# we presume installed build dependencies
from __future__ import annotations

from setuptools import setup
from setuptools_scm import ScmVersion


# <last tag>.post<commits since tag>.dev0 between releases, so a develop
# prerelease sorts after the tag and pip skips it without --pre.
def myversion_func(version: ScmVersion) -> str:
    if version.distance > 0:
        return version.format_with("{tag}.post{distance}.dev0")
    return version.format_with("{tag}")


setup(use_scm_version={"version_scheme": myversion_func})
