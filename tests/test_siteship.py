#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for `siteship-cli` package."""

import pytest
from click.testing import CliRunner

from siteship import cli


@pytest.fixture
def response():
    import requests
    return requests.get('https://siteship-cli.readthedocs.io/en/latest/')


def test_content(response):
    from bs4 import BeautifulSoup
    assert 'Welcome to Siteship’s documentation!' in BeautifulSoup(response.content, 'html.parser').title.string


def test_command_line_interface():
    """Test the Siteship CLI."""
    runner = CliRunner()
    result = runner.invoke(cli.siteship, input='../docs/')
    assert result.exit_code == 0
    assert 'siteship.sh - Static websites deployments made simple' in result.output

    help_result = runner.invoke(cli.siteship, ['--help'])
    assert help_result.exit_code == 0
    assert '--help  Show this message and exit.' in help_result.output
