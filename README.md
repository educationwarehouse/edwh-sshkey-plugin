# edwh-sshkey-plugin

[![PyPI - Version](https://img.shields.io/pypi/v/edwh-demo-plugin.svg)](https://pypi.org/project/edwh-demo-plugin)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/edwh-demo-plugin.svg)](https://pypi.org/project/edwh-demo-plugin)

-----

**Table of Contents**

- [Installation](#installation)
- [Guide](#guide)
- [Generating new keys](#generating-new-keys)
- [Adding keys](#adding-keys-to-remote)
- [Removing keys](#removing-ssh-keys-from-a-remote-machine)
- [Listing Local/Remote Keys](#list-ssh-keys-from-a-remote-or-local-machine)
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
- **owner**: owner of the server you are generating a key for
- **hostname**: hostname of the server you are generating the key for
- **goal**: What is the goal to use this key for, for example: 'production' or 'testing'

#### note:
you atleast need to give this function 2-3 parameters and a message else it will not work.

### Adding keys to remote
example for ubuntu@user.nl
```console
edwh sshkey.add-to-remote -H ubuntu@user.nl --keys_to_remote=owner-hostname-goal
```

possible arguments for `ew sshkey.add-to-remote`:
- **keys_to_remote**: all saved keys you want to add to the remote

### Removing SSH keys from a remote machine:
The delete_remote function is used to remove specified SSH keys from a remote machine. 
The function takes in an iterable of keys to be removed and a Connection object.

#### usage:
```console
edwh sshkey.delete-remote -H ubuntu@user.nl --keys_to_remote=owner-hostname-doel
```

possible arguments for `ew delete_remote`:
- **keys_to_remote**: An iterable of keys to be removed from the remote machine. If a string is provided, it is converted into a list with one element.

#### note:
The function retrieves all key information from the keyholder and checks if the command line key is present in the key information. 
If it is, the function retrieves the SSH key and removes it from the authorized_keys file on the remote machine.
After successfully removing the key, the function prints a success message indicating that the specified key has been removed.

### List SSH keys from a remote or local machine:
```console
edwh sshkey.list -H ubuntu@user.nl
```

#### Note:
this list all found known and unknown keys on the local or remote server.

## License
`edwh-ssh-key-plugin` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
