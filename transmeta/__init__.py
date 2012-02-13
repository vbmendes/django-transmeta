import copy

from django.db import models
from django.db.models.fields import NOT_PROVIDED
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.forms.forms import pretty_name
from django.utils.datastructures import SortedDict
from django.utils.translation import get_language, to_locale
from django.utils.functional import lazy

LANGUAGE_CODE = 0
LANGUAGE_NAME = 1


def get_languages():
    return getattr(settings, 'TRANSMETA_LANGUAGES', settings.LANGUAGES)


def get_real_fieldname(field, lang=None):
    if lang is None:
        lang = to_locale(get_language()) # both 'en-US' and 'en' -> 'en'
    return str('%s_%s' % (field, lang))


def get_field_language(real_field):
    """ return language for a field. i.e. returns "en" for "name_en" """
    return real_field.split('_')[1]


def get_fallback_fieldname(field, lang=None):
    return get_real_fieldname(field, lang=fallback_language())


def get_real_fieldname_in_each_language(field):
    return [get_real_fieldname(field, lang[LANGUAGE_CODE])
            for lang in get_languages()]


def canonical_fieldname(db_field):
    """ all "description_en", "description_fr", etc. field names will return "description" """
    return getattr(db_field, 'original_fieldname', db_field.name) # original_fieldname is set by transmeta


def fallback_language():
    """ returns fallback language """
    return getattr(settings, 'TRANSMETA_DEFAULT_LANGUAGE', \
                   settings.LANGUAGE_CODE)


def get_all_translatable_fields(model, model_trans_fields=None, column_in_current_table=False):
    """ returns all translatable fields in a model (including superclasses ones) """
    if model_trans_fields is None:
        model_trans_fields = set()
    model_trans_fields.update(set(getattr(model._meta, 'translatable_fields', [])))
    for parent in model.__bases__:
        if getattr(parent, '_meta', None) and (not column_in_current_table or parent._meta.abstract):
            get_all_translatable_fields(parent, model_trans_fields, column_in_current_table)
    return tuple(model_trans_fields)


def default_value(field):
    '''
    When accessing to the name of the field itself, the value
    in the current language will be returned. Unless it's set,
    the value in the default language will be returned.
    '''

    def default_value_func(self):
        attname = lambda x: get_real_fieldname(field, x)
        locale = to_locale(get_language())
        if getattr(self, attname(locale), None):
            result = getattr(self, attname(locale))
        elif getattr(self, attname(locale[:2]), None):
            result = getattr(self, attname(locale[:2]))
        else:
            default_language = fallback_language()
            result = getattr(self, attname(default_language), None)
        return result

    return default_value_func


class TransMeta(models.base.ModelBase):
    '''
    Metaclass that allow a django field, to store a value for
    every language. The syntax to us it is next:

        class MyClass(models.Model):
            __metaclass__ = transmeta.TransMeta

            my_field = models.CharField(max_length=20)
            my_i18n_field = models.CharField(max_length=30)

            class Meta:
                translate = ('my_i18n_field',)

    Then we'll be able to access a specific language by
    <field_name>_<language_code>. If just <field_name> is
    accessed, we'll get the value of the current language,
    or if null, the value in the default language.
    '''

    def __new__(cls, name, bases, attrs):
        attrs = SortedDict(attrs)
        if 'Meta' in attrs and hasattr(attrs['Meta'], 'translate'):
            fields = attrs['Meta'].translate
            delattr(attrs['Meta'], 'translate')
        else:
            new_class = super(TransMeta, cls).__new__(cls, name, bases, attrs)
            # we inherits possible translatable_fields from superclasses
            abstract_model_bases = [base for base in bases if hasattr(base, '_meta') \
                                    and base._meta.abstract]
            translatable_fields = []
            for base in abstract_model_bases:
                if hasattr(base._meta, 'translatable_fields'):
                    translatable_fields.extend(list(base._meta.translatable_fields))
            new_class._meta.translatable_fields = tuple(translatable_fields)
            return new_class

        if not isinstance(fields, tuple):
            raise ImproperlyConfigured("Meta's translate attribute must be a tuple")

        default_language = fallback_language()

        for field in fields:
            if not field in attrs or \
               not isinstance(attrs[field], models.fields.Field):
                    raise ImproperlyConfigured(
                        "There is no field %(field)s in model %(name)s, "\
                        "as specified in Meta's translate attribute" % \
                        dict(field=field, name=name))
            original_attr = attrs[field]
            for lang in get_languages():
                lang_code = lang[LANGUAGE_CODE]
                lang_attr = copy.copy(original_attr)
                lang_attr.original_fieldname = field
                lang_attr_name = get_real_fieldname(field, lang_code)
                if lang_code != default_language:
                    # only will be required for default language
                    if not lang_attr.null and lang_attr.default is NOT_PROVIDED:
                        lang_attr.null = True
                    if not lang_attr.blank:
                        lang_attr.blank = True
                lang_attr.verbose_name = LazyString(field, lang_attr, lang_code)
                attrs[lang_attr_name] = lang_attr
            del attrs[field]
            attrs[field] = property(default_value(field))

        new_class = super(TransMeta, cls).__new__(cls, name, bases, attrs)
        if hasattr(new_class, '_meta'):
            new_class._meta.translatable_fields = fields
        return new_class


class LazyString(object):

    def __init__(self, fieldname, field, lang):
        self.fieldname = fieldname
        self.original_verbose_name = field.verbose_name
        self.lang = lang

    def __unicode__(self):
        original_verbose_name = self.original_verbose_name or pretty_name(unicode(self.fieldname))
        verbose_name = u'%s %s' % (original_verbose_name, dict(settings.LANGUAGES)[self.lang])
        return verbose_name.lower()
