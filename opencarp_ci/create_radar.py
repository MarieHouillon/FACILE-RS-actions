#!/usr/bin/env python
import argparse
from datetime import date
from pathlib import Path

from .utils import settings
from .utils.http import fetch_dict, fetch_files, fetch_list
from .utils.metadata import RadarMetadata
from .utils.radar import (create_radar_dataset, fetch_radar_token,
                          upload_radar_assets)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('assets', nargs='*', default=[],
                        help='Assets to be added to the repository.')
    parser.add_argument('--metadata-location', dest='metadata_locations', action='append', default=[],
                        help='Locations of the metadata YAML files')
    parser.add_argument('--creators-location', dest='creators_locations', action='append', default=[],
                        help='Locations of the creators YAML files')
    parser.add_argument('--contributors-location', dest='contributors_locations', action='append', default=[],
                        help='Locations of the contributors YAML files')
    parser.add_argument('--version', dest='version',
                        help='Version of the resource')
    parser.add_argument('--issued', dest='issued',
                        help='Date for the Issued field and publication year (format: \'%%Y-%%m-%%d\')')
    parser.add_argument('--radar-path', dest='radar_path',
                        help='Path to the Radar directory, where the assets are collected before upload.')
    parser.add_argument('--radar-url', dest='radar_url',
                        help='URL of the RADAR service.')
    parser.add_argument('--radar-username', dest='radar_username',
                        help='Username for the RADAR service.')
    parser.add_argument('--radar-password', dest='radar_password',
                        help='Password for the RADAR service.')
    parser.add_argument('--radar-client-id', dest='radar_client_id',
                        help='Client ID for the RADAR service.')
    parser.add_argument('--radar-client-secret', dest='radar_client_secret',
                        help='Client secret for the RADAR service.')
    parser.add_argument('--radar-contract-id', dest='radar_contract_id',
                        help='Contract ID for the RADAR service.')
    parser.add_argument('--radar-workspace-id', dest='radar_workspace_id',
                        help='Workspace ID for the RADAR service.')
    parser.add_argument('--radar-redirect-url', dest='radar_redirect_url',
                        help='Redirect URL for the OAuth workflow of the RADAR service.')
    parser.add_argument('--radar-email', dest='radar_email',
                        help='Email for the RADAR metadata.')
    parser.add_argument('--radar-backlink', dest='radar_backlink',
                        help='Backlink for the RADAR metadata.')
    parser.add_argument('--dry', action='store_true',
                        help='Perform a dry run, do not upload anything.')
    parser.add_argument('--log-level', dest='log_level',
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-file', dest='log_file',
                        help='Path to the log file')

    settings.setup(parser, validate=[
        'METADATA_LOCATIONS',
        'VERSION',
        'RADAR_PATH',
        'RADAR_URL',
        'RADAR_CLIENT_ID',
        'RADAR_CLIENT_SECRET',
        'RADAR_REDIRECT_URL',
        'RADAR_USERNAME',
        'RADAR_PASSWORD',
        'RADAR_CONTRACT_ID',
        'RADAR_WORKSPACE_ID',
        'RADAR_EMAIL',
        'RADAR_BACKLINK'
    ])

    # setup the bag directory
    radar_path = Path(settings.RADAR_PATH).expanduser()
    if radar_path.exists():
        parser.error('RADAR_PATH exists.')
    radar_path.mkdir()

    # prepare radar payload
    metadata = fetch_dict(settings.METADATA_LOCATIONS)
    creators = fetch_list(settings.CREATORS_LOCATIONS)
    contributors = fetch_list(settings.CONTRIBUTORS_LOCATIONS)

    metadata['creators'] = sorted(creators, key=lambda item: item.get('family_name') or item.get('name'))
    metadata['contributors'] = sorted(contributors, key=lambda item: item.get('family_name') or item.get('name'))
    metadata['issued'] = settings.ISSUED or date.today().strftime('%Y-%m-%d')
    metadata['version'] = settings.VERSION

    # override title to include version
    metadata['title'] = '{title} ({version})'.format(**metadata)

    radar_metadata = RadarMetadata(metadata, settings.RADAR_EMAIL, settings.RADAR_BACKLINK)
    radar_json = radar_metadata.to_json()

    # collect assets
    fetch_files(settings.ASSETS, radar_path)

    if not settings.DRY:
        # obtain oauth token
        headers = fetch_radar_token(settings.RADAR_URL, settings.RADAR_CLIENT_ID, settings.RADAR_CLIENT_SECRET,
                                    settings.RADAR_REDIRECT_URL, settings.RADAR_USERNAME, settings.RADAR_PASSWORD)

        # create radar dataset
        dataset_id = create_radar_dataset(settings.RADAR_URL, settings.RADAR_WORKSPACE_ID, headers, radar_json)

        # # upload assets
        upload_radar_assets(settings.RADAR_URL, dataset_id, headers, settings.ASSETS, radar_path)


if __name__ == "__main__":
    main()
