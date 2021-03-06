#!/usr/bin/env python3

"""bintray.py: Upload files to Bintray"""

__author__ = "Cameron McQuinn"
__copyright__ = "Copyright 2019, Cameron McQuinn"
__email__ = "cameron.mcquinn@gmail.com"

import requests
import argparse
import subprocess
import os
import time
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('user', help='Bintray user name')
    parser.add_argument('repo', help='Bintray repo to upload to', type=str)
    parser.add_argument('package', help='Name of package on Bintray', type=str)
    parser.add_argument(
        'file', help='Path to the file to be uploaded to Bintray', type=str)
    args = parser.parse_args()

    # build version string and append to url
    result = subprocess.run('git rev-parse --short HEAD'.split(), stdout=subprocess.PIPE, encoding='UTF-8')
    commit = result.stdout.strip() # get short commit hash from output of git rev-parse
    result = subprocess.run('git rev-parse --abbrev-ref HEAD'.split(), stdout=subprocess.PIPE, encoding='UTF-8')
    branch = os.getenv('TRAVIS_BRANCH') if os.getenv('TRAVIS') else result.stdout.strip() # get branch name
    timefmt = '%Y%m%d%H%m'
    timestr = time.strftime(timefmt)
    version = '{time}-{branch}-{commit}'.format(
        time=timestr, branch=branch, commit=commit)

    # build artifact name
    name = '{}-{}'.format(args.package, version)

    # append file extension to name
    for ext in args.file.split('.')[1:]:
        name = name + '.' + ext

    # build url for upload
    bintray = 'https://api.bintray.com/content'
    url = '{api}/{user}/{repo}/{name}'.format(
        api=bintray, user=args.user, repo=args.repo, name=name)

    # get API key from environment variable
    key = os.getenv('BINTRAY_KEY')

    # build header
    header = {
        'X-Bintray-Package': args.package,
        'X-Bintray-Version': version,
        'X-Bintray-Publish': '1',
        'X-Bintray-Override': '1'
    }

    # upload to Bintray
    print('Uploading file {} to Bintray via POST request...'.format(name))
    with open(args.file, 'rb') as fp:
        r = requests.put(url, headers=header, data=fp, auth=(args.user, key))

    print('Response: {}'.format(r.text))

    # raise an exception if request resulted in a bad status code
    r.raise_for_status()


if __name__ == "__main__":
    main()
