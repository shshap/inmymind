from urllib.parse import urlparse

from . import logger
from .mongo_service import MongoService
from .restapi import RestfulApi

db_services = {'mongo': MongoService}


def run_api_server(host, port, database_url):
    db = urlparse(database_url).scheme
    DB = db_services.get(db, None)
    if DB is None:
        raise ValueError(f"no available db service for {db}")
    api = RestfulApi(host, port)
    api.run(DB(database_url))
