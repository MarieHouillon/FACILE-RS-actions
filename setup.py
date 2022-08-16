import re

from setuptools import find_packages, setup

# get metadata from module using a regexp
with open('opencarp_ci/__init__.py') as f:
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
    url='https://github.com/rdmorganiser/rdmo',
    description=u'RDMO is a tool to support the systematic planning, organisation and implementation of the data management throughout the course of a research project.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    install_requires=install_requires,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django :: 2.2',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.5'
    ],
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'create_bag=opencarp_ci.create_bag:main',
            'create_bagpack=opencarp_ci.create_bagpack:main',
            'create_cff=opencarp_ci.create_cff:main',
            'create_datacite=opencarp_ci.create_datacite:main',
            'create_radar=opencarp_ci.create_radar:main',
            'create_release=opencarp_ci.create_release:main',
            'run_bibtex_pipeline=opencarp_ci.run_bibtex_pipeline:main',
            'run_docstring_pipeline=opencarp_ci.run_docstring_pipeline:main',
            'run_markdown_pipeline=opencarp_ci.run_markdown_pipeline:main'
        ]
    }
)
