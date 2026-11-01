# -*- coding: utf-8 -*-
"""STEP acceptance criteria, assessed for staff.

ELIGIBLE = Condition 1 (NYS resident) AND Condition 2 (grade 7-12) AND
Condition 3 (3a economically disadvantaged OR 3b STEM need).

The assessment never decides an application: every submission goes to staff
review (see rules.py). It records which conditions the answers meet, so staff
don't have to work it out from the form. 3b is always a staff judgment.

Like rules.py, this module imports nothing from Plone. See
docs/eligibility_rules.md for the criteria and the income table's source.
"""
from dataclasses import dataclass
from decimal import Decimal
from typing import Tuple


MET = 'met'
NOT_MET = 'not met'
UNDETERMINED = 'undetermined'

#: Program year of INCOME_LIMITS.
INCOME_YEAR = '2026-2027'

#: NYSED C/STEP & HEOP income eligibility criteria, 2026-2027 column:
#: household size -> highest eligible annual income, in US dollars.
#: Source: "Income Eligibility Criteria 2022-23 through 2027-2028".
INCOME_LIMITS = {
    1: Decimal('28953'),
    2: Decimal('39128'),
    3: Decimal('49303'),
    4: Decimal('59478'),
    5: Decimal('69653'),
    6: Decimal('79828'),
    7: Decimal('90003'),
    8: Decimal('100178'),
}

#: household_size uses 9 for "9 or more", beyond the table's last row.
NINE_OR_MORE = 9

GRADES = ('7', '8', '9', '10', '11', '12')

#: other_economic_disadvantage code -> how the summary names it.
CATEGORICAL_INDICATORS = {
    'public_assistance': 'Family Assistance / Safety Net or Family Day-Care',
    'foster_care': 'foster care, no money from natural parents',
    'ward_of_state': 'ward of the State or a county',
}


@dataclass(frozen=True)
class Check:
    """The outcome of one condition, with the answers behind it."""

    condition: str
    status: str
    detail: str

    def __str__(self):
        return '{0}: {1} ({2})'.format(
            self.condition, self.status, self.detail)


@dataclass(frozen=True)
class Assessment:
    """Every condition's check plus the overall conclusion."""

    checks: Tuple[Check, ...]
    overall: str

    def lines(self):
        return tuple(str(check) for check in self.checks) + (
            'Overall: {0}'.format(self.overall),)


def _money(amount):
    return '${0:,.0f}'.format(amount)


def check_residency(payload):
    answer = payload.get('nys_resident')
    if answer is True:
        return Check('1 NYS resident', MET, 'answered yes')
    if answer is False:
        return Check('1 NYS resident', NOT_MET, 'answered no')
    return Check('1 NYS resident', UNDETERMINED, 'not answered')


def check_grade(payload):
    grade = payload.get('current_grade')
    if grade in GRADES:
        return Check('2 grade 7-12', MET, 'grade {0}'.format(grade))
    if grade is None:
        return Check('2 grade 7-12', UNDETERMINED, 'not answered')
    return Check('2 grade 7-12', NOT_MET, 'grade {0}'.format(grade))


def check_income(payload):
    """Return (status, detail) for the income part of 3a alone."""
    income = payload.get('household_income')
    size = payload.get('household_size')
    if income is None:
        return NOT_MET, 'no income given'
    if size is None:
        return UNDETERMINED, 'no household size given'
    income = Decimal(income)
    if size >= NINE_OR_MORE:
        # The table stops at 8. Limits rise with household size, so income
        # within the 8-person limit is within the limit for any larger one.
        limit = INCOME_LIMITS[8]
        if income <= limit:
            return MET, (
                'income {0} is within the 8-person limit of {1}, so within '
                'the limit for 9 or more, {2} limits'.format(
                    _money(income), _money(limit), INCOME_YEAR))
        return UNDETERMINED, (
            'income {0} for a household of 9 or more; the {1} table stops '
            'at 8 people, so staff must check'.format(
                _money(income), INCOME_YEAR))
    limit = INCOME_LIMITS[size]
    if income <= limit:
        return MET, 'income {0} is at or below {1} for {2}, {3} limits'.format(
            _money(income), _money(limit), _people(size), INCOME_YEAR)
    return NOT_MET, 'income {0} is above {1} for {2}, {3} limits'.format(
        _money(income), _money(limit), _people(size), INCOME_YEAR)


def _people(size):
    return '1 person' if size == 1 else '{0} people'.format(size)


def check_economic(payload):
    """Condition 3a: any one indicator, or income within the limit."""
    met = []
    if payload.get('free_reduced_lunch') is True:
        met.append('free or reduced-price lunch (self-reported; school to '
                   'verify)')
    indicator = payload.get('other_economic_disadvantage')
    if indicator in CATEGORICAL_INDICATORS:
        met.append(CATEGORICAL_INDICATORS[indicator])
    income_status, income_detail = check_income(payload)
    if income_status == MET:
        met.append(income_detail)
    if met:
        return Check('3a economically disadvantaged', MET, '; '.join(met))
    if income_status == UNDETERMINED:
        return Check('3a economically disadvantaged', UNDETERMINED,
                     income_detail)
    return Check('3a economically disadvantaged', NOT_MET,
                 'no indicator selected; ' + income_detail)


def check_stem_need(payload):
    """Condition 3b: only whether there is a statement for staff to judge."""
    statement = payload.get('stem_statement')
    if statement and statement.strip():
        return Check('3b STEM need', UNDETERMINED,
                     'statement provided; staff to judge')
    return Check('3b STEM need', NOT_MET, 'no statement')


def assess(payload):
    """Assess a STEP payload against the acceptance criteria."""
    residency = check_residency(payload)
    grade = check_grade(payload)
    economic = check_economic(payload)
    stem = check_stem_need(payload)
    checks = (residency, grade, economic, stem)
    return Assessment(checks, _overall(residency, grade, economic, stem))


def _overall(residency, grade, economic, stem):
    failed = [c.condition.split()[0] for c in (residency, grade)
              if c.status == NOT_MET]
    if failed:
        return 'does not meet the criteria (condition {0} not met)'.format(
            ' and '.join(failed))
    if UNDETERMINED in (residency.status, grade.status):
        return 'undetermined (condition 1 or 2 not answered)'
    if economic.status == MET:
        return 'meets the criteria (1, 2 and 3a)'
    has_statement = stem.status == UNDETERMINED
    if economic.status == UNDETERMINED:
        if has_statement:
            return ('undetermined: staff to check income (3a) or judge the '
                    'STEM statement (3b)')
        return 'undetermined: staff to check income (3a)'
    if has_statement:
        return ('meets the criteria only if staff judge the STEM statement '
                'shows need (3b)')
    return 'does not meet the criteria (no 3a indicator and no STEM statement)'
