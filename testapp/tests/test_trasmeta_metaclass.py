# coding: utf8

from django.utils.translation import activate
from django.test import TestCase

from testapp.models import TestModel, InheritedTestModel

class TrasMetaMetaClassTestCase(TestCase):

    def assertIsFieldPresent(self, field, model):
        self.assertIn(field, model._meta.get_all_field_names())

    def test_field_for_english_was_created(self):
        self.assertIsFieldPresent('i18n_field_en', TestModel)

    def test_field_for_portuguese_was_created(self):
        self.assertIsFieldPresent('i18n_field_pt_BR', TestModel)

    def test_original_field_name_for_i18n_field_en_should_retrieve_i18n_field(self):
        self.assertEqual('i18n_field', TestModel._meta.get_field('i18n_field_en').original_fieldname)

    def test_original_field_name_for_i18n_field_pt_BR_should_retrieve_i18n_field(self):
        self.assertEqual('i18n_field', TestModel._meta.get_field('i18n_field_pt_BR').original_fieldname)

    def test_field_for_english_verbose_name_should_be_the_verbose_name_with_the_language_name(self):
        self.assertEqual('i18n field english', unicode(TestModel._meta.get_field('i18n_field_en').verbose_name))

    def test_field_without_language_defined_should_respect_the_active_language(self):
        obj = TestModel(i18n_field_en='value', i18n_field_pt_BR='valor')
        activate('en')
        self.assertEqual('value', obj.i18n_field)
        activate('pt-br')
        self.assertEqual('valor', obj.i18n_field)

    def test_field_without_language_defined_should_return_the_default_language_value_if_theres_no_value_for_the_active_language(self):
        obj = TestModel(i18n_field_en='value')
        activate('pt-br')
        self.assertEqual('value', obj.i18n_field)

    def test_model_meta_should_have_an_attribute_with_the_translatable_fields(self):
        self.assertIn('i18n_field', TestModel._meta.translatable_fields)

    def test_field_for_english_was_created_in_inherited_model(self):
        self.assertIsFieldPresent('i18n_field_en', InheritedTestModel)

