""" A Chaos Toolkit driver to run Terraform commands """
import functools
import json
import os
import subprocess
from copy import deepcopy
from itertools import chain
from typing import Dict, List

from chaoslib.exceptions import InterruptExecution
from logzero import logger


def _run(*cmd: List[List[str]], capture_output: bool = False, text: bool = False):
    _cmd = list(chain(*cmd))
    return subprocess.run(_cmd, shell=False, capture_output=capture_output, text=text, check=False)


def singleton(cls):
    """A singleton wrapper for any class"""

    @functools.wraps(cls)
    def wrapper_singleton(*args, **kwargs):
        if not wrapper_singleton.instance_:
            wrapper_singleton.instance_ = cls(*args, **kwargs)
        return wrapper_singleton.instance_

    wrapper_singleton.instance_ = None
    return wrapper_singleton


@singleton
class Terraform:
    """
    The Terraform driver to run CLI commands from the Python program

    Attributes
    ----------
    retain: bool
        A flag to indicate if created resources should be retained at the end of the experiment.
        By default all resources are destroyed
    silent: bool
        Suppress Terraform output in ChaosToolkit logs
    chdir: str
        A path to the terraform working directory. If the directory does not exists the experiment
        is interrupted with an InterruptExecution exception
    args: Dict
        Terraform variables overrides
    output_config: Dict
        Configuration to map Terraform output to configuration variables

    Raises
    ------
    InterruptExecution
        If the chdir path does not exists we interrupt the experiment execution immediately
    """

    def __init__(
        self,
        retain: bool = False,
        silent: bool = False,
        chdir: str = None,
        args: Dict = None,
        output_config: Dict = None,
    ):
        super().__init__()
        self.retain = retain
        self.silent = silent
        self.chdir = chdir
        self.args = args or {}
        self.output_config = output_config or {}

    @property
    def _terraform(self):
        if self.chdir:
            if not os.path.exists(self.chdir):
                raise InterruptExecution(f"Terraform: chdir [{self.chdir}] does not exists")
            if not os.path.isdir(self.chdir):
                raise InterruptExecution(f"Terraform: chdir [{self.chdir}] is not a directory")
            return ["terraform", f"-chdir={self.chdir}"]
        return ["terraform"]

    def terraform_init(self):
        """
        Initialize Terraform modules

        Raises
        ------
        InterruptExecution
            Interrupts the experiment execution if Terraform modules could not be initialized
        """
        if not os.path.exists(".terraform"):
            result = _run(self._terraform, ["init"], capture_output=self.silent)
            if result.returncode != 0:
                if self.silent:
                    logger.error(result.stderr.decode("utf-8"))
                raise InterruptExecution("Failed to initialize terraform")

    def apply(self, **kwargs):
        """
        Apply the Terraform stack

        Parameters
        ----------
        kwargs: Dict
            Keyword arguments to temporarily override Terraform variables for the apply

        Raises
        ------
        InterruptExecution
            Interrupts the experiment execution if the Terraform stack failed to create
        """

        args = deepcopy(self.args)
        args.update(kwargs)

        var_overrides = []
        for key, value in args.items():
            string_value = value
            if isinstance(value, bool):
                string_value = str(value).lower()
            var_overrides.extend(["-var", f"{key}={string_value}"])

        result = _run(
            self._terraform,
            ["apply", "-auto-approve"],
            var_overrides,
            capture_output=self.silent,
        )
        if result.returncode != 0:
            if self.silent:
                logger.error(result.stderr.decode("utf-8"))
            raise InterruptExecution("Failed to apply terraform stack terraform")

    def output(self):
        """
        Reads Terraform stack outputs into a Python dict

        Returns
        -------
        dict
            A dictionary of output parameters from the Terraform stack
        """
        result = _run(self._terraform, ["output", "-json"], capture_output=True, text=True)
        outputs = json.loads(result.stdout)
        return outputs

    def destroy(self):
        """
        Destroy the resources created by the Terraform stack
        """
        _run(
            self._terraform,
            ["destroy", "-auto-approve"],
            capture_output=self.silent,
        )
