#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for listscraper.py."""
from __future__ import unicode_literals
import unittest
import mock
import pywikibot
from collections import Counter, OrderedDict
from batchupload.listscraper import MappingList


class TestMappingListBase(unittest.TestCase):

    """Base mocks used for MappingList tests."""

    def setUp(self):
        construct_page_patcher = mock.patch(
            'batchupload.listscraper.MappingList.construct_page')
        self.mock_construct_page = construct_page_patcher.start()
        self.mock_construct_page.return_value = 'pwb.Page'
        self.addCleanup(construct_page_patcher.stop)

        create_dir_patcher = mock.patch(
            'batchupload.listscraper.common.create_dir')
        self.mock_create_dir = create_dir_patcher.start()
        self.addCleanup(create_dir_patcher.stop)


class TestMappingListInit(TestMappingListBase):

    """Test the __init__ method."""

    def test_init_all_args(self):
        ml = MappingList(
            page='prefix/page_name',
            parameters=['A', 'b'],
            header_template='{{header_t}}',
            row_template_name='row_t',
            site='a site',
            mapping_dir='a dir',
            wikitext_dir='b dir',
        )
        self.mock_create_dir.assert_has_calls([
            mock.call('a dir'),
            mock.call('b dir')
        ])
        self.mock_construct_page.assert_called_once_with(
            'a site', 'prefix/page_name')
        self.assertEquals(ml.page_name, 'page_name')
        self.assertEquals(ml.page, 'pwb.Page')
        self.assertEquals(
            ml.parameters,
            OrderedDict([('A', 'A'), ('b', 'b')])
        )
        self.assertEquals(ml.header_template, '{{header_t}}')
        self.assertEquals(ml.row_template, 'row_t')

    def test_init_dict_parameters(self):
        ml = MappingList(
            page='prefix/page_name',
            parameters=OrderedDict([('A', 'A'), ('B', 'b')]),
            row_template_name='row_t'
        )
        self.assertEquals(
            ml.parameters,
            OrderedDict([('A', 'A'), ('B', 'b')])
        )

    def test_init_default_row(self):
        ml = MappingList(
            page='prefix/page_name',
            parameters=['A', 'b']
        )
        self.assertEquals(
            ml.row_template,
            'User:André Costa (WMSE)/mapping-row'
        )


class TestMappingListBaseWithList(TestMappingListBase):

    """Base setup for MappingList instance method tests."""

    def setUp(self):
        super(TestMappingListBaseWithList, self).setUp()

        self.mapping_list = MappingList(
            page='prefix/page_name',
            parameters=['A'],
            header_template='{{header_t}}',
            row_template_name='row_t'
        )


class TestParseEntries(TestMappingListBaseWithList):

    """Test the parse_entries method."""

    def test_parse_entries_no_content(self):
        self.assertEqual(self.mapping_list.parse_entries(''), [])


class TestMakeListRow(TestMappingListBaseWithList):

    """Test the make_list_row method."""

    def setUp(self):
        super(TestMakeListRow, self).setUp()
        self.data = {
            'A': 'A value',
            'B': ['B', 'b'],
            'C': '',
            'E': 'E value'
        }
        self.expected_output = 'block_template'
        self.default_template = 'row_t'

        output_template_patcher = mock.patch(
            'batchupload.listscraper.helpers.output_block_template')
        self.mock_output_template = output_template_patcher.start()
        self.mock_output_template.return_value = self.expected_output
        self.addCleanup(output_template_patcher.stop)

    def test_make_list_row_no_data(self):
        self.mapping_list.parameters = OrderedDict()

        self.assertEquals(
            self.mapping_list.make_list_row({}),
            self.expected_output)
        self.mock_output_template.assert_called_once_with(
            self.default_template, {}, 0)

    def test_make_list_row_parameter_dict(self):
        self.mapping_list.parameters = OrderedDict([
            ('B', 'E'), ('C', 'C'), ('D', 'D'), ('A', 'A')
        ])
        self.expected_data = OrderedDict([
            ('E', 'B/b'), ('C', ''), ('D', ''), ('A', 'A value')
        ])

        self.assertEquals(
            self.mapping_list.make_list_row(self.data),
            self.expected_output)
        self.mock_output_template.assert_called_once_with(
            self.default_template, self.expected_data, 0)

    def test_make_list_row_row_template(self):
        self.mapping_list.parameters = OrderedDict()

        self.assertEquals(
            self.mapping_list.make_list_row({}, template='foo'),
            self.expected_output)
        self.mock_output_template.assert_called_once_with(
            'foo', {}, 0)

    def test_make_list_row_delimiter(self):
        self.mapping_list.parameters = OrderedDict([('B', 'B')])
        self.expected_data = OrderedDict([('B', 'B;b')])

        self.assertEquals(
            self.mapping_list.make_list_row(self.data, delimiter=';'),
            self.expected_output)
        self.mock_output_template.assert_called_once_with(
            self.default_template, self.expected_data, 0)


