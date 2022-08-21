#!/usr/bin/env python
import argparse
from datetime import date

from .utils import settings
from .utils.metadata import CodemetaMetadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--codemeta-location', dest='codemeta_location',
                        help='Locations of the main codemeta.json JSON file')
    parser.add_argument('--prepare-tag', dest='prepare_tag',
                        help='Prepare tag for the release.')
    parser.add_argument('--log-level', dest='log_level',
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-file', dest='log_file',
                        help='Path to the log file')

    settings.setup(parser, validate=[
        'CODEMETA_LOCATION',
        'PREPARE_TAG'
    ])

    release_tag = settings.PREPARE_TAG.split('-')[-1]

    if settings.CODEMETA_LOCATION:
        codemeta = CodemetaMetadata()
        codemeta.fetch(settings.CODEMETA_LOCATION)

        if 'version' in codemeta.data:
            codemeta.data['version'] = settings.PREPARE_TAG.split('-')[-1]

        if 'dateModified' in codemeta.data:
            codemeta.data['dateModified'] = date.today().isoformat()

        codemeta.write(settings.CODEMETA_LOCATION)

    print(release_tag)


if __name__ == "__main__":
    main()
