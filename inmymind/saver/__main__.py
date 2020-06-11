from pathlib import Path

import click

from . import Saver
from .saver_service import saver_service


@click.group()
def main():
    pass


@main.command(name='save')
@click.argument('result_name')
@click.argument('path')
@click.option('-r', '--api', default='http://localhost:5000')
def save_click(restapi, result_name, path):
    """
    DATABASE_URL:
    RESULT_NAME: parser name [pose|feelings|color_image|depth_image]
    DATA: path to some raw data as consumed from the message queue. example: {'user_id': 21, 'username: 'Amit', '<field>': {...}, '<field>': {...}}
    """
    saver = Saver(restapi)
    with open(path, 'r') as reader:
        data = reader.read()
    saver.save(result_name, data)


@main.command(name='run-saver')
@click.argument('restapi_url')
@click.argument('mq_url')
def run_click(restapi_url, mq_url):
    """
    RESTAPI_URL: url of the RESTful api wrapping the database
    mq_url: url of the message queue the saver consuming from
    """
    saver_service(restapi_url, mq_url)


main()