class TestMappingToTable(TestMappingListBaseWithList):

    """Test the mapping_to_table method."""

    def setUp(self):
        super(TestMappingToTable, self).setUp()

        row_patcher = mock.patch(
            'batchupload.listscraper.MappingList.make_list_row')
        self.mock_make_row = row_patcher.start()
        self.mock_make_row.return_value = 'row'
        self.addCleanup(row_patcher.stop)

    def test_mapping_to_table_no_data(self):
        self.mapping_list.parameters = OrderedDict()

        self.assertEquals(
            self.mapping_list.mapping_to_table([]),
            '{{header_t}}\n|}\n')
        self.mock_make_row.assert_not_called()

    def test_mapping_to_table_basic(self):
        # self.mapping_list.parameters = ['A']
        data = [
            (2, {'A': 'a'}),
            (1, {'A': 'b'}),
            (4, {'A': 'c'})
        ]
        expected_output = (
            '{{header_t}}\n'
            'row\nrow\nrow\n'
            '|}\n'
        )

        self.assertEquals(
            self.mapping_list.mapping_to_table(data),
            expected_output)
        # order of calls reflects the underlying sorting
        self.mock_make_row.assert_has_calls([
            mock.call({'A': 'c'}, template=None),
            mock.call({'A': 'a'}, template=None),
            mock.call({'A': 'b'}, template=None)
        ])

    def test_mapping_to_table_same_frequency_no_secondary(self):
        # self.mapping_list.parameters = ['A']
        data = [
            (0, {'A': 'a'}),
            (0, {'A': 'b'})
        ]
        expected_output = (
            '{{header_t}}\n'
            'row\nrow\n'
            '|}\n'
        )

        try:
            self.assertEquals(
                self.mapping_list.mapping_to_table(data),
                expected_output)
            self.mock_make_row.assert_has_calls([
                mock.call({'A': 'a'}, template=None),
                mock.call({'A': 'b'}, template=None)
            ], any_order=True)
        except TypeError:
            self.fail("mappings_to_wikipage() raised TypeError unexpectedly!")

    def test_mapping_to_table_same_frequency_default_secondary(self):
        # self.mapping_list.parameters = ['A']
        self.mapping_list.options['name_key'] = 'A'
        data = [
            (0, {'A': 'a'}),
            (0, {'A': 'b'})
        ]
        expected_output = (
            '{{header_t}}\n'
            'row\nrow\n'
            '|}\n'
        )

        try:
            self.assertEquals(
                self.mapping_list.mapping_to_table(data),
                expected_output)
            self.mock_make_row.assert_has_calls([
                mock.call({'A': 'b'}, template=None),
                mock.call({'A': 'a'}, template=None)
            ], any_order=True)
        except TypeError:
            self.fail("mappings_to_wikipage() raised TypeError unexpectedly!")

    def test_mapping_to_table_same_frequency_override_secondary(self):
        # self.mapping_list.parameters = ['A']
        data = [
            (0, {'A': 'a'}),
            (0, {'A': 'b'})
        ]
        expected_output = (
            '{{header_t}}\n'
            'row\nrow\n'
            '|}\n'
        )

        try:
            self.assertEquals(
                self.mapping_list.mapping_to_table(
                    data, secondary_sort_key='A'),
                expected_output)
            self.mock_make_row.assert_has_calls([
                mock.call({'A': 'b'}, template=None),
                mock.call({'A': 'a'}, template=None)
            ], any_order=True)
        except TypeError:
            self.fail("mappings_to_wikipage() raised TypeError unexpectedly!")

    def test_mapping_to_table_error_on_no_header(self):
        self.mapping_list.header_template = None
        expected_error = (
            "A header template is necessary for outputting as a wikipage.")

        with self.assertRaises(pywikibot.Error) as cm:
            self.mapping_list.mapping_to_table([], '')
        self.assertEqual(
            str(cm.exception),
            expected_error
        )


