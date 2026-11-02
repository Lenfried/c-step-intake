# -*- coding: utf-8 -*-
"""The STEP school pick-list stores schools in NYSED reporting format."""
from types import SimpleNamespace

from c_step_intake.content.step_application import IStepApplication
from c_step_intake.db.serializer import DERIVED
from c_step_intake.eligibility import rules
from c_step_intake.testing import C_STEP_INTAKE_INTEGRATION_TESTING
from c_step_intake.tests.test_eligibility_rules import step_payload
from c_step_intake.vocabularies import parse_school
from c_step_intake.vocabularies import SCHOOL_NOT_LISTED
from c_step_intake.vocabularies import SCHOOLS_FILE
from c_step_intake.vocabularies import step_schools
from zope.component import getUtility
from zope.interface import Invalid
from zope.schema.interfaces import IVocabularyFactory

import json
import unittest

YORK = 'YORK EARLY COLLEGE ACADEMY  (QUEENS) 342800011284'


def listed_schools():
    with open(SCHOOLS_FILE, encoding='utf-8') as data:
        return [school for borough in json.load(data)['boroughs']
                for school in borough['schools']]


class TestSchoolList(unittest.TestCase):

    def test_every_school_in_the_file_is_offered_verbatim(self):
        values = [term.value for term in step_schools()][1:]
        self.assertEqual(listed_schools(), values)
        self.assertEqual(1998, len(values))

    def test_not_listed_is_the_first_choice(self):
        first = list(step_schools())[0]
        self.assertEqual(SCHOOL_NOT_LISTED, first.value)
        self.assertIn('isn’t listed', str(first.title))

    def test_stored_value_is_the_reporting_format(self):
        term = step_schools().getTermByToken('342800011284')
        self.assertEqual(YORK, term.value)
        self.assertEqual('YORK EARLY COLLEGE ACADEMY (Queens)', term.title)
        self.assertEqual(
            ('YORK EARLY COLLEGE ACADEMY', 'QUEENS', '342800011284'),
            parse_school(term.value))

    def test_beds_codes_are_unique_tokens(self):
        # Some names repeat ("SUMMIT SCHOOL (THE)" twice in Queens); the BEDS
        # code tells them apart.
        tokens = [term.token for term in step_schools()]
        self.assertEqual(len(tokens), len(set(tokens)))

    def test_parse_school_rejects_other_formats(self):
        for value in ('York Early College Academy',
                      'YORK EARLY COLLEGE ACADEMY (QUEENS) 342800011284',
                      'YORK EARLY COLLEGE ACADEMY  (QUEENS) 3428000112',
                      SCHOOL_NOT_LISTED, None):
            self.assertIsNone(parse_school(value), value)


class TestSchoolField(unittest.TestCase):

    layer = C_STEP_INTAKE_INTEGRATION_TESTING

    def test_vocabulary_is_registered(self):
        factory = getUtility(IVocabularyFactory, 'c_step_intake.StepSchools')
        self.assertIn(YORK, factory(None))

    def test_school_name_only_accepts_listed_schools(self):
        field = IStepApplication['school_name'].bind(None)
        field.validate(YORK)
        field.validate(SCHOOL_NOT_LISTED)
        with self.assertRaises(Exception):
            field.validate('York Early College Academy')

    def test_unlisted_school_must_be_named(self):
        with self.assertRaises(Invalid):
            IStepApplication.validateInvariants(SimpleNamespace(
                school_name=SCHOOL_NOT_LISTED, school_name_other='  '))
        IStepApplication.validateInvariants(SimpleNamespace(
            school_name=SCHOOL_NOT_LISTED,
            school_name_other='Ward Melville High School, East Setauket'))
        IStepApplication.validateInvariants(SimpleNamespace(
            school_name=YORK, school_name_other=None))


class TestUnlistedSchoolRules(unittest.TestCase):

    def test_unnamed_unlisted_school_is_missing_after_school_name(self):
        missing = rules.missing_fields(rules.STEP, step_payload(
            school_name=SCHOOL_NOT_LISTED, current_grade=None, first_name=''))
        self.assertEqual(('first_name', 'school_name_other', 'current_grade'),
                         missing)

    def test_named_unlisted_school_is_complete(self):
        self.assertEqual((), rules.missing_fields(rules.STEP, step_payload(
            school_name=SCHOOL_NOT_LISTED, school_name_other='Ward Melville')))

    def test_listed_school_needs_no_other_name(self):
        self.assertEqual((), rules.missing_fields(rules.STEP, step_payload()))


class TestSchoolColumn(unittest.TestCase):

    def test_listed_school_is_written_in_reporting_format(self):
        obj = SimpleNamespace(school_name=YORK, school_name_other='ignored')
        self.assertEqual(YORK, DERIVED['school_name'](obj))

    def test_unlisted_school_is_written_as_typed(self):
        obj = SimpleNamespace(school_name=SCHOOL_NOT_LISTED,
                              school_name_other='Ward Melville High School')
        self.assertEqual('Ward Melville High School',
                         DERIVED['school_name'](obj))
