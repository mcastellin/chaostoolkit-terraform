"""
Terraform control module

This module allows Chaos Toolkit users to create infrastructure resources using Terraform scripts
for the experiment execution.
"""
from typing import Any, Dict

from chaoslib.exceptions import InterruptExecution
from chaoslib.types import Configuration, Experiment, Journal, Secrets, Settings
from logzero import logger

from .driver import Terraform

CONFIG_PREFIX = "tf_conf__"
EXPORT_VAR_PREFIX = "tf_out__"


def configure_control(
    silent: bool = True,
    retain: bool = False,
    chdir: str = None,
    variables: Dict = None,
    outputs: Dict = None,
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
        retain created resources after the end of the experiment
    chdir: str
        change the Terraform working directory
    variables: Dict
        input variables configuration for Terraform
    outputs: Dict
       defines how to map Terraform outputs to ChaosToolkit variables. By default
       output values are always mapped using the "tf_out__" prefix.

    Raises
    ------
    InterruptExecution
        If terraform init fails we interrupt the experiment execution immediately
    """
    # pylint: disable=unused-argument
    tf_vars = {}
    if variables:
        for key, value in variables.items():
            tf_vars[key] = _resolve_variable(configuration, key, value)

    params = {
        "retain": bool(configuration.get(f"{CONFIG_PREFIX}retain", retain)),
        "silent": bool(configuration.get(f"{CONFIG_PREFIX}silent", silent)),
        "chdir": configuration.get(f"{CONFIG_PREFIX}chdir", chdir),
    }
    logger.info(
        "Terraform: retain stack after experiment completion: %s",
        str(params.get("retain")),
    )

    driver = Terraform(**params, args=tf_vars, output_config=outputs)
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
        if key in driver.output_config:
            export_name = driver.output_config[key]
            configuration[export_name] = value.get("value")


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


def _resolve_variable(configuration, key, value) -> Any:
    if isinstance(value, dict):
        if "name" not in value:
            raise InterruptExecution(f"Terraform: parameter {key} should specify either a value or a 'name' key.")

        parameter_name = value["name"]
        if parameter_name not in configuration:
            raise InterruptExecution(f"Terraform: could not resolve value for variable {key} in configuration")

        return configuration[parameter_name]

    return value
