import io
import logging
from datetime import datetime
from xml.dom.minidom import parseString
from xml.sax.saxutils import XMLGenerator

logger = logging.getLogger(__file__)


class DataciteMetadata(object):

    doi_prefix = 'https://doi.org/'
    orcid_prefix = 'https://orcid.org/'
    ror_prefix = 'https://ror.org/'

    name_types = {
        'Person': 'Personal',
        'Organization': 'Organizational'
    }

    def __init__(self, data):
        self.stream = io.StringIO()
        self.xml = XMLGenerator(self.stream, 'utf-8')

        self.data = data
        logger.debug('data = %s', self.data)

    def to_xml(self):
        self.render_document()

        dom = parseString(self.stream.getvalue())
        xml = dom.toprettyxml()
        logger.debug('xml = %s', xml)
        return xml

    def render_node(self, tag, args={}, text=None):
        self.xml.startElement(tag, {k: v for k, v in args.items() if v is not None})
        if text:
            self.xml.characters(str(text))
        self.xml.endElement(tag)

    def render_document(self):
        self.xml.startDocument()
        self.xml.startElement('resource', {
            'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
            'xmlns': 'http://datacite.org/schema/kernel-4',
            'xsi:schemaLocation': 'http://datacite.org/schema/kernel-4 http://schema.datacite.org/meta/kernel-4.3/metadata.xsd'
        })

        if '@id' in self.data:
            if self.data['@id'].startswith(self.doi_prefix):
                self.render_node('identifier', {'identifierType': 'DOI'}, self.data['@id'].replace(self.doi_prefix, ''))
            else:
                self.render_node('identifier', {'identifierType': 'URL'}, self.data['@id'])

        if 'author' in self.data:
            self.xml.startElement('creators', {})
            for author in self.data['author']:
                if 'givenName' in author and 'familyName' in author:
                    name = '{} {}'.format(author['givenName'], author['familyName'])
                else:
                    name = author.get('name')

                if name is not None:
                    self.xml.startElement('creator', {})
                    self.render_node('creatorName', {
                        'nameType': self.name_types[author.get('@type', 'Person')]
                    }, name)

                    if 'givenName' in author:
                        self.render_node('givenName', {}, author['givenName'])

                    if 'familyName' in author:
                        self.render_node('familyName', {}, author['familyName'])

                    if '@id' in author:
                        if author['@id'].startswith(self.orcid_prefix):
                            self.render_node('nameIdentifier', {
                                'nameIdentifierScheme': 'ORCID',
                                'schemeURI': 'http://orcid.org'
                            }, author['@id'].replace(self.orcid_prefix, ''))

                    for affiliation in author.get('affiliation', []):
                        affiliation_attrs = {}

                        if '@id' in affiliation:
                            if affiliation['@id'].startswith(self.ror_prefix):
                                affiliation_attrs = {
                                    'affiliationIdentifier': affiliation['@id'],
                                    'affiliationIdentifierScheme': 'ROR'
                                }

                        if 'name' in affiliation:
                            self.render_node('affiliation', affiliation_attrs, affiliation['name'])

                    self.xml.endElement('creator')
            self.xml.endElement('creators')

        if 'name' in self.data:
            self.xml.startElement('titles', {})
            self.render_node('title', {}, self.data['name'])
            if 'alternateName' in self.data:
                self.render_node('title', {
                    'titleType': 'AlternativeTitle'
                }, self.data['alternateName'])
            self.xml.endElement('titles')

        if 'publisher' in self.data and 'name' in self.data['publisher']:
            self.render_node('publisher', {}, self.data['publisher']['name'])

        if 'dateModified' in self.data:
            self.render_node('publicationYear', {}, datetime.strptime(self.data['dateModified'], '%Y-%m-%d').year)

        if 'keywords' in self.data:
            self.xml.startElement('subjects', {})
            for keyword in self.data['keywords']:
                if isinstance(keyword, str):
                    self.render_node('subject', {}, keyword)
                else:
                    if 'name' in keyword:
                        subject_args = {}
                        if 'inDefinedTermSet' in keyword:
                            subject_args['schemeURI'] = keyword['inDefinedTermSet']
                        if 'url' in keyword:
                            subject_args['valueURI'] = keyword['url']
                        self.render_node('subject', subject_args, keyword['name'])
            self.xml.endElement('subjects')

        contributors = self.data.get('contributor', []) + self.data.get('copyrightHolder', [])
        if contributors:
            self.xml.startElement('contributors', {})
            for contributor in contributors:
                if 'givenName' in contributor and 'familyName' in contributor:
                    name = '{} {}'.format(contributor['givenName'], contributor['familyName'])
                else:
                    name = contributor.get('name')

                if name is not None:
                    if contributor in self.data.get('copyrightHolder', []):
                        contributor_type = 'RightsHolder'
                    elif 'additionalType' in contributor:
                        contributor_type = contributor['additionalType']
                    else:
                        contributor_type = None

                    self.xml.startElement('contributor', {
                        'contributorType': contributor_type
                    } if contributor_type is not None else {})
                    self.render_node('contributorName', {
                        'nameType': self.name_types[contributor.get('@type', 'Person')]
                    }, name)

                    if 'givenName' in contributor:
                        self.render_node('givenName', {}, contributor['givenName'])

                    if 'familyName' in contributor:
                        self.render_node('familyName', {}, contributor['familyName'])

                    if '@id' in contributor:
                        if contributor['@id'].startswith(self.orcid_prefix):
                            self.render_node('nameIdentifier', {
                                'nameIdentifierScheme': 'ORCID',
                                'schemeURI': 'http://orcid.org'
                            }, contributor['@id'].replace(self.orcid_prefix, ''))

                    for affiliation in contributor.get('affiliation', []):
                        affiliation_attrs = {}

                        if '@id' in affiliation:
                            if affiliation['@id'].startswith(self.ror_prefix):
                                affiliation_attrs = {
                                    'affiliationIdentifier': affiliation['@id'],
                                    'affiliationIdentifierScheme': 'ROR'
                                }

                        if 'name' in affiliation:
                            self.render_node('affiliation', affiliation_attrs, affiliation['name'])

                    self.xml.endElement('contributor')
            self.xml.endElement('contributors')

        self.xml.startElement('dates', {})
        if 'dateCreated' in self.data:
            self.render_node('date', {
                'dateType': 'Created'
            }, self.data['dateCreated'])
        if 'dateModified' in self.data:
            self.render_node('date', {
                'dateType': 'Issued'
            }, self.data['dateModified'])
        self.xml.endElement('dates')

        self.render_node('language', {}, 'en-US')

        if 'applicationCategory' in self.data:
            self.render_node('resource', {
                'resourceType': 'Software' if self.data.get('@type') == 'SoftwareSourceCode' else None
            }, self.data['applicationCategory'])

        if 'sameAs' in self.data:
            self.xml.startElement('alternateIdentifiers', {})
            self.render_node('alternateIdentifier', {
                'alternateIdentifierType': 'URL'
            }, self.data['sameAs'])
            self.xml.endElement('alternateIdentifiers')

        if any(key in self.data for key in ['referencePublication', 'codeRepository']):
            self.xml.startElement('relatedIdentifiers', {})
            if 'referencePublication' in self.data:
                self.render_node('relatedIdentifier', {
                    'relatedIdentifierType': 'DOI',
                    'relationType': 'IsDocumentedBy'
                }, self.data['referencePublication'].replace(self.doi_prefix, ''))
            if 'codeRepository' in self.data:
                self.render_node('relatedIdentifier', {
                    'relatedIdentifierType': 'URL',
                    'relationType': 'IsSupplementTo'  # like zenodo does it
                }, self.data['codeRepository'])
            self.xml.endElement('relatedIdentifiers')

        if 'version' in self.data:
            self.render_node('version', {}, self.data['version'])

        if 'license' in self.data and 'name' in self.data['license']:
            self.xml.startElement('rightsList', {})
            self.render_node('rights', {
                'rightsURI': self.data['license'].get('url')
            }, self.data['license']['name'])
            self.xml.endElement('rightsList')

        if 'description' in self.data:
            self.xml.startElement('descriptions', {})
            self.render_node('description', {
                'descriptionType': 'Abstract'
            }, self.data['description'])
            self.xml.endElement('descriptions')

        if 'funding' in self.data:
            self.xml.startElement('fundingReferences', {})
            for funding in self.data['funding']:
                self.xml.startElement('fundingReference', {})

                if 'funder' in funding:
                    if 'name' in funding['funder']:
                        self.render_node('funderName', {}, funding['funder']['name'])

                    if '@id' in funding['funder'] and funding['funder']['@id'].startswith(self.ror_prefix):
                        self.render_node('funderIdentifier', {
                            'funderIdentifierType': 'ROR',
                            'schemeURI': 'https://ror.org'
                        }, funding['funder']['@id'])

                if 'identifier' in funding:
                    self.render_node('awardNumber', {
                        'awardURI': funding.get('url')
                    }, funding['identifier'])

                if 'name' in funding:
                    self.render_node('awardTitle', {}, funding['name'])

                self.xml.endElement('fundingReference')
            self.xml.endElement('fundingReferences')

        self.xml.endElement('resource')
