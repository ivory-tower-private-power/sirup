
import os
import subprocess
import time
import pytest
from sirup import utils


def test_list_of_strings_contains_two_strings():
    strings_to_check = ["message 1", "message 2"]
    list_of_strings = ["here is message 1 and here is message 2", 
                        "here is message 1 but not the other",
                        "none"]

    result = utils.list_of_strings_contains_two_strings(strings_to_check=strings_to_check, list_of_strings=list_of_strings)
    assert result, "returns False when True expected"

    list_of_strings = ["here is message 1 but not the other",
                        "none"]
    result = utils.list_of_strings_contains_two_strings(strings_to_check=strings_to_check, list_of_strings=list_of_strings)
    assert not result, "returns True when False expected"


def test_sudo_read_file_without_sudo(mocker):
    mocker.patch("subprocess.run")
    utils.sudo_read_file("myfile.txt")
    subprocess.run.assert_called_once_with(["cat", "myfile.txt"], capture_output=True, check=True)

def test_sudo_read_file_with_sudo(mocker):
    mocker.patch("subprocess.run")
    utils.sudo_read_file("myfile.txt", "my_password")
    subprocess.run.assert_called_once_with(["sudo", "cat", "myfile.txt"], input="my_password".encode(), capture_output=True, check=True)


@pytest.fixture
def file_to_read(tmp_path):
    target_output = os.path.join(tmp_path, "testfile.txt")
    with open(target_output, 'w+', encoding="utf-8") as file:
        file.writelines(["hello\n", "world\n"])
    return target_output

def test_sudo_read_file_correct_output(file_to_read):
    content = utils.sudo_read_file(file_to_read)
    assert content == ["hello", "world"], "content not read correctly"


@pytest.fixture
def log_file_with_connection(tmp_path):
    target_output = os.path.join(tmp_path, "logfile_test.txt")
    with open(target_output, 'w+', encoding="utf-8") as file:
        file.writelines(["some message\n", "another message\n", "some time and date Initialization Sequence Completed"])
    return target_output

def test_check_connection_returns_true(log_file_with_connection):
    output = utils.check_connection(log_file_with_connection, 1, None)
    assert output, "check_connection does not return True when it should"

def test_check_connection_timeout(file_to_read):
    start_time = time.time()
    output = utils.check_connection(file_to_read, 4, None)
    assert time.time() - start_time >= 4, "timeout not respected"
    assert not output, "check_connection does not return False when it should"