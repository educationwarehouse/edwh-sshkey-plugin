from fabric import task
from datetime import datetime
from yaml.loader import SafeLoader
from pprint import pprint
import pathlib
import yaml
import time
import os
import subprocess
import platform

YAML_KEYS_PATH = pathlib.Path("~/.ssh/known_keys.yaml").expanduser()


def create_new_keyholder():
    with open(YAML_KEYS_PATH, "x") as new_key_holder:
        new_key_holder.close()


def create_new_yaml_file_if_not_exists():
    if not YAML_KEYS_PATH.exists():
        create_new_keyholder()


def open_new_keyholder(read: bool):
    if YAML_KEYS_PATH.exists():
        return open(YAML_KEYS_PATH, "r" if read else "w")
    else:
        create_new_keyholder()


def get_keys_from_keyholder():
    key_holder = open_new_keyholder(True)
    key_db: dict = yaml.load(key_holder, Loader=SafeLoader)

    if key_db is None:
        print(
            "functionality for generating local keys automaticly and adding them to the keyholder currently isn't supported"
        )
        print("please run create to generate a new key")
        exit(255)

    return dict(key_db.setdefault("keys"))


def get_key_count(keys, command_line_key):
    return len([key for key in keys if key in command_line_key])


def add_keys_to_remote(c, command_line_keys, all_key_information):
    for command_line_key in command_line_keys:
        if command_line_key not in all_key_information:
            break

        all_key_information_remote_items = dict(
            all_key_information[command_line_key].items()
        )

        keys = [
            name
            for name in ["sleutel", "datetime", "who@hostname", "message"]
            if name in all_key_information_remote_items
        ]

        if len(keys) == 4:
            c.run(
                f'echo "{all_key_information_remote_items["sleutel"]}" >> ~/.ssh/authorized_keys'
            )
            c.run("touch ~/.ssh/keys")
            c.run("sort -u ~/.ssh/authorized_keys > ~/.ssh/keys")
            time.sleep(1)
            c.run("cp ~/.ssh/keys ~/.ssh/authorized_keys")
            c.run("rm ~/.ssh/keys")
            print(
                f"Het is gelukt! De \033[1m{command_line_key}\033[0m key is toegevoegd."
            )


def remote_key_doesnt_exist(c, command_line_keys, all_key_information):
    # verwijder alle keys die WEL in de yaml file staan
    not_in_yaml_keys = [
        which_key
        for which_key in command_line_keys
        if which_key not in all_key_information.keys()
    ]
    print(
        f'Verkeerde \033[1m{" ".join(not_in_yaml_keys)}\033[0m key, controleer eerst of je de juiste key hebt ingevuld. Of als die wel in de YAML file staat.'
    )
    for which_key in not_in_yaml_keys:
        new_key = which_key.replace("-", " ")

        # maak de key aan die nog NIET in de yaml file stond
        if input(f"Wil je de {which_key} key aanmaken? [Y/n]: ") in ("y", "Y", ""):
            generate_message = str(
                input("Wat is het bericht dat je mee wilt geven? Deze MOET: ")
            )
            if not generate_message:
                print("Je moet een message invullen!")
                exit(1)
            key_split = new_key.split()
            generate(
                c,
                generate_message,
                owner=key_split[0],
                hostname=key_split[1],
                doel=new_key.split()[2] if len(new_key.split()) == 3 else "",
            )

            add_to_remote(c, command_line_keys)


# met irerable kan je meerdere cli keys in 1 regel meegeven.
@task(iterable=["remote_keys"])
# append key to remote is kort gezegd dat je via de YAML file de public key IN de opgegeven remote machine zet
def add_to_remote(c, keys_to_remote: list):
    """
    command-line-key is/zijn de key(s) die je toevoegd aan de remote machine.
    Je kan meerdere opgeven.
    Als er een key bij zit die NIET in de yaml file staat kan je die aanmaken door bij de input vraag 'y' mee te geven.
    LET OP: je moet dan wel een bericht mee geven, anders breekt het programma af.
    De private/public key staan in de ~/.managed_ssh_keys-{key_name}
    """
    if type(keys_to_remote) == str:
        keys_to_remote = [keys_to_remote]

    # open de yaml file zodat die kan lezen welke head_keys er al zijn
    all_key_information = dict(get_keys_from_keyholder())

    # controleert of het aantal command_line_key's wel gelijk staan aan de keys die nodig zijn, zo niet gaat die je
    # vragen in de cli of de onjuiste key wil veranderen
    key_count = get_key_count(all_key_information.keys(), keys_to_remote)

    if key_count == len(keys_to_remote):
        add_keys_to_remote(c, keys_to_remote, all_key_information)
    else:
        remote_key_doesnt_exist(c, keys_to_remote, all_key_information)


