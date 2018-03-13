# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from setuptools import setup
version = '0.2.2'
repo = 'BatchUploadTools'

setup(
    name='BatchUploadTools',
    packages=['batchupload'],
    install_requires=['pywikibot==3.0-dev', 'future', 'mwparserfromhell'],
    dependency_links=['git+https://github.com/wikimedia/pywikibot-core.git#egg=pywikibot-3.0-dev'],
    version=version,
    description='Framework for mass-importing images to Wikimedia Commons.',
    author='André Costa',
    author_email='',
    url='https://github.com/lokal-profil/' + repo,
    download_url='https://github.com/lokal-profil/' + repo + '/tarball/' + version,
    keywords=['Wikimedia Commons', 'Wikimedia', 'Commons', 'pywikibot', 'API'],
    classifiers=[
        'Programming Language :: Python :: 2.7'
        'Programming Language :: Python :: 3.4'
    ],
)
