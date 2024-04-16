import json
import pytest
from os import path

from facile_rs.utils.metadata import CodemetaMetadata

# Get current script location
SCRIPT_DIR = path.dirname(path.realpath(__file__))

class TestCodemeta:
    metadata = CodemetaMetadata()

    def test_fetch(self):
        """Test fetching a JSON CodeMeta file
        """
        self.metadata.fetch(path.join(SCRIPT_DIR, 'codemeta_test.json'))
        with open(path.join(SCRIPT_DIR, 'codemeta_test.json')) as f:
            assert json.load(f) == self.metadata.data

    def test_fetch_authors(self):
        """Test fetching authors from multiple files containing duplicates.
        """
        self.metadata.fetch(path.join(SCRIPT_DIR, 'codemeta_test.json'))
        self.metadata.fetch_authors([
            path.join(SCRIPT_DIR, 'codemeta_test.json'),
            path.join(SCRIPT_DIR, 'authors_test.json')
            ])
        with open(path.join(SCRIPT_DIR, 'authors_test.json')) as f:
            for author in json.load(f)['author']:
                assert author in self.metadata.data['author']

    def test_fetch_contributors(self):
        """Test fetching contributors when initial dataset contains a unique contributor
        """
        self.metadata.fetch(path.join(SCRIPT_DIR, 'codemeta_test.json'))
        self.metadata.fetch_contributors([path.join(SCRIPT_DIR, 'contributors_test.json')])
        with open(path.join(SCRIPT_DIR, 'contributors_test.json')) as f:
            for contributor in json.load(f)['contributor']:
                print(contributor)
                print(self.metadata.data['contributor'])
                assert contributor in self.metadata.data['contributor']

    def test_compute_names(self):
        self.metadata.data = {
            'author': [
                {'@type': 'Person', 'familyName': 'Author', 'givenName': 'One'}
            ],
            'contributor': [
                {'@type': 'Person', 'name': 'O Contributor', 'familyName': 'Contributor', 'givenName': 'One'},
                {'@id': 'http://orcid.org/9999-9999-9999-9999', '@type': 'Person',
                 'email': 'another.contributor@example.com',
                 'familyName': 'Contributor', 'givenName': 'Another'}
            ]
        }
        self.metadata.compute_names()
        # 'name' field doesn't exist
        assert self.metadata.data['author'][0]['name'] == 'One Author'
        assert self.metadata.data['contributor'][1]['name'] == 'Another Contributor'
        # 'name' field already exists and shouldn't be overwritten
        assert self.metadata.data['contributor'][0]['name'] == 'O Contributor'

    def test_remove_doubles(self):
        self.metadata.data = {
            'author': [
                # Entries with same 'name' are considered duplicates
                {'@type': 'Person', 'name': 'One Author', 'email': 'oa@kit.edu'},
                {'@type': 'Person', 'name': 'One Author', 'email': 'oauthor@kit.edu'},
                {'@type': 'Person', 'familyName': 'Author', 'givenName': 'One', 'email': 'oa@kit.edu'}
            ],
            'contributor': [
                # Entries with same '@id' are considered duplicates
                {'@type': 'Person', 'familyName': 'Author', 'givenName': 'One', '@id': 'http://orcid.org/9999-9999-9999-9999'},
                {'@type': 'Person', 'familyName': 'Author', 'givenName': 'O', '@id': 'http://orcid.org/9999-9999-9999-9999'},
            ]
        }
        self.metadata.remove_doubles()
        expected_result = {
            'author': [
                {'@type': 'Person', 'name': 'One Author', 'email': 'oa@kit.edu'},
                {'@type': 'Person', 'familyName': 'Author', 'givenName': 'One', 'email': 'oa@kit.edu'}
            ],
            'contributor': [
                {'@type': 'Person', 'familyName': 'Author', 'givenName': 'One', '@id': 'http://orcid.org/9999-9999-9999-9999'}
            ]
        }
        assert self.metadata.data == expected_result

    def test_sort_persons(self):
        for key in ['author', 'contributor']:
            self.metadata.data[key] = [
                    {'@type': 'Person', 'name': 'Firstname Lastname'},
                    {'@type': 'Person', 'familyName': 'Author', 'givenName': 'One', 'email': 'oa@kit.edu'},
                    {'@type': 'Organization', 'name': 'First organization', 'additionalType': 'anotherType'},
                    {'@type': 'Organization', 'name': 'Zyx organization'},
                    {'@type': 'Organization', 'name': 'Another organization'}
                ]
        self.metadata.sort_persons()
        expected_result = {}
        for key in ['author', 'contributor']:
            expected_result[key] = [
                    # Organizations first...
                    {'@type': 'Organization', 'name': 'Another organization'},
                    {'@type': 'Organization', 'name': 'Zyx organization'},
                    {'@type': 'Person', 'familyName': 'Author', 'givenName': 'One', 'email': 'oa@kit.edu'},
                    {'@type': 'Person', 'name': 'Firstname Lastname'},
                    # ... Unless they have an additionalType
                    {'@type': 'Organization', 'name': 'First organization', 'additionalType': 'anotherType'},
                ]
        assert expected_result == self.metadata.data
