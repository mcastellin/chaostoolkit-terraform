import functools
import json
import os
import subprocess
from copy import deepcopy
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


def singleton(cls):
    """Creates a singleton wrapper for any calss"""

    @functools.wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if not wrapper_singleton.instance_:
            wrapper_singleton.instance_ = cls(*args, **kwargs)
        return wrapper_singleton.instance_

    wrapper_singleton.instance_ = None
    return wrapper_singleton


@singleton
class Terraform:
    def __init__(self):
        super().__init__()
        self.retain = False
        self.silent = False
        self.args = {}

    def configure(self, retain: bool = False, silent: bool = False, args: Dict = None):
        self.retain = retain
        self.silent = silent
        self.args = args or {}

    def terraform_init(self):
        if not os.path.exists(".terraform"):
            result = subprocess.run(
                "terraform init",
                capture_output=self.silent,
                shell=True,
            )
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
            var_overrides.append(f"-var {key}='{string_value}'")
        opts = " ".join(var_overrides)

        result = subprocess.run(
            f"terraform apply {opts} -auto-approve",
            capture_output=self.silent,
            shell=True,
        )
        if result.returncode != 0:
            raise InterruptExecution("Failed to apply terraform stack terraform")

    def output(self):
        result = subprocess.run(
            "terraform output -json",
            shell=True,
            capture_output=True,
            text=True,
        )
        outputs = json.loads(result.stdout)
        return outputs

    def destroy(self):
        subprocess.run(
            "terraform destroy -auto-approve",
            capture_output=self.silent,
            shell=True,
        )
