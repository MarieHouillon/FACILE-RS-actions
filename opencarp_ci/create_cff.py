#!/usr/bin/env python
import argparse
from pathlib import Path

from .utils import settings
from .utils.metadata import CodemetaMetadata, CffMetadata


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--codemeta-location', dest='codemeta_location',
                        help='Locations of the main codemeta.json JSON file')
    parser.add_argument('--creators-location', dest='creators_locations', action='append', default=[],
                        help='Locations of codemeta JSON files for additional creators')
    parser.add_argument('--contributors-location', dest='contributors_locations', action='append', default=[],
                        help='Locations of codemeta JSON files for additional contributors')
    parser.add_argument('--cff-path', dest='cff_path',
                        help='Path to the cff output file')
    parser.add_argument('--no-sort-authors', dest='sort_authors', action='store_false',
                        help='Do not sort authors alphabetically, keep order in codemeta.json file')    
    parser.set_defaults(sort_authors=True)
    parser.add_argument('--log-level', dest='log_level',
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-file', dest='log_file',
                        help='Path to the log file')

    settings.setup(parser, validate=[
        'CODEMETA_LOCATION'
    ])

    codemeta = CodemetaMetadata()
    codemeta.fetch(settings.CODEMETA_LOCATION)
    codemeta.fetch_authors(settings.CREATORS_LOCATIONS)
    codemeta.fetch_contributors(settings.CONTRIBUTORS_LOCATIONS)
    codemeta.compute_names()
    codemeta.remove_doubles()
    if settings.SORT_AUTHORS:
        codemeta.sort_persons()

    cff_metadata = CffMetadata(codemeta.data)
    cff_yaml = cff_metadata.to_yaml()

    if settings.CFF_PATH:
        Path(settings.CFF_PATH).expanduser().write_text(cff_yaml)
    else:
        print(cff_yaml)


if __name__ == "__main__":
    main()