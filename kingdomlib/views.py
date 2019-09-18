# -*- coding: utf-8 -*-
"""
   kingdomlib.views
   ~~~~~~~~~~~~~~~~
"""

from werkzeug.datastructures import MultiDict
from flask import request
from flask_wtf import FlaskForm

from .errors import FormError


class SimpleView(object):
    def __init__(self, name=None):
        self.name = name or ''
        self.deferred = []

    def route(self, rule, **options):
        def wrapper(f):
            self.deferred.append((f, rule, options))
            return f
        return wrapper

    def register(self, bp, url_prefix=None):
        if url_prefix is None:
            url_prefix = f'/{self.name}'

        for f, rule, options in self.deferred:
            endpoint = options.pop('endpoint', f.__name__)
            bp.add_url_rule(url_prefix + rule, endpoint, f, **options)


class SimpleForm(FlaskForm):
    @classmethod
    def create_api_form(cls, obj=None):
        formdata = MultiDict(request.form.to_dict())
        form = cls(formdata=formdata, obj=obj, meta={'csrf': False})
        form._obj = obj
        if not form.validate():
            raise FormError(form)
        return form

    def _validate_obj(self, key, value):
        obj = getattr(self, '_obj', None)
        return obj and getattr(obj, key) == value