class TestMappingsToWikipage(TestMappingListBaseWithList):

    """Test the mappings_to_wikipage method."""

    def setUp(self):
        super(TestMappingsToWikipage, self).setUp()
        self.new_data = [
            (2, {'A': 'a'}),
            (1, {'A': 'b'}),
            (4, {'A': 'c'})
        ]

        table_patcher = mock.patch(
            'batchupload.listscraper.MappingList.mapping_to_table')
        self.mock_make_table = table_patcher.start()
        self.mock_make_table.return_value = 'table'
        self.addCleanup(table_patcher.stop)

    def test_mappings_to_wikipage_no_data(self):
        self.mapping_list.parameters = OrderedDict()

        self.assertEquals(
            self.mapping_list.mappings_to_wikipage([]), '')
        self.mock_make_table.assert_not_called()

    def test_mappings_to_wikipage_basic(self):
        # self.mapping_list.parameters = ['A']
        expected_output = 'intro\ntable'

        self.assertEquals(
            self.mapping_list.mappings_to_wikipage(
                self.new_data, intro_text='intro'),
            expected_output)
        self.mock_make_table.assert_called_with(self.new_data, None, None)

    def test_mappings_to_wikipage_dict(self):
        # self.mapping_list.parameters = ['A']
        new_data = OrderedDict()
        new_data['foo'] = [
            (1, {'A': 'a'}),
            (2, {'A': 'b'})]
        new_data['bar'] = [(4, {'A': 'c'})]
        expected_output = (
            'intro\n'
            '\n===foo===\n'
            'table'
            '\n===bar===\n'
            'table'
        )

        self.assertEquals(
            self.mapping_list.mappings_to_wikipage(
                new_data, intro_text='intro'),
            expected_output)
        self.mock_make_table.assert_has_calls([
            mock.call(new_data['foo'], None, None),
            mock.call(new_data['bar'], None, None)
        ])

    def test_mappings_to_wikipage_preserved(self):
        preserved_data = [{'A': 'd'}]
        # self.mapping_list.parameters = ['A']
        expected_output = (
            'intro\n'
            'table'
            '\n===Preserved mappings===\n'
            'table'
        )

        self.assertEquals(
            self.mapping_list.mappings_to_wikipage(
                self.new_data, preserved_data, 'intro'),
            expected_output)
        self.mock_make_table.assert_has_calls([
            mock.call(self.new_data, None, None),
            mock.call([(0, {'A': 'd'})], None, None)
        ])

    def test_mappings_to_wikipage_override_templates(self):
        # self.mapping_list.parameters = ['A']
        expected_output = 'table'

        self.assertEquals(
            self.mapping_list.mappings_to_wikipage(
                self.new_data, header_template='{{header}}',
                row_template_name='row_template'),
            expected_output)
        self.mock_make_table.assert_called_with(
            self.new_data, '{{header}}', 'row_template')

    def test_mappings_to_wikipage_allow_empty_string_header(self):
        self.mapping_list.header_template = ""

        try:
            self.mapping_list.mappings_to_wikipage([], '')
        except pywikibot.Error:
            self.fail("mappings_to_wikipage() raised Error unexpectedly!")


