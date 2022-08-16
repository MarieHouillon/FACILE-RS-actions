import logging

from ..http import fetch_dict

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
            if key in self.data:
                for thing in self.data[key]:
                    if 'name' not in thing and ('givenName' in thing and 'familyName' in thing):
                        thing['name'] = '{} {}'.format(thing['givenName'], thing['familyName'])

    def remove_doubles(self):
        for key in ['author', 'contributor']:
            if key in self.data:
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

        if 'author' in self.data:
            self.data['author'] = sorted(self.data['author'], key=get_key)
        if 'contributor' in self.data:
            self.data['contributor'] = sorted(self.data['contributor'], key=get_key)
