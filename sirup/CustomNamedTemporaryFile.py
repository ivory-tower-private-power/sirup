import os
import subprocess
import tempfile
from subprocess import PIPE


# adapted from https://stackoverflow.com/questions/23212435/permission-denied-to-write-to-my-temporary-file

class CustomNamedTemporaryFile:
    """Context manager with temporary file name that is deleted on __exit__
    """
    def __init__(self, password, mode='wb', suffix=None):
        self._mode = mode
        self._suffix = suffix
        self._pwd = password

    def __enter__(self):
        # Generate a random temporary file name
        file_name = os.path.join(tempfile.gettempdir(), os.urandom(8).hex())
        if self._suffix is not None:
            file_name = file_name + self._suffix
        self.file_name = file_name
        return self.file_name

    def __exit__(self, exc_type, exc_val, exc_tb):
        with open(self.file_name, "rb"): # make sure file is closed properly
            pass

        cmd = ["sudo", "-S", "rm", "-rf", self.file_name]
        with subprocess.Popen(cmd, stdin=PIPE, text=True) as process:
            _ = process.communicate(input=self._pwd)

        assert not os.path.exists(self.file_name), "temporary file not deleted"