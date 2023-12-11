#!/usr/bin/env python
import argparse
from datetime import date
from pathlib import Path

from .utils import settings
from .utils.metadata import CodemetaMetadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--codemeta-location', dest='codemeta_location',
                        help='Location of the main codemeta.json JSON file')
    parser.add_argument('--version', dest='version',
                        help='Version of the resource')
    parser.add_argument('--date', dest='date',
                        help='Date for dateModified (format: \'%%Y-%%m-%%d\')')
    parser.add_argument('--log-level', dest='log_level',
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-file', dest='log_file',
                        help='Path to the log file')

    settings.setup(parser, validate=[
        'CODEMETA_LOCATION',
        'VERSION'
    ])

    codemeta = CodemetaMetadata()
    codemeta.fetch(settings.CODEMETA_LOCATION)

    codemeta.data['version'] = settings.VERSION
    codemeta.data['dateModified'] = settings.DATE or date.today().strftime('%Y-%m-%d')

    Path(settings.CODEMETA_LOCATION).expanduser().write_text(codemeta.to_json())


if __name__ == "__main__":
    main()
