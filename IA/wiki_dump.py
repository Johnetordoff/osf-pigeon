import os
import math
import asyncio
import requests
import argparse
from ratelimit import sleep_and_retry
from ratelimit.exception import RateLimitException
from settings import SLEEP_PERIOD, OSF_API_URL

HERE = os.path.dirname(os.path.abspath(__file__))


class WikiDumpError(Exception):
    pass


@sleep_and_retry
def get_with_retry(url):
    resp = requests.get(url)
    if resp.status_code in (429, 500, 503):
        raise RateLimitException(
            message='Too many requests, sleeping.',
            period_remaining=SLEEP_PERIOD
        )  # This will be caught by @sleep_and_retry and retried

    return resp.json()


@sleep_and_retry
async def get_wiki_pages(guid, page, result={}):
    url = f'{OSF_API_URL}v2/registrations/{guid}/wikis/?page={page}'
    resp = requests.get(url)
    if resp.status_code in (429, 500, 503):
        raise RateLimitException(
            message='Too many requests, sleeping.',
            period_remaining=SLEEP_PERIOD
        )  # This will be caught by @sleep_and_retry and retried

    result[page] = requests.get(url).json()['data']
    return result


@sleep_and_retry
async def write_wiki_content(page):
    resp = requests.get(page['links']['download'])
    if resp.status_code in (429, 500, 503):
        raise RateLimitException(
            message='Too many requests, sleeping.',
            period_remaining=SLEEP_PERIOD
        )  # This will be caught by @sleep_and_retry and retried

    with open(os.path.join(HERE, f'/{page["attributes"]["name"]}.md'), 'wb') as fp:
        fp.write(resp.content)


async def main(guid):
    """
    Usually asynchronous requests/writes are reserved for times when it's truely necessary, but
    given the fact that we have like 4 days left in the sprint and this going to be the first
    py3 thing in the repo, I've decided to whip out the big guns and concurrently gather all
    wiki pages simultaneously (except for the first one) and then stream them all to local
    files simultaneously just because it's easy to do with py3 and will save a nano-second or two.

    :param guid:
    :return:
    """

    url = f'{OSF_API_URL}v2/registrations/{guid}/wikis/?page=1'
    tasks = []

    data = get_with_retry(url)
    result = {1: data['data']}

    if data['links']['next'] is not None:
        pages = math.ceil(int(data['meta']['total']) / int(data['meta']['per_page']))
        for i in range(1, pages):
            task = get_wiki_pages(guid, i + 1, result)
            tasks.append(task)

    await asyncio.gather(*tasks)
    pages_as_list = []
    # through the magic of async all our pages have loaded.
    for page in list(result.values()):
        pages_as_list += page

    write_tasks = []
    for page in pages_as_list:
        write_tasks.append(write_wiki_content(page))

    await asyncio.gather(*write_tasks)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-id',
        '--guid',
        help='The guid of the registration if who\'s wiki you want to dump.',
        required=True
    )
    args = parser.parse_args()

    guid = args.guid
    asyncio.run(main(guid))
