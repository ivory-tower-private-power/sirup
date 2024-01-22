.. _getting_started:

Getting started 
=================


Start up
-----------

`sirup` works with two important files: a file with authentication credentials (`auth_file`) for the VPN service, and one or multiple VPN configuration files (`config_file`). 
The `auth_file` contains the username and password associated with the account. For ProtonVPN, this information can be found under the `OpenVPN/IKEv2 username` in the `Account` tab of a user's profile. The data should be stored like this in the `auth_file`: 

.. code-block:: console 

    mysusername 
    mypassword


Here, `myusername` is just the string of the username itself, and `mypassword` is the associated password. Keep this file in a safe location and don't share it with others. 

The `config_file` is a `OpenVPN` configuration file. They usually end with `.ovpn` and are available from the VPN provider. Download all or a sample of the configuration files of your account and store them in a specific folder. 

.. note:: 
    Not all VPN services provide configuration files for `OpenVPN`. If you want to use `sirup`, check whether they make these files available before making an account with them.


After getting these files ready, we can use `sirup`. 

.. code-block:: python 

    import os 
    import getpass 
    import time 

    seed = 123 
    my_auth_file = "/path/to/credentials.txt" # this is the auth_file described above
    config_path = "/path/to/config/files/" # this is the path to where one or more `config_file`s are stored, as described above. 



Connecting to a single server 
-------------------------------

The :class:`sirup.VPNConnector.VPNConnector` class can be used as follows to connect to a specific server:

.. code-block:: python 

    from sirup.VPNConnector import VPNConnector

    my_config_file = os.path.join(config_path, "name-of-one-config-file.ovpn")
    pwd = getpass.getpass("Please enter your sudo password") 

    connector = VPNConnector(auth_file=my_auth_file, config_file=my_config_file)

    print(connector.base_ip) # IP address of the machine when no VPN tunnel is active.

    connector.connect(pwd=pwd)

    print(connector.current_ip) # should be different from base_ip

    time.sleep(10)
    connector.disconnect(pwd=pwd)

    print(connector.current_ip) # should be same as base_ip above



Rotating the IP address by rotating across servers 
-----------------------------------------------------

The :class:`sirup.IPRotator.IPRotator` class can be used to iteratively change the IP address. For this, it is necessary to have multiple ``config_file`` s downloaded.


.. code-block:: python 

    from sirup.IPRotator import IPRotator

    rotator = IPRotator(auth_file=my_auth_file, config_location=config_path, seed=seed) # this will ask for the sudo password

    print(rotator.connector.base_ip) # IP address of the machine when no VPN tunnel is active.

    rotator.connect()
    print(rotator.connector.current_ip) # should be different from base_ip

    rotator.rotate()
    print(rotator.connector.current_ip) # should be different from previous IP 

    rotator.disconnect()

    print(rotator.connector.current_ip) # should be same as base_ip above



Important 
---------

To make sure that the VPN tunnels work correctly and do not reveal the original IP address of the device, have a look at :ref:`correct_connection`.


