import fabric.connection
import invoke
from fabric import task
from datetime import datetime
from yaml.loader import SafeLoader
import pathlib
import yaml
import os
import subprocess
import platform
import getpass

# the path where the yaml file with the keys is stored
YAML_KEYS_PATH = pathlib.Path("~/.ssh/known_keys.yaml").expanduser()


def local_connection(c):
    return "invoke" in str(type(c))


def create_new_yaml_file_if_not_exists():
    """
    Checks if the yaml file exists, if not it will create a new one.
    """
    if not YAML_KEYS_PATH.exists():
        YAML_KEYS_PATH.touch()


def open_new_keyholder(read: bool):
    """
    To open the yaml file, this function will be called.
    """
    create_new_yaml_file_if_not_exists()
    return YAML_KEYS_PATH.open("r" if read else "w")


def get_keys_from_keyholder(gen=False) -> dict:
    """
    This function retrieves keys from a keyholder.

    The function first opens a new keyholder and loads its contents as a dictionary using the yaml library.
    If the keyholder is empty, the function prints an error message and exits with code 255.
    Otherwise, it returns a dictionary of keys from the keyholder.

    :return: A dictionary of keys from the keyholder.
    """
    # It opens the keyholder and loads its contents as a dictionary using the yaml library.
    key_holder = open_new_keyholder(True)
    key_db: dict = yaml.load(key_holder, Loader=SafeLoader)
    # This checks if the keyholder is empty. If empty -> exit with code 255
    if key_db is None:
        if gen:
            return {}

        print(
            "functionality for generating local keys automaticly and adding them to the keyholder currently isn't supported"
        )
        print("please run `ew sshkey.generate` to generate a new key")
        exit(255)

    # This returns a dictionary of keys from the keyholder.
    return dict(key_db.setdefault("keys"))


def get_key_count(keys, command_line_key):
    """
    This function takes in two arguments: a list of keys and a command line key. It returns the number of times the keys appear in the command line key.

    :param keys: A list of keys to search for in the command line key.
    :type keys: list
    :param command_line_key: The command line key to search for the keys in.
    :type command_line_key: str
    :return: The number of times the keys appear in the command line key.
    :rtype: int
    """
    # The length of the list of keys that appear in the command line key is returned.
    return len([key for key in keys if key in command_line_key])


def add_keys_to_remote(c, command_line_keys, all_key_information):
    """
    Adds SSH keys to a remote server's authorized keys file.

    :param c: An object representing a connection to the remote server.
    :type c: Connection
    :param command_line_keys: A list of keys to be added to the remote server.
    :type command_line_keys: list
    :param all_key_information: A dictionary containing information about all available keys.
    :type all_key_information: dict
    """
    # If the user enters a key that isn't in the YAML file, it will break out of the loop.
    for command_line_key in command_line_keys:
        if command_line_key not in all_key_information:
            break

        all_key_information_remote_items = all_key_information[command_line_key]

        if all(
            attr in all_key_information_remote_items
            for attr in ("key", "datetime", "who@hostname", "message")
        ):
            # It puts the keys in the authorized_keys file on the remote server.
            # So the public key is now on the remote server.
            # This means that the user can now log in to the remote server using the private key.
            c.run(
                f'echo "{all_key_information_remote_items["key"]}" >> ~/.ssh/authorized_keys'
            )
            # This is a way to check if the key is already in the authorized_keys file.
            # By making another file with all the keys and call the function 'sort -u' on it.
            # This function sorts the keys and removes duplicates.
            c.run("sort -u ~/.ssh/authorized_keys > ~/.ssh/keys")
            c.run("mv ~/.ssh/keys ~/.ssh/authorized_keys")
            print(
                f"It worked out! The \033[1m{command_line_key}\033[0m key is added to the remote server."
            )


def remote_key_doesnt_exist(c, command_line_keys, all_key_information):
    """
    This function checks if the keys provided in the command line are present in the YAML file.
    If a key is not present in the YAML file, the user is prompted to create it.

    :param c: Connection object
    :param command_line_keys: List of keys provided in the command line
    :param all_key_information: Dictionary containing all key information from the YAML file
    """
    # removing all keys that are already in the yaml file, so we can create the ones that are not in the yaml file
    # and then add them to the yaml file
    not_in_yaml_keys = [
        which_key
        for which_key in command_line_keys
        if which_key not in all_key_information.keys()
    ]
    print(
        f'Wrong \033[1m{" ".join(not_in_yaml_keys)}\033[0m key, '
        f"first check if you filled in the right key. Or if it is in the YAML file."
    )
    # Here is the '-' replaced with a space, so it can be used in the generate function.
    # The generate function requires two out of three arguments to be filled in. So that's why the key is split.
    for which_key in not_in_yaml_keys:
        if "-" not in which_key:
            print(
                f"\033[1m{which_key}\033[0m isn't a valid host-name please give it up with the format: owner-hostname-goal"
            )
            continue

        new_key = which_key.replace("-", " ")

        # Create the key that isn't in the YAML file.
        if input(f"Do you want to create {which_key}? [Y/n]: ").replace(" ", "") in (
            "y",
            "Y",
            "",
        ):
            generate_message = str(
                input("What message do you want to go with the ssh-key? REQUIRED: ")
            )
            if not generate_message:
                print("Please give up a message for the next time!")
                exit(1)
            key_split = new_key.split()

            if len(key_split) > 3:
                print(
                    f"to many arguments given in the key: {which_key} format needs to be: owner-hostname-goal"
                )
                exit(1)

            # This is to create a new key, the split is to make sure that the key is in the right format.
            generate(
                c,
                generate_message,
                owner=key_split[0],
                hostname=key_split[1],
                goal=new_key.split()[2] if len(key_split) == 3 else "",
            )
            # eventually it will add the keys that are just created
            add(c, command_line_keys)