class TestMappingsMerger(TestMappingListBaseWithList):

    """Test the mappings_merger method."""

    def setUp(self):
        super(TestMappingsMerger, self).setUp()
        self.data = [
            ({'A': 'a'}, 2),
            ({'A': 'b'}, 1),
            ({'A': 'c'}, 4)
        ]

        get_old_patcher = mock.patch(
            'batchupload.listscraper.MappingList.load_old_mappings')
        self.mock_get_old = get_old_patcher.start()
        self.mock_get_old.return_value = []
        self.addCleanup(get_old_patcher.stop)

        make_entry_patcher = mock.patch(
            'batchupload.listscraper.MappingList.make_entry')
        self.mock_make_entry = make_entry_patcher.start()
        self.mock_make_entry.return_value = 'entry'
        self.addCleanup(make_entry_patcher.stop)

    def test_mappings_merger_no_data(self):
        self.assertEquals(
            self.mapping_list.mappings_merger([]),
            ([], []))
        self.mock_get_old.assert_called_once()
        self.mock_make_entry.assert_not_called()

    def test_mappings_merger_list(self):
        data = [
            ('a', 2),
            ('b', 3),
            ('c', 1)
        ]

        self.assertEquals(
            self.mapping_list.mappings_merger(data),
            ([(2, 'entry'), (3, 'entry'), (1, 'entry')],
             [])
        )
        self.mock_get_old.assert_called_once()
        self.mock_make_entry.assert_has_calls([
            mock.call('a', None, 2, None, 'name', 'frequency'),
            mock.call('b', None, 3, None, 'name', 'frequency'),
            mock.call('c', None, 1, None, 'name', 'frequency')
        ])

    def test_mappings_merger_dict(self):
        data = [
            ({'name': 'a', 'foo': 'b'}, 2),
            ({'name': 'b'}, 3),
            ({'name': 'c'}, 1)
        ]

        self.assertEquals(
            self.mapping_list.mappings_merger(data),
            ([(2, 'entry'), (3, 'entry'), (1, 'entry')],
             [])
        )
        self.mock_get_old.assert_called_once()
        self.mock_make_entry.assert_has_calls([
            mock.call('a', {'foo': 'b'}, 2, None, 'name', 'frequency'),
            mock.call('b', {}, 3, None, 'name', 'frequency'),
            mock.call('c', {}, 1, None, 'name', 'frequency')
        ])

    def test_merge_old_and_new_counter_compatibility(self):
        counter = Counter(a=2, b=3, c=1)
        data = counter.most_common()

        self.assertEquals(
            self.mapping_list.mappings_merger(data),
            ([(3, 'entry'), (2, 'entry'), (1, 'entry')],
             [])
        )
        self.mock_get_old.assert_called_once()
        self.mock_make_entry.assert_has_calls([
            mock.call('b', None, 3, None, 'name', 'frequency'),
            mock.call('a', None, 2, None, 'name', 'frequency'),
            mock.call('c', None, 1, None, 'name', 'frequency')
        ])

    def test_mappings_merger_with_old(self):
        self.mock_get_old.return_value = [
            {'name': 'a', 'frequency': 2, 'foo': 'barA'},
            {'name': 'b', 'frequency': 3, 'foo': 'barB'},
            {'name': 'd', 'frequency': 4, 'foo': 'barD'},
            {'name': 'e', 'frequency': 5}
        ]
        data = [
            ('a', 2),
            ('b', 3),
            ('c', 1)
        ]

        self.assertEquals(
            self.mapping_list.mappings_merger(data),
            ([(2, 'entry'), (3, 'entry'), (1, 'entry')],
             ['entry', 'entry'])
        )
        self.mock_get_old.assert_called_once()
        self.mock_make_entry.assert_has_calls([
            mock.call('a', None, 2,
                      {'name': 'a', 'frequency': 0,  'foo': 'barA'},
                      'name', 'frequency'),
            mock.call('b', None, 3,
                      {'name': 'b', 'frequency': 0, 'foo': 'barB'},
                      'name', 'frequency'),
            mock.call('c', None, 1, None, 'name', 'frequency'),
            mock.call('d', None, 0,
                      {'name': 'd', 'frequency': 0, 'foo': 'barD'},
                      'name', 'frequency'),
            mock.call('e', None, 0, {'name': 'e', 'frequency': 0},
                      'name', 'frequency')
        ], any_order=True)  # order of 0 frequency entries is not guaranteed

    def test_mappings_merger_dict_override_keys(self):
        data = [
            ({'name': 'a', 'foo': 'b'}, 2),
            ({'foo': 'b'}, 3),
            ({'foo': 'c'}, 1)
        ]
        self.mock_get_old.return_value = [
            {'freq': 2, 'foo': 'd'}]

        self.assertEquals(
            self.mapping_list.mappings_merger(
                data, name_key='foo', freq_key='freq'),
            ([(2, 'entry'), (3, 'entry'), (1, 'entry')],
             ['entry'])
        )
        self.mock_get_old.assert_called_once()
        self.mock_make_entry.assert_has_calls([
            mock.call('b', {'name': 'a'}, 2, None, 'foo', 'freq'),
            mock.call('b', {}, 3, None, 'foo', 'freq'),
            mock.call('c', {}, 1, None, 'foo', 'freq'),
            mock.call('d', None, 0, {'freq': 0, 'foo': 'd'}, 'foo', 'freq')
        ])

    def test_mappings_merger_name_not_str(self):
        data = []
        self.mock_get_old.return_value = [
            {'name': '', 'frequency': 2, 'foo': ['barA']}]
        expected_error = (
            'name_key must correspond to a string value not a "list"')

        with self.assertRaises(ValueError) as cm:
            self.mapping_list.mappings_merger(data, name_key='foo')
        self.assertEqual(
            str(cm.exception),
            expected_error
        )

    def test_mappings_merger_with_empty_string(self):
        self.mock_get_old.return_value = [
            {'name': '', 'frequency': 2, 'foo': 'barA'}]
        data = [('', 2)]

        self.assertEquals(
            self.mapping_list.mappings_merger(data),
            ([(2, 'entry')],
             [])
        )
        self.mock_get_old.assert_called_once()
        self.mock_make_entry.assert_called_once_with(
            '', None, 2, {'name': '', 'frequency': 0,  'foo': 'barA'},
            'name', 'frequency')

    def test_mappings_merger_trim_preserved_without_data(self):
        self.mock_get_old.return_value = [{'name': 'b', 'frequency': 3}]
        self.mock_make_entry.return_value = None
        data = []

        self.assertEquals(
            self.mapping_list.mappings_merger(data),
            ([], [])
        )
        self.mock_get_old.assert_called_once()
        self.mock_make_entry.assert_called_once_with(
            'b', None, 0, {'name': 'b', 'frequency': 0},
            'name', 'frequency')


