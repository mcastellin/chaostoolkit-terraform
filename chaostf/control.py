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
from logzero import logger

from .driver import Terraform

VAR_NAME_PREFIX = "tf__"


def configure_control(
    configuration: Configuration = None,
    secrets: Secrets = None,
    settings: Settings = None,
    experiment: Experiment = None,
):
    tf_vars = {}
    if configuration:
        for key, value in configuration.items():
            if key.startswith(VAR_NAME_PREFIX):
                tf_key = key.replace(VAR_NAME_PREFIX, "")
                tf_vars[tf_key] = value

    for key, _ in tf_vars.items():
        configuration.pop(f"{VAR_NAME_PREFIX}{key}")

    retain = configuration.get("tf_conf__retain", False)
    logger.info("Terraform: retain stack after experiment completion: %s", str(retain))

    driver = Terraform()
    driver.configure(retain=bool(retain), args=tf_vars)
    driver.terraform_init()


def before_experiment_control(
    context: Experiment,
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    """
    before-control of the experiment's execution

    Called by the Chaos Toolkit before the experiment's begin but after the
    configuration and secrets have been loaded.
    """
    driver = Terraform()
    driver.apply()
    for key, value in driver.output().items():
        configuration[f"tf_out__{key}"] = value.get("value")


def after_experiment_control(
    context: Experiment,
    state: Journal,
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    driver = Terraform()
    if not driver.retain:
        driver.destroy()
    else:
        logger.info(
            "Terraform: stack resources will be retained after experiment completion."
        )
