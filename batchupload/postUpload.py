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


def trim_parent_category(category):
    """
    Remove a category from any files already in one of its sub-categories.

    @param category: the category name (with or without the Category:-prefix)
    """
    summary = 'Removing parent category when image already in subcategory'
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

    pywikibot.output(
        'Removed {num} pages from {cat}'.format(num=len(uncat), cat=category))
