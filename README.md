BatchUploadTools [![Build Status](https://travis-ci.org/lokal-profil/BatchUploadTools.svg?branch=master)](https://travis-ci.org/lokal-profil/BatchUploadTools)
=======

An attempt of unifying the various tools for batch uploads under one repo.

Heavily based on the [LSH](https://github.com/lokal-profil/LSH) repo


## To install

You can install `BatchUploadTools` via `pip` using:
`pip install git+https://github.com/lokal-profil/BatchUploadTools.git`

If it is your first time running pywikibot you will also have to set up a
`user-config.py` file.

## Running as a different user:

To run as a different user to your standard pywikibot simply place a
modified `user-config.py`-file in the top directory.

To use a different user for a particular batchupload place the `user-config.py`
in the subdirectory and run the script with `-dir:<sub-directory>`.

## When creating a new batch upload

Extend `make_info` to create own methods for reading and processing the indata.
Any method marked as abstract must be implemented locally. You can make use
of the various helper functions in the other classes.

If you are making use of mappings lists on Wikimedia Commons then create a
`MappingList` instance for each such list to manage the creation of the
mapping tables, the harvest of the tables when mapped and the preservation of
old mappings when new lists are needed for later uploads.

Alternatively you can make use of only the prep-uploader/uploader tools by
creating your own indata file. This must then be a json file where each media
file is represented by a dictionary entry with the *original filename* (without
the file extension) as the key and the following values:
 - `info`: the wikitext to be used on the description page (e.g. an information
   template)
 - `filename`: the filename to be used on Commons (without the file extension)
 - `cats`: a list of content categories (without "Category" prefix)
 - `meta_cats`: a list of meta categories (without "Category" prefix)

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
    - Input filename or url to file (as key)
4. Run the prep-uploader to rename the media files and create the text file
   for the associated file description page. \*
5. Run the uploader to upload it all

\* This step is not needed for _upload by url_.

## Using mapping lists
To generate new tables:

1. collect the data you wish mapped
2. create a `MappingList` instance
3. use `mappings_merger()` or `multi_table_mappings_merger` to combine the
   collected data with pre-existing data. (set `update=False` if there is no pre-existing data).
4. pass the result to `save_as_wikitext()`

To make use of the mapping list data:

1. create a `MappingList` instance
2. load the existing data using `load_old_mappings()`
3. pass the result to `consume_entries()`

## Post-upload processing
To make use of the post-upload processing tools use `import batchupload.postUpload`.

## Usage example:

For usage examples see [lokal-profil/upload_batches](https://github.com/lokal-profil/upload_batches).
In particular SMM-images.

## Handling upload errors

In most cases it is worth doing a second pass over any files which trigger an
error since it is either a temporary hick-up or the file was actually uploaded.
Below follows a list of of common errors and what to do about them (when known).

1. `stashedfilenotfound: Could not find the file in the stash.` Seems to
   primarilly be due to larger files. Solution: Manually upload this using
   Upload Wizard.
2. `stashfailed: This file contains HTML or script code that may be erroneously interpreted by a web browser.`
   Either you really have html tags in your exif data or you have triggered [T143610](https://phabricator.wikimedia.org/T143610).
   Smaller files can often be uploaded unchunked (slow).
3. `stashfailed: Cannot upload this file because Internet Explorer would detect it as "$1", which is a disallowed and potentially dangerous file type`
   No clue yet. See [T147720](https://phabricator.wikimedia.org/T147720)

## Something on SDC

...

## Something on runnign as stand-alone

...