@task(
    help={
        "keys-to-remote": "list of keys you want to add to the remote server",
    },
    iterable=["keys_to_remote"],
)
def add(c, keys_to_remote: list):
    """
    Adds the specified SSH key(s) to the remote machine. You can add multiple keys at once.

    The private/public key is located local in the ~/.managed_ssh_keys-{key_name} directory.
    You can see who has the private/public key, by looking at the YAML file.
    There is a key called 'who@hostname', that's the person who created the new ssh key.


    If there are keys that are not in the YAML file, the user is prompted to create them.
    NOTE: you must provide a message, otherwise the program will terminate.
    """
    if local_connection(c):
        if input("are you sure you want to add local keys(Y/n): ").replace(
            " ", ""
        ) not in ["Y", "y", ""]:
            print("please use `edwh -H ubuntu@user.nl sshkey.add because ")
            exit(255)
        else:
            print("Adding keys to local known_hosts")

    # If keys_to_remote is a string, convert it to a list with a single element
    if type(keys_to_remote) == str:
        keys_to_remote = [keys_to_remote]

    # check which keys are already in the YAML file
    all_key_information = get_keys_from_keyholder()

    # check if given keys exist else ask to generate them
    key_count = get_key_count(all_key_information.keys(), keys_to_remote)

    if key_count == len(keys_to_remote):
        add_keys_to_remote(c, keys_to_remote, all_key_information)
    else:
        remote_key_doesnt_exist(c, keys_to_remote, all_key_information)


@task(
    help={
        "keys_to_remote": "list of keys you want to remove from the server",
    },
    iterable=["keys_to_remote"],
)
def delete(c, keys_to_remote):
    """
    Removes the specified SSH key(s) from the remote machine. You can remove multiple keys at once.
    """
    if local_connection(c):
        if input("are you sure you want to add local keys(Y/n").replace(
            " ", ""
        ) not in ["Y", "y", ""]:
            print("please use `edwh -H ubuntu@user.nl sshkey.delete to remove remote keys ")
            exit(255)
        else:
            print("Removing local keys from known_hosts")

    # If keys_to_remote is a string, convert it to a list with a single element
    if isinstance(keys_to_remote, str):
        keys_to_remote = [keys_to_remote]

    # Get all key information from the keyholder
    all_key_information = get_keys_from_keyholder()

    # Loop through each key specified in keys_to_remote
    for command_line_key in keys_to_remote:
        # If the key is not found in all_key_information, break out of the loop
        if command_line_key not in all_key_information:
            break

        # Get the SSH key from all_key_information and remove newlines
        ssh_key = all_key_information[command_line_key]["key"].strip()
        # Remove the key from the remote server's authorized_keys file
        c.run(f'grep -v "{ssh_key}" ~/.ssh/authorized_keys > ~/.ssh/keys')
        c.run("mv ~/.ssh/keys ~/.ssh/authorized_keys")
        # Print a success message
        print(f"Success! The {command_line_key} key has been removed.")
    else:
        print("please give up keys using edwh.sshkey.delete -k [keys]")


