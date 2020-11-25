import logging
import os
from pathlib import Path

from dotenv import load_dotenv


class Settings(object):

    _shared_state = {}

    DEFAULTS = {
        'LOG_LEVEL': 'WARN',
        'DRY': False
    }

    def __init__(self):
        self.__dict__ = self._shared_state

    def __str__(self):
        return str(vars(self))

    def setup(self, parser, validate=[]):
        # setup env from .env file
        load_dotenv(Path().cwd() / '.env')

        # get the args from the parser
        args = parser.parse_args()

        # combine settings from args and os.environ
        args_dict = vars(args)
        for key, value in args_dict.items():
            attr = key.upper()

            if value not in [None, []]:
                attr_value = value
            elif os.environ.get(attr):
                if isinstance(value, list):
                    attr_value = os.environ.get(attr).split()
                else:
                    attr_value = os.environ.get(attr)
            else:
                if isinstance(value, list):
                    attr_value = self.DEFAULTS.get(attr, [])
                else:
                    attr_value = self.DEFAULTS.get(attr)

            setattr(self, attr, attr_value)

        # setup logs
        self.LOG_LEVEL = self.LOG_LEVEL.upper()
        self.LOG_FILE = Path(self.LOG_FILE).expanduser().as_posix() if self.LOG_FILE else None
        logging.basicConfig(level=self.LOG_LEVEL, filename=self.LOG_FILE,
                            format='[%(asctime)s] %(levelname)s %(name)s: %(message)s')

        errors = []
        for key in validate:
            if getattr(self, key) is None:
                errors.append(key)

        if len(errors) == 1:
            parser.error('{} is missing.'.format(errors[0]))
        elif len(errors) >= 1:
            parser.error('{} are missing.'.format(', '.join(errors)))


settings = Settings()
