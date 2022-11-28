import json
import logging
import re
from datetime import datetime

logger = logging.getLogger(__file__)


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

    def as_dict(self):
        # prepare radar payload
        archive_date = datetime.utcnow()

        radar_dict = {
            'technicalMetadata': {
                "retentionPeriod": 10,
                "archiveDate": int(archive_date.timestamp()),
                "responsibleEmail": self.responsible_email,
                "publicationBacklink": self.publication_backlink,
                "schema": {
                    "key": "RDDM",
                    "version": "09"
                }
            },
            'descriptiveMetadata': {
                'language': 'ENG'
            }
        }

        if 'identifier' in self.data and isinstance(self.data['identifier'], list):
            for identifier in self.data['identifier']:
                if identifier.get('propertyID') == 'RADAR':
                    radar_dict['id'] = identifier['value']

        if 'name' in self.data:
            radar_dict['descriptiveMetadata']['title'] = self.data['name']

        if 'dateModified' in self.data:
            production_year = datetime.strptime(self.data.get('dateModified'), '%Y-%m-%d')
            publish_date = datetime.strptime(self.data['dateModified'], '%Y-%m-%d')

            radar_dict['technicalMetadata']['publishDate'] = int(publish_date.timestamp())
            radar_dict['descriptiveMetadata']['productionYear'] = production_year.year
            radar_dict['descriptiveMetadata']['publicationYear'] = publish_date.year

        if 'sameAs' in self.data:
            radar_dict['descriptiveMetadata']['alternateIdentifiers'] = {
                'alternateIdentifier': []
            }
            radar_dict['descriptiveMetadata']['alternateIdentifiers']['alternateIdentifier'].append({
                'value': self.data['sameAs'],
                'alternateIdentifierType': 'URL'
            })

        if 'downloadUrl' in self.data:
            radar_dict['descriptiveMetadata']['alternateIdentifiers'] = {
                'alternateIdentifier': []
            }
            radar_dict['descriptiveMetadata']['alternateIdentifiers']['alternateIdentifier'].append({
                'value': self.data['downloadUrl'],
                'alternateIdentifierType': 'URL'
            })

        if any(key in self.data for key in ['referencePublication', 'codeRepository']):
            radar_dict['descriptiveMetadata']['relatedIdentifiers'] = {
                'relatedIdentifier': []
            }
            if 'referencePublication' in self.data and self.data['referencePublication'].get('@id', '').startswith(self.doi_prefix):
                radar_dict['descriptiveMetadata']['relatedIdentifiers']['relatedIdentifier'].append({
                    'value': self.data['referencePublication']['@id'].replace(self.doi_prefix, ''),
                    'relatedIdentifierType': 'DOI',
                    'relationType': self.radar_value('IsDocumentedBy')
                })
            if 'codeRepository' in self.data:
                radar_dict['descriptiveMetadata']['relatedIdentifiers']['relatedIdentifier'].append({
                    'value': self.data['codeRepository'],
                    'relatedIdentifierType': 'URL',
                    'relationType': self.radar_value('IsSupplementTo')  # like zenodo does it
                })

        if 'author' in self.data:
            radar_dict['descriptiveMetadata']['creators'] = {
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

                    radar_dict['descriptiveMetadata']['creators']['creator'].append(radar_creator)

        if 'contributors' in self.data:
            radar_dict['descriptiveMetadata']['contributors'] = {
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

                radar_dict['descriptiveMetadata']['contributors']['contributor'].append(radar_contributor)

        if 'alternateName' in self.data:
            radar_dict['descriptiveMetadata']['additionalTitles'] = {
                'additionalTitle': []
            }
            radar_dict['descriptiveMetadata']['additionalTitles']['additionalTitle'].append({
                'value': self.data['alternateName'],
                'additionalTitleType': self.radar_value('AlternativeTitle')
            })

        if 'description' in self.data:
            radar_dict['descriptiveMetadata']['descriptions'] = {
                'description': []
            }
            radar_dict['descriptiveMetadata']['descriptions']['description'].append({
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
                radar_dict['descriptiveMetadata']['keywords'] = {
                    'keyword': []
                }
                for keyword in keywords:
                    radar_dict['descriptiveMetadata']['keywords']['keyword'].append(keyword)

            if subjects:
                radar_dict['descriptiveMetadata']['subjectAreas'] = {
                    'subjectArea': []
                }
                for subject in subjects:
                    radar_dict['descriptiveMetadata']['subjectAreas']['subjectArea'].append({
                        'controlledSubjectAreaName': self.radar_value(subject)
                    })

        if 'publisher' in self.data and 'name' in self.data['publisher']:
            radar_dict['descriptiveMetadata']['publishers'] = {
                'publisher': [self.data['publisher']['name']]
            }

        if 'applicationCategory' in self.data:
            radar_dict['descriptiveMetadata']['resource'] = {
                'value': self.data['applicationCategory']
            }
            if self.data.get('@type') == 'SoftwareSourceCode':
                radar_dict['descriptiveMetadata']['resource']['resourceType'] = self.radar_value('Software')

        if 'license' in self.data:
            if isinstance(self.data['license'], str):
                radar_dict['descriptiveMetadata']['rights'] = {
                    'controlledRights': 'OTHER',
                    'additionalRights': self.data['license']
                }
            elif isinstance(self.data['license'], dict) and 'name' in self.data['license']:
                radar_dict['descriptiveMetadata']['rights'] = {
                    'controlledRights': 'OTHER',
                    'additionalRights': self.data['license']['name']
                }

        if 'copyrightHolder' in self.data and 'name' in self.data['copyrightHolder']:
            radar_dict['descriptiveMetadata']['rightsHolders'] = {
                'rightsHolder': [
                    self.data['copyrightHolder']['name']
                ]
            }
        else:
            radar_dict['descriptiveMetadata']['rightsHolders'] = {
                'rightsHolder': [
                    'The authors'
                ]
            }

        if 'funding' in self.data:
            radar_dict['descriptiveMetadata']['fundingReferences'] = {
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

                radar_dict['descriptiveMetadata']['fundingReferences']['fundingReference'].append(radar_funding_reference)

        logger.debug('radar_dict = %s', json.dumps(radar_dict, indent=2))
        return radar_dict
