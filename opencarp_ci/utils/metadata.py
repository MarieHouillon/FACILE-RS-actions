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
        self.data = {}

    def fetch(self, locations):
        if locations:
            for location in locations:
                self.data.update(fetch_dict(location))

    def fetch_authors(self, locations):
        if locations:
            if 'author' not in self.data:
                self.data['author'] = []
            for location in locations:
                self.data['author'] += fetch_dict(location).get('author', [])

    def fetch_contributors(self, locations):
        if locations:
            if 'contributor' not in self.data:
                self.data['contributor'] = []
            for location in locations:
                self.data['contributor'] += fetch_dict(location).get('author', [])

    def compute_names(self):
        for key in ['author', 'contributor']:
            for thing in self.data[key]:
                if 'name' not in thing and ('givenName' in thing and 'familyName' in thing):
                    thing['name'] = '{} {}'.format(thing['givenName'], thing['familyName'])

    def remove_doubles(self):
        for key in ['author', 'contributor']:
            ids = set()
            names = set()
            things = []
            for thing in self.data[key]:
                thing_id = thing.get('@id')
                thing_name = thing.get('name')
                if thing_id in ids or thing_name in names:
                    pass
                else:
                    things.append(thing)
                    if thing_id is not None:
                        ids.add(thing_id)
                    if thing_name is not None:
                        names.add(thing_name)
            self.data[key] = things

    def sort_persons(self):
        def get_key(item):
            key = item.get('familyName', item.get('name', ''))

            if item.get('@type') == 'Organization':
                # put organzations first unless they have an additionalType
                if item.get('additionalType') is None:
                    key = '!' + key
                else:
                    key = '~' + key

            return key

        self.data['author'] = sorted(self.data['author'], key=get_key)
        self.data['contributor'] = sorted(self.data['contributor'], key=get_key)


