# coding: utf8

from django.utils.translation import activate
from django.test import TestCase

from testapp.models import TestModel

class TrasMetaMetaClassTestCase(TestCase):

    def assertIsFieldPresent(self, field, model):
        self.assertIn(field, model._meta.get_all_field_names())

    def test_field_for_english_were_created(self):
        self.assertIsFieldPresent('i18n_field_en', TestModel)

    def test_field_for_portuguese_were_created(self):
        self.assertIsFieldPresent('i18n_field_pt_BR', TestModel)

    def test_field_for_english_verbose_name_should_be_the_verbose_name_with_the_language_name(self):
        self.assertEqual('I18n field English', unicode(TestModel._meta.get_field('i18n_field_en').verbose_name))

    def test_field_without_language_defined_should_respect_the_active_language(self):
        obj = TestModel(i18n_field_en='value', i18n_field_pt_BR='valor')
        activate('en')
        self.assertEqual('value', obj.i18n_field)
        activate('pt-br')
        self.assertEqual('valor', obj.i18n_field)

