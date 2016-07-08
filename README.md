BatchUploadTools
=======

An attempt of unifying the various tools for batch uploads under one repo.

Heavily based on the [LSH](https://github.com/lokal-profil/LSH) repo


## Running as a different user:

To run as a different user to your standard pywikibot simply place a
modified `user-config.py`-file in the top directory.

To use a different user for a particular batchupload place the `user-config.py`
in the subdirectory and run the script with `-dir:<sub-driectory>`.
Remember to set `password_file = "<sub-driectory>/secretPasswords"` in the
`user-config`.
