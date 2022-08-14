import io
import json
import logging
import re
from datetime import datetime
from xml.dom.minidom import parseString
from xml.sax.saxutils import XMLGenerator

from .http import fetch_dict

logger = logging.getLogger(__file__)


class CodemetaMetadata(object):

    def __init__(self):
        self.data = None

    def fetch(self, locations):
        self.data = fetch_dict(locations)

    def fetch_authors(self, locations):
        if locations:
            if 'author' not in self.data:
                self.data['author'] = []
            self.data['author'] = fetch_dict(locations).get('author', [])

    def fetch_contributors(self, locations):
        if locations:
            if 'contributor' not in self.data:
                self.data['contributor'] = []
            self.data['contributor'] += fetch_dict(locations).get('author', [])

    def sort_persons(self):
        def get_key(item):
            key = item.get('familyName', item.get('name', ''))

            if item.get('@type') == 'Organization':
                # put organzations first
                key = '!' + key

            return key

        self.data['author'] = sorted(self.data['author'], key=get_key)
        self.data['contributor'] = sorted(self.data['contributor'], key=get_key)


class RadarMetadata(object):

    def __init__(self, data, responsible_email, publication_backlink):
        self.data = data
        self.responsible_email = responsible_email
        self.publication_backlink = publication_backlink
        logger.debug('data = %s', self.data)

    def radar_value(self, string):
        # converts CamelCase to all caps and underscores, e.g. HostingInstitution -> HOSTING_INSTITUTION
        return '_'.join([s.upper() for s in re.findall('([A-Z][a-z]+)', string)])

    def to_json(self):
        # prepare radar payload
        archive_date = datetime.utcnow()
        production_year = datetime.strptime(self.data.get('created') or self.data.get('issued'), '%Y-%m-%d')
        publish_date = datetime.strptime(self.data['issued'], '%Y-%m-%d')

        radar_json = {
            'technicalMetadata': {
                "retentionPeriod": 10,
                "archiveDate": int(archive_date.timestamp()),
                "publishDate": int(publish_date.timestamp()),
                "responsibleEmail": self.responsible_email,
                "publicationBacklink": self.publication_backlink,
                "schema": {
                    "key": "RDDM",
                    "version": "09"
                }
            },
            'descriptiveMetadata': {
                'title': self.data['title'],
                'productionYear': production_year.year,
                'publicationYear': publish_date.year,
                'language': 'ENG'
            }
        }

        if 'alternate_identifiers' in self.data:
            radar_json['descriptiveMetadata']['alternateIdentifiers'] = {
                'alternateIdentifier': []
            }
            for alternate_identifier in self.data['alternate_identifiers']:
                radar_json['descriptiveMetadata']['alternateIdentifiers']['alternateIdentifier'].append({
                    'value': alternate_identifier['alternate_identifier'],
                    'alternateIdentifierType': alternate_identifier['alternate_identifier_type']
                })

        if 'related_identifiers' in self.data:
            radar_json['descriptiveMetadata']['relatedIdentifiers'] = {
                'relatedIdentifier': []
            }
            for related_identifier in self.data['related_identifiers']:
                if related_identifier['relation_type'] not in ['IsVersionOf']:
                    radar_json['descriptiveMetadata']['relatedIdentifiers']['relatedIdentifier'].append({
                        'value': related_identifier['related_identifier'],
                        'relatedIdentifierType': related_identifier['related_identifier_type'],
                        'relationType': self.radar_value(related_identifier['relation_type'])
                    })

        if 'creators' in self.data:
            radar_json['descriptiveMetadata']['creators'] = {
                'creator': []
            }

            for creator in self.data['creators']:
                radar_creator = {
                    'creatorName': creator['name']
                }

                if 'given_name' in creator:
                    radar_creator['givenName'] = creator['given_name']

                if 'family_name' in creator:
                    radar_creator['familyName'] = creator['family_name']

                if 'orcid' in creator:
                    radar_creator['nameIdentifier'] = [{
                        'value': creator['orcid'],
                        'schemeURI': 'http://orcid.org',
                        'nameIdentifierScheme': 'ORCID',
                    }]

                for affiliation in creator.get('affiliations', []):
                    radar_creator['creatorAffiliation'] = affiliation['name']

                radar_json['descriptiveMetadata']['creators']['creator'].append(radar_creator)

        if 'contributors' in self.data:
            radar_json['descriptiveMetadata']['contributors'] = {
                'contributor': []
            }

            for contributor in self.data['contributors']:
                radar_contributor = {
                    'contributorName': contributor['name'],
                    'contributorType': self.radar_value(contributor['contributor_type'])
                }

                if contributor.get('name_type') != 'Organizational':
                    radar_contributor['givenName'] = contributor['given_name']
                    radar_contributor['familyName'] = contributor['family_name']

                    if 'orcid' in contributor:
                        radar_contributor['nameIdentifier'] = [{
                            'value': contributor['orcid'],
                            'schemeURI': 'http://orcid.org',
                            'nameIdentifierScheme': 'ORCID',
                        }]
                    for affiliation in contributor.get('affiliations', []):
                        radar_contributor['contributorAffiliation'] = affiliation['name']

                radar_json['descriptiveMetadata']['contributors']['contributor'].append(radar_contributor)

        if 'additional_titles' in self.data:
            radar_json['descriptiveMetadata']['additionalTitles'] = {
                'additionalTitle': []
            }
            for additional_title in self.data['additional_titles']:
                radar_json['descriptiveMetadata']['additionalTitles']['additionalTitle'].append({
                    'value': additional_title['additional_title'],
                    'additionalTitleType': self.radar_value(additional_title.get('additional_title_type', 'AlternativeTitle'))
                })

        if 'descriptions' in self.data:
            radar_json['descriptiveMetadata']['descriptions'] = {
                'description': []
            }
            for description in self.data['descriptions']:
                radar_json['descriptiveMetadata']['descriptions']['description'].append({
                    'value': description['description'],
                    'descriptionType': self.radar_value(description.get('description_type', 'Abstract'))
                })

        if 'keywords' in self.data:
            radar_json['descriptiveMetadata']['keywords'] = {
                'keyword': []
            }
            for keyword in self.data['keywords']:
                radar_json['descriptiveMetadata']['keywords']['keyword'].append(keyword)

        if 'publisher' in self.data:
            radar_json['descriptiveMetadata']['publishers'] = {
                'publisher': [self.data['publisher']]
            }

        if 'radar_subjects' in self.data:
            radar_json['descriptiveMetadata']['subjectAreas'] = {
                'subjectArea': []
            }
            for subject in self.data['radar_subjects']:
                radar_json['descriptiveMetadata']['subjectAreas']['subjectArea'].append({
                    'controlledSubjectAreaName': self.radar_value(subject)
                })

        if 'resource' in self.data:
            radar_json['descriptiveMetadata']['resource'] = {
                'value': self.data['resource'],
                'resourceType': self.radar_value(self.data.get('resource_type', 'Software')),
            }

        if 'rights' in self.data:
            radar_json['descriptiveMetadata']['rights'] = {
                'controlledRights': 'OTHER',
                'additionalRights': self.data['rights']
            }

        if 'rights_holder' in self.data:
            radar_json['descriptiveMetadata']['rightsHolders'] = {
                'rightsHolder': [self.data['rights_holder']]
            }

        if 'funding_references' in self.data:
            radar_json['descriptiveMetadata']['fundingReferences'] = {
                'fundingReference': []
            }
            for funding_reference in self.data['funding_references']:
                radar_funding_reference = {
                    'funderName': funding_reference['name']
                }

                if 'ror' in funding_reference:
                    radar_funding_reference['funderIdentifier'] = {
                        'value': funding_reference['ror'],
                        'type': 'OTHER'
                    }

                if 'award_number' in funding_reference:
                    radar_funding_reference['awardNumber'] = funding_reference['award_number']
                if 'award_uri' in funding_reference:
                    radar_funding_reference['awardURI'] = funding_reference['award_uri']
                if 'award_title' in funding_reference:
                    radar_funding_reference['awardTitle'] = funding_reference['award_title']

                radar_json['descriptiveMetadata']['fundingReferences']['fundingReference'].append(radar_funding_reference)

        logger.debug('radar_json = %s', json.dumps(radar_json, indent=2))
        return radar_json


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
                                'schemeURI': 'http://orcid.org',
                                'nameIdentifierScheme': 'ORCID'
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
            for subject in self.data['keywords']:
                if 'name' in subject:
                    subject_args = {}
                    if 'inDefinedTermSet' in subject:
                        subject_args['schemeURI'] = subject['inDefinedTermSet']
                    if 'url' in subject:
                        subject_args['valueURI'] = subject['url']
                    self.render_node('subject', subject_args, subject['name'])
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
                    self.xml.startElement('contributor', {
                        'contributorType': contributor['additionalType']
                    } if 'additionalType' in contributor else {})
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
                                'schemeURI': 'http://orcid.org',
                                'nameIdentifierScheme': 'ORCID'
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

        if '@type' in self.data:
            if self.data['@type'] == 'SoftwareSourceCode':
                self.render_node('resource', {
                    'resourceType': 'Software'
                }, 'SoftwareSourceCode')

        if 'sameAs' in self.data:
            self.xml.startElement('alternateIdentifiers', {})
            self.render_node('alternateIdentifier', {
                'alternateIdentifierType': 'URL'
            }, self.data['sameAs'])
            self.xml.endElement('alternateIdentifiers')

        if 'referencePublication' in self.data:
            self.xml.startElement('relatedIdentifiers', {})
            if 'referencePublication' in self.data:
                self.render_node('relatedIdentifier', {
                    'relatedIdentifierType': 'DOI',
                    'relationType': 'IsDocumentedBy'
                }, self.data['referencePublication'])
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
                            'schemeURI': 'https://ror.org',
                            'funderIdentifierType': 'ROR'
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
