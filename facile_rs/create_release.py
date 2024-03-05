#!/usr/bin/env python
import argparse
import logging

import requests

from .utils import settings

logger = logging.getLogger(__file__)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('assets', nargs='*', default=[],
                        help='Assets to be included in the release.')
    parser.add_argument('--release-tag', dest='release_tag',
                        help='Tag for the release.')
    parser.add_argument('--release-description', dest='release_description',
                        help='Description for the release.')
    parser.add_argument('--release-api-url', dest='release_api_url',
                        help='API URL to create the release.')
    parser.add_argument('--private-token', dest='private_token',
                        help='The PRIVATE_TOKEN to be used with the GitLab API.')
    parser.add_argument('--dry', action='store_true',
                        help='Perform a dry run, do not perfrom the final request.')
    parser.add_argument('--log-level', dest='log_level',
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-file', dest='log_file',
                        help='Path to the log file')

    settings.setup(parser, validate=[
        'RELEASE_TAG',
        'RELEASE_API_URL',
        'PRIVATE_TOKEN'
    ])

    assets = []
    for asset_location in settings.ASSETS:
        assets.append({
            'name': asset_location.split('/')[-1],
            'url': asset_location
        })

    release_json = {
        'name': settings.RELEASE_TAG,
        'tag_name': settings.RELEASE_TAG
    }

    if settings.RELEASE_DESCRIPTION:
        release_json['description'] = settings.RELEASE_DESCRIPTION.strip()

    if assets:
        release_json['assets'] = {
            'links': assets
        }

    if settings.DRY:
        print(release_json)
    else:
        logging.debug('release_json = %s', release_json)
        response = requests.post(settings.RELEASE_API_URL, headers={
            'Content-Type': 'application/json',
            'Private-Token': settings.PRIVATE_TOKEN
        }, json=release_json)
        response.raise_for_status()


if __name__ == "__main__":
    main()