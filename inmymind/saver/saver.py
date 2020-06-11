import json

from . import logger, config

from .save_methods import handle_user, handle_snapshot


class Saver:
    """
    Saves data to the DB.
    :arg: restapi_url - the url of the RESTful API that wrapping the db service.
    NOTE: the url is the API's url and not the DB's url.
    """

    def __init__(self, restapi_url=config['api']['default_url']):
        self.restapi_url = restapi_url

    def save(self, result_name, data):
        #### NOTE: here to fulfill the project requirements, but is not practically in use in the code, the save_all_types is been used ####
        self.save_all_types('snapshot', data=data)

    def save_all_types(self, data_type: str, data):
        """
        Gets the data and to be sent to the api, and the type ('user' or 'snapshot')
        """
        try:
            if data_type == 'snapshot':
                handle_snapshot(data, self.restapi_url)
            elif data_type == 'user':
                logger.debug(f'dedicated a user! {json.loads(data)}')
                handle_user(data, self.restapi_url)
            else:
                raise TypeError(f"data type {data_type} is not supported, only 'snapshot' and 'user' are ok")
        except Exception as e:
            logger.warning(f'please check this data again: {str(e)}')