class TestMultiTableMappingsMerger(TestMappingListBaseWithList):

    """Test the multi_table_mappings_merger method."""

    def setUp(self):
        super(TestMultiTableMappingsMerger, self).setUp()
        self.data = OrderedDict([
            ('first', Counter(a=2, b=3, c=1)),
            ('second', Counter(d=2)),
            ('third', Counter(f=5)),
        ])

        self.merger_returns = None  # override per test
        mappings_merger_patcher = mock.patch(
            'batchupload.listscraper.MappingList.mappings_merger')
        self.mock_mappings_merger = mappings_merger_patcher.start()
        self.mock_mappings_merger.side_effect = self.mock_merger_returns
        self.addCleanup(mappings_merger_patcher.stop)

    def mock_merger_returns(self, *args, **kwargs):
        """Mock mappings_merger returns by returning from a list"""
        return self.merger_returns.pop(0)

    def test_multi_table_mappings_merger_no_data(self):
        self.assertEquals(
            self.mapping_list.multi_table_mappings_merger(OrderedDict()),
            (OrderedDict(), []))
        self.mock_mappings_merger.assert_not_called()

    def test_multi_table_mappings_merger_no_old(self):
        self.merger_returns = [
            ('wikitext_first', []),
            ('wikitext_second', []),
            ('wikitext_third', []),
        ]
        self.assertEquals(
            self.mapping_list.multi_table_mappings_merger(self.data),
            (OrderedDict([
                ('first', 'wikitext_first'),
                ('second', 'wikitext_second'),
                ('third', 'wikitext_third')]),
            [])
        )
        self.mock_mappings_merger.assert_has_calls([
            mock.call([('b', 3), ('a', 2), ('c', 1)], name_key='name', update=False),
            mock.call([('d', 2)], name_key='name', update=False),
            mock.call([('f', 5)], name_key='name', update=False)
        ])

    def test_multi_table_mappings_merger_check_flags(self):
        self.merger_returns = [
            ('wikitext_first', []),
            ('wikitext_second', []),
            ('wikitext_third', []),
        ]
        self.assertEquals(
            self.mapping_list.multi_table_mappings_merger(
                self.data, name_key='foo', update=True),
            (OrderedDict([
                ('first', 'wikitext_first'),
                ('second', 'wikitext_second'),
                ('third', 'wikitext_third')]),
            [])
        )
        self.mock_mappings_merger.assert_has_calls([
            mock.call([('b', 3), ('a', 2), ('c', 1)], name_key='foo', update=True),
            mock.call([('d', 2)], name_key='foo', update=False),
            mock.call([('f', 5)], name_key='foo', update=False)
        ])

    def test_multi_table_mappings_merger_handle_preserved(self):
        # initial old: c-f only e should be left
        self.merger_returns = [
            ('wikitext_first', [{'foo':'d'}, {'foo':'e'}, {'foo':'f'}]),
            ('wikitext_second', [ {'foo':'c'}, {'foo':'e'}, {'foo':'f'}]),
            ('wikitext_third', [{'foo':'c'}, {'foo':'d'}, {'foo':'e'}]),
        ]
        self.assertEquals(
            self.mapping_list.multi_table_mappings_merger(
                self.data, name_key='foo', update=True),
            (OrderedDict([
                ('first', 'wikitext_first'),
                ('second', 'wikitext_second'),
                ('third', 'wikitext_third')]),
            [{'foo': 'e'}])
        )
        self.mock_mappings_merger.assert_has_calls([
            mock.call([('b', 3), ('a', 2), ('c', 1)], name_key='foo', update=True),
            mock.call([('d', 2)], name_key='foo', update=False),
            mock.call([('f', 5)], name_key='foo', update=False)
        ])


