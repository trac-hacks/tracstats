#!/usr/bin/python3

import os.path
from setuptools import setup

# Utility function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = 'TracStats',
    version = '0.7.0',
    description = "A Trac plugin for project statistics",
    long_description = read('README.md'),
    author = "John Benediktsson, Drik Stöcker",
    author_email = 'trac@dstoecker.de',
    url = "https://github.com/trac-hacks/tracstats",
    download_url = "https://github.com/trac-hacks/tracstats/zipball/master#egg=TracStats-0.6.1",
    packages=['tracstats'],
    classifiers = [
        "Development Status :: 4 - Beta",
        "Framework :: Trac",
        "License :: OSI Approved :: BSD License",
    ],
    package_data={
        'tracstats': [
            'htdocs/*.css',
            'htdocs/*.png',
            'htdocs/*.gif',
            'htdocs/*.js',
            'templates/*.html'
        ]
    },
    entry_points = {
        'trac.plugins': [
            'tracstats.web_ui = tracstats.web_ui',
        ]
    },
    dependency_links = ['http://github.com/trac-hacks/tracstats/zipball/master#egg=TracStats-0.6.1']
)
