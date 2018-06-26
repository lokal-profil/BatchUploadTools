#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for common.py."""
from __future__ import unicode_literals
import unittest
import tempfile
import os
import json
from batchupload.common import (
    strip_dict_entries,
    strip_list_entries,
    is_int,
    is_pos_int,
    open_and_read_file,
    open_and_write_file,
    trim_list,
    MyError,
    deep_sort,
    modify_path,
    create_dir,
    listify,
    sorted_dict,
    add_or_increment,
    interpret_bool,
    pop,
    relabel_inner_dicts,
    invert_dict
)


class TestStripDictEntries(unittest.TestCase):

    """Test the strip_dict_entries method."""

    def test_strip_dict_entries_empty_dict(self):
        self.assertEqual(strip_dict_entries({}), {})

    def test_strip_dict_entries(self):
        input_value = {'id': 'identifier'}
        expected = {'id': 'identifier'}
        self.assertEqual(strip_dict_entries(input_value), expected)

    def test_strip_dict_entries_with_whitespace_in_key(self):
        input_value = {' id\n ': 'identifier'}
        expected = {'id': 'identifier'}
        self.assertEqual(strip_dict_entries(input_value), expected)

    def test_strip_dict_entries_with_whitespace_in_value(self):
        input_value = {'id': ' \t\nidentifier '}
        expected = {'id': 'identifier'}
        self.assertEqual(strip_dict_entries(input_value), expected)

    def test_strip_dict_entries_ignore_non_string_values(self):
        input_value = {'int': 5, 'list': ['aa', ' aa']}
        expected = {'int': 5, 'list': ['aa', ' aa']}
        self.assertEqual(strip_dict_entries(input_value), expected)

    def test_strip_dict_entries_error_on_non_dict(self):
        input_value = 123
        with self.assertRaises(MyError) as cm:
            strip_dict_entries(input_value)
        self.assertEqual(cm.exception.value,
                         'strip_dict_entries() expects a dictionary object'
                         'as input but found "int"')


class TestStriplistEntries(unittest.TestCase):

    """Test the strip_list_entries method."""

    def test_strip_list_entries_empty_list(self):
        self.assertEqual(strip_list_entries([]), [])

    def test_strip_list_entries(self):
        input_value = ['id', 'identifier']
        expected = ['id', 'identifier']
        self.assertEqual(strip_list_entries(input_value), expected)

    def test_strip_list_entries_with_whitespace(self):
        input_value = [' id\n', 'identifier']
        expected = ['id', 'identifier']
        self.assertEqual(strip_list_entries(input_value), expected)

    def test_strip_list_entries_ignore_non_string_values(self):
        input_value = [5, ['aa', ' aa']]
        expected = [5, ['aa', ' aa']]
        self.assertEqual(strip_list_entries(input_value), expected)

    def test_strip_list_entries_error_on_non_list(self):
        input_value = 123
        with self.assertRaises(MyError) as cm:
            strip_list_entries(input_value)
        self.assertEqual(cm.exception.value,
                         'strip_list_entries() expects a list object'
                         'as input but found "int"')


class TestIsInt(unittest.TestCase):

    """Test the is_int method."""

    def test_empty_string_fail(self):
        s = ''
        result = is_int(s)
        self.assertEqual(result, False)

    def test_none_fail(self):
        s = None
        result = is_int(s)
        self.assertEqual(result, False)

    def test_random_string_fail(self):
        s = 'random_string'
        result = is_int(s)
        self.assertEqual(result, False)

    def test_float_fail(self):
        s = '123.456'
        result = is_int(s)
        self.assertEqual(result, False)

    def test_valid_negative_int_succeed(self):
        s = '-123'
        result = is_int(s)
        self.assertEqual(result, True)

    def test_valid_int_succeed(self):
        s = '123'
        result = is_int(s)
        self.assertEqual(result, True)


class TestIsPosInt(unittest.TestCase):

    """Test the is_pos_int method."""

    def test_empty_string_fail(self):
        s = ''
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_none_fail(self):
        s = None
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_random_string_fail(self):
        s = 'random_string'
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_float_fail(self):
        s = '123.456'
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_negative_int_fail(self):
        s = '-123'
        result = is_pos_int(s)
        self.assertEqual(result, False)

    def test_valid_int_succeed(self):
        s = '123'
        result = is_pos_int(s)
        self.assertEqual(result, True)


class TestOpenFileBase(unittest.TestCase):

    """Test base for open_and_read_file() and open_and_write_file()."""

    def setUp(self):
        # Create a temporary file
        self.test_data = '{"list": ["a", "b", "c"], "två": "2", "ett": 1}'
        self.test_infile = tempfile.NamedTemporaryFile()
        self.test_outfile = tempfile.NamedTemporaryFile(delete=False)
        self.test_infile.write(self.test_data.encode('utf-8'))
        self.test_infile.seek(0)

    def tearDown(self):
        # Closes and removes the file
        self.test_infile.close()
        os.remove(self.test_outfile.name)


