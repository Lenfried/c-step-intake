# -*- coding: utf-8 -*-
"""Unit tests for the eligibility engine.

No Plone layer: rules.py imports no framework code, so these run in
milliseconds. When the program's criteria are agreed, add one test per row of
the decision table here before touching rules.py.
"""
import unittest
from datetime import date
from decimal import Decimal

from c_step_intake.eligibility import rules
from c_step_intake.eligibility.decision import MANUAL_REVIEW
from c_step_intake.eligibility.decision import REQUEST_INFO


def step_payload(**overrides):
    payload = {
        'first_name': 'Ada',
        'last_name': 'Lovelace',
        'date_of_birth': date(2010, 12, 10),
        'student_email': 'ada@example.edu',
        'student_phone_number': '718-262-2000',
        'street_address': '94-20 Guy R Brewer Blvd',
        'city': 'Jamaica',
        'state': 'NY',
        'zip_code': '11451',
        'nys_resident': True,
        'household_size': 4,
        'school_name': 'York Early College Academy',
        'current_grade': '11',
        'cumulative_gpa': Decimal('88'),
        'parent1_first_name': 'Anne',
        'parent1_last_name': 'Byron',
        'parent1_email': 'anne@example.com',
        'parent1_phone': '718-262-2001',
    }
    payload.update(overrides)
    return payload


def cstep_payload(**overrides):
    payload = {
        'first_name': 'Grace',
        'last_name': 'Hopper',
        'date_of_birth': date(2004, 12, 9),
        'student_email': 'grace@york.cuny.edu',
        'student_phone_number': '718-262-2002',
        'street_address': '94-20 Guy R Brewer Blvd',
        'city': 'Jamaica',
        'state': 'NY',
        'zip_code': '11451',
        'nys_resident': True,
        'household_size': 2,
        'emplid': '12345678',
        'classification': 'junior',
        'major': 'computer_science_bs',
        'gpa': Decimal('3.4'),
        'degree_type': 'bachelors',
        'support_statement': 'I would benefit from tutoring in calculus.',
        'consent': True,
    }
    payload.update(overrides)
    return payload


class TestCompleteness(unittest.TestCase):

    def test_complete_step_application_goes_to_manual_review(self):
        decision = rules.decide(rules.STEP, step_payload())
        self.assertEqual(MANUAL_REVIEW, decision.outcome)
        self.assertEqual('flag_for_review', decision.transition)
        self.assertEqual((), decision.missing_fields)

    def test_complete_cstep_application_goes_to_manual_review(self):
        decision = rules.decide(rules.CSTEP, cstep_payload())
        self.assertEqual(MANUAL_REVIEW, decision.outcome)

    def test_missing_field_requests_info_and_names_the_field(self):
        decision = rules.decide(rules.STEP, step_payload(school_name=None))
        self.assertEqual(REQUEST_INFO, decision.outcome)
        self.assertEqual(('school_name',), decision.missing_fields)
        self.assertIn('school_name', decision.reason)

    def test_blank_string_counts_as_missing(self):
        decision = rules.decide(rules.STEP, step_payload(first_name='   '))
        self.assertEqual(('first_name',), decision.missing_fields)

    def test_false_boolean_is_an_answer_not_a_gap(self):
        # A student who is not a NY resident has answered the question. The
        # completeness check must not confuse False with unanswered.
        decision = rules.decide(rules.STEP, step_payload(nys_resident=False))
        self.assertEqual((), decision.missing_fields)

    def test_missing_fields_are_reported_in_schema_order(self):
        decision = rules.decide(
            rules.STEP,
            step_payload(city=None, first_name=None),
        )
        self.assertEqual(('first_name', 'city'), decision.missing_fields)

    def test_household_income_is_never_required(self):
        # Income is optional by design; a categorical indicator may stand in.
        decision = rules.decide(rules.STEP, step_payload(household_income=None))
        self.assertEqual((), decision.missing_fields)

    def test_career_aspiration_is_never_required(self):
        # Optional by design; it only matters for applicants whose major is
        # not itself STEM/licensure, and that rule is not yet implemented.
        decision = rules.decide(rules.CSTEP, cstep_payload(career_aspiration=None))
        self.assertEqual((), decision.missing_fields)

    def test_step_and_cstep_require_different_fields(self):
        # A CSTEP payload is not a complete STEP application and vice versa.
        self.assertTrue(rules.missing_fields(rules.STEP, cstep_payload()))
        self.assertTrue(rules.missing_fields(rules.CSTEP, step_payload()))

    def test_unknown_program_is_an_error(self):
        with self.assertRaises(ValueError):
            rules.decide('mstep', step_payload())


class TestAuditability(unittest.TestCase):

    def test_every_decision_carries_the_rules_version(self):
        for program, payload in (
            (rules.STEP, step_payload()),
            (rules.CSTEP, cstep_payload()),
            (rules.STEP, step_payload(school_name=None)),
        ):
            decision = rules.decide(program, payload)
            self.assertEqual(rules.RULES_VERSION, decision.rules_version)

    def test_decision_is_immutable(self):
        decision = rules.decide(rules.STEP, step_payload())
        with self.assertRaises(Exception):
            decision.outcome = 'accept'

    def test_no_payload_reaches_a_decision_of_reject(self):
        # Guard rail while the criteria are undefined: nothing may auto-reject
        # until docs/eligibility_rules.md is signed off. Delete this test in
        # the same commit that adds the first reject rule.
        for payload in (step_payload(), step_payload(cumulative_gpa=Decimal('0'))):
            self.assertNotEqual('reject', rules.decide(rules.STEP, payload).outcome)
