# coding: utf8

from django.db import models

from transmeta import TransMeta


class TestModel(models.Model):
    __metaclass__ = TransMeta

    i18n_field = models.CharField(max_length=255)

    class Meta:
        translate = ('i18n_field',)


class InheritedTestModel(TestModel):

    noni18n_field = models.CharField(max_length=255)
