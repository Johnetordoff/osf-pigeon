import requests
import os
import argparse
import logging
import settings
from zipfile import ZipFile
from IA.utils import (
    get_with_retry
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def main(guid, token, directory):
    path = os.path.join(directory, guid)

    zip_url = f'{settings.OSF_API_URL}v1/resources/{guid}/providers/osfstorage/?zip='

    try:
        os.mkdir(path)
    except FileExistsError:
        pass

    path = os.path.join(path, 'files')

    try:
        os.mkdir(path)
    except FileExistsError:
        pass

    if token:
        auth_header = {'Authorization': 'Bearer {}'.format(token)}
    else:
        auth_header = {}

    try:
        response = get_with_retry(zip_url.format(guid), headers=auth_header)
    except requests.exceptions.RequestException as e:
        logging.log(logging.ERROR, 'HTTP Request failed: {}'.format(e))
        raise

    zipfile_location = os.path.join(path, f'{guid}.zip')
    with open(zipfile_location, 'wb') as file:
        file.write(response.content)

    with ZipFile(zipfile_location, 'r') as zipObj:
        zipObj.extractall(path)

    os.remove(zipfile_location)
    print('File data successfully transferred!')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-g',
        '--guid',
        help='This is the GUID of the target node on the OSF',
        required=True
    )
    parser.add_argument(
        '-d',
        '--directory',
        help='This is the target Directory for the project and its files'
    )
    parser.add_argument(
        '-t',
        '--token',
        help='This is the bearer token for auth. This is required'
    )
    args = parser.parse_args()
    guid = args.guid
    directory = args.directory
    token = args.token

    if not directory:
        # Setting default to current directory
        directory = '.'

    main(guid, token, directory)
