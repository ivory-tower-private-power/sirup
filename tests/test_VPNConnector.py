
import os
import tempfile
from subprocess import PIPE
from unittest import mock
import pytest
import requests
from sirup.VPNConnector import VPNConnector


## Fixtures
@pytest.fixture
def connect_command():
    temp_dir = tempfile.gettempdir()
    return ["sudo", "-S", "openvpn",
           "--config", "config_file",
           "--auth-user-pass", "auth_file",
           "--log", os.path.join(temp_dir, "openvpn.log"),
           "--daemon"]

## Tests


@mock.patch("sirup.VPNConnector.TemporaryFileWithRootPermission")
@mock.patch("sirup.VPNConnector.get_ip") 
@mock.patch("subprocess.Popen")
def test_start_vpn(mock_popen, mock_get_ip, mock_temp_file, connect_command):
    """Test that OpenVPN is started with the right arguments.

    Comment
    -------
    We need to mock 3 things
    - subprocess.Popen, which we expect to be called with certain arguments by the connector.start_vpn value
    - sirup.VPNConnector.get_ip, which requires an internet connection and makes an API call for each test run 
    - TemporaryFileWithRootPermission, because it does `subprocess.run`, which calls Popen.__init__
    (see https://github.com/python/cpython/blob/main/Lib/subprocess.py). Without the mock, this interferes 
    with the test because Popen.__init__() is called twice.

    Note also that we patch the objects and functions from sirup.VPNConnector, and not from
    their source files. See also https://docs.python.org/3/library/unittest.mock.html#where-to-patch
    """
    ## Instantiate the class
    connector = VPNConnector("config_file", "auth_file")
    temp_dir = tempfile.gettempdir()

    ## Instantiate mocks and define properties 
    # The temp file used as log
    mock_temp_file_instance = mock_temp_file.return_value
    mock_temp_file_instance.file_name = os.path.join(temp_dir, "openvpn.log")
    # The Popen context manager that calls `cmd`
    process = mock_popen.return_value.__enter__.return_value 
    process.returncode = 0
    process.communicate.return_value = (b"", b"") # this fixes the error "not enough values to unpack"
    process.poll.return_value = None # this silences the CalledProcessError that shows up otherwise

    ## Main call
    connector.start_vpn(pwd="my_password") # Popen.__enter__ is also called when the log file is opened/created

    ## Assert 
    mock_get_ip.assert_called_once() # in the VPNConnector.__init__() call
    mock_popen.assert_called_once_with(connect_command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    process.communicate.assert_called_once_with("my_password".encode())

    ## Reset all mocks, and check with proc_id argument
    process.reset_mock()
    mock_get_ip.reset_mock()
    mock_popen.reset_mock()
    connect_command.extend(["--writepid", "file.txt"])
    connector.start_vpn(pwd="my_password", proc_id="file.txt")
    mock_popen.assert_called_once_with(connect_command, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    process.communicate.assert_called_once_with("my_password".encode())


# NOTE: raise_ovpn_exceptions is imported in VPNConnector. https://docs.python.org/3/library/unittest.mock.html#where-to-patch
@mock.patch("os.path.exists")
@mock.patch("sirup.VPNConnector.sudo_read_file")
@mock.patch("sirup.VPNConnector.raise_ovpn_exceptions") 
@mock.patch("sirup.VPNConnector.TemporaryFileWithRootPermission")
@mock.patch("subprocess.Popen")
def test_start_vpn_fails(mock_popen, mock_temp_file, mock_raise_exc, mock_read_file, mock_path_exists):
    """Mock a failing connection, test that raise_ovpn_exceptions and sudo_read_file are called."""
    ## Instantiate the class
    connector = VPNConnector("config_file", "auth_file", track_ip=False)
    temp_dir = tempfile.gettempdir()

    ## Instantiate mocks and define properties 
    # The temp file used as log
    mock_temp_file_instance = mock_temp_file.return_value
    mock_temp_file_instance.file_name = os.path.join(temp_dir, "openvpn.log")
    # The Popen context manager that calls `cmd`
    process = mock_popen.return_value.__enter__.return_value 
    process.returncode = 1
    process.communicate.return_value = (b"connection failed", b"error") # this fixes the error "not enough values to unpack"
    process.poll.return_value = None # this silences the CalledProcessError that shows up otherwise
    # os.path.exists
    mock_path_exists.return_value = True

    connector.start_vpn(pwd="my_password") 
    mock_raise_exc.assert_called_once()
    mock_read_file.assert_called_once_with(file=mock_temp_file_instance.file_name, pwd="my_password")


@mock.patch("sirup.VPNConnector.get_ip")
@mock.patch("sirup.VPNConnector.sudo_read_file")
@mock.patch.object(VPNConnector, "start_vpn")
@mock.patch("sirup.VPNConnector.check_connection")
@mock.patch("sirup.VPNConnector.TemporaryFileWithRootPermission")
def test_connect(mock_temp_file, mock_check_connection, mock_start_vpn, mock_read_file, mock_get_ip):
    "Test sequential execution of functions"
    ## Instantiate the class
    mock_get_ip.return_value = "old_ip"
    connector = VPNConnector("config_file", "auth_file", track_ip=True)
    assert connector.base_ip == "old_ip"
    mock_get_ip.reset_mock()
    temp_dir = tempfile.gettempdir()

    ## Instantiate mocks and define properties 
    # The temp file used as log
    mock_temp_file_instance = mock_temp_file.return_value
    mock_temp_file_instance.file_name = os.path.join(temp_dir, "openvpn.log")

    ## Main call
    connector.log_file = "my_log" # necessary for check_connection. Could this bee assigned to connector as a side effect 
    mock_check_connection.return_value = True
    mock_get_ip.return_value = "new_ip"
    connector.connect(pwd="my_password") # Popen.__enter__ is also called when the log file is opened/created

    ## Assert
    mock_start_vpn.assert_called_once()
    mock_check_connection.assert_called_once()
    mock_read_file.assert_called_once()
    mock_get_ip.assert_called_once()
    assert connector.current_ip == "new_ip"

    ## Test connection error
    mock_get_ip.side_effect = requests.ConnectionError
    with pytest.raises(requests.ConnectionError, match="Cannot get IP address"):
        connector.connect(pwd="my_password")

    # ## When connection fails: raise TimeOut error 
    mock_check_connection.return_value = False 
    mock_start_vpn.reset_mock()
    with pytest.raises(TimeoutError, match="Could not connect"):
        connector.connect(pwd="my_password")
    mock_start_vpn.assert_called_once()


@mock.patch("sirup.VPNConnector.get_vpn_pids")
@mock.patch("sirup.VPNConnector.TemporaryFileWithRootPermission")
@mock.patch("time.sleep")
@mock.patch("sirup.VPNConnector.get_ip") 
@mock.patch("subprocess.run")
def test_disconnect(mock_run, mock_get_ip, mock_sleep, mock_temp_file, mock_get_pids):
    mock_get_ip.return_value = "base_ip" 
    connector = VPNConnector("config_file", "auth_file")

    mock_get_ip.assert_called_once_with()
    mock_get_ip.reset_mock()

    # Set properties of the connector instance 
    temp_dir = tempfile.gettempdir()
    mock_temp_file_instance = mock_temp_file.return_value
    mock_temp_file_instance.file_name = os.path.join(temp_dir, "openvpn.log")

    connector._vpn_process_id = str(1234) #pylint: disable=protected-access
    connector.log_file = mock_temp_file_instance

    mock_get_pids.return_value = ["1234", "5992"]
    mock_get_ip.return_value = "base_ip"

    # Call
    connector.disconnect("my_password")

    # Assert 
    expected_cmd = ["sudo", "-S", "kill", "1234"]
    mock_run.assert_called_once_with(expected_cmd, input="my_password".encode(), check=True)
    mock_get_ip.assert_called_once_with()
    mock_sleep.assert_called_once_with(5)

    # Test when new IP address is not the same as the base ip 
    mock_get_ip.return_value = "not_base_ip"
    with pytest.raises(RuntimeWarning, match="Expected to go back to base IP address"):
        connector.disconnect("my_password")


def test_repr():
    connector = VPNConnector("config_file", "auth_file", track_ip=False)
    repr_result = repr(connector) 
    repr_expected = "VPNConnector('config_file', 'auth_file', track_ip=False)"
    assert repr_result == repr_expected, "prints wrong repr"