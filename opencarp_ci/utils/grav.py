import logging
import os
from pathlib import Path

import frontmatter

logger = logging.getLogger(__file__)


def collect_pages(grav_path, pipeline_name):
    pages_path = Path(grav_path).expanduser() / 'pages'

    # walk the grav repo to find the files with `pipeline: carputils`
    pages = []
    for root, dirs, files in os.walk(pages_path):
        for file_name in files:
            file_path = Path(root) / file_name
            if file_path.suffix == '.md' and file_path.stem not in ['modular']:
                try:
                    page = frontmatter.load(file_path)
                    if page.get('pipeline') == pipeline_name:
                        logger.debug('file_path = %s', file_path)
                        pages.append((file_path, page, page.get('source')))

                except TypeError:
                    # if a file has issues with the metadata, just ignore it
                    pass

    return pages
