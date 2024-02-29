#!/usr/bin/env python
import argparse
from pathlib import Path

import bagit

from .utils import settings
from .utils.checksum import get_sha256, get_sha512
from .utils.http import fetch_dict, fetch_files


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('assets', nargs='*',
                        help='Assets to be added to the bag.')
    parser.add_argument('--bag-path', dest='bag_path',
                        help='Path to the Bag directory')
    parser.add_argument('--bag-info-location', dest='bag_info_locations', action='append', default=[],
                        help='Locations of the bag-info YAML/JSON files')
    parser.add_argument('--datacite-path', dest='datacite_path',
                        help='Path to the DataCite XML file')
    parser.add_argument('--log-level', dest='log_level',
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-file', dest='log_file',
                        help='Path to the log file')

    settings.setup(parser, validate=[
        'BAG_PATH',
        'DATACITE_PATH'
    ])

    # setup the bag
    bag_path = Path(settings.BAG_PATH).expanduser()
    if bag_path.exists():
        parser.error('{} already exists.'.format(bag_path))
    bag_path.mkdir()

    # collect assets
    fetch_files(settings.ASSETS, bag_path)

    # fetch bag-info
    bag_info = {}
    for location in settings.BAG_INFO_LOCATIONS:
        bag_info.update(fetch_dict(location))

    # create bag using bagit
    bag = bagit.make_bag(bag_path, bag_info)
    bag.save()

    # get datacite.xml and put it in the bag
    datacite_path = Path(settings.DATACITE_PATH).expanduser()
    datacite_xml = datacite_path.read_text()
    datacite_bag_path = bag_path / 'metadata' / 'datacite.xml'
    datacite_bag_path.parent.mkdir()
    datacite_bag_path.write_text(datacite_xml)

    with open(bag_path / 'tagmanifest-sha256.txt', 'a') as f:
        f.write('{} metadata/datacite.xml\n'.format(get_sha256(datacite_path)))

    with open(bag_path / 'tagmanifest-sha512.txt', 'a') as f:
        f.write('{} metadata/datacite.xml\n'.format(get_sha512(datacite_path)))


if __name__ == "__main__":
    main()
