#!/usr/bin/env python
import argparse
import logging
from pathlib import Path

import frontmatter
import pypandoc

from .utils import settings
from .utils.grav import collect_pages

logger = logging.getLogger(__file__)

TEMPLATE = '''
---
nocite: '@*'
---
'''


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('--grav-path', dest='grav_path',
                        help='Path to the grav repository directory.')
    parser.add_argument('--pipeline', dest='pipeline',
                        help='Name of the pipeline as specified in the GRAV metadata.')
    parser.add_argument('--pipeline-source', dest='pipeline_source',
                        help='Path to the source directory for the pipeline.')
    parser.add_argument('--pipeline-csl', dest='pipeline_csl',
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

    # loop over the found pages and write the content into the files
    for page_path, page, source in collect_pages(settings.GRAV_PATH, settings.PIPELINE):
        source_path = Path(settings.PIPELINE_SOURCE).expanduser() / source
        logger.debug('page_path = %s, source_path = %s', page_path, source_path)

        extra_args = ['--bibliography={}'.format(source_path), '--citeproc', '--wrap=preserve']
        if settings.PIPELINE_CSL:
            extra_args.append('--csl={}'.format(settings.PIPELINE_CSL))

        page.content = pypandoc.convert_text(TEMPLATE, to='html', format='md',
                                             extra_args=extra_args)

        logger.info('writing publications to %s', page_path)
        open(page_path, 'w').write(frontmatter.dumps(page))


if __name__ == "__main__":
    main()
