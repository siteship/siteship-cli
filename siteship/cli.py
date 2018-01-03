# -*- coding: utf-8 -*-

"""Console script for siteship."""

import click
import configparser
import os
import netrc
import shutil
import tempfile
import time
import requests
import requests_toolbelt


API_URL = 'https://siteship.sh/api/'


@click.group()
def main(args=None):
    """Console script for siteship."""
    click.echo("Replace this message by putting your code into "
               "siteship.cli.main")
    click.echo("See click documentation at http://click.pocoo.org/")


@main.command()
@click.option('--site', help='site ID')
@click.option('--path', help='path to the static content directory')
@click.option('--domain', help='your-custom-domain.com')
def deploy(site, path, domain):
    config = configparser.ConfigParser()
    config.read('.siteship')

    # Read configuration from disk
    site = next(iter(config.sections() or []), None) if not site else site
    conf = dict(config.items(site)) if site else {}

    if path:
        conf.update({'path': path})
    if domain:
        conf.update({'domain': domain})

    # Write configuration to disk
    with open('.siteship', 'w') as configfile:
        config[site] = conf
        config.write(configfile)

    # NetRC
    print(netrc.netrc())

    with tempfile.TemporaryDirectory() as directory:
        archive = shutil.make_archive(os.path.join(directory, 'archive'), 'zip', conf['path'])
        encoder = requests_toolbelt.MultipartEncoder({
            'site': site,
            'upload': (
                '{}.zip'.format(int(time.time())),
                open(archive, 'rb'),
                'application/zip'
            ),
        })

        def progress_callback(encoder, bar):
            def callback(monitor):
                bar.update(monitor.bytes_read)
            return callback

        with click.progressbar(length=encoder.len, label='Uploading content') as bar:
            monitor = requests_toolbelt.MultipartEncoderMonitor(encoder, progress_callback(encoder, bar))
            r = requests.post(
                '{}deploys/'.format(API_URL),
                data=monitor,
                headers={
                    'Content-Type': 'multipart/form-data',
                    'Authorization': 'Token {}'.format('XXX')
                }
            )
            print(r.json())


if __name__ == "__main__":
    main()
