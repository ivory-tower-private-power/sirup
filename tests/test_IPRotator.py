"""Tests for the sirup.IPRotator module.
"""

from unittest import mock
import pytest
import requests
from sirup.IPRotator import IPRotator
from sirup.utils import RotationList


@mock.patch("sirup.IPRotator.check_password")
@mock.patch("sirup.IPRotator.kill_all_connections")
@mock.patch("getpass.getpass")
def test_instantiate(mock_getpass, mock_kill, mock_check_pw, tmp_path): 
    # NOTE: tmp_path is a built-in fixture of mock
    config_files = ["file1", "file2", "file3"] # TODO: make this fixture available across tests. similar instance used in test_utils.py
    for f in config_files:
        (tmp_path / f).touch()
    
    mock_getpass.return_value = "my_password"
    mock_check_pw.return_value = True
    instance = IPRotator("path/to/auth/file", tmp_path)

    assert instance.connector is None, "connector wrongly instantiated"
    assert instance.pwd == "my_password"
    mock_getpass.assert_called_once()
    assert instance.auth_file == "path/to/auth/file"
    assert isinstance(instance.config_queue, RotationList)
    mock_kill.assert_called_once_with("my_password")


@mock.patch("sirup.IPRotator.check_password")
@mock.patch("sirup.IPRotator.kill_all_connections")
@mock.patch("getpass.getpass")
def test_repr(mock_getpass, mock_kill, mock_check_pw, tmp_path):# pylint: disable=unused-argument
    # NOTE: tmp_path is a built-in fixture of mock
    config_files = ["file1", "file2", "file3"] # TODO: make this fixture available across tests. similar instance used in test_utils.py
    for f in config_files:
        (tmp_path / f).touch()
    
    mock_getpass.return_value = "my_password"
    mock_check_pw.return_value = True
    instance = IPRotator("path/to/auth/file", tmp_path)
    repr_output = repr(instance)
    #pylint: disable=protected-access
    repr_expected = "IPRotator(auth_file='path/to/auth/file', "\
         f"pwd=<SECRET>, track_ip=True, config_location={instance._other_inputs['config_location']}, "\
         f"seed={instance._other_inputs['seed']}, config_file_rule={instance._other_inputs['config_file_rule']})"
    assert repr_output == repr_expected
    #pylint: enable=protected-access

#pylint: disable=too-many-arguments
@mock.patch("sirup.IPRotator.time.sleep")
@mock.patch("sirup.IPRotator.VPNConnector")
@mock.patch("sirup.IPRotator.check_password")
@mock.patch("sirup.IPRotator.kill_all_connections")
@mock.patch("getpass.getpass")
def test_connect(mock_getpass, mock_kill, mock_check_pw, mock_connector, mock_sleep, tmp_path):    
    # NOTE: tmp_path is a built-in fixture of mock
    config_files = ["file1", "file2", "file3"] # TODO: make this fixture available across tests. similar instance used in test_utils.py
    for f in config_files:
        (tmp_path / f).touch()
    
    mock_getpass.return_value = "my_password"
    mock_check_pw.return_value = True
    mock_connect = mock_connector.return_value.connect # NOTE: AAR -- need to mock the methods from the return value
    instance = IPRotator("path/to/auth/file", tmp_path)
    
    instance.connect()
    mock_connect.assert_called_once_with(pwd="my_password")

    # Test errors: TimeoutError when max trials is reached
    mock_connect.reset_mock()
    mock_connect.side_effect = TimeoutError
    with pytest.raises(TimeoutError, match="Failed to connect"):
        instance.connect(max_trials=1)
    # TODO: this is not immediate; need to trigger it somehow?

    # Test error: sleep when max trials is not reached
    mock_connect.reset_mock()
    mock_connect.side_effect = TimeoutError
    instance.connect(max_trials=2)

    # Test errors: connection error
    mock_connect.reset_mock()
    mock_kill.reset_mock()
    mock_sleep.reset_mock()
    mock_connect.side_effect = requests.ConnectionError
    instance.connect()
    mock_kill.assert_called_once_with("my_password")
    mock_sleep.assert_called_once()

#pylint: enable=too-many-arguments

        
