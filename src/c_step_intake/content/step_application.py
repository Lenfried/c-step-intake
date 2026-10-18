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
from z3c.form.browser.radio import RadioFieldWidget
from zope import schema
from zope.interface import implementer


class IStepApplication(model.Schema):
    """Schema for a STEP (high school) application."""

    model.fieldset(
        'school',
        label=_('School'),
        fields=['school_name', 'current_grade', 'cumulative_gpa'],
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

    school_name = schema.TextLine(
        title=_('School name'),
        required=True,
    )

    current_grade = schema.Choice(
        title=_('Current grade'),
        vocabulary=GRADE_LEVEL,
        required=True,
    )

    # High schools in New York City commonly report a 0-100 average rather
    # than a 4.0 GPA, so the range accepts both. Which scale a given number
    # is on cannot be inferred reliably -- see docs/field_mapping.md, Q4.
    cumulative_gpa = schema.Decimal(
        title=_('Cumulative GPA'),
        description=_(
            'Enter your GPA as it appears on your transcript, on either a '
            '4.0 scale or a 100-point scale.'
        ),
        min=Decimal('0'),
        max=Decimal('100'),
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
