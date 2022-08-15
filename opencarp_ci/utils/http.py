import json
import logging
import shutil
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

logger = logging.getLogger(__file__)


def fetch_files(locations, path):
    for location in locations:
        target = path / location.split('/')[-1]

        logger.debug('location = %s, target = %s', location, target)

        if urlparse(location).scheme:
            response = requests.get(location)
            response.raise_for_status()
            with open(target, 'wb') as f:
                f.write(response.content)

        else:
            shutil.copyfile(location, target)


def fetch_list(locations):
    data = []
    for location in locations:
        for obj in fetch(location):
            if obj not in data:
                data.append(obj)
    return data


def fetch_dict(locations):
    data = {}
    for location in locations:
        data.update(fetch(location))
    return data


def fetch(location):
    parsed_url = urlparse(location)
    if parsed_url.scheme:
        logger.debug('location = %s', location)

        response = requests.get(location)
        response.raise_for_status()

        if parsed_url.path.endswith('.json'):
            return json.loads(response.text)
        elif parsed_url.path.endswith('.yml') or parsed_url.path.endswith('.yaml'):
            return yaml.safe_load(response.text)
        else:
            raise RuntimeError('{} is not a JSON or YAML file.')
    else:
        path = Path(location).expanduser()
        with open(Path(location).expanduser()) as f:
            if path.suffix == '.json':
                return json.load(f)
            elif path.suffix in ['.yml', '.yaml']:
                return yaml.safe_load(f.read())
            else:
                raise RuntimeError('{} is not a JSON or YAML file.')
