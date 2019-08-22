# -*- coding: utf-8 -*-
"""
   kingdomlib.utils
   ~~~~~~~~~~~~~~~~
"""

from datetime import date, datetime
from flask import request

ROBOT_BROWSERS = ('google', 'msn', 'yahoo', 'ask', 'aol')
ROBOT_KEYWORDS = ('spider', 'bot', 'crawler', '+http')
MOBILE_PLATFORMS = ('iphone', 'android', 'wii')


def json_encode(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def xmldatetime(date):
    return date.strftime('%Y-%m-%dT%H:%M:%SZ')


def is_robot():
    ua = str(request.user_agent).lower()
    for key in ROBOT_KEYWORDS:
        if key in ua:
            return True
    return request.user_agent.browser in ROBOT_BROWSERS


def is_mobile():
    return request.user_agent.platform in MOBILE_PLATFORMS


def is_blank(value=None):
    value = value or ''
    return not (value and value.strip())


def is_not_blank(value=None):
    value = value or ''
    return bool(value and value.strip())


def is_json():
    if request.is_xhr:
        return True

    if request.path.startswith('/api/'):
        return True

    if request.accept_mimetypes.accept_json:
        return True

    return False


class Pagination(object):
    def __init__(self, total, page=1, perpage=20):
        self.total = total
        self.page = page
        self.perpage = perpage

        pages = int((total - 1) / perpage) + 1
        self.pages = pages

        if page > 1:
            self.prev = page - 1
        else:
            self.prev = None
        if page < pages:
            self.next = page + 1
        else:
            self.next = None

    def __getitem__(self, item):
        return getattr(self, item)

    def keys(self):
        return ['total', 'page', 'perpage', 'prev', 'next', 'pages']

    def fetch(self, q):
        offset = (self.page - 1) * self.perpage
        if offset:
            q = q.offset(offset)
        return q.limit(self.perpage).all()


class Empty(object):
    def __eq__(self, other):
        return isinstance(other, Empty)

    def __ne__(self, other):
        return not self == other

    def __nonzero__(self):
        return False

    def __bool__(self):
        return False

    def __str__(self):
        return "Empty"

    def __repr__(self):
        return '<Empty>'


EMPTY = Empty()
