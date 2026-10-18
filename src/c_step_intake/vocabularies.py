# -*- coding: utf-8 -*-
"""Vocabularies shared by the STEP and CSTEP application schemas.

Terms carry a stable machine ``value`` and a human ``title``. Only the value is
persisted and written to PostgreSQL, so option wording can be reworded for
applicants without invalidating stored records or breaking report queries.
"""
from c_step_intake import _
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
