from setuptools import setup
version = '0.0.1'
repo = 'BatchUploadTools'

setup(
    name='BatchUploadTools',
    packages=['batchupload'],
    install_requires=['pywikibot==3.0-dev'],
    dependency_links=['git+https://github.com/wikimedia/pywikibot-core.git#egg=pywikibot-3.0-dev'],
    version=version,
    description='Framework for mass-importing images to Wikimedia Commons.',
    author='Andre Costa',
    author_email='',
    url='https://github.com/lokal-profil/' + repo,
    download_url='https://github.com/lokal-profil/' + repo + '/tarball/' + version,
    keywords=['Wikimedia Commons', 'Wikimedia', 'Commons', 'pywikibot', 'API'],
    classifiers=[],
)
