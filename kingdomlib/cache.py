# -*- coding: utf-8 -*-
"""
   flask_kingdom.storage
   ~~~~~~~~~~~~~~~~~~~~~
"""

from functools import wraps
from contextlib import contextmanager
from werkzeug.utils import cached_property
from werkzeug.local import LocalProxy
from flask import g, current_app
from .contrib.cache import Cache

# define cache times
ONE_DAY = 86400
ONE_HOUR = 3600
FIVE_MINUTES = 300


def use_redis(prefix='kingdom'):
    """Get redis object from app extensions"""
    key = f'{prefix}_redis'

    d = getattr(g, key, None)

    if d is not None:
        return d
    return current_app.extensions[key]


def use_cache(prefix='kingdom'):
    return current_app.extensions[prefix + '_cache']


def init_app(app):
    """Init cache app"""
    from redis import StrictRedis

    # register
    Cache(app, config_prefix='KINGDOM')

    client = StrictRedis(decode_responses=True)
    app.extensions['kingdom_redis'] = client


cache = LocalProxy(use_cache)
redis = LocalProxy(use_redis)


@contextmanager
def execute_pipeline(prefix='kingdom'):
    key = prefix + '_redis'
    redis = current_app.extensions[key]
    with redis.pipeline() as pipe:
        setattr(g, key, pipe)
        yield
        delattr(g, key)
        pipe.execute()


def cached(key_pattern, expire=ONE_HOUR):
    def wrapper(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if '%s' in key_pattern and args:
                key = key_pattern % args
            elif '%(' in key_pattern and kwargs:
                key = key_pattern % kwargs
            else:
                key = key_pattern
            rv = cache.get(key)
            if rv:
                return rv
            rv = f(*args, **kwargs)
            cache.set(key, rv, timeout=expire)
            return rv
        return decorated
    return wrapper


class RedisStat(object):
    KEY_PREFIX = 'stat:{}'

    def __init__(self, ident):
        self.ident = ident
        self._key = self.KEY_PREFIX.format(ident)

    def increase(self, field, step=1):
        redis.hincrby(self._key, field, step)

    def get(self, key, default=0):
        return self.value.get(key, default)

    def __getitem__(self, item):
        return self.value[item]

    def __setitem__(self, item, value):
        redis.hset(self._key, item, int(value))

    @cached_property
    def value(self):
        return redis.hgetall(self._key)

    @classmethod
    def get_many(cls, ids):
        with redis.pipeline() as pipe:
            for i in ids:
                pipe.hgetall(cls.KEY_PREFIX.format(i))
            return pipe.execute()

    @classmethod
    def get_dict(cls, ids):
        rv = cls.get_many(ids)
        return dict(zip(ids, rv))
