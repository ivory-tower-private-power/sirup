
# How to use the `sirup` package to manage your IP address in python

When scraping data from the internet, it can be handy to use an IP address that is different from your real IP address. The `sirup` package in python allows you to do this in a flexible way through a VPN service.

**Note**
When using IP rotationg for webscraping, it is important to respect the law and not overload target website. This means, for instance, moderating the number of requests made to a website in a given time. 

**Note**
The package works only on Linux at the moment.


## What you need 

### 1. `openvpn`

[OpenVPN](https://en.wikipedia.org/wiki/OpenVPN) is a system that allows you to create secure VPN connections. You can install it by following [these instructions](https://community.openvpn.net/openvpn/wiki/OpenvpnSoftwareRepos).


### 2. Root access to your computer

Because internet connections are an important security concern, `OpenVPN` requires root access -- this is the equivalent to administrator rights on a windows computer. If you have root access, you can for instance run the following command on your terminal:

```bash
sudo ls -lh # will ask you for your root password
``` 


## Installing and setting up `sirup`

You can install `sirup` as follows:

```python
python -m pip install sirup
```

To use the package and change your IP address, you need to connect to a VPN server, and for this, you need an account with a VPN service provider that offers OpenVPN configuration files for your account. At the time of writing, examples of such services are ProtonVPN and Surfshark. We will use ProtonVPN in this tutorial.

After creating an account, we need to download two sets of files. 

First, we download credentials that identify our Proton account when using OpenVPN. On the ProtonVPN website, click on "Account" and then you see something like this:

![file](./screenshot-proton-username-clean.png)

Copy and paste the username and the password into a `txt` file that looks like this:

```txt
username
password
```

Then, save the file as "proton_credentials.txt". Remember where it is stored -- we will need it later.

Second, we need configuration files. The files have the file ending `.ovpn` and allow OpenVPN to connect to a server from the VPN service provider. In ProtonVPN, go to the "Download" section of your account. Select the options as follows:


![file](./screenshot-proton-ovpn-files.png)

And download the configuration file(s) you want to use. Store the downloaded files on your computer, and remember the location. If you want to rotate your IP address across many servers, you need many configuration files, and it is best you store them together in a separate directory.

Now we are ready!


## Using `sirup`

We start by defining the relevant file paths. When you execute the code below, you will be asked to enter the root password, which is necessary to make the connection.


```python
import getpass
auth_file = "proton_credentials.txt"
pwd = getpass.getpass("Please enter your root password:")
```

## Changing the IP address with `sirup`


Now we can use the `VPNConnector` to change our IP address. We will use the `"my_config_file.ovpn"` configuration file.

```python
from sirup.VPNConnector import VPNConnector

config_file = "my_config_file.ovpn"
```

The code below first connects to the server associated with `"my_config_file.ovpn"` and then disconnects again. 

```python
connector = VPNConnector(auth_file, config_file)

# Let's see the current IP address when no VPN tunnel is active
print(connector.base_ip) 

connector.connect(pwd=pwd)

# Now the IP address should differ
print(connector.current_ip)

connector.disconnect(pwd=pwd)

# Now current_ip should be the same as base_ip above
print(connector.current_ip) 

```

## Rotating the IP address with `sirup`

Instead of connecting to a single server, we can also rotate across many different servers -- which means we rotate our IP address across a set of potential addresses.

To do this, we store multiple `.ovpn` configuration files in a directory, say "/path/to/config/files/".

```python
config_path = "/path/to/config/files/" 
```

The following code connects to two different servers before disconnecting again:

```python
from sirup.IPRotator import IPRotator

rotator = IPRotator(auth_file=my_auth_file, config_location=config_path, seed=seed) # this will ask for the root password

print(rotator.connector.base_ip) 

rotator.connect()
print(rotator.connector.current_ip) 

rotator.rotate()
print(rotator.connector.current_ip) 

rotator.disconnect()

print(rotator.connector.current_ip) 

```

That's it! You're now ready to manage your IP address with python! You can find the complete documentation of the package under [https://sirup-vpn.readthedocs.io/](https://sirup-vpn.readthedocs.io/en/latest/getting_started.html).