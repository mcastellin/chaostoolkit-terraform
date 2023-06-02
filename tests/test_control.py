from unittest.mock import patch
from chaosterraform import control


@patch("chaosterraform.control.Terraform", autospec=True)
def test_configure_control_with_parameters(mocked_driver):
    control.configure_control(silent=False, retain=True, chdir="../testfolder/one", configuration={})

    mocked_driver.assert_called_once_with(silent=False, retain=True, chdir="../testfolder/one", args={})
    mock_instance = mocked_driver.return_value
    mock_instance.terraform_init.assert_called()


@patch("chaosterraform.control.Terraform", autospec=True)
def test_configure_control_with_terraform_variables(mocked_driver):
    configuration = {
        "tf__variable_str": "sg-00001111",
        "tf__one_more_bool_var": True,
        "tf__numeric": 1.2,
    }

    control.configure_control(configuration=configuration)

    expected_variables = {
        "variable_str": "sg-00001111",
        "one_more_bool_var": True,
        "numeric": 1.2,
    }

    mocked_driver.assert_called_once_with(silent=True, retain=False, chdir=None, args=expected_variables)


@patch("chaosterraform.control.Terraform", autospec=True)
def test_configure_control_configuration_override(mocked_driver):
    configuration = {
        "tf_conf__silent": False,
        "tf_conf__retain": True,
        "tf_conf__chdir": "my/other/folder/path",
    }

    control.configure_control(silent=True, retain=False, chdir="some/folder", configuration=configuration)

    mocked_driver.assert_called_once_with(silent=False, retain=True, chdir="my/other/folder/path", args={})


@patch("chaosterraform.control.Terraform", autospec=True)
def test_before_experiment_control_with_outputs(mocked_driver):
    outputs = {
        "dns_name": {"value": "example.com"},
        "desired_count": {"value": 1},
        "cpu_units": {"value": 1024},
    }
    configuration = {}
    mock_instance = mocked_driver.return_value
    mock_instance.output.return_value = outputs
    control.before_experiment_control(context=None, configuration=configuration)

    mock_instance.apply.assert_called_once()
    mock_instance.output.assert_called_once()

    assert configuration.get("tf_out__dns_name") == "example.com"
    assert configuration.get("tf_out__desired_count") == 1
    assert configuration.get("tf_out__cpu_units") == 1024


@patch("chaosterraform.control.Terraform", autospec=True)
def test_after_method(mocked_driver):
    configuration = {}
    mock_instance = mocked_driver.return_value
    mock_instance.retain = False

    control.after_experiment_control(context=None, state=None, configuration=configuration)

    mock_instance.destroy.assert_called_once()


@patch("chaosterraform.control.Terraform", autospec=True)
def test_after_method_retain_resources(mocked_driver):
    configuration = {}
    mock_instance = mocked_driver.return_value
    mock_instance.retain = True

    control.after_experiment_control(context=None, state=None, configuration=configuration)

    mock_instance.destroy.assert_not_called()
