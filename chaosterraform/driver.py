import functools
import json
import os
import subprocess
from copy import deepcopy
from itertools import chain
from typing import Any, Dict, List

from chaoslib.exceptions import InterruptExecution
from chaoslib.types import (
    Activity,
    Configuration,
    Experiment,
    Hypothesis,
    Journal,
    Run,
    Secrets,
    Settings,
)


def _run(*cmd: List[List[str]], capture_output: bool = False, text: bool = False):
    _cmd = list(chain(*cmd))
    return subprocess.run(_cmd, shell=False, capture_output=capture_output, text=text)


def singleton(cls):
    """Creates a singleton wrapper for any class"""

    @functools.wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if not wrapper_singleton.instance_:
            wrapper_singleton.instance_ = cls(*args, **kwargs)
        return wrapper_singleton.instance_

    wrapper_singleton.instance_ = None
    return wrapper_singleton


@singleton
class Terraform:
    def __init__(
        self,
        retain: bool = False,
        silent: bool = False,
        chdir: str = None,
        args: Dict = None,
    ):
        super().__init__()
        self.retain = retain
        self.silent = silent
        self.chdir = chdir
        self.args = args or {}

    @property
    def _terraform(self):
        if self.chdir:
            if not os.path.exists(self.chdir):
                raise InterruptExecution(
                    f"Terraform: chdir [{self.chdir}] does not exists"
                )
            if not os.path.isdir(self.chdir):
                raise InterruptExecution(
                    f"Terraform: chdir [{self.chdir}] is not a directory"
                )
            return ["terraform", f"-chdir={self.chdir}"]
        return ["terraform"]

    def terraform_init(self):
        if not os.path.exists(".terraform"):
            result = _run(self._terraform, ["init"], capture_output=self.silent)
            if result.returncode != 0:
                raise InterruptExecution("Failed to initialize terraform")

    def apply(self, **kwargs):
        args = deepcopy(self.args)
        args.update(kwargs)

        var_overrides = []
        for key, value in args.items():
            string_value = value
            if isinstance(value, bool):
                string_value = str(value).lower()
            var_overrides.extend(["-var", f"{key}='{string_value}'"])

        result = _run(
            self._terraform,
            ["apply", "-auto-approve"],
            var_overrides,
            capture_output=self.silent,
        )
        if result.returncode != 0:
            raise InterruptExecution("Failed to apply terraform stack terraform")

    def output(self):
        result = _run(
            self._terraform, ["output", "-json"], capture_output=True, text=True
        )
        outputs = json.loads(result.stdout)
        return outputs

    def destroy(self):
        _run(
            self._terraform,
            ["destroy", "-auto-approve"],
            capture_output=self.silent,
        )