class TestMakeEntry(unittest.TestCase):

    """Test the make_entry method."""

    def setUp(self):
        self.base_format = {
            'name': '',
            'more': '',
            'frequency': 0,
            'technique': [],
            'creator': '',
            'wikidata': '',
            'link': '',
            'category': [],
            'other': ''
        }

    def test_make_entry_empty(self):
        result = MappingList.make_entry('a name', None, 0, None)
        self.assertEquals(
            result,
            None
        )

    def test_make_entry_new_no_entry(self):
        entry = None
        previous = None
        expected = self.base_format
        expected['name'] = 'a name'
        expected['frequency'] = 2

        result = MappingList.make_entry('a name', entry, 2, previous)
        self.assertEquals(result, expected)

    def test_make_entry_new_with_entry(self):
        entry = {'more': 'foo', 'bar': 'foobar'}
        previous = None
        expected = {
            'name': 'a name',
            'more': 'foo',
            'bar': 'foobar',
            'frequency': 2
        }

        result = MappingList.make_entry('a name', entry, 2, previous)
        self.assertEquals(result, expected)

    def test_make_entry_new_with_previous_no_entry(self):
        entry = None
        previous = {'name': 'a name', 'frequency': 0,
                    'more': 'foo', 'bar': 'foobar'}
        expected = {
            'name': 'a name',
            'more': 'foo',
            'bar': 'foobar',
            'frequency': 2
        }

        result = MappingList.make_entry('a name', entry, 2, previous)
        self.assertEquals(result, expected)

    def test_make_entry_new_with_previous_and_entry(self):
        entry = {'more': 'foo'}
        previous = {'name': 'a name', 'frequency': 0, 'bar': 'foobar'}
        expected = {
            'name': 'a name',
            'more': 'foo',
            'bar': 'foobar',
            'frequency': 2
        }

        result = MappingList.make_entry('a name', entry, 2, previous)
        self.assertEquals(result, expected)

    def test_make_entry_new_no_frequency_with_previous(self):
        entry = None
        previous = {'name': 'a name', 'frequency': 0, 'bar': 'foobar'}
        expected = {
            'name': 'a name',
            'bar': 'foobar',
            'frequency': 0
        }

        result = MappingList.make_entry('a name', entry, 0, previous)
        self.assertEquals(result, expected)

    def test_make_entry_new_no_frequency_with_previous_no_value(self):
        entry = None
        previous = {'name': 'a name', 'frequency': 0}
        expected = None

        result = MappingList.make_entry('a name', entry, 0, previous)
        self.assertEquals(result, expected)


class TestCleanEntry(TestMappingListBaseWithList):

    """Test the clean_entry method."""

    def test_clean_entry_no_data(self):
        self.assertEquals(self.mapping_list.clean_entry({}), {})

    def test_clean_entry_escaped_pipe(self):
        entry = {
            'str': '[[foo{{!}}bar]]',
            'list': [
                'foo',
                '[[foo{{!}}bar]]'
                ]
        }
        expect = {
            'str': '[[foo|bar]]',
            'list': [
                'foo',
                '[[foo|bar]]'
                ]
        }
        self.assertEquals(self.mapping_list.clean_entry(entry), expect)

    def test_clean_entry_na_value(self):
        entry = {
            'str_1': '-',
            'str_2': 'foo',
            'list': [
                'foo',
                '-'
                ]
        }
        expect = {
            'str_1': '',
            'str_2': 'foo',
            'list': [
                'foo'
                ]
        }
        self.assertEquals(self.mapping_list.clean_entry(entry), expect)


