import re

from setuptools import find_packages, setup

# get metadata from module using a regexp
with open('facile_rs/__init__.py') as f:
    metadata = dict(re.findall(r'__(.*)__ = [\']([^\']*)[\']', f.read()))

# get install_requires from requirements.txt
with open('requirements.txt') as f:
    install_requires = f.readlines()

setup(
    name=metadata['title'],
    version=metadata['version'],
    author=metadata['author'],
    author_email=metadata['email'],
    maintainer=metadata['author'],
    maintainer_email=metadata['email'],
    license=metadata['license'],
    url='https://git.opencarp.org/openCARP/FACILE-RS',
    description=u'FACILE-RS automates tasks around the archival and long term preservation of software repositories',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5'
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'create_bag=facile_rs.create_bag:main',
            'create_bagpack=facile_rs.create_bagpack:main',
            'create_cff=facile_rs.create_cff:main',
            'create_datacite=facile_rs.create_datacite:main',
            'create_radar=facile_rs.create_radar:main',
            'create_release=facile_rs.create_release:main',
            'prepare_radar=facile_rs.prepare_radar:main',
            'prepare_release=facile_rs.prepare_release:main',
            'run_bibtex_pipeline=facile_rs.run_bibtex_pipeline:main',
            'run_docstring_pipeline=facile_rs.run_docstring_pipeline:main',
            'run_markdown_pipeline=facile_rs.run_markdown_pipeline:main'
        ]
    }
)
