# -*- coding: utf-8 -*-
"""STEP application -- the high-school (grades 7-12) program.

Identity, contact, address and household fields come from the shared
behaviors. Only the fields specific to a school-age applicant live here.

STEP applicants are minors, so parent/guardian contact details are required
rather than optional; this is a legal requirement, not a variant of the CSTEP
form.
"""
from decimal import Decimal

from plone.dexterity.content import Item
from plone.schema import Email
from plone.supermodel import model
from c_step_intake import _
from c_step_intake.interfaces import IApplication
from c_step_intake.vocabularies import GRADE_LEVEL
from c_step_intake.vocabularies import SCHOOL_NOT_LISTED
from z3c.form.browser.radio import RadioFieldWidget
from zope import schema
from zope.interface import implementer
from zope.interface import Invalid
from zope.interface import invariant


class IStepApplication(model.Schema):
    """Schema for a STEP (high school) application."""

    model.fieldset(
        'school',
        label=_('School'),
        fields=['school_name', 'school_name_other', 'current_grade',
                'cumulative_gpa'],
    )

    model.fieldset(
        'household',
        label=_('Household'),
        fields=['free_reduced_lunch'],
    )

    model.fieldset(
        'guardian',
        label=_('Parent / Guardian'),
        fields=[
            'parent1_first_name',
            'parent1_last_name',
            'parent1_email',
            'parent1_phone',
            'parent2_first_name',
            'parent2_last_name',
            'parent2_email',
            'parent2_phone',
        ],
    )

    model.fieldset(
        'statement',
        label=_('STEM statement'),
        fields=['stem_statement'],
    )

    # A pick-list, so the value is already in NYSED reporting format
    # ("NAME  (COUNTY) BEDSCODE"); see vocabularies.step_schools.
    school_name = schema.Choice(
        title=_('School name'),
        description=_(
            'Start typing to search. If your school isn\u2019t in the list, '
            'choose \u201cMy school isn\u2019t listed\u201d and type its name '
            'below.'
        ),
        vocabulary='c_step_intake.StepSchools',
        required=True,
    )

    school_name_other = schema.TextLine(
        title=_('School name, if not listed'),
        description=_(
            'Only if you chose \u201cMy school isn\u2019t listed\u201d above. '
            'Include the school\u2019s city or county.'
        ),
        required=False,
    )

    current_grade = schema.Choice(
        title=_('Current grade'),
        vocabulary=GRADE_LEVEL,
        required=True,
    )

    # High schools in New York City commonly report a 0-100 average rather
    # than a 4.0 GPA. No upper bound is enforced; only negative values are
    # rejected. Which scale a given number is on cannot be inferred
    # reliably -- see docs/field_mapping.md, Q4.
    cumulative_gpa = schema.Decimal(
        title=_('Cumulative GPA'),
        description=_(
            'Enter your GPA as it appears on your transcript, on either a '
            '4.0 scale or a 100-point scale.'
        ),
        min=Decimal('0'),
        required=True,
    )

    free_reduced_lunch = schema.Bool(
        title=_('Do you receive free or reduced-price school lunch?'),
        required=False,
    )

    parent1_first_name = schema.TextLine(
        title=_('Parent / guardian first name'),
        required=True,
    )

    parent1_last_name = schema.TextLine(
        title=_('Parent / guardian last name'),
        required=True,
    )

    parent1_email = Email(
        title=_('Parent / guardian email'),
        required=True,
    )

    parent1_phone = schema.TextLine(
        title=_('Parent / guardian phone'),
        required=True,
    )

    parent2_first_name = schema.TextLine(
        title=_('Second parent / guardian first name'),
        required=False,
    )

    parent2_last_name = schema.TextLine(
        title=_('Second parent / guardian last name'),
        required=False,
    )

    parent2_email = Email(
        title=_('Second parent / guardian email'),
        required=False,
    )

    parent2_phone = schema.TextLine(
        title=_('Second parent / guardian phone'),
        required=False,
    )

    # STEP eligibility condition 3b: an applicant who is not economically
    # disadvantaged can still qualify on STEM need, which program staff judge
    # from this statement. It is optional because condition 3a alone also
    # qualifies, and it is read during review only -- never written to
    # step_student (see field_map.UNMAPPED).
    stem_statement = schema.Text(
        title=_(
            'How would you express your need of, or how would you greatly '
            'benefit from, academic enrichment or support in the STEM areas?'
        ),
        description=_(
            'Optional. Program staff read this when reviewing your '
            'application. It is especially important if none of the '
            'household questions apply to you.'
        ),
        required=False,
    )

    @invariant
    def unlisted_school_is_named(data):
        if getattr(data, 'school_name', None) == SCHOOL_NOT_LISTED:
            if not (getattr(data, 'school_name_other', None) or '').strip():
                raise Invalid(_(
                    'Please type your school\u2019s name, since you chose '
                    '\u201cMy school isn\u2019t listed\u201d.'))


IStepApplication.setTaggedValue(
    'plone.autoform.widgets',
    {'current_grade': RadioFieldWidget, 'free_reduced_lunch': RadioFieldWidget},
)


@implementer(IStepApplication, IApplication)
class StepApplication(Item):
    """A STEP application."""

    program = 'step'

    @property
    def title(self):
        return '{0}, {1}'.format(self.last_name or '', self.first_name or '')

    @title.setter
    def title(self, value):
        pass
