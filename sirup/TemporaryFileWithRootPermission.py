import os
import subprocess
import tempfile


# adapted from https://stackoverflow.com/questions/23212435/permission-denied-to-write-to-my-temporary-file

class TemporaryFileWithRootPermission:
    """Temporary file that requires root permission.
    The purpose of this class is to handle files that the `openvpn` CLI writes to.
    Because the CLI works with root permission, the files it writes to also require root permission,
    and can for instance only be removed with root permission.
    
    When used as a context manager, a random file name in a temporary directory 
    is generated, which can then be used like normal file. Upon `__exit__`, the file is deleted. 

    When used without a context manager, the `create_path` method needs to be called to generate 
    the file name. The filename can be passed on to other tasks, like the openvpn subprocesses.
    To remove the file one needs to call `self.remove`. 

    Args:
        passsword (str): Password for the user with root access. 
        suffix (str, optional): suffix to be appended after the random file name. 
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
    
    def create_path(self, file_name):
        """Create the full path to a new file in the temp directory. 
        Remove any existing file with the same name.

        Args:
            file_name (str): name of the file in the temp directory.
        """
        if self._suffix is not None:
            file_name = file_name + self._suffix
        self.file_name = os.path.join(tempfile.gettempdir(), file_name)
        if os.path.exists(self.file_name): 
            self.remove()
    
    def remove(self):
        "Remove the file."
        cmd = ["sudo", "-S", "rm", "-rf", self.file_name]
        subprocess.run(cmd, input=self._pwd.encode(), check=True)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if os.path.exists(self.file_name):
            with open(self.file_name, "rb"): # make sure file is closed properly
                pass

        cmd = ["sudo", "-S", "rm", "-rf", self.file_name]
        subprocess.run(cmd, input=self._pwd.encode(), check=True)

        assert not os.path.exists(self.file_name), "temporary file not deleted"