import os
import asyncio
import json
import mock
from mock import call
import unittest
import responses
from nose.tools import assert_equal
from IA.IA_wiki_dump import main

HERE = os.path.dirname(os.path.abspath(__file__))


def wiki_metadata():
    with open(os.path.join(HERE, 'fixtures/wiki-metadata-response.json'), 'r') as fp:
        return json.loads(fp.read())


def wiki_metadata_two_pages():
    with open(os.path.join(HERE, 'fixtures/wiki-metadata-response-page-1.json'), 'r') as fp:
        page1 = json.loads(fp.read())

    with open(os.path.join(HERE, 'fixtures/wiki-metadata-response-page-2.json'), 'r') as fp:
        page2 = json.loads(fp.read())

    return page1, page2


class TestWikiDumper(unittest.TestCase):

    @responses.activate
    def test_wiki_dump(self):
        responses.add(
            responses.Response(
                responses.GET,
                'https://localhost:8000/v2/registrations/fxehm/wikis/',
                json=wiki_metadata(),
            )
        )
        responses.add(
            responses.Response(
                responses.GET,
                'https://localhost:8000/v2/wikis/dtns3/content/',
                body=b'dtns3 data',
            ),
        )
        responses.add(
            responses.Response(
                responses.GET,
                'https://localhost:8000/v2/wikis/md549/content/',
                body=b'md549 data',
            ),
        )
        responses.add(
            responses.Response(
                responses.GET,
                'https://localhost:8000/v2/wikis/p8kxa/content/',
                body=b'p8kxa data',
            ),
        )

        with mock.patch('builtins.open', mock.mock_open()) as m:
            asyncio.run(main('fxehm'))
            assert m.call_args_list == [
                call('/home.md', 'wb'),
                call('/test1Ω≈ç√∫˜µ≤≥≥÷åß∂ƒ©˙∆∆˚¬…æ.md', 'wb'),
                call('/test2.md', 'wb')
            ]
            handle = m()

            assert handle.write.call_args_list == [
                call(b'dtns3 data'),
                call(b'md549 data'),
                call(b'p8kxa data')
            ]

    @responses.activate
    def test_wiki_dump_retry(self):
        responses.add(
            responses.Response(
                responses.GET,
                'https://localhost:8000/v2/registrations/fxehm/wikis/',
                status=429,
                headers={'Retry-After': '1'},
            )
        )
        responses.add(
            responses.Response(
                responses.GET,
                'https://localhost:8000/v2/registrations/fxehm/wikis/',
                json=wiki_metadata(),
            )
        )
        responses.add(
            responses.Response(
                responses.GET,
                'https://localhost:8000/v2/wikis/dtns3/content/',
                body=b'dtns3 data',
            ),
        )
        responses.add(
            responses.Response(
                responses.GET,
                'https://localhost:8000/v2/wikis/md549/content/',
                body=b'md549 data',
            ),
        )
        responses.add(
            responses.Response(
                responses.GET,
                'https://localhost:8000/v2/wikis/p8kxa/content/',
                body=b'p8kxa data',
            ),
        )

        with mock.patch('builtins.open', mock.mock_open()) as m:
            asyncio.run(main('fxehm'))
            assert m.call_args_list == [
                call('/home.md', 'wb'),
                call('/test1Ω≈ç√∫˜µ≤≥≥÷åß∂ƒ©˙∆∆˚¬…æ.md', 'wb'),
                call('/test2.md', 'wb')
            ]
            handle = m()

            assert handle.write.call_args_list == [
                call(b'dtns3 data'),
                call(b'md549 data'),
                call(b'p8kxa data')
            ]

    @responses.activate
    def test_wiki_dump_multiple_pages(self):
        page1, page2 = wiki_metadata_two_pages()
        responses.add(
            responses.Response(
                responses.GET,
                'https://localhost:8000/v2/registrations/fxehm/wikis/',
                json=page1,
                match_querystring=True,
            )
        )
        responses.add(
            responses.Response(
                responses.GET,
                'https://localhost:8000/v2/registrations/fxehm/wikis/?page=2',
                json=page2,
                match_querystring=True,
            )
        )

        data = page1['data'] + page2['data']
        for wiki in data:
            responses.add(
                responses.Response(
                    responses.GET,
                    f'https://localhost:8000/v2/wikis{wiki["attributes"]["path"]}/content/',
                    body=f'{wiki["attributes"]["path"]} data',
                ),
            )

        with mock.patch('builtins.open', mock.mock_open()) as m:
            asyncio.run(main('fxehm'))
            assert_equal(
                m.call_args_list,
                [call(f'/{wiki["attributes"]["name"]}.md', 'wb') for wiki in data]
            )

            handle = m()
            assert_equal(
                handle.write.call_args_list,
                [call(f'{wiki["attributes"]["path"]} data'.encode()) for wiki in data]
            )