class TestOpenReadFile(TestOpenFileBase):

    """Test open_and_read_file()."""

    def test_read_data(self):
        expected_data = '{"list": ["a", "b", "c"], "två": "2", "ett": 1}'
        result = open_and_read_file(self.test_infile.name)
        self.assertEqual(result, expected_data)

    def test_read_json_data(self):
        expected_data = {'list': ['a', 'b', 'c'], 'två': '2', 'ett': 1}
        result = open_and_read_file(self.test_infile.name, as_json=True)
        self.assertEqual(deep_sort(result),
                         deep_sort(expected_data))


class TestOpenWriteFile(TestOpenFileBase):

    """Test open_and_read_file()."""

    def test_write_data(self):
        to_write = '{"list": ["a", "b", "c"], "två": "2", "ett": 1}'
        open_and_write_file(self.test_outfile.name, to_write)
        self.assertEqual(self.test_outfile.read().decode('utf-8'),
                         self.test_data)

    def test_write_json_data(self):
        to_write = {'list': ['a', 'b', 'c'], 'två': '2', 'ett': 1}
        open_and_write_file(self.test_outfile.name, to_write, as_json=True)
        json_out = json.loads(self.test_outfile.read().decode('utf-8'))
        json_in = json.loads(self.test_data)
        self.assertEqual(deep_sort(json_out),
                         deep_sort(json_in))


class TestTrimList(unittest.TestCase):

    """Test trim_list()."""

    def test_trim_list_none(self):
        self.assertEqual(trim_list(None), None)

    def test_trim_list_empty_list(self):
        self.assertEqual(trim_list([]), [])

    def test_trim_list(self):
        input_value = ['a', '', 'c']
        expected = ['a', 'c']
        self.assertEqual(trim_list(input_value), expected)

    def test_trim_list_with_whitespace(self):
        input_value = [' a\n', ' ', 'c']
        expected = ['a', 'c']
        self.assertEqual(trim_list(input_value), expected)

    def test_trim_list_ignore_non_string_values(self):
        input_value = [5, ['aa', ' aa']]
        expected = [5, ['aa', ' aa']]
        self.assertEqual(trim_list(input_value), expected)


class TestListify(unittest.TestCase):

    """Test listify()."""

    def test_listify_none(self):
        self.assertEqual(listify(None), None)

    def test_listify_empty_list(self):
        self.assertEqual(listify([]), [])

    def test_listify_list(self):
        input_value = ['a', 'c']
        expected = ['a', 'c']
        self.assertEqual(listify(input_value), expected)

    def test_listify_string(self):
        input_value = 'a string'
        expected = ['a string']
        self.assertEqual(listify(input_value), expected)


class TestModifyDirBase(unittest.TestCase):

    """Test base for modify_path() and create_dir()."""

    def setUp(self):
        # Create a temporary file
        self.test_file = tempfile.NamedTemporaryFile()
        self.test_dir = tempfile.mkdtemp()
        self.out_path = 'out'

    def tearDown(self):
        # Closes and removes the file
        self.test_file.close()
        os.rmdir(self.test_dir)


class TestModifyPath(TestModifyDirBase):

    """Test modify_path()."""

    def test_modify_path_with_empty_args(self):
        self.assertEqual(modify_path('', ''), '')

    def test_modify_path_with_empty_dir(self):
        self.assertEqual(modify_path('', self.out_path), self.out_path)

    def test_modify_path_with_empty_none_dir(self):
        self.assertEqual(modify_path(None, self.out_path), self.out_path)

    def test_modify_path_valid(self):
        expected = os.path.join(self.test_dir, self.out_path)
        self.assertEqual(modify_path(self.test_dir, self.out_path),
                         expected)

    def test_modify_path_no_valid_path(self):
        with self.assertRaises(MyError) as cm:
            modify_path('not_a_directory', self.out_path)
        self.assertEqual(cm.exception.value,
                         '"not_a_directory" is not a directory.')

    def test_modify_path_file_as_path(self):
        with self.assertRaises(MyError) as cm:
            modify_path(self.test_file.name, self.out_path)
        self.assertEqual(cm.exception.value,
                         '"%s" is not a directory.' % self.test_file.name)


class TestCreateDir(TestModifyDirBase):

    """Test create_dir().

    TODO: Could redo with mock to prevent accidental creation.
    """

    def test_create_dir_with_empty_arg(self):
        with self.assertRaises(MyError) as cm:
            create_dir('')
        self.assertEqual(cm.exception.value,
                         'Cannot create directory without a name.')

    def test_create_dir_valid(self):
        in_data = os.path.join(self.test_dir, self.out_path)
        create_dir(in_data)
        self.assertTrue(os.path.isdir(in_data))

        os.rmdir(in_data)

    def test_create_dir_already_exists(self):
        create_dir(self.test_dir)
        self.assertTrue(os.path.isdir(self.test_dir))

    def test_create_dir_file_already_exists(self):
        with self.assertRaises(MyError) as cm:
            create_dir(self.test_file.name)
        self.assertEqual(cm.exception.value,
                         'Cannot create the directory "%s" as a file with '
                         'that name already exists.' % self.test_file.name)


