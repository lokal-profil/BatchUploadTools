#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Toolkit for creating, scraping and combining (wikitext) mapping lists."""
from __future__ import unicode_literals
from builtins import dict
from collections import OrderedDict
import os
import pywikibot
import batchupload.common as common
import batchupload.helpers as helpers

OUT_PATH = 'connections'


class MappingEntry(dict):
    """
    A single entry in a mapping list.

    This is simply a wrapper for a dict to allow for hashing.
    """

    def __init__(self, *args, **kwargs):
        """Initialise as a dict. Values may only be strings or lists."""
        super(MappingEntry, self).__init__(self, *args, **kwargs)

    def __hash__(self):
        """Implement hash to allow for e.g. sorting and sets."""
        return hash(
            frozenset(
                (k, MappingEntry.hash_if_list(v))
                for k, v in self.items()))

    @staticmethod
    def hash_if_list(val):
        """Convert lists to frozensets, return rest."""
        if isinstance(val, list):
            return frozenset(val)
        return val


class MappingList(object):
    """Template based wikitext list for mapping concepts to wiki entries."""

    def __init__(self, page, parameters, header_template=None,
                 row_template_name='User:André Costa (WMSE)/mapping-row',
                 site=None, mapping_dir=None, wikitext_dir=None, options=None):
        """
        Initialise an mapping list.

        @param page: name of page (incl. prefixes) where list (should) live.
        @param parameters: a list of mapping keys in data to use as parameters
            or an OrderedDict with {data key: template parameter} pairs.
        @param header_template: the header template (incl. any parameters) and
            "{{ }}".
        @param row_template_name: the name of the row template.
            (Default: User:André Costa (WMSE)/mapping-row)
        @param mapping_dir: Directory in which to save scraped mappings.
            (Default: OUT_PATH)
        @param wikitext_dir: Directory in which to save created wikitext
            mapping lists. (Default: OUT_PATH)
        @param site: pywikibot.Site on which the page lives.
            (Default: Wikimedia Commons)
        @param options: dict of overriding option settings.
        """
        self.options = self.set_options(options)
        self.page_name = page.rpartition('/')[2]
        self.page = MappingList.construct_page(site, page)
        self.header_template = header_template
        self.row_template = row_template_name
        self.mapping_dir = mapping_dir or OUT_PATH
        self.wikitext_dir = wikitext_dir or OUT_PATH

        # store as dict internally for uniform handling
        if isinstance(parameters, list):
            self.parameters = OrderedDict([(k, k) for k in parameters])
        else:
            self.parameters = parameters

        # create out_paths if they don't exist
        common.create_dir(self.mapping_dir)
        common.create_dir(self.wikitext_dir)

    # @todo: add default_parameters
    # @tood: revisit where these are passed between functions and this could be
    #        dropped. Keeping them as args where used could be relevant for
    #        testing.
    def set_options(self, overriding_options):
        """
        Set various options to default or override in initialisation.

        @param overriding_options: dict of options to use instead of default
            values.
        """
        overriding_options = overriding_options or {}

        # default options
        options = {
            # the value used to indicate that a mapping is not applicable or
            # not needed (as opposed to being left unmapped).
            'na_value': '-',
            # delimiter used to separate list values.
            'list_delimiter': '/',
            # key in the mapping entry to be used for name and secondary
            # sorting. Cannot be a multi-valued (list) field.
            'name_key': 'name',
            # key in the mapping entry to be used for frequency.
            'freq_key': 'frequency'
        }

        for k, v in overriding_options.items():
            if k in options:
                options[k] = v
            else:
                raise common.MyError('{} is not a recognised option'.format(k))

        return options

    @staticmethod
    def construct_page(site, page):
        """
        Construct the Page object containing the list.

        @param page: name of page (incl. prefixes) where list (should) live.
        @param site: pywikibot.Site on which the page lives (Def:
            Wikimedia Commons)
        """
        site = site or pywikibot.Site('commons', 'commons')
        return pywikibot.Page(site, title=page)

    def scrape(self):
        """
        Scrape lists on commons and overwrite local files.

        If the page does not exist a warning is raised and no file is created.
        """
        if not self.page.exists():
            pywikibot.warning(
                'The list page {} does not exist!'.format(self.page.title()))
        else:
            parsed_data = self.parse_entries(self.page.get())
            mapping_file = os.path.join(
                self.mapping_dir, 'commons-{}.json'.format(self.page_name))
            common.open_and_write_file(mapping_file, parsed_data, as_json=True)
            pywikibot.output('Created {}'.format(mapping_file))

    # @todo: move defaults to set_options? Re-use in make_entry
    # @todo: Combine defaults somehow with self.parameters
    def parse_entries(self, contents, default_params=None, list_delimiter='/'):
        """
        Return a list of all parameters for instances of a given template.

        Values are returned in the same format as their default values
        (a string or a list of strings).
        If the corresponding default value is a list then "/" (or another
        specified list_delimiter) in parameter values are interpreted as a
        separator for list entries.

        "<small>"-tags are striped from the input.

        @param content: wikicode
        @param default_params: dict of expected params and their default
            values. Values must be either strings or lists.
        @param list_delimiter: delimiter used as separator for list entries.
            Defaults to '/'.
        @return: list of MappingEntry
        """
        default_params = default_params or {
            'name': '',
            'more': '',
            'frequency': '',
            'technique': [],
            'creator': '',
            'wikidata': '',
            'link': '',
            'category': [],
            'other': ''}

        entries = helpers.get_all_template_entries(contents, self.row_template)
        units = []
        for entry in entries:
            params = default_params.copy()
            for key, value in entry.items():
                # @todo: consider dropping this or moving to entry cleaner
                value = value.replace('<small>', '').replace('</small>', '')
                value = value.strip()  # in case of empty <small>-tags
                if not value:
                    continue
                if key in params:
                    if isinstance(params[key], list):
                        params[key] = [v.strip()
                                       for v in value.split(list_delimiter)]
                    else:
                        params[key] = value
                else:
                    pywikibot.output(
                        'Unrecognised parameter: {} = {}'.format(key, value))
            unit = MappingEntry(**params.copy())
            if unit not in units:
                # remove identical duplicates
                units.append(unit)
        return units

    def load_old_mappings(self, update=False):
        """
        Load and return any locally stored old mappings.

        @param update: update any local old mappings by retrieving scraping
            online pages.
        """
        if update:
            self.scrape()

        old_mapping = []
        mapping_file = os.path.join(
            self.mapping_dir, 'commons-{}.json'.format(self.page_name))
        if os.path.exists(mapping_file):
            loaded = common.open_and_read_file(mapping_file, as_json=True)
            # convert dict to MappingEntry
            old_mapping = [MappingEntry(**entry) for entry in loaded]
        return old_mapping

    def save_as_wikitext(self, new_data, preserved_data=None, intro_text=''):
        """
        Output mapping lists in wiki format.

        @param new_data: the new (non-zero frequency) mapping data as a list of
            (frequency, mapping entry) tuples. Or a dict of such lists where
            the key is used as a section title.
        @param preserved_data: the preserved (zero frequency) mapping data as
            a list of mapping entries.
        @param intro_text: Wikitext to top the page with (may also contain
            categories)
        """
        wiki_file = os.path.join(
            self.wikitext_dir, 'commons-{}.wiki'.format(self.page_name))
        wiki_text = self.mappings_to_wikipage(
            new_data, preserved_data, intro_text)
        common.open_and_write_file(wiki_file, wiki_text)

    def mappings_merger(self, need_mapping, name_key='name',
                        freq_key='frequency', update=False):
        """
        Output mapping lists in wiki format, merging with any existing.

        @param need_mapping: list of (object, frequency) tuples. The object is
            either a string (used as name) or a dict or OrderedDict where
            name_key is used for name and other values are interpreted as
            template values. For a Counter send most_common().
        @param name_key: key in the passed object used for name. Cannot be a
            multi-valued (list) field. (Default: "name")
        @param freq_key: key in the passed object used for frequency.
            (Default: "frequency")
        @param update: update any local old mappings by scraping online pages.
        @return: (new_mappings, preserved_mappings) tuple where the first is a
            list of (frequency, mapping entry) tuples and the second a list of
            mapping entries.
        """
        old_mapping = self.load_old_mappings(update)

        # reset frequency and turn into dict
        previous = dict()
        for entry in old_mapping:
            key = entry[name_key]
            if not common.is_str(key):
                raise ValueError('name_key must correspond to a string value '
                                 'not a "{}"'.format(type(key).__name__))
            entry[freq_key] = 0
            previous[key] = entry  # since these are all lists

        # add frequency + any new objects
        new_mapping = []
        for entry, freq in need_mapping:
            if common.is_str(entry):
                name = entry
                entry = None
            else:
                name = entry.pop(name_key)

            if name in previous:
                new_entry = MappingList.make_entry(
                    name, entry, freq, previous[name], name_key, freq_key)
                del previous[name]
            else:
                new_entry = MappingList.make_entry(
                    name, entry, freq, None, name_key, freq_key)

            new_mapping.append((freq, new_entry))

        # preserve any remaining mappings
        preserved = []
        for k, v in previous.items():
            entry = MappingList.make_entry(k, None, 0, v, name_key, freq_key)
            if entry:
                # trim any old entries without mapped data
                preserved.append(entry)

        return new_mapping, preserved

    def multi_table_mappings_merger(self, need_mapping,
                                    name_key='name', update=False):
        """
        Output multiple mapping lists, merged with any existing mappings.

        Used when dumping multiple lists to one page where each type is dumped
        as a separate table.

        A known issue is that the harvester treats these as one list and so
        deals badly with the same entry appearing in multiple lists.
        The safest solution is to not mix different lists on a page.

        @param need_mapping: an OrderedDict where the key is used as a table
            header and the value must be a Counter.
        @param name_key: key in the passed object used for name. Cannot be a
            multi-valued (list) field. (Default: "name")
        @param update: update any local old mappings by scraping online pages.
        @return: (new_mappings, preserved_mappings) tuple where the first is
            an OrderedDict of lists of (frequency, mapping entry) tuples and
            the second a list of mapping entries.
        """
        merged_data = OrderedDict()
        preserved_data = {}
        for key in sorted(need_mapping.keys()):
            merged_entries, preserved_entries = self.mappings_merger(
                need_mapping.get(key).most_common(), name_key=name_key,
                update=update)
            update = False  # only update first time (if at all)
            merged_data[key] = merged_entries

            # combine entries to only keep those which are still unused
            preserved_keys = [entry.get(name_key)
                              for entry in preserved_entries]
            if not preserved_data:
                # first time around
                preserved_data = {entry.get(name_key): entry
                                  for entry in preserved_entries}
            for key in list(preserved_data.keys()):
                if key not in preserved_keys:
                    del preserved_data[key]

        return merged_data, list(preserved_data.values())

    # @todo: should re-use default_params, and these should respect
    #        name_key, freq_key.
    # @todo: name_key, freq_key should be stored instead of passed
    @staticmethod
    def make_entry(name, entry, frequency, previous=None, name_key='name',
                   freq_key='frequency'):
        """
        Create a list entry in the relevant format.

        It is either created from scratch or by reusing mappings.
        @param name: the name associated with an entry
        @param entry: data for the entry
        @param frequency: frequency of the entry
        @param previous: previous mapping for the entry
        @param name_key: key in the passed object used for name. Cannot be a
            multi-valued (list) field. (Default: "name")
        @param freq_key: key in the passed object used for frequency.
            (Default: "frequency")
        @return: MappingEntry
        """
        if frequency > 0:
            if not entry:
                if previous:
                    previous[freq_key] = frequency
                    return previous
                else:
                    return {
                        'name': name,
                        'more': '',
                        'frequency': frequency,
                        'technique': [],
                        'creator': '',
                        'wikidata': '',
                        'link': '',
                        'category': [],
                        'other': ''
                    }
            else:
                entry[name_key] = name
                entry[freq_key] = frequency
                if previous:
                    for k, v in previous.items():
                        entry[k] = entry.get(k) or v  # add but don't overwrite
                return MappingEntry(**entry)

        if previous:
            for k, v in previous.items():
                # if any entry is non-empty
                if v and k not in (name_key, freq_key):
                    return previous

    def mappings_to_wikipage(self, new_data, preserved_data=None,
                             intro_text='', header_template=None,
                             row_template_name=None):
        """
        Output mappings as a wikipage.

        @param new_data: the new (non-zero frequency) mapping data as a list of
            (frequency, mapping entry) tuples. Or a dict of such lists where
            the key is used as a section title.
        @param preserved_data: the preserved (zero frequency) mapping data as
            a list of mapping entries.
        @param intro_text: Wikitext to top the page with (may also contain
            categories)
        @param header_template: the header template (incl. any parameters) and
            "{{ }}".
        @param row_template_name: the name of the row template
        """
        # to side-step the need for a header template use an empty string
        preserved_data = preserved_data or []
        wiki = '{}\n'.format(intro_text)

        # output new data
        if isinstance(new_data, dict):
            for title, data in new_data.items():
                if not data:
                    continue
                wiki += u'\n==={}===\n'.format(title)
                wiki += self.mapping_to_table(
                    data, header_template, row_template_name)
        elif new_data:
            wiki += self.mapping_to_table(
                new_data, header_template, row_template_name)

        # output preserved mappings (if any)
        if preserved_data:
            preserved_data_w_freqs = [(0, entry) for entry in preserved_data]
            wiki += u'\n===Preserved mappings===\n'
            wiki += self.mapping_to_table(
                preserved_data_w_freqs, header_template, row_template_name)

        return wiki.strip()

    # @todo: secondary_sort_key = name_key used in make_entry
    def mapping_to_table(self, data, header_template=None,
                         row_template_name=None, secondary_sort_key=None):
        """
        Output a mapping dataset as a wikitable.

        The secondary sort key is used to reduce the amount of re-arranging
        caused in the preserved mappings.

        @param new_data: mapping data as a list of (frequency, mapping entry)
            tuples.
        @param header_template: the header template (incl. any parameters) and
            "{{ }}".
        @param row_template_name: the name of the row template
        @param secondary_sort_key: the key in the mapping_entry to use for
            (reverse) sorting when frequencies are tied. Overrides the default
            name_key option.
        """
        header_template = header_template or self.header_template
        secondary_sort_key = secondary_sort_key or self.options.get('name_key')
        if header_template is None:
            raise pywikibot.Error(
                "A header template is necessary for outputting as a wikipage.")
        footer = u'|}\n'

        if secondary_sort_key:
            data.sort(reverse=True,
                      key=lambda x: (x[0], x[1].get(secondary_sort_key)))
        else:
            data.sort(reverse=True, key=lambda x: x[0])

        table_body = ''
        for freq, entry in data:
            table_body += '{}\n'.format(
                self.make_list_row(entry, template=row_template_name))
        return '{head}\n{body}{foot}'.format(
            head=header_template, body=table_body, foot=footer)

    def make_list_row(self, data, template=None, delimiter='/'):
        """
        Create the list template for a single mapping entry.

        @param data: the mapping data for a single entry
        @param template: the row template to use
        @param delimiter: delimiter to use for lists
        @return: str
        """
        template_data = OrderedDict()
        template = template or self.row_template

        for data_key, template_key in self.parameters.items():
            data_val = data.get(data_key)
            if isinstance(data_val, (set, list)):
                data_val = delimiter.join(data_val)
            elif data_val is None:
                data_val = ''
            template_data[template_key] = data_val
        return helpers.output_block_template(template, template_data, 0)

    def consume_entries(self, units, key_val, require=None, only=None):
        """
        Clean a scraped mapping list and return as a dict.

        If the field used as dict key is empty or non-unique a warning is raise
        and that entry skipped.

        @param units: a list of entry-dict items as returned by parse_entries
        @param key_val: the name of the field to use as dict key.
        @param require: a field or list of fields where at least one must be
            non-empty for the entry to be presented.
            Default: None = all entries returned.
        @param only: only return the value of this field
        """
        if require:
            require = common.listify(require)  # allow both single str and list

        presentable_units = {}
        for entry in units:
            clean_entry = self.clean_entry(entry)
            if require and not any(clean_entry.get(r) for r in require):
                continue

            key = clean_entry.get(key_val)
            if not key:
                pywikibot.warning('The field intended as dict key was empty!')
                continue
            elif key in presentable_units:
                # @todo: this should compare values and keep any with content
                # and only warn if two have differing content
                pywikibot.warning('The dict key was not unique! - {}'.format(
                    key))
                continue

            if only:
                presentable_units[key] = clean_entry.get(only)
            else:
                presentable_units[key] = clean_entry

        return presentable_units

    def clean_entry(self, entry):
        """
        Clean the entry-dict items of table formatting unrelated to real data.

        Note that they are not safe to convert back to wikitable after this.
        """
        for key, value in entry.items():
            if isinstance(value, list):
                value = [v.replace('{{!}}', '|') for v in value]
                value = list(
                    filter(lambda x: x != self.options.get('na_value'), value))
            else:
                value = value.replace('{{!}}', '|')
                if value == self.options.get('na_value'):
                    value = ''
            entry[key] = value

        return entry


