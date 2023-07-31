import os
import tempfile
from unittest import mock
from sirup.TemporaryFileWithRootPermission import TemporaryFileWithRootPermission


def test_instantiated_correctly():
    instance = TemporaryFileWithRootPermission("my_password", ".txt")
    assert instance._pwd == "my_password", "_pwd wrongly instantiated"#pylint: disable=protected-access
    assert instance._suffix == ".txt", "_suffix wrongly instantiated."#pylint: disable=protected-access
    new_instance = TemporaryFileWithRootPermission("my_password")
    assert new_instance._suffix is None#pylint: disable=protected-access


def test_create_nonexisting_file():
    instance = TemporaryFileWithRootPermission("my_password", ".txt")
    instance.create("my_file") 
    expected = os.path.join(tempfile.gettempdir(), "my_file" + ".txt")
    assert instance.file_name == expected, "create does not give correct file_name attribute."

@mock.patch("sirup.TemporaryFileWithRootPermission.TemporaryFileWithRootPermission.remove")
@mock.patch("os.path.exists")
def test_create_existing_file(mock_exists, mock_remove):
    instance = TemporaryFileWithRootPermission("my_password", ".txt")
    mock_exists.return_value = True 
    instance.create("my_file")
    expected_full_file_name = os.path.join(tempfile.gettempdir(), "my_file.txt")
    mock_exists.assert_called_once_with(expected_full_file_name)
    mock_remove.assert_called_once_with()


@mock.patch("subprocess.run")
def test_remove(mock_run):
    instance = TemporaryFileWithRootPermission("my_password", ".txt")
    instance.file_name = "/path/to/file.txt"
    instance.remove()
    expected_cmd = ["sudo", "-S", "rm", "-rf", "/path/to/file.txt"]
    mock_run.assert_called_once_with(expected_cmd, input="my_password".encode(), check=True)

@mock.patch("subprocess.run")
@mock.patch("os.urandom") # mock b/c of randomness
def test_context_manager(mock_urandom, mock_run):
    file_name_with_suffix = b'k\xa3K\xa3'.hex() + ".txt"   
    expected_filename = os.path.join(tempfile.gettempdir(), file_name_with_suffix)
    mock_urandom.return_value = b'k\xa3K\xa3'
    with TemporaryFileWithRootPermission("my_password", ".txt") as temp_file:
        assert temp_file == expected_filename, "wrong temporary file name in context manager"

    mock_urandom.assert_called_once_with(8)
    expected_cmd = ["sudo", "-S", "rm", "-rf", expected_filename]
    mock_run.assert_called_once_with(expected_cmd, input="my_password".encode(), check=True)