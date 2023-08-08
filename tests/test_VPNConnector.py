
import os
import tempfile
from subprocess import PIPE
from unittest import mock
from sirup.VPNConnector import VPNConnector


@mock.patch("sirup.VPNConnector.TemporaryFileWithRootPermission")
@mock.patch("sirup.VPNConnector.get_ip") 
@mock.patch("subprocess.Popen")
def test_start_vpn(mock_popen, mock_get_ip, mock_temp_file):
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
    cmd_expected = ["sudo", "-S", "openvpn",
           "--config", "config_file",
           "--auth-user-pass", "auth_file",
           "--log", os.path.join(temp_dir, "openvpn.log"),
           "--daemon"]
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
    mock_popen.assert_called_once_with(cmd_expected, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    process.communicate.assert_called_once_with("my_password".encode())

    ## Reset all mocks, and check with proc_id argument
    process.reset_mock()
    mock_get_ip.reset_mock()
    mock_popen.reset_mock()
    cmd_expected.extend(["--writepid", "file.txt"])
    connector.start_vpn(pwd="my_password", proc_id="file.txt")
    mock_popen.assert_called_once_with(cmd_expected, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    process.communicate.assert_called_once_with("my_password".encode())

@mock.patch("sirup.VPNConnector.get_vpn_pids")
@mock.patch("sirup.VPNConnector.TemporaryFileWithRootPermission")
@mock.patch("time.sleep")
@mock.patch("sirup.VPNConnector.get_ip") 
@mock.patch("subprocess.run")
def test_disconnect(mock_run, mock_get_ip, mock_sleep, mock_temp_file, mock_get_pids): 
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

    # Call
    connector.disconnect("my_password")

    # Assert 
    expected_cmd = ["sudo", "-S", "kill", "1234"]
    mock_run.assert_called_once_with(expected_cmd, input="my_password".encode(), check=True)
    mock_get_ip.assert_called_once_with()
    mock_sleep.assert_called_once_with(5)
