#!/usr/bin/env python

from setuptools import setup, find_packages

PACKAGE = 'TracStats'
VERSION = '0.2'

setup(
    name=PACKAGE, version=VERSION,
    description="A plugin for project statistics",
    packages=find_packages(exclude=['ez_setup', '*.tests*']),
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
    }
)

