#!/usr/bin/env python
import argparse
from datetime import date
from pathlib import Path

from .utils import settings
from .utils.http import fetch_dict, fetch_list
from .utils.metadata import DataciteMetadata


def main():
    parser = argparse.ArgumentParser()

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
    parser.add_argument('--datacite-path', dest='datacite_path',
                        help='Path to the DataCite XML output file')
    parser.add_argument('--log-level', dest='log_level',
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-file', dest='log_file',
                        help='Path to the log file')

    settings.setup(parser, validate=[
        'METADATA_LOCATIONS'
    ])

    metadata = fetch_dict(settings.METADATA_LOCATIONS)
    creators = fetch_list(settings.CREATORS_LOCATIONS)
    contributors = fetch_list(settings.CONTRIBUTORS_LOCATIONS)

    metadata['creators'] = sorted(creators, key=lambda item: item.get('family_name') or item.get('name'))
    metadata['contributors'] = sorted(contributors, key=lambda item: item.get('family_name') or item.get('name'))
    metadata['issued'] = settings.ISSUED or date.today().strftime('%Y-%m-%d')
    metadata['version'] = settings.VERSION

    datacite_renderer = DataciteMetadata(metadata)
    datacite_xml = datacite_renderer.to_xml()

    if settings.DATACITE_PATH:
        Path(settings.DATACITE_PATH).expanduser().write_text(datacite_xml)
    else:
        print(datacite_xml)


if __name__ == "__main__":
    main()
