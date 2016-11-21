BatchUploadTools [![Build Status](https://travis-ci.org/lokal-profil/BatchUploadTools.svg?branch=master)](https://travis-ci.org/lokal-profil/BatchUploadTools)
=======

An attempt of unifying the various tools for batch uploads under one repo.

Heavily based on the [LSH](https://github.com/lokal-profil/LSH) repo


## Running as a different user:

To run as a different user to your standard pywikibot simply place a
modified `user-config.py`-file in the top directory.

To use a different user for a particular batchupload place the `user-config.py`
in the subdirectory and run the script with `-dir:<sub-directory>`.

## Protocol for a batch upload
1. Load indata to a dictionary
2. Process the indata to generate mapping lists
3. Load the indata and the mappings to produce a list of original filenames
   (of media files) and their final filenames as well as json holding the
   following for each file:
    - Maintenance categories
    - Content categories
    - File description
    - Output filename
    - Input filename (as key)
4. Run the prep-uploader to rename the media files and create the text file
   for the associated file description page.
5. Run the uploader to upload it all

## When creating a new batch upload
Extend make_info to create own methods for reading and processing the indata.
Any method marked as abstract must be implemented locally. You can make use
of the various helper functions in the other classes.

