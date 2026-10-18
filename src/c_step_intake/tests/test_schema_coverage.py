# -*- coding: utf-8 -*-
"""Guards against the field map falling behind the form.

Adding a field to a schema without deciding where it goes in PostgreSQL is the
easiest way for the two to drift apart, and the drift is invisible until IT
notices a column is always null. These tests fail loudly instead.
"""
import unittest

from c_step_intake.behaviors.applicant_identity import IApplicantIdentity
from c_step_intake.behaviors.economic_eligibility import IEconomicEligibility
from c_step_intake.content.cstep_application import ICstepApplication
from c_step_intake.content.step_application import IStepApplication
from c_step_intake.db import field_map
from c_step_intake.db.serializer import DERIVED
from c_step_intake.eligibility import rules
from zope.schema import getFieldNames


SHARED = (IApplicantIdentity, IEconomicEligibility)
STEP_SCHEMATA = SHARED + (IStepApplication,)
CSTEP_SCHEMATA = SHARED + (ICstepApplication,)


def field_names(schemata):
    names = set()
    for schema in schemata:
        names.update(getFieldNames(schema))
    return names


class TestSchemaCoverage(unittest.TestCase):

    def test_every_step_field_is_mapped_or_explicitly_unmapped(self):
        self._assert_covered(STEP_SCHEMATA)

    def test_every_cstep_field_is_mapped_or_explicitly_unmapped(self):
        self._assert_covered(CSTEP_SCHEMATA)

    def test_no_stale_mappings(self):
        # A mapping whose Plone field no longer exists would silently produce
        # a null column.
        known = field_names(STEP_SCHEMATA) | field_names(CSTEP_SCHEMATA)
        self.assertEqual(set(), field_map.mapped_fields() - known)

    def test_no_stale_unmapped_entries(self):
        known = field_names(STEP_SCHEMATA) | field_names(CSTEP_SCHEMATA)
        self.assertEqual(set(), set(field_map.UNMAPPED) - known)

    def test_required_at_submit_fields_all_exist(self):
        for program, schemata in (
            (rules.STEP, STEP_SCHEMATA),
            (rules.CSTEP, CSTEP_SCHEMATA),
        ):
            missing = set(rules.REQUIRED_AT_SUBMIT[program]) - field_names(schemata)
            self.assertEqual(set(), missing, program)

    def test_every_derived_column_has_a_getter(self):
        # A derived column with no entry in serializer.DERIVED raises KeyError
        # on the first submission, not at import time.
        derived = {m.column for m in field_map.APPLICATIONS if not m.field}
        self.assertEqual(set(), derived - set(DERIVED))

    def test_no_orphan_getters(self):
        derived = {m.column for m in field_map.APPLICATIONS if not m.field}
        self.assertEqual(set(), set(DERIVED) - derived)

    def _assert_covered(self, schemata):
        uncovered = (
            field_names(schemata)
            - field_map.mapped_fields()
            - set(field_map.UNMAPPED)
        )
        self.assertEqual(
            set(),
            uncovered,
            'Unmapped schema fields. Add them to field_map.APPLICATIONS or, '
            'if they are deliberately not stored, to field_map.UNMAPPED: '
            '{0}'.format(sorted(uncovered)),
        )
