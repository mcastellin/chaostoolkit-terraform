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
CONFIG_PREFIX = "tf_conf__"
EXPORT_VAR_PREFIX = "tf_out__"


def configure_control(
    silent: bool = True,
    retain: bool = False,
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

    params = {
        "retain": bool(configuration.get(f"{CONFIG_PREFIX}retain", retain)),
        "silent": bool(configuration.get(f"{CONFIG_PREFIX}silent", silent)),
    }
    logger.info(
        "Terraform: retain stack after experiment completion: %s",
        str(params.get("retain")),
    )

    driver = Terraform()
    driver.configure(**params, args=tf_vars)
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
    logger.info("Terraform: creating required resources for experiment")
    driver.apply()
    for key, value in driver.output().items():
        logger.info("Terraform: reading configuration value for [%s]", key)
        configuration[f"{EXPORT_VAR_PREFIX}{key}"] = value.get("value")


def after_experiment_control(
    context: Experiment,
    state: Journal,
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    driver = Terraform()
    if not driver.retain:
        logger.info("Terraform: removing experiment resources")
        driver.destroy()
    else:
        logger.info(
            "Terraform: stack resources will be retained after experiment completion."
        )
