#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Various tools for post upload processes."""
import pywikibot

commons = None  # the Commons site object


def load_commons_site():
    """Ensure Commons is only loaded once."""
    global commons
    if commons is None:
        commons = pywikibot.Site('commons', 'commons')


def trim_parent_category(category, summary=None, verbose=True):
    """
    Remove a category from any files already in one of its sub-categories.

    @param category: the category name (with or without the Category:-prefix)
    @param summary: override the default summary
    @param verbose: if verbose output is desired. Default: True.
    @return: the number of pages removed from the category
    """
    summary = 'Removing parent category when file already in subcategory'
    load_commons_site()
    if not category.startswith('Category:'):
        category = 'Category:{0}'.format(category)
    cat = pywikibot.Category(commons, category)
    subcats = set(cat.subcategories())

    uncat = []  # pages for which to remove the category

    for page in cat.articles(namespaces=6, content=True):
        page_cats = set(page.categories())
        if page_cats.intersection(subcats):
            uncat.append(page)

    for page in uncat:
        page.change_category(oldCat=cat, newCat=None, summary=summary)

    if verbose:
        pywikibot.output(
            'Removed {num} pages from {cat}'.format(
                num=len(uncat), cat=category))

    return len(uncat)


def trim_second_category(start_category, del_category, in_filename=None,
                         summary=None, verbose=True):
    """
    Remove a category from any files in a second category.

    @param start_category: the name of the category to start with (with or
        without the Category:-prefix)
    @param del_category: the name of the category to remove to start with (with
        or without the Category:-prefix)
    @param in_filename: string which must be part of the filename for action
        to be taken. Default: None
    @param summary: override the default summary
    @param verbose: if verbose output is desired. Default: True.
    @return: the number of pages removed from the category
    """
    load_commons_site()
    if not start_category.startswith('Category:'):
        start_category = 'Category:{0}'.format(start_category)
    if not del_category.startswith('Category:'):
        del_category = 'Category:{0}'.format(del_category)
    summary = summary or \
        'Removing {del_category} for file already in {start_category}'.format(
            del_category=del_category, start_category=start_category)

    start_cat = pywikibot.Category(commons, start_category)
    del_cat = pywikibot.Category(commons, del_category)

    counter = 0
    for page in start_cat.articles(namespaces=6, content=True):
        if in_filename and in_filename not in page.title():
            continue
        page_cats = set(page.categories())
        if del_cat in page_cats:
            page.change_category(oldCat=del_cat, newCat=None, summary=summary)
            counter += 1

    if verbose:
        pywikibot.output(
            '{start_cat}: Removed {num} pages from {del_cat}'.format(
                num=counter, del_cat=del_category, start_cat=start_category))

    return counter
