# Changelog

<!--next-version-placeholder-->

## v0.1.5 (2023-05-15)
### Fix
* Fix that some people get a os.getlogin() error, os.getlogin() returns the name of the user logged in on the controlling terminal of the process. Typically processes in user session (tty, X session) have a controlling terminal. Processes spawned by a service manager like init, systemd, or upstart usually do not have a controlling terminal. You have to get the user information by other means. Our documentation for os.getlogin() recommends getpass.getuser(). which is used ([`4437128`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/44371287c9a02688b1277517641222845510be13))

## v0.1.4 (2023-05-15)
### Fix
* Error messages improvements and key generation gives more info with the keys ([`e82a53a`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/e82a53a565a7cf1416b4794d10dfbf1eabd4288d))

## v0.1.3 (2023-05-15)
### Fix
* Small docs fix ([`6655f04`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/6655f045d5a773742de6b37f7df93497d05b3a71))
* Removal of debug messages ([`4ef8861`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/4ef8861d364041f11c3ec5598c40015400f7de24))
* List shadow, -remote remote because of also being able to run local, show text if running local, showing key_names during listing keys, able to list private keys, bug where keys where the "keys: " was added per generation of an key ([`2c0fabd`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/2c0fabdca2bab14ca1e206b08f967130d86ffa2b))
* Local and remote are now somewhat separated + eod ([`a040491`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/a0404917d3f6faad156e6a8b1605ca78babffa2a))

## v0.1.2 (2023-05-12)
### Fix
* Prevents an error on list of an empty key file. ([`6369365`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/6369365def512e55c7cc1eba43940d6bea840fef))

## v0.1.1 (2023-05-12)
### Fix
* Some small docs changes ([`94445e2`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/94445e2968148e18eaddd14506e8eb1c0b7bd6e9))
* Now works with the plugin architecture, some minor tweaks required in pyproject.toml ([`bd645ff`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/bd645ffadb0523291995cfd2caefeb9c45de567c))

## v0.1.0 (2023-05-12)
### Feature
* Added documentation ([`332a9ac`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/332a9ac25e677eb0c76b98929e61695ce0edbddd))

### Fix
* Small bug fixes ([`3ff5fd2`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/3ff5fd20a32142cb29f5070ad1e7c7e8b6e9fa6a))
* Fixed list moves with only being able to show local keys and not remote ([`653e7b4`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/653e7b4871abbf8877544b94090e4bf4aa9fb378))
* Add_to_remote and delete_remote fixed so they actually add and remove the keys. they did nothing previously due to me not being able to test the functions from home :/ ([`965de2e`](https://github.com/educationwarehouse/edwh-sshkey-plugin/commit/965de2e7690f90bffa15819180520d574552a1f5))
