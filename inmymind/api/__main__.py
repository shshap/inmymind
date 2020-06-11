import click

from .restapi_service import run_api_server


@click.group()
def main():
    pass


@main.command(name='run-server')
@click.option('--host', '-h', default='127.0.0.1', help='IP of the API server')
@click.option('--port', '-p', default=5000, help='PORT of the API server')
@click.option('--database', '-d', default='mongo://localhost:27017')
def run_click(host, port, database):
    """
    DATABASE_URL: url of the database that the API will wrap
    """
    run_api_server(host, port, database)


main()
