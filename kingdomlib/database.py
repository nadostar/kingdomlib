# -*- coding: utf-8 -*-
"""
   kingdomlib.database
   ~~~~~~~~~~~~~~~~~~~
"""

from flask import abort, json
from sqlalchemy import func, event
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Query, class_mapper
from sqlalchemy.orm.exc import UnmappedClassError

from .cache import cache, ONE_DAY, FIVE_MINUTES
from .errors import NotFound
from .utils import is_json, json_encode

CACHE_TIMES = {
    'get': ONE_DAY,
    'count': ONE_DAY,
    'ff': FIVE_MINUTES,
    'fc': FIVE_MINUTES,
}

CACHE_MODEL_PREFIX = 'db'


class CacheQuery(Query):
    def get(self, ident):
        mapper = self._only_full_mapper_zero('get')

        if isinstance(ident, (list, tuple)):
            suffix = '-'.join(map(str, ident))
        else:
            suffix = str(ident)

        key = mapper.class_.generate_cache_prefix('get') + suffix
        rv = cache.get(key)
        if rv:
            return rv
        rv = super(CacheQuery, self).get(ident)
        if rv is None:
            return None
        cache.set(key, rv, CACHE_TIMES['get'])
        return rv

    def get_dict(self, ident):
        if not ident:
            return {}

        mapper = self._only_full_mapper_zero('get')
        if len(mapper.primary_key) != 1:
            raise NotImplementedError

        prefix = mapper.class_.generate_cache_prefix('get')
        keys = {prefix + str(i) for i in ident}
        rv = cache.get_dict(*keys)

        missed = {i for i in ident if rv[prefix + str(i)] is None}

        rv = {k.lstrip(prefix): rv[k] for k in rv}

        if not missed:
            return rv

        pk = mapper.primary_key[0]
        missing = self.filter(pk.in_(missed)).all()
        to_cache = {}
        for item in missing:
            ident = str(getattr(item, pk.name))
            to_cache[prefix + ident] = item
            rv[ident] = item

        cache.set_many(to_cache, CACHE_TIMES['get'])
        return rv

    def get_many(self, ident, clean=True):
        d = self.get_dict(ident)
        if clean:
            return list(_itervalues(d, ident))
        return [d[str(k)] for k in ident]

    def filter_first(self, **kwargs):
        mapper = self._only_entity_zero()

        prefix = mapper.class_.generate_cache_prefix('ff')
        key = prefix + '-'.join(['%s$%s' % (k, kwargs[k]) for k in kwargs])
        rv = cache.get(key)
        if rv:
            return rv
        rv = self.filter_by(**kwargs).first()
        if rv is None:
            return None
        # it is hard to invalidate this cache, expires in 2 minutes
        cache.set(key, rv, CACHE_TIMES['ff'])
        return rv

    def filter_count(self, **kwargs):
        mapper = self._only_entity_zero()
        model = mapper.class_
        if not kwargs:
            key = model.generate_cache_prefix('count')
            rv = cache.get(key)
            if rv is not None:
                return rv
            q = self.select_from(model).with_entities(func.count(1))
            rv = q.scalar()
            cache.set(key, rv, CACHE_TIMES['count'])
            return rv

        prefix = model.generate_cache_prefix('fc')
        key = prefix + '-'.join(['%s$%s' % (k, kwargs[k]) for k in kwargs])
        rv = cache.get(key)
        if rv:
            return rv
        q = self.select_from(model).with_entities(func.count(1))
        rv = q.filter_by(**kwargs).scalar()
        cache.set(key, rv, CACHE_TIMES['fc'])
        return rv

    def get_or_404(self, ident):
        data = self.get(ident)
        if data:
            return data

        if is_json():
            mapper = self._only_full_mapper_zero('get')
            key = '%s "%r"' % (mapper.class_.__name__, ident)
            raise NotFound(key)
        abort(404)

    def first_or_404(self, **kwargs):
        data = self.filter_first(**kwargs)
        if data:
            return data

        if is_json():
            mapper = self._only_full_mapper_zero('get')
            key = mapper.class_.__name__
            if len(kwargs) == 1:
                key = '%s "%s"' % (key, list(kwargs.values())[0])
            raise NotFound(key)
        abort(404)


class CacheProperty(object):
    def __init__(self, sa):
        self.sa = sa

    def __get__(self, obj, type):
        try:
            mapper = class_mapper(type)
            if mapper:
                return CacheQuery(mapper, session=self.sa.session())
        except UnmappedClassError:
            return None


class BaseMixin(object):
    def __getitem__(self, key):
        return getattr(self, key)

    def to_dict(self):
        return {c.key: getattr(self, c.key)
                for c in inspect(self).mapper.column_attrs}

    def to_json(self):
        return json.dumps(self.to_dict(), default=json_encode)

    @classmethod
    def generate_cache_prefix(cls, name):
        prefix = f'{CACHE_MODEL_PREFIX}:{name}:{cls.__tablename__}'
        if hasattr(cls, '__cache_version__'):
            return f'{prefix}|{cls.__cache_version__}'
        return f'{prefix}:'

    @classmethod
    def __declare_last__(cls):
        @event.listens_for(cls, 'after_insert')
        def receive_after_insert(mapper, conn, target):
            cache.inc(target.generate_cache_prefix('count'))

        @event.listens_for(cls, 'after_update')
        def receive_after_update(mapper, conn, target):
            key = _unique_key(target, mapper.primary_key)
            cache.set(key, target, CACHE_TIMES['get'])

        @event.listens_for(cls, 'after_delete')
        def receive_after_delete(mapper, conn, target):
            key = _unique_key(target, mapper.primary_key)
            cache.delete_many(key, target.generate_cache_prefix('count'))


def _unique_suffix(target, primary_key):
    return '-'.join(map(lambda k: str(getattr(target, k.name)), primary_key))


def _unique_key(target, primary_key):
    key = _unique_suffix(target, primary_key)
    return target.generate_cache_prefix('get') + key


def _itervalues(data, ident):
    for k in ident:
        item = data[str(k)]
        if item is not None:
            yield item
