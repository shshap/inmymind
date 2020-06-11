from pathlib import Path

import click

from . import run_parser
from .parser_service import parser_service


@click.group()
def main():
    pass


@main.command(name='parse')
@click.argument('result_name')
@click.argument('path')
def parse_click(result_name, path):
    """
    RESULT_NAME: parser name [pose|feelings|color_image|depth_image]
    PATH: path to some raw data in mind format
    """
    path = Path(path).resolve()
    with open(path, 'rb') as reader:
        data = reader.read()
    print(run_parser(result_name, data, format='mind'))


@main.command(name='run-parser')
@click.argument('result_name')
@click.argument('url')
def run_click(result_name, url):
    """
    RESULT_NAME: parser name [pose|feelings|color_image|depth_image]
    PATH: path to some raw data in mind format
    """
    parser_service(result_name, url)


main()
