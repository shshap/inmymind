import inspect
from functools import partial
from pathlib import Path

from . import logger
from .drivers import DriverFile
from .readers import reader_mind
from .writers import writer_http

drivers = {'file': DriverFile}
readers = {'mind': reader_mind}
writers = {'http': writer_http}


class Manager:
    """The main class of the client. Abstract Handler of the connections between the Driver, the Reader and the
    Writer. Is not aware to to protocol.
    :param:driver - configurations of the driver, as dict. must include 'path'
    :param:writer - configurations of the writer, as dict
    """

    def __init__(self, driver, writer):
        path = driver['path']
        try:
            driver_class = drivers.get(driver['protocol'], None)
            if driver_class is None:
                raise ValueError(f"Do not have driver for {driver['protocol']} protocol")
            self.driver = driver_class(path, driver)

            sample_format = Path(path).suffixes[-2].replace('.', '')
            self.reader = readers.get(sample_format, None)
            if self.reader is None:
                raise ValueError(f'do not know to handle {sample_format} sample format')
            if inspect.isgeneratorfunction(self.reader):
                # going to give the reader the arguments, without cause the first read.
                # generator function can be given an argument that won't cause the first yield
                self.reader = self.reader(self.driver)
            else:
                # functools.partial is the solution for regular function
                self.reader = partial(self.driver)

            self.writer = writers.get(writer['protocol'], None)
            if self.writer is None:
                raise ValueError(f"Do not have writer for {writer['protocol']} protocol")
            self.writer = partial(self.writer, writer)
        except Exception as error:
            self.stop()
            raise Exception(f'initialize manager failed: {str(error)}')
        self.reader_type = type(self.reader).__name__
        self.sample = None  # fd
        self.items_counter = 0

    def run(self):
        logger.debug('in run')
        try:
            while True:
                ret = self._read_next_item()
                if ret == 0:
                    continue
                if ret == 1:
                    logger.info('client is done with success')
                    self.stop()
                    return 0
                if ret == 2:
                    logger.warning(f'error occurred while handling item number {self.items_counter}')
        except (Exception, KeyboardInterrupt) as error:
            logger.warning(str(error))
            logger.info('closing client')
            self.stop()
            return 1

    def _read_next_item(self):
        logger.debug('in read_next_item')
        item = next(self.reader) if self.reader_type == 'generator' else self.reader()
        if item is None:
            return 1
        self.items_counter += 1
        return self.writer(item)

    def stop(self):
        if hasattr(self, 'driver'):
            self.driver.close()


def upload_sample(host='127.0.0.1', port=8000, path=''):
    """
    Used if the client uploads the data by http protocol.
    :return: 0 on success, 1 on failure
    """

    path = str(Path(path).resolve())
    manager = Manager(driver={'protocol': 'file', 'path': path},
                      writer={'protocol': 'http', 'host': host, 'port': port})
    try:
        return manager.run()
    except (Exception, KeyboardInterrupt) as error:
        logger.warning(str(error))
        logger.info('closing client')
        manager.stop()
        return 1
