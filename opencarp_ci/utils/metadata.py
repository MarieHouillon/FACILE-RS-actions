import io
import json
import logging
import re
from datetime import datetime
from xml.dom.minidom import parseString
from xml.sax.saxutils import XMLGenerator

logger = logging.getLogger(__file__)


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
                "publicationBacklink": self.publication_backlink
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
                    'creatorName': creator['name'],
                    'givenName': creator['given_name'],
                    'familyName': creator['family_name']
                }

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

                if contributor.get('name_type') != 'Organisational':
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

        if 'identifier' in self.data:
            self.render_node('identifier', {'identifierType': 'DOI'}, self.data['identifier'])

        if 'creators' in self.data:
            self.xml.startElement('creators', {})
            for creator in self.data['creators']:
                self.xml.startElement('creator', {})
                self.render_node('creatorName', {'nameType': 'Personal'}, creator['name'])
                self.render_node('givenName', {}, creator.get('given_name'))
                self.render_node('familyName', {}, creator.get('family_name'))

                if 'orcid' in creator:
                    self.render_node('nameIdentifier', {
                        'schemeURI': 'http://orcid.org',
                        'nameIdentifierScheme': 'ORCID'
                    }, creator['orcid'])

                for affiliation in creator.get('affiliations', []):
                    self.render_node('affiliation', {
                        'affiliationIdentifier': 'https://ror.org/{}'.format(affiliation['ror']),
                        'affiliationIdentifierScheme': 'ROR'
                    } if 'ror' in affiliation else {}, affiliation['name'])

                self.xml.endElement('creator')
            self.xml.endElement('creators')

        self.xml.startElement('titles', {})
        self.render_node('title', {}, self.data['title'])
        if 'additional_titles' in self.data:
            for additional_title in self.data['additional_titles']:
                self.render_node('title', {
                    'titleType': additional_title.get('additional_title_type', 'AlternativeTitle')
                }, additional_title['additional_title'])
        self.xml.endElement('titles')

        if 'publisher' in self.data:
            self.render_node('publisher', {}, self.data['publisher'])

        if 'issued' in self.data:
            self.render_node('publicationYear', {}, datetime.strptime(self.data['issued'], '%Y-%m-%d').year)

        if 'subjects' in self.data:
            self.xml.startElement('subjects', {})
            for subject in self.data['subjects']:
                subject_args = {}
                if 'scheme_uri' in subject:
                    subject_args['schemeURI'] = subject['scheme_uri']
                if 'value_uri' in subject:
                    subject_args['valueURI'] = subject['value_uri']
                self.render_node('subject', subject_args, subject['subject'])
            self.xml.endElement('subjects')

        if 'contributors' in self.data:
            self.xml.startElement('contributors', {})
            for contributor in self.data.get('contributors', []):
                self.xml.startElement('contributor', {
                    'contributorType': contributor['contributor_type']
                })
                self.render_node('contributorName', {'nameType': contributor['name_type']}, contributor['name'])

                if contributor['name_type'] == 'Personal':
                    self.render_node('givenName', {}, contributor.get('given_name'))
                    self.render_node('familyName', {}, contributor.get('family_name'))

                if 'orcid' in contributor:
                    self.render_node('nameIdentifier', {
                        'schemeURI': 'http://orcid.org',
                        'nameIdentifierScheme': 'ORCID'
                    }, contributor['orcid'])

                if 'ror' in contributor:
                    self.render_node('nameIdentifier', {
                        'schemeURI': 'https://ror.org',
                        'nameIdentifierScheme': 'ROR'
                    }, contributor['ror'])

                for affiliation in contributor.get('affiliations', []):
                    self.render_node('affiliation', {
                        'affiliationIdentifier': 'https://ror.org/{}'.format(affiliation['ror']),
                        'affiliationIdentifierScheme': 'ROR'
                    } if 'ror' in affiliation else {}, affiliation['name'])

                self.xml.endElement('contributor')
            self.xml.endElement('contributors')

        self.xml.startElement('dates', {})
        if 'created' in self.data:
            self.render_node('date', {
                'dateType': 'Created'
            }, self.data['created'])
        if 'issued' in self.data:
            self.render_node('date', {
                'dateType': 'Issued'
            }, self.data['issued'])
        self.xml.endElement('dates')

        self.render_node('language', {}, 'en-US')

        if 'resource' in self.data:
            self.render_node('resource', {
                'resourceType': self.data.get('resource_type', 'Software')
            }, self.data['resource'])

        if 'alternate_identifiers' in self.data:
            self.xml.startElement('alternateIdentifiers', {})
            for alternate_identifier in self.data['alternate_identifiers']:
                self.render_node('alternateIdentifier', {
                    'alternateIdentifierType': alternate_identifier['alternate_identifier_type']
                }, alternate_identifier['alternate_identifier'])
            self.xml.endElement('alternateIdentifiers')

        if 'related_identifiers' in self.data:
            self.xml.startElement('relatedIdentifiers', {})
            for related_identifier in self.data['related_identifiers']:
                self.render_node('relatedIdentifier', {
                    'relatedIdentifierType': related_identifier['related_identifier_type'],
                    'relationType': related_identifier['relation_type']
                }, related_identifier['related_identifier'])
            self.xml.endElement('relatedIdentifiers')

        if 'version' in self.data:
            self.render_node('version', {}, self.data['version'])

        self.xml.startElement('rightsList', {})
        self.render_node('rights', {
            'rightsURI': self.data.get('rights_uri')
        }, self.data['rights'])
        self.xml.endElement('rightsList')

        if 'descriptions' in self.data:
            self.xml.startElement('descriptions', {})
            for description in self.data['descriptions']:
                self.render_node('description', {
                    'descriptionType': description.get('description_type', 'Abstract')
                }, description['description'])
            self.xml.endElement('descriptions')

        if 'funding_references' in self.data:
            self.xml.startElement('fundingReferences', {})
            for funding_reference in self.data['funding_references']:
                self.xml.startElement('fundingReference', {})
                self.render_node('funderName', {}, funding_reference['name'])

                if 'ror' in funding_reference:
                    self.render_node('funderIdentifier', {
                        'schemeURI': 'https://ror.org',
                        'funderIdentifierType': 'ROR'
                    }, funding_reference['ror'])

                if 'award_number' in funding_reference:
                    self.render_node('awardNumber', {
                        'awardURI': funding_reference.get('award_uri')
                    }, funding_reference['award_number'])

                if 'award_title' in funding_reference:
                    self.render_node('awardTitle', {}, funding_reference['award_title'])

                self.xml.endElement('fundingReference')
            self.xml.endElement('fundingReferences')

        self.xml.endElement('resource')
