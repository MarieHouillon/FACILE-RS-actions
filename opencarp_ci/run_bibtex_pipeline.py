#!/usr/bin/env python
import argparse
import logging
import re
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
    parser.add_argument('--pipeline-template', dest='pipeline_template',
                        help='Path to the template for the pipeline.')
    parser.add_argument('--pipeline-csl', dest='pipeline_csl',
                        help='Path to the source directory for the pipeline.')
    parser.add_argument('--log-level', dest='log_level',
                        help='Log level (ERROR, WARN, INFO, or DEBUG)')
    parser.add_argument('--log-file', dest='log_file',
                        help='Path to the log file')

    settings.setup(parser, validate=[
        'GRAV_PATH',
        'PIPELINE',
        'PIPELINE_SOURCE',
        'PIPELINE_TEMPLATE'
    ])

    # open and read the template file:
    source_path = Path(settings.PIPELINE_SOURCE).expanduser()
    template_path = Path(settings.PIPELINE_TEMPLATE).expanduser()
    content = template_path.read_text()

    # use a regexp to get the shortcodes
    bibtex_files = re.findall(r'\[\[\s*(.*?)\s*\]\]', content)

    # loop over files and produce publication list using pandoc
    for file_name in bibtex_files:
        file_path = source_path / file_name
        logger.debug('file_path = %s', file_path)

        extra_args = ['--bibliography={}'.format(file_path)]
        if settings.PIPELINE_CSL:
            extra_args.append('--csl={}'.format(settings.PIPELINE_CSL))

        html = pypandoc.convert_text(TEMPLATE, to='html', format='md',
                                     filters=['pandoc-citeproc'],
                                     extra_args=extra_args)
        sub_pattern = r'\[\[\s*{}\s*\]\]'.format(re.escape(file_name))
        content = re.sub(sub_pattern, '<>', content).replace('<>', html)

    # loop over the found pages and write the content into the files
    for page_path, page, _ in collect_pages(settings.GRAV_PATH, settings.PIPELINE):
        page.content = content

        logger.info('writing publications to %s', page_path)
        open(page_path, 'w').write(frontmatter.dumps(page))


if __name__ == "__main__":
    main()
