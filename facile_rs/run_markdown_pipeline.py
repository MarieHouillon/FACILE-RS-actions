#!/usr/bin/env python
import argparse
import json
import logging
from pathlib import Path

import frontmatter
import yaml

from .utils import settings
from .utils.grav import collect_pages

logger = logging.getLogger(__file__)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--grav-path', dest='grav_path',
                        help='Path to the grav repository directory.')
    parser.add_argument('--pipeline', dest='pipeline',
                        help='Name of the pipeline as specified in the GRAV metadata.')
    parser.add_argument('--pipeline-source', dest='pipeline_source',
                        help='Path to the source directory for the pipeline.')
    parser.add_argument('--log-level', dest='log_level',
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-file', dest='log_file',
                        help='Path to the log file')

    settings.setup(parser, validate=[
        'GRAV_PATH',
        'PIPELINE',
        'PIPELINE_SOURCE'
    ])

    # loop over the tagged pages and write the content into the files
    for page_path, page, source in collect_pages(settings.GRAV_PATH, settings.PIPELINE):
        source_path = Path(settings.PIPELINE_SOURCE).expanduser() / source

        # read the source file
        if source_path.suffix in ['.json']:
            data = json.loads(source_path.read_text())
            if source_path.name == 'codemeta.json':
                page.metadata['codemeta'] = data
            else:
                page.metadata['items'] = data
        elif source_path.suffix in ['.yml', '.yaml']:
            page.metadata['items'] = yaml.safe_load(source_path.read_text())
        else:
            page.content = source_path.read_text()

        # write the page file
        logger.info('writing content to %s', page_path)
        page_path.write_text(frontmatter.dumps(page))


if __name__ == "__main__":
    main()
