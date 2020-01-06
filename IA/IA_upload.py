import os
import argparse
import asyncio
from settings import (
    OSF_COLLECTION_NAME,
    IA_ACCESS_KEY,
    IA_SECRET_KEY,
)
from internetarchive import upload as IA_upload

async_IA_upload = asyncio.coroutine(IA_upload)

HERE = os.path.dirname(os.path.abspath(__file__))


async def gather_and_upload(bucket_name: str, parent: str):
    '''
    This script traverses through a directory uploading everything in it to Internet Archive.
    '''

    tasks = []

    directory_path = os.path.join(HERE, parent)
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            path = os.path.join(root, file)
            task = async_IA_upload(
                bucket_name,
                files=[path],
                access_key=IA_ACCESS_KEY,
                secret_key=IA_SECRET_KEY,
                headers={'x-archive-meta01-collection': OSF_COLLECTION_NAME}
            )
            tasks.append(task)

    await asyncio.gather(*tasks)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-b',
        '--bucket',
        help='The name of the bucket you want to dump in.',
        required=True,
    )
    parser.add_argument(
        '-s',
        '--source',
        help='The name of the folder you want to dump.',
        required=True,
    )
    args = parser.parse_args()
    bucket = args.bucket
    source = args.source

    asyncio.run(gather_and_upload(bucket, source))
