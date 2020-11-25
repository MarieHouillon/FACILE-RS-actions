import logging

import requests

logger = logging.getLogger(__file__)


def fetch_radar_token(radar_url, client_id, client_secret, redirect_url, username, password):
    url = radar_url + '/radar/api/tokens'
    try:
        response = requests.post(url, json={
            'clientId': client_id,
            'clientSecret': client_secret,
            'redirectUrl': redirect_url,
            'userName': username,
            'userPassword': password
        })
        response.raise_for_status()
        logger.debug('response = %s', response.json())
    except requests.exceptions.HTTPError as e:
        print(response.text)
        raise e

    tokens = response.json()
    return {
        'Authorization': 'Bearer {}'.format(tokens['access_token'])
    }


def create_radar_dataset(radar_url, workspace_id, headers, radar_json):
    url = radar_url + '/radar/api/workspaces/{}/datasets'.format(workspace_id)
    try:
        response = requests.post(url, headers=headers, json=radar_json)
        response.raise_for_status()
        logger.debug('response = %s', response.json())
        return response.json()['id']
    except requests.exceptions.HTTPError as e:
        print(response.text)
        raise e


def upload_radar_assets(radar_url, dataset_id, headers, assets, path):
    url = radar_url + '/radar-ingest/upload/{}/file'.format(dataset_id)
    for location in assets:
        target = path / location.split('/')[-1]
        files = {'upload_file': open(target, 'rb')}

        try:
            response = requests.post(url, files=files, headers=headers)
            response.raise_for_status()
            logger.debug('response = %s', response.text)
        except requests.exceptions.HTTPError as e:
            print(response.text)
            raise e
