"""
Terraform control module

This module allows Chaos Toolkit users to create infrastructure resources using Terraform scripts
for the experiment execution.
"""
from chaoslib.types import Configuration, Experiment, Journal, Secrets, Settings
from logzero import logger

from .driver import Terraform

VAR_NAME_PREFIX = "tf__"
CONFIG_PREFIX = "tf_conf__"
EXPORT_VAR_PREFIX = "tf_out__"


def configure_control(
    silent: bool = True,
    retain: bool = False,
    chdir: str = None,
    configuration: Configuration = None,
    secrets: Secrets = None,
    settings: Settings = None,
    experiment: Experiment = None,
):
    """
    Configure terraform control for the experiment execution

    Parameters
    ----------
    silent: bool
        suppress Terraform logs in ChaosToolkit experiment logs
    retain: bool
        retain created resources at the end of the experiment
    chdir: str
        change the Terraform working directory

    Raises
    ------
    InterruptExecution
        If terraform init fails we interrupt the experiment execution immediately
    """
    # pylint: disable=unused-argument
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
        "chdir": configuration.get(f"{CONFIG_PREFIX}chdir", chdir),
    }
    logger.info(
        "Terraform: retain stack after experiment completion: %s",
        str(params.get("retain")),
    )

    driver = Terraform(**params, args=tf_vars)
    driver.terraform_init()


def before_experiment_control(
    context: Experiment,
    configuration: Configuration = None,
    secrets: Secrets = None,
    **kwargs,
):
    """
    before-control of the experiment's execution

    Apply the Terraform stack before the experiment execution. As the experiment did not start
    yet, if the resources creation fails the execution is interrupted immediately.

    Raises
    ------
    InterruptExecution
        interrupts the experiment execution if resources creation fails
    """
    # pylint: disable=unused-argument
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
    """
    after-control of the experiment's execution

    Destroy resources after the experiment execution unless retain specifically requested by
    the experiment using the `retain` parameter
    """
    # pylint: disable=unused-argument
    driver = Terraform()
    if not driver.retain:
        logger.info("Terraform: removing experiment resources")
        driver.destroy()
    else:
        logger.info("Terraform: stack resources will be retained after experiment completion.")