class TestConsumeEntries(TestMappingListBaseWithList):

    """Test the consume_entries method."""

    def setUp(self):
        super(TestConsumeEntries, self).setUp()

        patcher = mock.patch(
            'batchupload.listscraper.MappingList.clean_entry')
        self.mock_clean_entry = patcher.start()
        self.mock_clean_entry.side_effect = lambda x: x  # bounce the value
        self.addCleanup(patcher.stop)

        patcher = mock.patch(
            'batchupload.listscraper.pywikibot.warning')
        self.mock_warning = patcher.start()
        self.addCleanup(patcher.stop)

    def test_consume_entries_no_data(self):
        self.assertEquals(
            self.mapping_list.consume_entries([], ''), {})
        self.mock_clean_entry.assert_not_called()

    def test_consume_entries_basic(self):
        data = [
            {'key': 'a', 'val': 'b'},
            {'key': 'c', 'val': 'd'}
        ]
        expect = {
            'a': {'key': 'a', 'val': 'b'},
            'c': {'key': 'c', 'val': 'd'}
        }

        self.assertEquals(
            self.mapping_list.consume_entries(data, 'key'), expect)
        self.mock_clean_entry.assert_has_calls([
            mock.call({'key': 'a', 'val': 'b'}),
            mock.call({'key': 'c', 'val': 'd'})
        ])
        self.mock_warning.assert_not_called()

    def test_consume_entries_only(self):
        data = [
            {'key': 'a', 'val': 'b', 'foo': 'bar'},
            {'key': 'c', 'val': 'd', 'foo': 'bar'}
        ]
        expect = {
            'a': 'b',
            'c': 'd'
        }

        self.assertEquals(
            self.mapping_list.consume_entries(data, 'key', only='val'), expect)

    def test_consume_entries_require_str(self):
        data = [
            {'key': 'a', 'val': 'b', 'foo': 'bar'},
            {'key': 'c', 'val': 'd'}
        ]
        expect = {
            'a': {'key': 'a', 'val': 'b', 'foo': 'bar'}
        }

        self.assertEquals(
            self.mapping_list.consume_entries(data, 'key', require='foo'),
            expect)

    def test_consume_entries_require_list(self):
        data = [
            {'key': 'a', 'val': 'b', 'foo': 'A'},
            {'key': 'c', 'val': 'd', 'bar': 'B'},
            {'key': 'e', 'val': 'f', 'foo': 'A', 'bar': 'B'},
            {'key': 'g', 'val': 'h'}
        ]
        expect = {
            'a': {'key': 'a', 'val': 'b', 'foo': 'A'},
            'c': {'key': 'c', 'val': 'd', 'bar': 'B'},
            'e': {'key': 'e', 'val': 'f', 'foo': 'A', 'bar': 'B'}
        }

        self.assertEquals(
            self.mapping_list.consume_entries(
                data, 'key', require=['foo', 'bar']),
            expect)

    def test_consume_entries_warn_no_key(self):
        data = [
            {'key': 'a', 'foo': 'b'},
            {'key': 'c', 'bar': 'd'},
            {'key': 'e', 'foo': 'f'},
        ]
        expect = {
            'b': {'key': 'a', 'foo': 'b'},
            'f': {'key': 'e', 'foo': 'f'}
        }

        self.assertEquals(
            self.mapping_list.consume_entries(data, 'foo'), expect)
        self.mock_warning.assert_called_once_with(
            'The field intended as dict key was empty!')

    def test_consume_entries_warn_not_unique_key(self):
        data = [
            {'key': 'a', 'foo': 'b'},
            {'key': 'c', 'foo': 'b'},
            {'key': 'e', 'foo': 'f'},
        ]
        expect = {
            'b': {'key': 'a', 'foo': 'b'},
            'f': {'key': 'e', 'foo': 'f'}
        }

        self.assertEquals(
            self.mapping_list.consume_entries(data, 'foo'), expect)
        self.mock_warning.assert_called_once_with(
            'The dict key was not unique! - b')