# @todo: consider optionally tying this in already at the parsing step
#        that way a roundtrip would enrich a list.
def get_wikidata_info(qid, site=None, cache=None):
    """
    Query Wikidata for additional info about a list entry with a qid.

    If a cache is provided this is used to reduce the number
    of lookups.

    Death year is looked up to assist with Public Domain logic.

    @param qid: Qid for the Wikidata item
    @param site: pywikibot.Site object for Wikidata
    @param cache: dict to use for caching
    @return: bool
    """
    wikidata = site or pywikibot.Site('wikidata', 'wikidata')
    # cannot use cache = cache or {} as this also discards an empty cache
    if cache is None:
        cache = {}

    if qid in cache:
        return cache[qid]

    item = pywikibot.ItemPage(wikidata, qid)
    if not item.exists():
        cache[qid] = {}
    else:
        commonscat = return_first_claim(item, 'P373')
        creator = return_first_claim(item, 'P1472')
        death_year = return_first_claim(item, 'P570')
        if death_year:
            death_year = death_year.year
        cache[qid] = {
            'commonscat': commonscat,
            'creator': creator,
            'death_year': death_year
        }

    return cache[qid]


def return_first_claim(item, prop):
    """Return the first claim of a Wikidata item for a given property."""
    claims = item.claims.get(prop)
    if claims:
        return claims[0].target
