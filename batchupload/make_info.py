#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Abstract class for producing mapping tables and file description pages.

@TODO: add an entry point to make/update mappings
"""
from past.builtins import basestring
from builtins import dict, object
import batchupload.common as common
import batchupload.helpers as helpers
import os
import pywikibot
from abc import ABCMeta, abstractmethod
from future.utils import with_metaclass


def make_info_page(data):
    """
    Given a data entry from a make_info output, create a file description page.

    @param data: dict with the keys {cats, meta_cats, info, filename}
    @return: str
    """
    separator = u'\n\n'  # standard separation before categories
    txt = data['info']

    if data['meta_cats']:
        txt += separator
        txt += u'<!-- Metadata categories -->\n'
        for cat in data['meta_cats']:
            txt += u'[[Category:%s]]\n' % cat

    if data['cats']:
        txt += separator
        txt += u'<!-- Content categories -->\n'
        for cat in data['cats']:
            txt += u'[[Category:%s]]\n' % cat

    return txt


class MakeBaseInfo(with_metaclass(ABCMeta, object)):
    """Abstract class for generating descriptions and filenames for a batch."""

    def __init__(self, base_meta_cat, batch_label, **options):
        """
        Initialise a makeBaseInfo object.

        @param base_meta_cat: base_name for maintanance categories
        @param batch_label: label for this particular batch
        """
        self.data = dict()  # the processed metadata
        self.mappings = dict()  # any loaded mappings
        self.cwd_path = u''  # path to directory in which to work
        self.base_meta_cat = base_meta_cat
        self.batch_cat = self.make_maintanance_cat(batch_label)

    @abstractmethod
    def load_data(self, in_file):
        """
        Load the provided data and make suitable for input to process_data().

        The provided data can be in any format and include more than one file.
        The output format can likewise be anything which is accepted by
        process_data().

        @param in_file: the path to the metadata file or list of such paths
        """
        pass

    @abstractmethod
    def load_mappings(self, update=True):
        """
        Load the mapping files and package them appropriately.

        The loaded mappings are stored as self.mappings

        @param update: whether to first download the latest mappings
        """
        # should this actually carry code
        # improve docstring
        pass

    @abstractmethod
    def process_data(self, raw_data):
        """
        Process the output of load_data into a format usable by make_info().

        The processed data is stored in self.data, a dict of items or objects.

        @param raw_data: output from load_data()
        """
        pass

    @abstractmethod
    def make_info_template(self, item):
        """
        Make a filled in information (or similar) template for a single file.

        @param item: the metadata for the media file in question
        @return: str
        """
        pass

    @abstractmethod
    def generate_filename(self, item):
        """
        Produce a descriptive filename for a single media file.

        This method is responsible for identifying the components which
        should be passed through helpers.format_filename().

        @param item: the metadata for the media file in question
        @return: str
        """
        pass

    @abstractmethod
    def generate_content_cats(self, item):
        """
        Produce categories related to the media file contents.

        @param item: the metadata for the media file in question
        @return: list of categories (without "Category:" prefix)
        """
        pass

    @abstractmethod
    def generate_meta_cats(self, item, content_cats):
        """
        Produce maintanance categories related to a media file.

        @param item: the metadata for the media file in question
        @param content_cats: any content categories for the file
        @return: list of categories (without "Category:" prefix)
        """
        pass

    @abstractmethod
    def get_original_filename(self, item):
        """
        Return the original filename, without file extension, of a media file.

        This can either consist of returning a particular data field or require
        processing the metadata.

        @param item: the metadata for the media file in question
        @return: str
        """
        pass

    def make_maintanance_cat(self, cat):
        """
        Return a category name with the base_meta_cat prefix.

        @param cat: the string to prefix
        @return: str
        """
        return u'%s: %s' % (self.base_meta_cat, cat)

    def make_info(self):
        """
        Make an object containing the processed info related to a media file.

        The returned object is a dict where the keys are the (extension-less)
        original filenames and the values are:
        info: A filled in information (or similar) template
        filename: the filename to be used on Commons (without file extension)
        cats: a list of content categories (without "Category" prefix)
        meta_cats: a list of meta categories (without "Category" prefix)

        @return dict:
        """
        out_data = dict()
        for k, v in self.data.items():
            original_filename = self.get_original_filename(v)
            info = self.make_info_template(v)
            filename = self.generate_filename(v)
            cats = self.generate_content_cats(v)
            meta_cats = self.generate_meta_cats(v, cats)
            out_data[original_filename] = {
                u'info': info, u'filename': filename,
                u'cats': cats, u'meta_cats': meta_cats}
        return out_data

    def run(self, in_file, base_name=None):
        """
        Entry point for outputting info data.

        Loads indata and any mappings to produce a make_info json file.

        @param in_file: filename (or tuple of such) containing the metadata
        @param base_name: base name to use for output
            (defaults to same as in_file)
        """
        if not base_name:
            if isinstance(in_file, basestring):
                base_name, ext = os.path.splitext(in_file)
            else:
                raise common.MyError(
                    u'A base name must be provided if multiple in_files '
                    u'are provided')

        self.cwd_path = os.path.split(base_name)[0]
        raw_data = self.load_data(in_file)
        self.process_data(raw_data)
        self.load_mappings()
        out_data = self.make_info()

        # store output
        out_file = u'%s.json' % base_name
        common.open_and_write_file(out_file, out_data, as_json=True)
        pywikibot.output(u'Created %s' % out_file)

        # store filenames
        out_file = u'%s.filenames.txt' % base_name
        out = u''
        for k in sorted(out_data.keys()):
            out += u'%s|%s\n' % (k, out_data[k][u'filename'])
        common.open_and_write_file(out_file, out)
        pywikibot.output(u'Created %s' % out_file)

    @staticmethod
    def handle_args(args):
        """Parse and load all of the basic arguments.

        Also passes any needed arguments on to pywikibot and sets any defaults.

        @param args: arguments to be handled
        @type args: list of strings
        @return: list of options
        @rtype: dict
        """
        options = {
            'in_file': None,
            'base_name': None,
        }

        for arg in pywikibot.handle_args(args):
            option, sep, value = arg.partition(':')
            if option == '-in_file':
                options['in_file'] = helpers.convertFromCommandline(value)
            elif option == '-base_name':
                options['base_name'] = helpers.convertFromCommandline(value)

        return options

    @classmethod
    def main(cls, usage=None, *args):
        """Command line entry-point."""
        usage = usage or \
            u'Usage:' \
            u'\tpython make_info.py -in_file:PATH -dir:PATH\n' \
            u'\t-in_file:PATH path to metadata file\n' \
            u'\t-dir:PATH specifies the path to the directory containing a ' \
            u'user_config.py file (optional)\n' \
            u'\tExample:\n' \
            u'\tpython make_info.py -in_file:SMM/metadata.csv -dir:SMM\n'

        # Load pywikibot args and handle local args
        options = cls.handle_args(args)

        if options['in_file']:
            info = cls(**options)
            info.run(options['in_file'], options['base_name'])
        else:
            pywikibot.output(usage)


if __name__ == "__main__":
    MakeBaseInfo.main()
