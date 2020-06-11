import click

from . import upload_sample


@click.group()
def main():
    pass


@main.command(name='upload-sample')
@click.argument('path', required=1)
@click.option('--host', '-h', default='127.0.0.1', help='IP of the server')
@click.option('--port', '-p', default=8000, type=int, help='PORT of the server')
def upload_click(host, port, path):
    """PATH: path to the sample"""
    return upload_sample(host, port, path)


main()
