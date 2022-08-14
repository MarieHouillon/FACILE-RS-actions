import json
import logging
import shutil
from pathlib import Path
from urllib.parse import urlparse

import requests

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
        for obj in fetch_json(location):
            if obj not in data:
                data.append(obj)
    return data


def fetch_dict(locations):
    data = {}
    for location in locations:
        data.update(fetch_json(location))
    return data


def fetch_json(location):
    if urlparse(location).scheme:
        logger.debug('location = %s', location)

        response = requests.get(location)
        response.raise_for_status()
        return json.loads(response.text)
    else:
        with open(Path(location).expanduser()) as f:
            return json.load(f)
