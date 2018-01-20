# -*- coding: utf-8 -*-

"""Console script for siteship."""

import click
import configparser
import os
import shutil
import tempfile
import requests

# Py2 / py3 support
try:
    FileNotFoundError
except NameError:
    FileNotFoundError = IOError

try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


from tinynetrc import Netrc
try:
    netrc = Netrc()
except FileNotFoundError:
    netrc = None


API_URL = 'https://siteship.sh/api/'


def render_validation_errors(response):
    for field, errors in response.json().items():
        click.echo('* {} - {}'.format(
            click.style(field, fg='red'),
            ', '.join(errors) if isinstance(errors, type([])) else errors
        ))


@click.group(invoke_without_command=True)
@click.pass_context
def siteship(ctx):
    """Console script for siteship."""
    click.echo('{} - {}'.format(
        click.style('siteship.sh', fg='green'),
        'Static websites deployments made simple\n'
    ))

    if netrc and urlparse(API_URL).hostname in netrc.hosts:
        credentials = netrc.hosts[urlparse(API_URL).hostname]
        click.echo('{}: {}'.format(
            click.style('email:', fg='green'),
            credentials[0]
        ))
        click.echo('{}: {}'.format(
            click.style('token:', fg='green'),
            '*' * len(credentials[2])
        ))
        click.echo('\n\n')
    ctx.invoke(deploy)


@siteship.command()
@click.option('--path', help='path to the static content directory')
@click.option('--domain', help='your-custom-domain.com')
@click.pass_context
def deploy(ctx, path, domain):
    # Get authentication details
    if not netrc or urlparse(API_URL).hostname not in netrc.hosts:
        ctx.invoke(login)

    config = configparser.ConfigParser()
    config.read('.siteship')

    # Read configuration from disk
    sites = config.sections()[:1]

    # TODO: Also check if domain not in configuration
    if not sites:
        if not path:
            path = click.prompt('Site content path', type=str)

        # Create a site for deployment
        r = requests.post(url='{}sites/'.format(API_URL))
        if r.status_code == requests.codes.created:
            click.echo(click.style('Site {} created.'.format(r.json()['domain']), fg='green'))

            # Write site configuration
            conf = {
                'path': path,
                'domain': r.json()['domain']
            }

            # Write configuration to disk
            with open('.siteship', 'w') as configfile:
                config[r.json()['id']] = conf
                config.write(configfile)

            # Updated sites
            sites = config.sections()[:1]

        elif str(r.status_code).startswith('4'):
            render_validation_errors(response=r)
        else:
            r.raise_for_status()

    # Upload site contents
    for site in sites:
        conf = dict(config.items(site))

        with tempfile.TemporaryDirectory() as directory:
            archive = shutil.make_archive(os.path.join(directory, 'archive'), 'zip', conf['path'])

            r = requests.post(
                url='{}deploys/'.format(API_URL),
                data={
                    'site': '{}sites/{}/'.format(API_URL, site)
                },
                files={
                    'upload': open(archive, 'rb')
                }
            )
            if r.status_code == requests.codes.created:
                click.echo(click.style('Site deployed successfully!', fg='green'))
            elif str(r.status_code).startswith('4'):
                render_validation_errors(response=r)
            else:
                r.raise_for_status()



@siteship.command()
def whoami():
    pass


@siteship.command()
def list():
    if netrc and urlparse(API_URL).hostname in netrc.hosts:
        r = requests.get('{}sites/'.format(API_URL))
        if r.status_code == requests.codes.ok:
            for site in r.json():
                click.echo('[{}] {} {}'.format(
                    site['id'],
                    click.style('*', fg='green'),
                    site['domain']
                ))
        elif str(r.status_code).startswith('4'):
            render_validation_errors(response=r)
        else:
            r.raise_for_status()
    else:
        click.echo(click.style('Please log in to list sites.', fg='red'))

@siteship.command()
@click.option('--email', prompt=True, help='Your login email')
@click.option('--password', prompt=True, hide_input=True, help='Your login password')
def register(email, password):
    r = requests.post('{}signup/'.format(API_URL), json={
        'email': email,
        'password': password
    })
    if r.status_code == requests.codes.created:
        netrc[urlparse(API_URL).hostname] = {
            'login': r.json()['email'],
            'password': r.json()['token']
        }
        netrc.save()
        click.echo(click.style('Signup completed you can now start shipping your sites!', fg='green'))
    elif str(r.status_code).startswith('4'):
        render_validation_errors(response=r)
    else:
        r.raise_for_status()


@siteship.command()
@click.option('--email', prompt=True, help='Your login email')
@click.option('--password', prompt=True, hide_input=True, help='Your login password')
def login(email, password):
    r = requests.post('{}auth/'.format(API_URL), json={
        'username': email,
        'password': password
    })
    r.raise_for_status()

    netrc[urlparse(API_URL).hostname] = {
        'login': email,
        'password': r.json()['token']
    }
    netrc.save()


@siteship.command()
def logout():
    if netrc and urlparse(API_URL).hostname in netrc.hosts:
        click.confirm('This will remove your login credentials!', abort=True)
        del netrc[urlparse(API_URL).hostname]
        netrc.save()
    else:
        click.echo(click.style('Not logged in.', fg='red'))


if __name__ == "__main__":
    siteship()
