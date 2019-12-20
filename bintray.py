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
    commit = os.getenv('TRAVIS_COMMIT')
    branch = os.getenv('TRAVIS_BRANCH')
    timefmt = '%Y%m%d%H%m'
    timestr = time.strftime(timefmt)
    version = '{time}-{branch}-{commit}'.format(
        time=timestr, branch=branch, commit=commit)

    # build artifact name
    name = '{}-{}'.format(args.package, version)

    # build url for upload
    bintray = 'https://api.bintray.com/content'
    url = '{api}/{user}/{repo}/{package}/{version}/{name}?publish=1'.format(
        api=bintray, user=args.user, repo=args.repo, package=args.package, version=version, name=name)

    # get API key from environment variable
    key = os.getenv('BINTRAY_KEY')

    # setup the file to be uploaded
    file = {'file': open(args.file, 'rb')}

    # upload to Bintray
    print('Uploading file {} to Bintray via POST request...'.format(name))
    r = requests.put(url, files=file, auth=(args.user, key))

    print('Response: {}'.format(r.text))

    # raise an exception if request resulted in a bad status code
    r.raise_for_status()


if __name__ == "__main__":
    main()
