# edwh-demo-plugin

[![PyPI - Version](https://img.shields.io/pypi/v/edwh-demo-plugin.svg)](https://pypi.org/project/edwh-demo-plugin)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/edwh-demo-plugin.svg)](https://pypi.org/project/edwh-demo-plugin)

-----

**Table of Contents**

- [Installation](#installation)
- [License](#license)

## Installation

```console
pip install edwh-sshkey-plugin
```

## Guide
### Generating new keys:
example for ubuntu@user.nl
```console
edwh sshkey.generate --message={message} --owner=ubuntu --hostname=user --doel=nl
```

possible arguments for `ew sshkey.generate`:
- **message**: REQUIRED, message to give with the ssh-keygen
- **owner**: ubuntu if ubuntu@user.nl
- **hostname**: user if ubuntu@user.nl
- **doel**: .nl if ubuntu@user.nl

#### note:
you atleast need to give this function 2-3 parameters and a message else it will not work.

### Adding keys to remote
example for ubuntu@user.nl
```console
edwh sshkey.add-to-remote -H ubuntu@user.nl --keys_to_remote=owner-hostname-doel
```

possible arguments for `ew sshkey.add-to-remote`:
- **keys_to_remote**: all saved keys you want to add to the remote


## License
`edwh-ssh-key-plugin` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
