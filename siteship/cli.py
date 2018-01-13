# -*- coding: utf-8 -*-

"""Console script for siteship."""

import click
import configparser
import os
import shutil
import tempfile
import requests

# Py2 support
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

from tinynetrc import Netrc
try:
    netrc = Netrc()
except FileNotFoundError:
    netrc = None


API_URL = 'https://siteship.sh/api/'


@click.group()
def siteship(args=None):
    """Console script for siteship."""
    click.echo("Replace this message by putting your code into "
               "siteship.cli.main")
    click.echo("See click documentation at http://click.pocoo.org/")


@siteship.command()
@click.option('--path', help='path to the static content directory')
@click.option('--domain', help='your-custom-domain.com')
@click.pass_context
def deploy(ctx, path, domain):
    # Get authentication details
    if 'siteship.sh' not in netrc.hosts:
        ctx.invoke(login)

    config = configparser.ConfigParser()
    config.read('.siteship')

    # Read configuration from disk
    for site in config.sections()[:1]:
        conf = dict(config.items(site))

        if path:
            conf.update({'path': path})
        if domain:
            conf.update({'domain': domain})

        # Write configuration to disk
        with open('.siteship', 'w') as configfile:
            config[site] = conf
            config.write(configfile)

        with tempfile.TemporaryDirectory() as directory:
            archive = shutil.make_archive(os.path.join(directory, 'archive'), 'zip', conf['path'])

            r = requests.post('{}deploys/'.format(API_URL), data={
                'site': '{}sites/{}/'.format(API_URL, site)
            },
            files={
                'upload': open(archive, 'rb')
            },
            headers={
                'Authorization': 'Token {}'.format('')
            })
            r.raise_for_status()


@siteship.command()
def whoami():
    if netrc:
        pass
    else:
        pass


@siteship.command()
def list():
    if netrc:
        r = requests.get('{}deploys/'.format(API_URL))
        print(r.json())
    else:
        pass

@siteship.command()
@click.option('--email')
@click.option('--password')
def register(email, password):
    print('register')


@siteship.command()
@click.option('--email', prompt=True, help='Your login email')
@click.option('--password', prompt=True, hide_input=True, help='Your login password')
def login(email, password):
    r = requests.post('{}auth/'.format(API_URL), json={
        'username': email,
        'password': password
    })
    r.raise_for_status()

    netrc['siteship.sh'] = {
        'login': email,
        'password': r.json()['token']
    }
    netrc.save()


@siteship.command()
def logout():
    click.confirm('This will remove your login credentials!', abort=True)
    del netrc['siteship.sh']
    netrc.save()


if __name__ == "__main__":
    siteship()
