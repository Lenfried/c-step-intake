# -*- coding: utf-8 -*-
"""STEP acceptance criteria assessment.

No Plone layer, like test_eligibility_rules.py.
"""
import unittest
from decimal import Decimal

from c_step_intake.eligibility import rules
from c_step_intake.eligibility import step_criteria as criteria
from c_step_intake.eligibility.decision import MANUAL_REVIEW
from c_step_intake.tests.test_eligibility_rules import cstep_payload
from c_step_intake.tests.test_eligibility_rules import step_payload


def assess(**overrides):
    return criteria.assess(step_payload(**overrides))


def economic(**overrides):
    return criteria.check_economic(step_payload(**overrides))


class TestIncomeTable(unittest.TestCase):

    def test_limits_are_the_2026_2027_column(self):
        self.assertEqual('2026-2027', criteria.INCOME_YEAR)
        self.assertEqual(
            [28953, 39128, 49303, 59478, 69653, 79828, 90003, 100178],
            [int(criteria.INCOME_LIMITS[size]) for size in range(1, 9)],
        )

    def test_income_at_the_limit_qualifies(self):
        check = economic(household_size=4, household_income=Decimal('59478'))
        self.assertEqual(criteria.MET, check.status)

    def test_income_one_dollar_over_the_limit_does_not(self):
        check = economic(household_size=4, household_income=Decimal('59479'))
        self.assertEqual(criteria.NOT_MET, check.status)
        self.assertIn('above $59,478 for 4 people', check.detail)

    def test_no_income_and_no_indicator_is_not_met(self):
        check = economic(household_income=None)
        self.assertEqual(criteria.NOT_MET, check.status)

    def test_nine_or_more_within_the_eight_person_limit_qualifies(self):
        check = economic(household_size=9, household_income=Decimal('100178'))
        self.assertEqual(criteria.MET, check.status)

    def test_nine_or_more_above_the_eight_person_limit_is_for_staff(self):
        # The 2026-27 table stops at 8 people, so there is no limit to
        # compare against. Staff decide; nothing is guessed.
        check = economic(household_size=9, household_income=Decimal('100179'))
        self.assertEqual(criteria.UNDETERMINED, check.status)
        self.assertIn('staff must check', check.detail)


class TestEconomicIndicators(unittest.TestCase):

    def test_each_indicator_alone_meets_3a(self):
        for code in ('public_assistance', 'foster_care', 'ward_of_state'):
            check = economic(other_economic_disadvantage=code,
                             household_income=Decimal('1000000'))
            self.assertEqual(criteria.MET, check.status, code)

    def test_free_lunch_alone_meets_3a_and_is_flagged_for_verification(self):
        check = economic(free_reduced_lunch=True, household_income=None)
        self.assertEqual(criteria.MET, check.status)
        self.assertIn('school to verify', check.detail)

    def test_free_lunch_no_or_unanswered_does_not_count(self):
        for answer in (False, None):
            check = economic(free_reduced_lunch=answer, household_income=None)
            self.assertEqual(criteria.NOT_MET, check.status, answer)

    def test_every_indicator_that_applies_is_listed(self):
        check = economic(free_reduced_lunch=True,
                         other_economic_disadvantage='foster_care',
                         household_size=2, household_income=Decimal('20000'))
        self.assertIn('lunch', check.detail)
        self.assertIn('foster care', check.detail)
        self.assertIn('$20,000', check.detail)


class TestOverall(unittest.TestCase):

    def test_resident_in_grade_and_disadvantaged_meets_the_criteria(self):
        result = assess(other_economic_disadvantage='ward_of_state')
        self.assertEqual('meets the criteria (1, 2 and 3a)', result.overall)

    def test_not_a_resident_does_not_meet_the_criteria(self):
        result = assess(nys_resident=False, free_reduced_lunch=True)
        self.assertIn('does not meet', result.overall)
        self.assertIn('condition 1', result.overall)

    def test_not_disadvantaged_can_still_qualify_on_stem_need(self):
        # From the criteria: not economically disadvantaged, eligible solely
        # on STEM need (3b) -- which staff judge.
        result = assess(household_income=Decimal('500000'),
                        stem_statement='I want to study robotics.')
        self.assertIn('only if staff judge the STEM statement',
                      result.overall)

    def test_no_statement_can_still_qualify_on_economic_need(self):
        # From the criteria: no STEM statement, eligible solely on 3a.
        result = assess(other_economic_disadvantage='public_assistance',
                        stem_statement=None)
        self.assertEqual('meets the criteria (1, 2 and 3a)', result.overall)

    def test_neither_3a_nor_3b_does_not_meet_the_criteria(self):
        result = assess(household_income=Decimal('500000'),
                        stem_statement='   ')
        self.assertIn('no 3a indicator and no STEM statement', result.overall)

    def test_income_for_staff_to_check_is_undetermined(self):
        result = assess(household_size=9, household_income=Decimal('150000'))
        self.assertIn('undetermined', result.overall)

    def test_lines_cover_every_condition_and_the_conclusion(self):
        lines = assess().lines()
        self.assertEqual(5, len(lines))
        self.assertTrue(lines[0].startswith('1 NYS resident: met'))
        self.assertTrue(lines[-1].startswith('Overall: '))


class TestDecisionCarriesTheAssessment(unittest.TestCase):

    def test_step_decision_records_the_assessment(self):
        decision = rules.decide(rules.STEP, step_payload(
            other_economic_disadvantage='foster_care'))
        data = decision.assessment.as_dict()
        self.assertEqual(
            ['1 NYS resident', '2 grade 7-12',
             '3a economically disadvantaged', '3b STEM need'],
            [check['condition'] for check in data['checks']])
        self.assertEqual('met', data['checks'][2]['status'])
        self.assertEqual('meets the criteria (1, 2 and 3a)', data['overall'])
        self.assertIn('meets the criteria', decision.reason)

    def test_failing_the_criteria_still_goes_to_staff(self):
        # Program decision: staff review everything; the rules never reject.
        decision = rules.decide(rules.STEP, step_payload(nys_resident=False))
        self.assertEqual(MANUAL_REVIEW, decision.outcome)
        self.assertIn('does not meet', decision.reason)

    def test_cstep_has_no_assessment_yet(self):
        decision = rules.decide(rules.CSTEP, cstep_payload())
        self.assertIsNone(decision.assessment)
