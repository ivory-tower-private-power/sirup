"""Tests for the sirup.IPRotator module.
"""

from unittest import mock
from sirup.IPRotator import IPRotator
from sirup.utils import RotationList


@mock.patch("sirup.IPRotator.kill_all_connections")
@mock.patch("getpass.getpass")
def test_instantiate(mock_getpass, mock_kill, tmp_path):   
    config_files = ["file1", "file2", "file3"] # TODO: make this fixture available across tests. similar instance used in test_utils.py
    for f in config_files:
        (tmp_path / f).touch()
    
    mock_getpass.return_value = "my_password"
    instance = IPRotator("path/to/auth/file", tmp_path)

    assert instance.connector is None, "connector wrongly instantiated"
    assert instance.pwd == "my_password"
    mock_getpass.assert_called_once()
    assert instance.auth_file == "path/to/auth/file"
    assert isinstance(instance.config_queue, RotationList)
    mock_kill.assert_called_once_with("my_password")