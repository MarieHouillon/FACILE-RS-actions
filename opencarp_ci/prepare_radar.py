#!/usr/bin/env python
import argparse
from pathlib import Path

from .utils import settings
from .utils.radar import (fetch_radar_token, create_radar_dataset, prepare_radar_dataset)
from .utils.metadata import RadarMetadata, CodemetaMetadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--codemeta-location', dest='codemeta_location',
                        help='Location of the main codemeta.json JSON file')
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
        'RADAR_URL',
        'RADAR_CLIENT_ID',
        'RADAR_CLIENT_SECRET',
        'RADAR_REDIRECT_URL',
        'RADAR_USERNAME',
        'RADAR_PASSWORD',
        'RADAR_WORKSPACE_ID',
        'RADAR_EMAIL',
        'RADAR_BACKLINK'
    ])

    if settings.CODEMETA_LOCATION:
        codemeta = CodemetaMetadata()
        codemeta.fetch(settings.CODEMETA_LOCATION)

        name = '{name} ({version}, in preparation)'.format(**codemeta.data)
    else:
        name = 'in preparation'

    radar_metadata = RadarMetadata({'name': name}, settings.RADAR_EMAIL, settings.RADAR_BACKLINK)
    radar_dict = radar_metadata.as_dict()

    if not settings.DRY:
        # obtain oauth token
        headers = fetch_radar_token(settings.RADAR_URL, settings.RADAR_CLIENT_ID, settings.RADAR_CLIENT_SECRET,
                                    settings.RADAR_REDIRECT_URL, settings.RADAR_USERNAME, settings.RADAR_PASSWORD)

        # create radar dataset
        dataset_id = create_radar_dataset(settings.RADAR_URL, settings.RADAR_WORKSPACE_ID, headers, radar_dict)
        dataset = prepare_radar_dataset(settings.RADAR_URL, dataset_id, headers)

        doi = dataset.get('descriptiveMetadata', {}).get('identifier', {}).get('value')
        doi_url = 'https://doi.org/' + doi

        if settings.CODEMETA_LOCATION:
            codemeta.data['@id'] = doi_url
            if 'identifier' in codemeta.data and isinstance(codemeta.data['identifier'], list):
                for identifier in codemeta.data['identifier']:
                    if identifier.get('propertyID') == 'DOI':
                        identifier['value'] = doi
                    elif identifier.get('propertyID') == 'RADAR':
                        identifier['value'] = dataset_id

            Path(settings.CODEMETA_LOCATION).expanduser().write_text(codemeta.to_json())
        else:
            print(dataset)


if __name__ == "__main__":
    main()
