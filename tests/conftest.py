
from unittest import mock
import pytest
from sirup.IPRotator import IPRotator


@pytest.fixture
@mock.patch("sirup.IPRotator.check_password")
@mock.patch("sirup.IPRotator.kill_all_connections")
@mock.patch("getpass.getpass")
def iprotator_instance(mock_getpass, mock_kill, mock_check_pw, tmp_path): #pylint: disable=unused-argument  
    """Create an instance of IP rotator for use across tests
    
    Note: tmp_path is a built-in fixture of mock
    """
    config_files = ["file1", "file2", "file3"] # TODO: make this fixture available across tests. similar instance used in test_utils.py
    for f in config_files:
        (tmp_path / f).touch()
    
    mock_getpass.return_value = "my_password"
    mock_check_pw.return_value = True
    instance = IPRotator("path/to/auth/file", tmp_path)
    return instance