class RadarMetadata(object):

    doi_prefix = 'https://doi.org/'
    orcid_prefix = 'https://orcid.org/'
    ror_prefix = 'https://ror.org/'

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
        production_year = datetime.strptime(self.data.get('dateModified'), '%Y-%m-%d')
        publish_date = datetime.strptime(self.data['dateModified'], '%Y-%m-%d')

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
                'title': self.data['name'],
                'productionYear': production_year.year,
                'publicationYear': publish_date.year,
                'language': 'ENG'
            }
        }

        if 'sameAs' in self.data:
            radar_json['descriptiveMetadata']['alternateIdentifiers'] = {
                'alternateIdentifier': []
            }
            radar_json['descriptiveMetadata']['alternateIdentifiers']['alternateIdentifier'].append({
                'value': self.data['sameAs'],
                'alternateIdentifierType': 'URL'
            })

        if any(key in self.data for key in ['referencePublication', 'codeRepository']):
            radar_json['descriptiveMetadata']['relatedIdentifiers'] = {
                'relatedIdentifier': []
            }
            radar_json['descriptiveMetadata']['relatedIdentifiers']['relatedIdentifier'].append({
                'value': self.data['referencePublication'].replace(self.doi_prefix, ''),
                'relatedIdentifierType': 'DOI',
                'relationType': self.radar_value('IsDocumentedBy')
            })
            radar_json['descriptiveMetadata']['relatedIdentifiers']['relatedIdentifier'].append({
                'value': self.data['codeRepository'],
                'relatedIdentifierType': 'URL',
                'relationType': self.radar_value('IsSupplementTo')  # like zenodo does it
            })

        if 'author' in self.data:
            radar_json['descriptiveMetadata']['creators'] = {
                'creator': []
            }

            for author in self.data['author']:
                if 'name' in author:
                    radar_creator = {
                        'creatorName': author['name']
                    }

                    if 'givenName' in author:
                        radar_creator['givenName'] = author['givenName']

                    if 'familyName' in author:
                        radar_creator['familyName'] = author['familyName']

                    if '@id' in author:
                        if author['@id'].startswith(self.orcid_prefix):
                            radar_creator['nameIdentifier'] = [{
                                'value': author['@id'].replace(self.orcid_prefix, ''),
                                'schemeURI': 'http://orcid.org',
                                'nameIdentifierScheme': 'ORCID',
                            }]

                    for affiliation in author.get('affiliation', []):
                        if 'name' in affiliation:
                            radar_creator['creatorAffiliation'] = affiliation['name']

                    radar_json['descriptiveMetadata']['creators']['creator'].append(radar_creator)

        if 'contributors' in self.data:
            radar_json['descriptiveMetadata']['contributors'] = {
                'contributor': []
            }

            for contributor in self.data['contributors']:
                if 'name' in contributor:
                    radar_contributor = {
                        'contributorName': author['name'],
                        'contributorType': self.radar_value(contributor['additionalType'])
                    }

                    if contributor.get('@type') == 'Person':
                        radar_contributor['givenName'] = contributor['givenName']
                        radar_contributor['familyName'] = contributor['familyName']

                        if '@id' in contributor:
                            if contributor['@id'].startswith(self.orcid_prefix):
                                radar_contributor['nameIdentifier'] = [{
                                    'value': contributor['@id'].replace(self.orcid_prefix, ''),
                                    'schemeURI': 'http://orcid.org',
                                    'nameIdentifierScheme': 'ORCID',
                                }]

                        for affiliation in contributor.get('affiliation', []):
                            if 'name' in affiliation:
                                radar_contributor['contributorAffiliation'] = affiliation['name']

                radar_json['descriptiveMetadata']['contributors']['contributor'].append(radar_contributor)

        if 'alternateName' in self.data:
            radar_json['descriptiveMetadata']['additionalTitles'] = {
                'additionalTitle': []
            }
            radar_json['descriptiveMetadata']['additionalTitles']['additionalTitle'].append({
                'value': self.data['alternateName'],
                'additionalTitleType': self.radar_value('AlternativeTitle')
            })

        if 'description' in self.data:
            radar_json['descriptiveMetadata']['descriptions'] = {
                'description': []
            }
            radar_json['descriptiveMetadata']['descriptions']['description'].append({
                'value': self.data['description'],
                'descriptionType': self.radar_value('Abstract')
            })

        if 'keywords' in self.data:
            keywords = []
            subjects = []
            for keyword in self.data['keywords']:
                if isinstance(keyword, str):
                    keywords.append(keyword)

                else:
                    if 'name' in keyword and \
                            keyword.get('@type') == 'DefinedTerm' and \
                            keyword.get('inDefinedTermSet', '').startswith('https://www.radar-service.eu/schemas/'):
                        subjects.append(keyword['name'])

            if keywords:
                radar_json['descriptiveMetadata']['keywords'] = {
                    'keyword': []
                }
                for keyword in keywords:
                    radar_json['descriptiveMetadata']['keywords']['keyword'].append(keyword)

            if subjects:
                radar_json['descriptiveMetadata']['subjectAreas'] = {
                    'subjectArea': []
                }
                for subject in subjects:
                    radar_json['descriptiveMetadata']['subjectAreas']['subjectArea'].append({
                        'controlledSubjectAreaName': self.radar_value(subject)
                    })

        if 'publisher' in self.data and 'name' in self.data['publisher']:
            radar_json['descriptiveMetadata']['publishers'] = {
                'publisher': [self.data['publisher']['name']]
            }

        if 'applicationCategory' in self.data:
            radar_json['descriptiveMetadata']['resource'] = {
                'value': self.data['applicationCategory']
            }
            if self.data.get('@type') == 'SoftwareSourceCode':
                radar_json['descriptiveMetadata']['resource']['resourceType'] = self.radar_value('Software')

        if 'license' in self.data and 'name' in self.data['license']:
            radar_json['descriptiveMetadata']['rights'] = {
                'controlledRights': 'OTHER',
                'additionalRights': self.data['license']['name']
            }

        if 'copyrightHolder' in self.data and 'name' in self.data['copyrightHolder']:
            radar_json['descriptiveMetadata']['rightsHolders'] = {
                'rightsHolder': [
                    self.data['copyrightHolder']['name']
                ]
            }

        if 'funding' in self.data:
            radar_json['descriptiveMetadata']['fundingReferences'] = {
                'fundingReference': []
            }
            for funding in self.data['funding']:
                radar_funding_reference = {}

                if 'funder' in funding:
                    if 'name' in funding['funder']:
                        radar_funding_reference['funderName'] = funding['funder']['name']

                    if '@id' in funding['funder'] and funding['funder']['@id'].startswith(self.ror_prefix):
                        radar_funding_reference['funderIdentifier'] = {
                            'value': funding['funder']['@id'],
                            'type': 'OTHER'
                        }

                if 'identifier' in funding:
                    radar_funding_reference['awardNumber'] = funding['identifier']
                if 'url' in funding:
                    radar_funding_reference['awardURI'] = funding['url']
                if 'name' in funding:
                    radar_funding_reference['awardTitle'] = funding['name']

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
