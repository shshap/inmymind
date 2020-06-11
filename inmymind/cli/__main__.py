from pathlib import Path

import click
import requests


@click.group()
def main():
    pass


@main.command(name='get-users')
@click.option('-h', '--host', default='127.0.0.1', help='IP of the API server')
@click.option('-p', '--port', default=5000, help='PORT of the API server')
def get_users(host, port):
    r = requests.get(f'http://{host}:{port}/users/')
    print(r.json())


@main.command(name='get-user')
@click.argument('user_id')
@click.option('-h', '--host', default='127.0.0.1', help='IP of the API server')
@click.option('-p', '--port', default=5000, help='PORT of the API server')
def get_user(user_id, host, port):
    r = requests.get(f'http://{host}:{port}/users/{user_id}/')
    print(r.json())


@main.command(name='get-snapshots')
@click.argument('user_id')
@click.option('-h', '--host', default='127.0.0.1', help='IP of the API server')
@click.option('-p', '--port', default=5000, help='PORT of the API server')
def get_snapshots(user_id, host, port):
    r = requests.get(f'http://{host}:{port}/users/{user_id}/snapshots')
    print(r.json())


@main.command(name='get-snapshot')
@click.argument('user_id')
@click.argument('snapshot_id')
@click.option('-h', '--host', default='127.0.0.1', help='IP of the API server')
@click.option('-p', '--port', default=5000, help='PORT of the API server')
def get_snapshot(user_id, snapshot_id, host, port):
    r = requests.get(f'http://{host}:{port}/users/{user_id}/snapshots/{snapshot_id}')
    print(r.json())


@main.command(name='get-result')
@click.argument('user_id')
@click.argument('snapshot_id')
@click.argument('result_name')
@click.argument('path', required=False)
@click.option('-h', '--host', default='127.0.0.1', help='IP of the API server')
@click.option('-p', '--port', default=5000, help='PORT of the API server')
@click.option('-s', '--save', type=bool, default=False,
              help="If specified, receives a path that the result's data will be saved to")
def get_result(user_id, snapshot_id, result_name, path, host, port, save):
    r = requests.get(f'http://{host}:{port}/users/{user_id}/snapshots/{snapshot_id}/{result_name}/')
    if save:
        path = Path(path).absolute()
        with open(path, 'wb') as f:
            f.write(r.json())
    else:
        print(r.json())


main()
