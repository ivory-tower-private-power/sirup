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
    "Test for object instantiation."
    # Don't use the iprotator_instance fixture here
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


def test_repr(iprotator_instance):
    repr_output = repr(iprotator_instance)
    #pylint: disable=protected-access
    repr_expected = "IPRotator(auth_file='path/to/auth/file', "\
         f"pwd=<SECRET>, track_ip=True, config_location={iprotator_instance._other_inputs['config_location']}, "\
         f"seed={iprotator_instance._other_inputs['seed']}, config_file_rule={iprotator_instance._other_inputs['config_file_rule']})"
    assert repr_output == repr_expected
    #pylint: enable=protected-access


@mock.patch.object(RotationList, "shuffle")
@mock.patch("sirup.IPRotator.time.sleep")
@mock.patch("sirup.IPRotator.VPNConnector")
@mock.patch("sirup.IPRotator.kill_all_connections")
def test_connect(mock_kill, mock_connector, mock_sleep, mock_rotation_list, iprotator_instance):    
   
    # We'll be using the return value of the mock_connector: (1) for the connect() fct; (2) for the assertion below
    mock_connector = mock_connector.return_value

    # Test without errors
    mock_connect = mock_connector.connect 
    iprotator_instance.connect(shuffle=True)
    mock_connect.assert_called_once_with(pwd="my_password")
    # pylint: disable=protected-access
    assert iprotator_instance.connector._extract_mock_name() == mock_connector._extract_mock_name(), \
        "iprotator_instance has uncorrect `connector` attribute"
    # pylint: enable=protected-access
    mock_rotation_list.assert_called_once_with(iprotator_instance.randomizer)

    # Test with errors: TimeoutError when max trials is reached
    mock_connect.reset_mock()
    mock_connect.side_effect = TimeoutError
    with pytest.raises(TimeoutError, match="Failed to connect"):
        iprotator_instance.connect(max_trials=1)

    # Test with errors: sleep when max trials is not reached
    mock_connect.reset_mock()
    mock_connect.side_effect = TimeoutError
    iprotator_instance.connect(max_trials=2)

    # Test with errors: connection error
    mock_connect.reset_mock()
    mock_kill.reset_mock()
    mock_sleep.reset_mock()
    mock_connect.side_effect = requests.ConnectionError
    iprotator_instance.connect()
    mock_kill.assert_called_once_with("my_password")
    mock_sleep.assert_called_once()


@mock.patch("sirup.IPRotator.VPNConnector")
def test_disconnect(mock_connector, iprotator_instance):

    iprotator_instance.connector = mock_connector.return_value
    mock_disconnect = iprotator_instance.connector.disconnect 

    iprotator_instance.disconnect()
    mock_disconnect.assert_called_once_with("my_password")
    assert iprotator_instance.connector is None, "connector not reset after disconnecting."


@mock.patch.object(IPRotator, "disconnect")
@mock.patch.object(IPRotator, "connect")
def test_rotate(mock_connect, mock_disconnect, iprotator_instance):   
    # Main call
    iprotator_instance.rotate()
    # Assert 
    mock_disconnect.assert_called_once_with()
    mock_connect.assert_called_once_with()