@task(
    help={
        "message": "a message to know what the key is used for, REQUIRED",
        "owner": "owner of the server you are generating a key for",
        "hostname": "hostname of the server you are generating the key for",
        "goal": "What is the goal to use this key for, for example: 'production' or 'testing'",
    }
)
def generate(c, message, owner="", hostname="", goal=""):
    """
    This function generates a new SSH key and saves it to a yaml file. (~/.ssh/known_keys.yaml)

    You need a message and 2 out of 3 arguments to generate a new key. (owner, hostname, goal) Otherwise it will fail.

    The private and public key is located local in the ~/.managed_ssh_keys-{key_name} directory.
    You can see who has the private/public key, by looking at the YAML file.
    There is a key called 'who@hostname', that's the person who created the new ssh key.
    """
    # Get the yaml keys or create a new YAML file if it does not already exist
    keys_dict = {"keys": {}}
    current_keys = get_keys_from_keyholder(gen=True)

    # Create a key name by joining the non-empty values of owner, hostname, and goal with a hyphen
    key_name = "-".join(_ for _ in (owner, hostname, goal) if _)
    # If less than two of three from owner, hostname, and goal are provided, print an error message and return
    if "-" not in key_name:
        print(
            "Please provide at least two of the following arguments: Owner, Hostname, goal"
        )
        return

    # If a file with the specified key name already exists, print an error message and return
    if pathlib.Path(f"~/.managed_ssh_keys-{key_name}").expanduser().exists():
        print(f"{key_name} already exists. Key generation aborted.")
        return

    # Run the ssh-keygen command to generate a new SSH key
    # As type of key we use rsa, with a bit size of 4096
    # The key is saved in ~/.ssh/.managed_ssh_keys-{key_name}
    # The key has no passphrase
    # The key has given a comment with the message
    curr_time = datetime.now().strftime("Datum: %Y-%m-%d Tijdstip: %H:%M:%S")
    host = f"{getpass.getuser()}@{platform.node()}"

    subprocess.run(
        f'ssh-keygen -t rsa -b 4096 -f ~/.ssh/.managed_ssh_keys-{key_name} -N "" -C "key name: {key_name} '
        f'message: {message} who@hostname: {host} {curr_time}"',
        shell=True,
    )
    keys_dict["keys"].update(current_keys)
    keys_dict["keys"][key_name] = {
        "key": open(
            pathlib.Path(f"~/.ssh/.managed_ssh_keys-{key_name}.pub").expanduser()
        ).read(),
        "datetime": curr_time,
        "who@hostname": host,
        "message": message,
    }

    # Open the YAML_KEYS_PATH file in append mode
    with open(YAML_KEYS_PATH, "w") as f:
        # Dump the key information to the YAML file
        yaml.dump(
            keys_dict,
            f,
            indent=4,
        )
    # Print a success message
    print(f"Public key saved in ~/.managed_ssh_keys-{key_name}.pub")
    print(f"Private key saved in ~/.managed_ssh_keys-{key_name}")


def get_keys(c, private):
    if not private:
        return get_keys_from_keyholder()

    key_names = get_keys_from_keyholder()
    keys = {}
    for key_name in key_names:
        # we should only be able to find 1 key
        private_key_file = pathlib.Path(f"~/.ssh/.managed_ssh_keys-{key_name}").expanduser()

        if private_key_file is None:
            print(f"[ERROR] private key for {key_name} not found!")
            print("exiting....")
            exit(1)

            # reinact yaml file so we don't need to parse this differently
        keys[key_name] = {"key": private_key_file.read_text()}
    return keys


@task(name="list")
def list_(c, private=False):
    """
    Lists all the local or local and remote ssh_keys.
    This function lists the authorized keys on a remote machine and compares them with the keys in a local YAML file.
    It separates the keys into three categories: local keys, remote known keys, and unrecognized keys.
    """
    # Load the keys from the YAML file
    all_key_information = get_keys(c, private)

    # Get the list of authorized keys from the remote machine
    if len(c.run("ls ~/.ssh/authorized_keys", warn=True, hide=True).stdout) > 0:
        remote_keys = c.run("cat ~/.ssh/authorized_keys", hide=True).stdout
    else:
        remote_keys = ""

    # Iterate through the keys and separate them into two lists
    key_names = {}
    local_keys = []
    remote_known_keys = []
    for key in all_key_information.keys():
        key_data = all_key_information[key]
        if key_data["key"] in remote_keys:
            remote_known_keys.append(key_data["key"].replace("\n", ""))
        else:
            local_keys.append(key_data["key"])

        key_names[key_data["key"]] = key
    remote_keys = remote_keys.split("\n")

    # Check for any unrecognized keys in the authorized_keys file
    if len(c.run("ls ~/.ssh/authorized_keys", warn=True, hide=True).stdout) > 0:
        unrecognized_keys = [
            remote_key
            for remote_key in remote_keys
            if remote_key not in remote_known_keys and remote_key != ""
        ]
    else:
        unrecognized_keys = [
            remote_key for remote_key in remote_keys if remote_key != ""
        ]

    if unrecognized_keys:
        print("\033[1mUnrecognized keys found in remote auth_keys:\033[0m")
        # If there are unrecognized keys, print them with a number, so you can see how many there are.
        for index in range(len(unrecognized_keys)):
            print(f"key {index+1}")
            print(unrecognized_keys[index])
            print()
        print()

    # Display the keys in a table
    if local_keys or remote_known_keys:
        if local_keys and local_connection(c):
            print("\033[1mLocal Keys\033[0m")
            for key in local_keys:
                print(f"Key {key_names[key]}:")
                print(f"\033[33m{key}\033[0m")

        if remote_known_keys:
            print("\033[1mRemote Keys\033[0m")
            for key in remote_known_keys:
                print(f"Key {key_names[key]}:")
                print(f"\033[33m{key}\033[0m")
        elif not local_connection(c):
            print("\033[1mNo remote keys have been found!\033[0m")
    else:
        print("No keys found in key_holder.yaml")
