"""
The Client's drivers handles the bringing of the data.
Every driver must be a class implemented in the following way:
- accept path and driver_conf arguments in initialization (explained in the DriverFile).
- have the following API:
        - read method that accept a size parameter.
        - close method, for example, to close the file or the connection.
"""

import gzip
from pathlib import Path

from . import logger


class DriverFile:
    """A driver that handles local files"""
    def __init__(self, path, driver_conf):
        """
        :param path: path to the file
        :param driver_conf: driver configurations if needed.
        """
        self.path = path
        file_format = Path(self.path).suffix.replace('.', '')
        if file_format == 'gz':
            self.open_func = gzip.open
        else:
            self.open_func = open
        try:
            self.sample = self.open_func(self.path, 'rb')
        except Exception as error:
            raise ValueError(f'bad path: {str(error)}')

    def read(self, size):
        logger.debug('in file read')
        return self.sample.read(size)

    def close(self):
        logger.debug('in file close')
        if self.sample is None:
            return
        self.sample.close()

