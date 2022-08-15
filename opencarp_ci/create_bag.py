#!/usr/bin/env python
import argparse
from pathlib import Path

import bagit

from .utils import settings
from .utils.http import fetch_dict, fetch_files


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('assets', nargs='*', default=[],
                        help='Assets to be added to the bag.')
    parser.add_argument('--bag-path', dest='bag_path',
                        help='Path to the Bag directory')
    parser.add_argument('--bag-info-location', dest='bag_info_locations', action='append', default=[],
                        help='Locations of the bag-info YAML/JSON files')
    parser.add_argument('--log-level', dest='log_level',
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-file', dest='log_file',
                        help='Path to the log file')

    settings.setup(parser, validate=[
        'BAG_PATH'
    ])

    # setup the bag
    bag_path = Path(settings.BAG_PATH).expanduser()
    if bag_path.exists():
        parser.error('BAG_PATH exists.')
    bag_path.mkdir()

    # collect assets
    fetch_files(settings.ASSETS, bag_path)

    # fetch bag-info
    bag_info = fetch_dict(settings.BAG_INFO_LOCATIONS)

    # create bag using bagit
    bag = bagit.make_bag(bag_path, bag_info)
    bag.save()


if __name__ == "__main__":
    main()
