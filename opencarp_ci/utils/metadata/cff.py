import logging
from datetime import datetime

import yaml

from ..http import fetch_json

logger = logging.getLogger(__file__)


class CffMetadata(object):

    doi_prefix = 'https://doi.org/'
    orcid_prefix = 'https://orcid.org/'
    ror_prefix = 'https://ror.org/'

    name_types = {
        'Person': 'Personal',
        'Organization': 'Organizational'
    }

    def __init__(self, data):
        self.data = data
        logger.debug('data = %s', self.data)

    def to_yaml(self):
        cff_json = {
            'cff-version': '1.2.0',
            'message': 'If you use this software, please cite the paper describing it as below. '
                       'Specific versions of the software can additionally be referenced using individual DOIs.',
            'type': 'Software'
        }

        if 'name' in self.data:
            cff_json['title'] = self.data['name']

        if 'description' in self.data:
            cff_json['abstract'] = self.data['description']

        if 'sameAs' in self.data:
            cff_json['url'] = self.data['sameAs']

        if 'author' in self.data:
            cff_json['authors'] = []
            for author in self.data['author']:
                cff_author = {}

                if 'givenName' in author:
                    cff_author['given-names'] = author['givenName']

                if 'familyName' in author:
                    cff_author['family-names'] = author['familyName']

                if '@id' in author and author['@id'].startswith(self.orcid_prefix):
                    cff_author['orcid'] = author['@id']

                if cff_author:
                    cff_json['authors'].append(cff_author)

            cff_json['name'] = self.data['name']

        if '@id' in self.data and self.data['@id'].startswith(self.doi_prefix):
            cff_json['identifier'] = {
                'type': 'doi',
                'value': self.data['@id']
            }

        if 'dateModified' in self.data:
            cff_json['date-released'] = datetime.strptime(self.data['dateModified'], '%Y-%m-%d').date()

        if 'license' in self.data:
            if 'name' in self.data['license']:
                cff_json['license'] = self.data['license']['name']

            if 'url' in self.data['license']:
                cff_json['license-url'] = self.data['license']['url']

        if 'codeRepository' in self.data:
            cff_json['repository-code'] = self.data['codeRepository']

        if 'referencePublication' in self.data:
            cff_json['preferred-citation'] = {}
            if self.data['referencePublication'].startswith(self.doi_prefix):
                doi_metadata = fetch_json(self.data['referencePublication'])

                if 'type' in doi_metadata:
                    cff_json['preferred-citation']['type'] = doi_metadata['type']

                cff_json['preferred-citation']['doi'] = self.data['referencePublication'].replace(self.doi_prefix, '')

                if 'title' in doi_metadata:
                    cff_json['preferred-citation']['title'] = doi_metadata['title']

                if 'author' in doi_metadata:
                    cff_json['preferred-citation']['authors'] = []
                    for doi_author in doi_metadata['author']:
                        cff_citation_author = {}

                        if 'family' in doi_author:
                            cff_citation_author['family-names'] = doi_author['family']

                        if 'given' in doi_author:
                            cff_citation_author['given-names'] = doi_author['given']

                        if 'ORCID' in doi_author:
                            cff_citation_author['orcid'] = doi_author['ORCID']

                        cff_json['preferred-citation']['authors'].append(cff_citation_author)

                if 'container-title' in doi_metadata:
                    cff_json['preferred-citation']['journal'] = doi_metadata['container-title']

                if 'published' in doi_metadata:
                    cff_json['preferred-citation']['year'] = doi_metadata['published']['date-parts'][0][0]

                if 'volume' in doi_metadata:
                    cff_json['preferred-citation']['volume'] = int(doi_metadata['volume'])

                if 'page' in doi_metadata:
                    cff_json['preferred-citation']['page'] = int(doi_metadata['page'])

        return yaml.dump(cff_json, allow_unicode=True, sort_keys=False, default_flow_style=False)
