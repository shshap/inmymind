import click

from .server import run_server


@click.group()
def main():
    pass


@main.command(name='run-server')
@click.option('-h', '--host', default='127.0.0.1', help='IP of the server')
@click.option('-p', '--port', default=8000, help='PORT of the server')
@click.argument('url', default='rabbitmq://localhost:5672/')
def run_click(host, port, url):
    """ URL: mq url in format: `scheme://username:password@host:port/`"""
    return run_server(host, port, None, url)


main()
