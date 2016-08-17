#!/usr/bin/env python
# encoding: utf-8

"""
A workflow for Alfred 3 (http://www.alfredapp.com/).

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

BASE_URL = b'http://dictionary.goo.ne.jp'
SEARCH_URL = b'{}/srch/all/{{query}}/m0u/'.format(BASE_URL)

MAX_CACHE_AGE = 3600  # 1 hour
MIN_QUERY_LENGTH = 2
log = None

def main(wf):
    """Run workflow."""
    query = wf.args[0]

    log.debug('query : %r', query)

    if wf.update_availble:
        wf.add_item('New version available',
                    'Action this item to update',
                    autocomplete='workflow:update',
                    icon='update-available.icns')

    if len(query) < MIN_QUERY_LENGTH:
        wf.add_item('Query too short', 'Keep typing...', icon=ICON_WARNING)
        wf.send_feedback()
        return 0


