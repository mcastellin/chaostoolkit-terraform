from typing import Any, Dict, List, Union

from chaoslib.exceptions import FailedActivity
from chaoslib.types import Configuration, Secrets
from logzero import logger

from .control import driver

__all__ = ["apply"]


def apply(
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    driver.apply(**kwargs)
