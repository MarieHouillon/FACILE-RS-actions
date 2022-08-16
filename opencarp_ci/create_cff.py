#!/usr/bin/env python
import argparse
from datetime import date
from pathlib import Path

from .utils import settings
from .utils.metadata import CodemetaMetadata, CffMetadata


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--metadata-location', dest='metadata_locations', action='append', default=[],
                        help='Locations of the codemeta JSON files')
    parser.add_argument('--creators-location', dest='creators_locations', action='append', default=[],
                        help='Locations of codemeta JSON files for additional creators')
    parser.add_argument('--contributors-location', dest='contributors_locations', action='append', default=[],
                        help='Locations of codemeta JSON files for additional contributors')
    parser.add_argument('--version', dest='version',
                        help='Version of the resource')
    parser.add_argument('--issued', dest='issued',
                        help='Date for the Issued field and publication year (format: \'%%Y-%%m-%%d\')')
    parser.add_argument('--cff-path', dest='cff_path',
                        help='Path to the cff output file')
    parser.add_argument('--log-level', dest='log_level',
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-file', dest='log_file',
                        help='Path to the log file')

    settings.setup(parser, validate=[
        'METADATA_LOCATIONS'
    ])

    codemeta = CodemetaMetadata()
    codemeta.fetch(settings.METADATA_LOCATIONS)
    codemeta.fetch_authors(settings.CREATORS_LOCATIONS)
    codemeta.fetch_contributors(settings.CONTRIBUTORS_LOCATIONS)
    codemeta.compute_names()
    codemeta.remove_doubles()
    codemeta.sort_persons()
    codemeta.data['dateModified'] = settings.ISSUED or date.today().strftime('%Y-%m-%d')
    codemeta.data['version'] = settings.VERSION

    cff_metadata = CffMetadata(codemeta.data)
    cff_yaml = cff_metadata.to_yaml()

    if settings.CFF_PATH:
        Path(settings.CFF_PATH).expanduser().write_text(cff_yaml)
    else:
        print(cff_yaml)


if __name__ == "__main__":
    main()
