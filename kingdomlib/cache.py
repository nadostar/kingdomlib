# -*- coding: utf-8 -*-
"""
   kingdomlib.cache
   ~~~~~~~~~~~~~~~~
"""

from functools import wraps
from contextlib import contextmanager
from werkzeug.utils import cached_property
from werkzeug.local import LocalProxy
from cachelib import NullCache, SimpleCache, FileSystemCache
from cachelib import MemcachedCache, RedisCache
from flask import g, current_app


class CacheFactory(object):
    def __init__(self, app, config_prefix='KINGDOM', **kwargs):
        self.config_prefix = config_prefix
        self.config = app.config

        cache_type = '_{}'.format(self._config('type'))
        kwargs.update(dict(
            default_timeout=self._config('DEFAULT_TIMEOUT', 100)
        ))

        try:
            self.cache = getattr(self, cache_type)(**kwargs)
        except AttributeError:
            raise RuntimeError(f'`{cache_type}` is not a valid cache type!')
        app.extensions[config_prefix.lower() + '_cache'] = self.cache

    def __getattr__(self, key):
        try:
            return object.__getattribute__(self, key)
        except AttributeError:
            try:
                return getattr(self.cache, key)
            except AttributeError:
                raise AttributeError(f'No such attribute: {key}')

    def _config(self, key, default='error'):
        key = key.upper()
        prior = f'{self.config_prefix}_CACHE_{key}'
        if prior in self.config:
            return self.config[prior]
        fallback = f'CACHE_{key}'
        if fallback in self.config:
            return self.config[fallback]
        if default == 'error':
            raise RuntimeError(f'{prior} is missing.')
        return default

    def _null(self, **kwargs):
        """Returns a :class:`NullCache` instance"""
        return NullCache()

    def _simple(self, **kwargs):
        """Returns a :class:`SimpleCache` instance
        .. warning::
            This cache system might not be thread safe. Use with caution.
        """
        kwargs.update(dict(threshold=self._config('threshold', 500)))
        return SimpleCache(**kwargs)

    def _memcache(self, **kwargs):
        """Returns a :class:`MemcachedCache` instance"""
        kwargs.update(dict(
            servers=self._config('MEMCACHED_SERVERS', None),
            key_prefix=self._config('key_prefix', None),
        ))
        return MemcachedCache(**kwargs)

    def _redis(self, **kwargs):
        """Returns a :class:`RedisCache` instance"""
        kwargs.update(dict(
            host=self._config('REDIS_HOST', 'localhost'),
            port=self._config('REDIS_PORT', 6379),
            password=self._config('REDIS_PASSWORD', None),
            db=self._config('REDIS_DB', 0),
            key_prefix=self._config('KEY_PREFIX', None),
        ))
        return RedisCache(**kwargs)

    def _filesystem(self, **kwargs):
        """Returns a :class:`FileSystemCache` instance"""
        kwargs.update(dict(
            threshold=self._config('threshold', 500),
        ))
        return FileSystemCache(self._config('dir', None), **kwargs)


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
    CacheFactory(app, config_prefix='KINGDOM')

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
