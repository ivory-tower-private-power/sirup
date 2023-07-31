import os
import subprocess
import tempfile


# adapted from https://stackoverflow.com/questions/23212435/permission-denied-to-write-to-my-temporary-file

class TemporaryFileWithRootPermission:
    """Context manager with temporary file name that is deleted on __exit__,
    which requires root permission.
    """
    def __init__(self, password, suffix=None):
        self._pwd = password
        self._suffix = suffix

    def __enter__(self):
        # Generate a random temporary file name
        file_name = os.path.join(tempfile.gettempdir(), os.urandom(8).hex())
        if self._suffix is not None:
            file_name = file_name + self._suffix
        self.file_name = file_name
        return self.file_name
    
    def create(self, file_name):
        """Creates a file path to a new file in the temp folder. 
        Remove any existing file with the same name"""
        if self._suffix is not None:
            file_name = file_name + self._suffix
        self.file_name = os.path.join(tempfile.gettempdir(), file_name)
        if os.path.exists(self.file_name): # TODO: this logic is not good for testing. depending on outcome of previous tests
            # (when one fails before removing the temp file), then os.path.exists() is true, otherwise not. better to 
            # always create the file? 
            self.remove()
    
    def remove(self):
        cmd = ["sudo", "-S", "rm", "-rf", self.file_name]
        subprocess.run(cmd, input=self._pwd.encode(), check=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.file_name):
            with open(self.file_name, "rb"): # make sure file is closed properly
                pass

        cmd = ["sudo", "-S", "rm", "-rf", self.file_name]
        subprocess.run(cmd, input=self._pwd.encode(), check=True)

        assert not os.path.exists(self.file_name), "temporary file not deleted"