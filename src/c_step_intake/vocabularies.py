# -*- coding: utf-8 -*-
"""Vocabularies shared by the STEP and CSTEP application schemas.

Terms carry a stable machine ``value`` and a human ``title``. Only the value is
persisted and written to PostgreSQL, so option wording can be reworded for
applicants without invalidating stored records or breaking report queries.
"""
from functools import lru_cache

import json
import os
import re

from c_step_intake import _
from zope.interface import provider
from zope.schema.interfaces import IVocabularyFactory
from zope.schema.vocabulary import SimpleTerm
from zope.schema.vocabulary import SimpleVocabulary


def _vocabulary(pairs):
    return SimpleVocabulary(
        [SimpleTerm(value=value, token=value, title=_(title))
         for value, title in pairs]
    )


GENDER = _vocabulary([
    ('female', 'Female'),
    ('male', 'Male'),
    ('non_binary', 'Non-binary'),
    ('prefer_not_to_say', 'Prefer not to say'),
])

# Single combined race/ethnicity question, matching the existing paper form.
# NYSED and federal reporting expect Hispanic/Latino ethnicity to be asked
# separately from race, and race to allow multiple selections. See
# docs/field_mapping.md, open question Q3.
ETHNICITY = _vocabulary([
    ('hispanic_latino', 'Hispanic or Latino'),
    ('black', 'Black or African American'),
    ('asian', 'Asian'),
    ('white', 'White'),
    ('american_indian', 'American Indian or Native Alaskan'),
    ('pacific_islander', 'Native Hawaiian or Pacific Islander'),
    ('unknown', 'Unknown'),
])

# Integer values so household size can be used directly in income-threshold
# arithmetic once thresholds are defined. 9 means "9 or more".
HOUSEHOLD_SIZE = SimpleVocabulary([
    SimpleTerm(value=size, token=str(size), title=_(str(size)))
    for size in range(1, 9)
] + [SimpleTerm(value=9, token='9', title=_('9 or more'))])

OTHER_ECONOMIC_DISADVANTAGE = _vocabulary([
    ('public_assistance',
     'My family receives family assistance program aid or safety net '
     'assistance through the New York State Office of Temporary and '
     'Disability Assistance or a county department of social services; or '
     'receives family day-care payments through the New York State Office of '
     'Children and Family Services or a county department of social services. '
     '(Examples: SNAP/food stamps, public assistance, SSI, subsidized '
     'childcare/daycare assistance, or other social services assistance.)'),
    ('foster_care',
     'I am living with foster parents and no financial support is provided by '
     'my natural (biological) parents.'),
    ('ward_of_state',
     'I am a ward of the State of New York or of a county.'),
])

GRADE_LEVEL = _vocabulary([
    ('7', '7th grade'),
    ('8', '8th grade'),
    ('9', '9th grade'),
    ('10', '10th grade'),
    ('11', '11th grade'),
    ('12', '12th grade'),
])

CLASSIFICATION = _vocabulary([
    ('freshman', 'Freshman'),
    ('sophomore', 'Sophomore'),
    ('junior', 'Junior'),
    ('senior', 'Senior'),
])

MAJOR = _vocabulary([
    ('accounting_finance_bs', 'Accounting and Finance BS'),
    ('aviation_management_bs', 'Aviation Management BS'),
    ('chemistry', 'Chemistry BA/BS'),
    ('computer_science_bs', 'Computer Science BS'),
    ('health_profession_bs', 'Health Profession BS'),
    ('information_systems_management_bs', 'Information Systems Management BS'),
    ('mathematics', 'Mathematics BA/BS'),
    ('nursing_bs', 'Nursing BS'),
    ('occupational_therapy', 'Occupational Therapy BS/MS'),
    ('physics_bs', 'Physics BS'),
    ('social_work', 'Social Work BS/MS'),
    ('other', 'Other'),
])

DEGREE_TYPE = _vocabulary([
    ('associates', 'Associates'),
    ('bachelors', 'Bachelors'),
    ('masters', 'Masters'),
])


# --- STEP schools ---------------------------------------------------------
#
# The STEP school field is a pick-list so that every value is already in the
# exact form NYSED reporting expects: "NAME  (COUNTY) BEDSCODE", e.g.
# "YORK EARLY COLLEGE ACADEMY  (QUEENS) 342800011284" (two spaces before the
# county, then the 12-digit BEDS code). The stored value is that string,
# verbatim from data/step_schools.json (NYSED IMF secondary schools, grades
# 7-12). To update the list, replace that file; saved applications keep the
# string they were submitted with.

#: Value of the "My school isn't listed" choice; school_name_other then holds
#: the school's name as typed.
SCHOOL_NOT_LISTED = 'other'

SCHOOLS_FILE = os.path.join(os.path.dirname(__file__), 'data',
                            'step_schools.json')

_SCHOOL = re.compile(
    r'^(?P<name>.+?)  \((?P<county>[A-Z ]+)\) (?P<code>\d{12})$')


def parse_school(value):
    """Return (name, county, BEDS code) of a listed school, or None."""
    match = _SCHOOL.match(value or '')
    return match.groups() if match else None


@lru_cache(maxsize=1)
def step_schools():
    """Build the school vocabulary once; the list only changes on release.

    Token: the BEDS code, unique even where two schools share a name.
    Title: what applicants see, e.g. "YORK EARLY COLLEGE ACADEMY (Queens)".
    """
    with open(SCHOOLS_FILE, encoding='utf-8') as data:
        boroughs = json.load(data)['boroughs']
    terms = [SimpleTerm(value=SCHOOL_NOT_LISTED, token=SCHOOL_NOT_LISTED,
                        title=_('My school isn\u2019t listed'))]
    for borough in boroughs:
        for school in borough['schools']:
            parsed = parse_school(school)
            if parsed is None:
                raise ValueError(
                    'Not in NYSED reporting format: {0!r}'.format(school))
            name, _county, code = parsed
            terms.append(SimpleTerm(
                value=school, token=code,
                title='{0} ({1})'.format(name, borough['label'])))
    return SimpleVocabulary(terms)


@provider(IVocabularyFactory)
def StepSchoolsVocabularyFactory(context):
    return step_schools()
