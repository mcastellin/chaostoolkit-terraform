from unittest.mock import patch
from chaosterraform import driver


class MockShellResponse:
    def __init__(self, returncode=0, text=""):
        self.returncode = returncode
        self.stdout = text


@patch("chaosterraform.driver.os.path")
def test_chdir(mocked_path):
    mocked_path.exists.return_value = True

    driver.Terraform.instance_ = None
    tf_driver = driver.Terraform(chdir="../testfolder/one")

    assert tf_driver._terraform == ["terraform", "-chdir=../testfolder/one"]


@patch("subprocess.run")
def test_init_default_args(mocked_run):
    mocked_run.return_value = MockShellResponse()
    driver.Terraform.instance_ = None
    tf_driver = driver.Terraform(silent=True)
    tf_driver.terraform_init()

    mocked_run.assert_called_once_with(
        ["terraform", "init"],
        shell=False,
        capture_output=True,
        text=False,
        check=False,
    )


@patch("subprocess.run")
def test_apply_default_args(mocked_run):
    mocked_run.return_value = MockShellResponse()
    driver.Terraform.instance_ = None
    tf_driver = driver.Terraform()
    tf_driver.apply()

    mocked_run.assert_called_once_with(
        ["terraform", "apply", "-auto-approve"],
        shell=False,
        capture_output=False,
        text=False,
        check=False,
    )


@patch("subprocess.run")
def test_apply_verbose(mocked_run):
    mocked_run.return_value = MockShellResponse()
    driver.Terraform.instance_ = None
    tf_driver = driver.Terraform(silent=True)
    tf_driver.apply()

    mocked_run.assert_called_once_with(
        ["terraform", "apply", "-auto-approve"],
        shell=False,
        capture_output=True,
        text=False,
        check=False,
    )


@patch("subprocess.run")
def test_destroy_default_args(mocked_run):
    driver.Terraform.instance_ = None
    tf_driver = driver.Terraform()
    tf_driver.destroy()

    mocked_run.assert_called_once_with(
        ["terraform", "destroy", "-auto-approve"],
        shell=False,
        capture_output=False,
        text=False,
        check=False,
    )


@patch("subprocess.run")
def test_output_strings(mocked_run):
    return_text = '{"expected":"value","one": "1","boolean":true,"number":999}'
    mocked_run.return_value = MockShellResponse(text=return_text)
    driver.Terraform.instance_ = None
    tf_driver = driver.Terraform()
    result = tf_driver.output()

    mocked_run.assert_called_once_with(
        ["terraform", "output", "-json"],
        shell=False,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.get("expected") == "value"
    assert result.get("one") == "1"
    assert result.get("boolean") is True
    assert result.get("number") == 999
