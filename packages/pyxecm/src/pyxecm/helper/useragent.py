"""Shared USER_AGENT construction for all pyxecm client modules."""

import platform
import sys
from importlib.metadata import version

import requests

APP_NAME = "pyxecm"
APP_VERSION = version("pyxecm")
PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
OS_INFO = f"{platform.system()} {platform.release()}"
ARCH_INFO = platform.machine()
REQUESTS_VERSION = requests.__version__


def build_user_agent(module_name: str) -> str:
    """Build a USER_AGENT string for a pyxecm client module.

    Args:
        module_name: The module identifier (e.g., "pyxecm.otcs").

    Returns:
        Formatted USER_AGENT string.

    """
    return (
        f"{APP_NAME}/{APP_VERSION} ({module_name}/{APP_VERSION}; "
        f"Python/{PYTHON_VERSION}; {OS_INFO}; {ARCH_INFO}; Requests/{REQUESTS_VERSION})"
    )
