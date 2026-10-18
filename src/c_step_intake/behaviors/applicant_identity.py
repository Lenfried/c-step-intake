# -*- coding: utf-8 -*-
"""Identity, contact and address fields shared by STEP and CSTEP applications.

Both programs collect this block verbatim, so it lives in one behavior rather
than being duplicated across the two content schemas. Program-specific fields
(school/grade/guardians for STEP, EMPLID/major/classification for CSTEP) stay
on their own content type.
"""
import re

from plone.autoform.interfaces import IFormFieldProvider
from plone.schema import Email
from plone.supermodel import model
from c_step_intake import _
from c_step_intake.vocabularies import ETHNICITY
from c_step_intake.vocabularies import GENDER
from z3c.form.browser.radio import RadioFieldWidget
from zope import schema
from zope.interface import Invalid
from zope.interface import provider


_ZIP_CODE = re.compile(r'^\d{5}(-\d{4})?$')
_PHONE_DIGITS = re.compile(r'\D')


def validate_zip_code(value):
    if not _ZIP_CODE.match(value or ''):
        raise Invalid(_('Enter a 5-digit ZIP code, optionally as 12345-6789.'))
    return True


def validate_phone(value):
    if len(_PHONE_DIGITS.sub('', value or '')) != 10:
        raise Invalid(_('Enter a 10-digit phone number, e.g. 718-262-2000.'))
    return True


@provider(IFormFieldProvider)
class IApplicantIdentity(model.Schema):
    """Who the applicant is and how to reach them."""

    model.fieldset(
        'contact',
        label=_('Contact & Address'),
        fields=[
            'student_email',
            'student_phone_number',
            'street_address',
            'apartment_number',
            'city',
            'state',
            'zip_code',
            'nys_resident',
        ],
    )

    first_name = schema.TextLine(
        title=_('First name'),
        required=True,
    )

    last_name = schema.TextLine(
        title=_('Last name'),
        required=True,
    )

    date_of_birth = schema.Date(
        title=_('Date of birth'),
        required=True,
    )

    gender = schema.Choice(
        title=_('Gender'),
        vocabulary=GENDER,
        required=True,
    )

    ethnicity = schema.Choice(
        title=_('Race / Ethnicity'),
        vocabulary=ETHNICITY,
        required=True,
    )

    student_email = Email(
        title=_('Email'),
        description=_('The applicant’s own email address.'),
        required=True,
    )

    student_phone_number = schema.TextLine(
        title=_('Phone number'),
        constraint=validate_phone,
        required=True,
    )

    street_address = schema.TextLine(
        title=_('Street address'),
        required=True,
    )

    apartment_number = schema.TextLine(
        title=_('Apartment number'),
        required=False,
    )

    city = schema.TextLine(
        title=_('City'),
        required=True,
    )

    state = schema.TextLine(
        title=_('State'),
        description=_('Two-letter abbreviation, e.g. NY.'),
        max_length=2,
        default='NY',
        required=True,
    )

    zip_code = schema.TextLine(
        title=_('ZIP code'),
        constraint=validate_zip_code,
        required=True,
    )

    nys_resident = schema.Bool(
        title=_('Are you a resident of New York State?'),
        required=True,
    )


IApplicantIdentity.setTaggedValue(
    'plone.autoform.widgets',
    {'gender': RadioFieldWidget, 'nys_resident': RadioFieldWidget},
)