# met irerable kan je meerdere cli keys in 1 regel meegeven
@task(iterable=["keys_to_remote"])
# delete key from remote is kort gezegd dat je via de YAML file de public key UIT de opgegeven remote machine zet
def delete_remote(c, keys_to_remote):
    """
    Removes the specified SSH key(s) from the remote machine.
    :param c: Connection object
    :param command_line_key: List of keys to be removed
    """
    if type(keys_to_remote) == str:
        keys_to_remote = [keys_to_remote]

    all_key_information = get_keys_from_keyholder()

    for command_line_key in keys_to_remote:
        if command_line_key not in all_key_information:
            break

        ssh_key = dict(all_key_information[command_line_key].items())[
            "sleutel"
        ].replace("\n", "")
        c.run(f'grep -v "{ssh_key}" ~/.ssh/authorized_keys > ~/.ssh/keys')
        c.run("mv ~/.ssh/keys ~/.ssh/authorized_keys")
        print(f"Success! The {command_line_key} key has been removed.")


@task
def generate(c, message, owner="", hostname="", doel=""):
    create_new_yaml_file_if_not_exists()

    key_name = "-".join(filter(bool, [owner, hostname, doel]))
    if sum([owner != "", hostname != "", doel != ""]) < 2:
        print(
            "Please provide at least two of the following arguments: Owner, Hostname, Doel"
        )
        return

    if os.path.exists(f"~/.managed_ssh_keys-{key_name}"):
        print(f"{key_name} already exists. Key generation aborted.")
        return

    subprocess.run(
        f'ssh-keygen -t rsa -b 4096 -f ~/.ssh/.managed_ssh_keys-{key_name} -N "" -C "{message}"',
        shell=True,
    )

    with open(YAML_KEYS_PATH, "a") as f:
        yaml.dump(
            {
                "keys": {
                    key_name: {
                        "sleutel": open(
                            pathlib.Path(
                                f"~/.ssh/.managed_ssh_keys-{key_name}.pub"
                            ).expanduser()
                        ).read(),
                        "datetime": datetime.today().strftime(
                            "Datum: %Y-%m-%d Tijdstip: %H:%M:%S"
                        ),
                        "who@hostname": f"{os.getlogin()}@{platform.node()}",
                        "message": message,
                    }
                }
            },
            f,
            indent=4,
        )
    # .managed_ssh_keys-sven.edwh.nl-ubuntu.pub
    print(f"Public key saved in ~/.managed_ssh_keys-{key_name}.pub")


def get_remote_name_by_key(all_key_information: dict, sleutel: str):
    return next(
        (
            host_name
            for host_name, value in all_key_information.items()
            if sleutel in value["sleutel"]
        ),
        "Couldn't find host name!",
    )


@task
def list(c):
    # Load the keys from the YAML file
    all_key_information = get_keys_from_keyholder()

    # Get the list of authorized keys from the remote machine
    if len(c.run("ls ~/.ssh/authorized_keys", warn=True, hide=True).stdout) > 0:
        remote_keys = c.run("cat ~/.ssh/authorized_keys", hide=True).stdout
    else:
        # print("[WARNING] remote authorized_keys not found!")
        remote_keys = ""

    # Iterate through the keys and separate them into two lists
    local_keys = []
    remote_known_keys = []
    for key_data in all_key_information.values():
        if key_data["sleutel"] in remote_keys:
            remote_known_keys.append(key_data["sleutel"].replace("\n", ""))
        else:
            local_keys.append(key_data["sleutel"])

    remote_keys = remote_keys.split("\n")

    # Check for any unrecognized keys in the authorized_keys file
    if len(c.run("ls ~/.ssh/authorized_keys", warn=True, hide=True).stdout) > 0:
        unrecognized_keys = [remote_key for remote_key in remote_keys if remote_key not in remote_known_keys and remote_key != ""]
    else:
        unrecognized_keys = [remote_key for remote_key in remote_keys if remote_key != ""]

    if unrecognized_keys:
        print("\033[1mUnrecognized keys found in remote auth_keys:\033[0m")
        for index in range(len(unrecognized_keys)):
            print(f"key {index+1}")
            print(unrecognized_keys[index])
            print()
        print()

    # Display the keys in a table
    if local_keys or remote_known_keys:
        if local_keys:
            print("\033[1mLocal Keys\033[0m")
            for key in local_keys:
                print(f"\033[33m{key}\033[0m")

        if remote_known_keys:
            print("\033[1mRemote Keys\033[0m")
            for key in remote_known_keys:
                print(f"\033[33m{key}\033[0m")
    else:
        print("No keys found in key_holder.yaml")
