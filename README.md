# sirup: simple IP rotation using python

A wrapper around the openvpn CLI to rotate the IP address in python programs. 

## Badges

(Customize these badges with your own links, and check https://shields.io/ or https://badgen.net/ to see which other badges are available.)

| fair-software.eu recommendations | |
| :-- | :--  |
| (1/5) code repository              | [![github repo badge](https://img.shields.io/badge/github-repo-000.svg?logo=github&labelColor=gray&color=blue)](git@github.com:ivory-tower-private-power/sirup) |
| (2/5) license                      | [![github license badge](https://img.shields.io/github/license/ivory-tower-private-power/sirup)](git@github.com:ivory-tower-private-power/sirup) |
| (3/5) community registry           | [![RSD](https://img.shields.io/badge/rsd-sirup-00a3e3.svg)](https://www.research-software.nl/software/sirup) [![workflow pypi badge](https://img.shields.io/pypi/v/sirup.svg?colorB=blue)](https://pypi.python.org/project/sirup/) |
| (4/5) citation                     | [![DOI](https://zenodo.org/badge/DOI/<replace-with-created-DOI>.svg)](https://doi.org/<replace-with-created-DOI>) |
| (5/5) checklist                    | [![workflow cii badge](https://bestpractices.coreinfrastructure.org/projects/<replace-with-created-project-identifier>/badge)](https://bestpractices.coreinfrastructure.org/projects/<replace-with-created-project-identifier>) |
| howfairis                          | [![fair-software badge](https://img.shields.io/badge/fair--software.eu-%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8F%20%20%E2%97%8B-yellow)](https://fair-software.eu) |
| **Other best practices**           | &nbsp; |
| Static analysis                    | [![workflow scq badge](https://sonarcloud.io/api/project_badges/measure?project=ivory-tower-private-power_sirup&metric=alert_status)](https://sonarcloud.io/dashboard?id=ivory-tower-private-power_sirup) |
| Coverage                           | [![workflow scc badge](https://sonarcloud.io/api/project_badges/measure?project=ivory-tower-private-power_sirup&metric=coverage)](https://sonarcloud.io/dashboard?id=ivory-tower-private-power_sirup) |
| Documentation                      | [![Documentation Status](https://readthedocs.org/projects/sirup/badge/?version=latest)](https://sirup.readthedocs.io/en/latest/?badge=latest) |
| **GitHub Actions**                 | &nbsp; |
| Build                              | [![build](git@github.com:ivory-tower-private-power/sirup/actions/workflows/build.yml/badge.svg)](git@github.com:ivory-tower-private-power/sirup/actions/workflows/build.yml) |
| Citation data consistency               | [![cffconvert](git@github.com:ivory-tower-private-power/sirup/actions/workflows/cffconvert.yml/badge.svg)](git@github.com:ivory-tower-private-power/sirup/actions/workflows/cffconvert.yml) |
| SonarCloud                         | [![sonarcloud](git@github.com:ivory-tower-private-power/sirup/actions/workflows/sonarcloud.yml/badge.svg)](git@github.com:ivory-tower-private-power/sirup/actions/workflows/sonarcloud.yml) |
| MarkDown link checker              | [![markdown-link-check](git@github.com:ivory-tower-private-power/sirup/actions/workflows/markdown-link-check.yml/badge.svg)](git@github.com:ivory-tower-private-power/sirup/actions/workflows/markdown-link-check.yml) |

## How to use sirup

Simple IP rotation using python.

## Requirements
- An account with a VPN service that supports openvpn (for instance ProtonVPN or surfshark)
- A linux OS and superuser rights

The project setup is documented in [project_setup.md](project_setup.md). Feel free to remove this document (and/or the link to this document) if you don't need it.

## Installation

To install sirup from GitHub repository, do:

```console
git clone git@github.com:ivory-tower-private-power/sirup.git
cd sirup
python -m pip install .
```

## Documentation

Include a link to your project's full documentation here.

## Contributing

If you want to contribute to the development of sirup,
have a look at the [contribution guidelines](CONTRIBUTING.md).

## Credits

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [NLeSC/python-template](https://github.com/NLeSC/python-template).
