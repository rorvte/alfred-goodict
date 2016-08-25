#!/usr/bin/env python
# encoding: utf-8

"""
A workflow for Alfred (http://www.alfredapp.com/).

Search the definitive Japanese dictionary at http://dictionary.goo.ne.jp
"""

from __future__ import print_function, unicode_literals

import sys
import urllib
import re
import htmlentitydefs
from hashlib import md5

from workflow import web, Workflow, ICON_WARNING
from bs4 import BeautifulSoup as BS
from bs4 import Tag

UPDATE_SETTINGS = {'github_slug': 'rorvte/alfred-goodict'}
USER_AGENT = 'Alfred-Goodict/{version} (https://github.com/rorvte/alfred-goodict)'

BASE_URL = b'http://dictionary.goo.ne.jp'
SEARCH_URL = b'{}/srch/all/{{query}}/m0u/'.format(BASE_URL)

MAX_CACHE_AGE = 3600  # 1 hour
log = None

def unescape(text):
    """Replace HTML entities with Unicode characters.

    From: http://effbot.org/zone/re-sub.htm#unescape-html
    """

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is

    return re.sub("&#?\w+;", fixup, text)

def flatten(elem, recursive=False):
    """Return the string contents of partial BS elem tree.

    :param elem: BeautifulSoup ``Tag`` or ``NavigableString``
    :param recursive: Whether to flatten children or entire subtree
    :returns: Flattened Unicode text contained in subtree

    """

    content = []

    if recursive:
        elems = elem.descendants
    else:
        elems = elem.contents

    for e in elems:
        # If processing recursively, a NavigableString for the
        # tag text will also be encountered
        if isinstance(e, Tag) and recursive:
            continue
        if hasattr(e, 'string') and e.string is not None:
            # log.debug('[%s] : %s', e.__class__.__name__, e.string)
            content.append(e.string)

    return unescape(re.sub(r'\s+', ' ', ''.join(content)))


def lookup(query):
    """Get results matching ``query`` from dictionary.goo.ne.jp"""

    results = []

    url = SEARCH_URL.format(query=urllib.quote(query.encode('utf-8')))
    log.debug(url)

    user_agent = USER_AGENT.format(version=wf.version)
    r = web.get(url, headers={'User-Agent': user_agent})
    # Send 404 if there are no results
    if r.status_code == 404:
        return results
    r.raise_for_status()

    # Parse results
    soup = BS(r.content, b'html5lib')
    elems = soup.find_all('ul', {'class', 'list-search-a'})

    for elem in elems:
        #log.debug('elem : %s', elem.prettify())
        result = {}
        header = elem.find('dt')
        if header is None:
            continue

        link = elem.find('a')
        term = query

        log.debug('term: %r', term)

        result['term'] = term
        result['url'] = BASE_URL + link['href']

        log.debug('URL : %r', result['url'])

        description_elem = elem.find('dd', {'class': 'text-b'})

        log.debug('raw description : %r', description_elem)

        description = flatten(description_elem, recursive=True)

        log.debug('flattened description : %r', description)

        result['description'] = description

        results.append(result)

    log.debug('{} results for `{}`'.format(len(results), query))

    return results


def main(wf):
    """Run workflow."""
    query = wf.args[0]

    log.debug('query : %r', query)

    if wf.update_available:
        wf.add_item('New version available',
                    'Action this item to update',
                    autocomplete='workflow:update',
                    icon='update-available.icns')

    def wrapper():
        return lookup(query)

    key = md5(query.encode('utf-8')).hexdigest()

    results = wf.cached_data(key, wrapper, max_age=MAX_CACHE_AGE)

    if not len(results):
        wf.add_item('Nothing found',
                    'Try a different query',
                    icon=ICON_WARNING)

    for d in results:
        wf.add_item(d['term'],
                    d['description'],
                    modifier_subtitles={'cmd': d['url']},
                    uid=d['url'],
                    arg=d['url'],
                    valid=True,
                    icon='icon.png')

    wf.send_feedback()

if __name__ == '__main__':
    wf = Workflow(update_settings=UPDATE_SETTINGS)
    log = wf.logger
    sys.exit(wf.run(main))


