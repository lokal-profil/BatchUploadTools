# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from setuptools import setup
version = '0.2.5'
repo = 'BatchUploadTools'

setup(
    name='BatchUploadTools',
    packages=['batchupload'],
    install_requires=[
        'future',
        'mwparserfromhell',
        'setuptools>50.0.0; python_version >= "3.6"',
        'pywikibot==5.4.0; python_version >= "3.6"',
        'pywikibot==3.0.20200703; python_version < "3.6"'
    ],
    version=version,
    description='Framework for mass-importing images to Wikimedia Commons.',
    author='André Costa',
    author_email='',
    url='https://github.com/lokal-profil/' + repo,
    download_url='https://github.com/lokal-profil/' + repo + '/tarball/' + version,
    keywords=['Wikimedia Commons', 'Wikimedia', 'Commons', 'pywikibot', 'API'],
    classifiers=[
        'Programming Language :: Python :: 2.7'
        'Programming Language :: Python :: 3.6'
        'Programming Language :: Python :: 3.7'
    ],
)
