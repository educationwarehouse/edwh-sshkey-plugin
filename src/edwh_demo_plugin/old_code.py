from fabric import task
from datetime import datetime
from tabulate import tabulate
from yaml.loader import SafeLoader
from invoke import runners
# from termcolor import colored
import pathlib
import yaml
import pprint
import time
import os
import uuid
import sys

@task
def generate_old(c, message, owner='', hostname='', doel=''):
    '''
    message: Geef een verduidelijke bericht mee aan de key die gegenareerd wordt.
    owner: Wie heeft de private key..?
    hostname: Specifieke host, bvb: productie - testomgeving - naam van de stagiar
    doel: Waarom maak je deze key aan? bvb: Sandfly, SSH
    De private/public key staan in de ~/.managed_ssh_keys-{key_name}
    '''
    # bekijk of de key_holder.yaml al bestaat, zo nee, maak die dan aan. zo ja, zorg er dan voor dat de keys
    # standaard wordt
    try:
        with open('key_holder.yaml', 'r') as stream:
            key_db: dict = yaml.load(stream, Loader=SafeLoader)
            all_key_information = key_db.setdefault('keys')
    except FileNotFoundError:
        os.popen('touch key_holder.yaml | echo "keys" > key_holder.yaml')
        all_key_information = {}
    # hierbij wordt gekeken of er wel 2/3 argumenten zijn, zo ja wordt het dan ook meteen op de goeie volgorde gezet
    how_many_arguments_in_cli = bool(owner != ''), bool(hostname != ''), bool(doel != '')
    if sum(how_many_arguments_in_cli) < 2:
        print("Je moet minimaal twee van de drie argumenten meegeven: Owner, Hostname, Doel")
        exit(1)
    key_name = []
    if bool(owner):
        key_name.append(owner)
    if bool(hostname):
        key_name.append(hostname)
    if bool(doel):
        key_name.append(doel)
    key_name = '-'.join(key_name)
    if key_name in all_key_information:
        print(f'{key_name} bestaat al, toevoegen afgebroken.')
        exit(1)
    print('De key wordt aangemaakt...')
    # met ssh-keygen wordt de key pair dus aangemaakt en wordt de public key in de yaml file gezet
    os.popen(f'ssh-keygen -t rsa -b 4096 -f ~/.managed_ssh_keys-{key_name} -N "" -C "{message}"').close()
    whoami_local_handle = os.popen('echo "$(whoami)@$(hostname)"')
    time.sleep(4)
    whoami_local = whoami_local_handle.read().replace('\n', '')
    whoami_local_handle.close()
    cat_local_public_key_handle = os.popen(f'cat ~/.managed_ssh_keys-{key_name}.pub')
    cat_local_public_key = cat_local_public_key_handle.read().replace('\n', '')
    cat_local_public_key_handle.close()
    # zo komt het dus er uit te zien in de yaml file
    sleutel_dict = {
        'keys':
            {key_name:
                {
                    'sleutel': cat_local_public_key,
                    'datetime': datetime.today().strftime("Datum: %Y-%m-%d Tijdstip: %H:%M:%S"),
                    'who@hostname': whoami_local,
                    'message': message
                }
            }
    }
    # voor de eerste keer (wanneer het script dus nog niet bestond) wordt de hoofdkey keys nog aangemaakt en anders wordt het erin toegevoegd.
    with open('key_holder.yaml', 'w') as stream:
        try:
            if key_db is not None:
                new_key_dict = sleutel_dict.pop('keys')
                all_key_information.update(new_key_dict)
                yaml.dump(key_db, stream, indent=4)
                pprint.pprint(new_key_dict)
                print(f'De private/public key staan in de ~/.managed_ssh_keys-{key_name}')
        except:
            yaml.dump(sleutel_dict, stream, indent=4)
            pprint.pprint(sleutel_dict)
            print(f'De private/public key staan in de ~/.managed_ssh_keys-{key_name}')


@task
def list_old(c):
    """
    Je krijgt een overzicht te zien van alle keys
    Als er ook al keys remote staan dan worden er twee lijstjes gemaakt: local & remote :::: remote
    Als er nog keys staan in de remote file en die niet herkent worden, krijg je de output te zien van die keys
    """
    with open('key_holder.yaml', 'r') as yaml_file:
        key_db: dict = yaml.load(yaml_file, Loader=SafeLoader)
        all_key_information = key_db.setdefault('keys')
    # ???????????????????????????????????????????????????????????????
    # ??TODO: als we yaml gebruiken waarom listen we autorized_keys??
    # ???????????????????????????????????????????????????????????????
    cat_remote_keys = c.run('cat ~/.ssh/authorized_keys', hide=True)
    cat_remote_keys = cat_remote_keys.stdout
    rows = []
    row_x = []
    row_y = []
    cat_list = []
    split_the_cat_list = '\|'
    clolumn_names = ['\033[1mlocal & remote', 'local\033[0m']
    for head_keys in all_key_information:
        # all_key_information[head_keys].items() laat de keys en values zien die in de sleutel staan
        for key, value in all_key_information[head_keys].items():
            # verwijder de datetime, who@hostname en message. zodat je alleen de sleutel te zien krijgt.
            if bool(key.find('datetime')) and bool(key.find('who@hostname')) and bool(key.find('message')) is True:
                # als de key value in de cat (remote keys file) staan:
                if value in cat_remote_keys:
                    # voeg dan die sleutel toe aan de row_x
                    row_x.append(head_keys)
                    cat_list.append(value)
                # als de key value NIET in de cat staat:
                else:
                    # voeg dan de sleutel toe aan de row_y
                    row_y.append(head_keys)
    try:
        # kijk of er nog andere keys op de remote machine staan, zo ja, geef daar dan de output van
        grep_cat_list = c.run(f'grep -v "{split_the_cat_list.join(cat_list)}" ~/.ssh/authorized_keys', hide=True)
        print('LET OP!')
        print('Er staan nog andere keys op de remote, alleen kan die niet herkend worden door het yaml file:\n')
        print(grep_cat_list.stdout)
        print()
    except:
        pass
    # dit zorgt ervoor dat de keys in de goede column komt te staan
    for bron_index in range(max(len(row_x), len(row_y))):
        rows.append([])
    for bron_index in range(max(len(row_x), len(row_y))):
        if bron_index < len(row_x):
            rows[bron_index].append(row_x[bron_index])
        if bron_index < len(row_y):
            rows[bron_index].append(row_y[bron_index])
        if len(rows[bron_index]) == 1:
            if not bool(''.join(rows[bron_index]) in row_x):
                rows[bron_index].insert(0, '')
                print(rows[bron_index][0])
    print('\033[1mDe lijst van de keys:\033[0m')
    if bool(row_x):
        print(tabulate(rows, headers=clolumn_names))
    else:
        print('Er staan nog geen keys op deze remote machine die in de yaml file staan...')
        print('\033[1mlocal\033[0m')
        for head_keys in all_key_information:
            print(head_keys)