class TestSortedDict(unittest.TestCase):

    """Test the sorted_dict method."""

    def test_sorted_dict_empty(self):
        self.assertEqual(sorted_dict({}), [])

    def test_sorted_dict_sort(self):
        input_value = {'a': 1, 'b': 3, 'c': 2}
        expected = [('b', 3), ('c', 2), ('a', 1)]
        self.assertEqual(sorted_dict(input_value), expected)


class TestAddOrIncrement(unittest.TestCase):

    """Test the add_or_increment method."""

    def test_add_or_increment_new_wo_key(self):
        dictionary = {}
        val = 'hej'
        expected = {'hej': 1}
        add_or_increment(dictionary, val)
        self.assertEqual(dictionary, expected)

    def test_add_or_increment_new_w_key(self):
        dictionary = {}
        key = 'freq'
        val = 'hej'
        expected = {'hej': {'freq': 1}}
        add_or_increment(dictionary, val, key)
        self.assertEqual(dictionary, expected)

    def test_add_or_increment_old_wo_key(self):
        dictionary = {'hej': 1}
        val = 'hej'
        expected = {'hej': 2}
        add_or_increment(dictionary, val)
        self.assertEqual(dictionary, expected)

    def test_add_or_increment_old_w_key(self):
        dictionary = {'hej': {'freq': 1}}
        key = 'freq'
        val = 'hej'
        expected = {'hej': {'freq': 2}}
        add_or_increment(dictionary, val, key)
        self.assertEqual(dictionary, expected)


class TestInterpretBool(unittest.TestCase):

    """Test the interpret_bool() method."""

    def test_interpret_bool_empty_value(self):
        with self.assertRaises(ValueError):
            interpret_bool(None)

    def test_interpret_bool_allow_bool(self):
        self.assertTrue(interpret_bool(True))
        self.assertFalse(interpret_bool(False))

    def test_interpret_bool_true_values(self):
        true_values = ['t', 'True', 'yes', 'Y']
        for val in true_values:
            self.assertTrue(interpret_bool(val))

    def test_interpret_bool_false_value(self):
        false_values = ['f', 'False', 'no', 'N']
        for val in false_values:
            self.assertFalse(interpret_bool(val))

    def test_interpret_bool_unknown_value(self):
        with self.assertRaises(ValueError) as cm:
            interpret_bool('Some value')
        self.assertEqual(
            cm.exception.args[0],
            "'Some value' cannot be interpreted as either True/False.")


class TestPop(unittest.TestCase):

    """Test the pop() method."""

    def test_pop_no_key(self):
        obj = {'foo': 'bar'}
        self.assertEqual(pop(obj, ''), None)

    def test_pop_not_poppable(self):
        with self.assertRaises(AttributeError):
            pop('foo', 'bar')

    def test_pop_has_key(self):
        obj = {'foo': 'bar'}
        self.assertEqual(pop(obj, 'foo'), 'bar')

    def test_pop_not_has_key(self):
        obj = {'foo': 'bar'}
        self.assertEqual(pop(obj, 'bar'), None)


class TestRelabelInnerDicts(unittest.TestCase):

    """Test the relabel_inner_dicts() method."""

    def test_relabel_inner_dicts_none(self):
        with self.assertRaises(AttributeError):
            relabel_inner_dicts(None, None)

    def test_relabel_inner_dicts_not_a_dict(self):
        with self.assertRaises(AttributeError):
            relabel_inner_dicts('not a dict', 'not a dict')

    def test_relabel_inner_dicts_basic(self):
        obj = {
            'a': {'name': 'A', 'type': 't'},
            'b': {'name': 'B', 'type': 't'}
        }
        key = {'name': 'namn'}
        expected = {
            'a': {'namn': 'A', 'type': 't'},
            'b': {'namn': 'B', 'type': 't'}
        }
        self.assertEqual(relabel_inner_dicts(obj, key), expected)
        self.assertEqual(obj, expected)

    def test_relabel_inner_dicts_missing_key(self):
        obj = {
            'a': {'name': 'A', 'type': 't'},
            'b': {'name': 'B', 'type': 't'}
        }
        key = {'name': 'namn', 'unmatched_key': 'x'}
        with self.assertRaises(KeyError):
            relabel_inner_dicts(obj, key)


class TestInvertDict(unittest.TestCase):

    """Test the invert_dict() method."""

    def test_invert_dict_none(self):
        with self.assertRaises(AttributeError):
            invert_dict(None)

    def test_invert_dict_not_dict(self):
        with self.assertRaises(AttributeError):
            invert_dict('not a dict')

    def test_invert_dict_basic(self):
        obj = {'a': 'A', 'b': 'B'}
        expected = {'A': 'a', 'B': 'b'}
        self.assertEqual(invert_dict(obj), expected)

    def test_invert_dict_not_hashable(self):
        obj = {'a': {'A': 1}, 'b': 'B'}
        with self.assertRaises(TypeError):
            invert_dict(obj)
