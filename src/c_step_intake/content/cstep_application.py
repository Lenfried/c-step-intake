# -*- coding: utf-8 -*-
"""CSTEP application -- the college (undergraduate/graduate) program.

Identity, contact, address and household fields come from the shared
behaviors. Only the fields specific to an enrolled college student live here.

Ported from the through-the-web type in yc.facultycv/ref/. Changes made
during the port, each recorded in docs/field_mapping.md:
  - gpa is a constrained Decimal, not free text, so the GPA rule can be
    evaluated reliably once it is defined.
  - Choice fields store short stable values instead of the full option prose.
  - consent and email_consent are booleans; email_consent is now optional,
    because a program application must not be conditioned on accepting
    marketing email.
"""
import re
from decimal import Decimal

from plone.dexterity.content import Item
from plone.supermodel import model
from c_step_intake import _
from c_step_intake.interfaces import IApplication
from c_step_intake.vocabularies import CLASSIFICATION
from c_step_intake.vocabularies import DEGREE_TYPE
from c_step_intake.vocabularies import MAJOR
from z3c.form.browser.radio import RadioFieldWidget
from zope import schema
from zope.interface import implementer
from zope.interface import invariant
from zope.interface import Invalid


_EMPLID = re.compile(r'^\d{8}$')


def validate_emplid(value):
    if not _EMPLID.match(value or ''):
        raise Invalid(_('A CUNY EMPLID is 8 digits.'))
    return True


def must_be_true(value):
    if value is not True:
        raise Invalid(_('You must confirm this to submit your application.'))
    return True


class ICstepApplication(model.Schema):
    """Schema for a CSTEP (college) application."""

    model.fieldset(
        'academics',
        label=_('Academics'),
        fields=[
            'emplid',
            'classification',
            'major',
            'major_other',
            'gpa',
            'degree_type',
        ],
    )

    model.fieldset(
        'statement',
        label=_('Statement'),
        fields=['support_statement', 'career_aspiration'],
    )

    model.fieldset(
        'consent',
        label=_('Consent'),
        fields=['consent', 'email_consent'],
    )

    emplid = schema.TextLine(
        title=_('EMPLID'),
        description=_('Your 8-digit CUNY EMPLID.'),
        constraint=validate_emplid,
        required=True,
    )

    classification = schema.Choice(
        title=_('Classification'),
        vocabulary=CLASSIFICATION,
        required=True,
    )

    major = schema.Choice(
        title=_('Major'),
        vocabulary=MAJOR,
        required=True,
    )

    major_other = schema.TextLine(
        title=_('Other major'),
        description=_('Required only if you selected “Other” above.'),
        required=False,
    )

    gpa = schema.Decimal(
        title=_('GPA'),
        description=_('On a 4.0 scale.'),
        min=Decimal('0'),
        max=Decimal('4'),
        required=True,
    )

    degree_type = schema.Choice(
        title=_('Degree or certification being pursued'),
        vocabulary=DEGREE_TYPE,
        required=True,
    )

    support_statement = schema.Text(
        title=_(
            'How would you express your need of, or how would you greatly '
            'benefit from, academic enrichment or support in the STEM areas?'
        ),
        required=True,
    )

    # CSTEP eligibility is not limited to applicants already majoring in a
    # STEM field or licensed profession: an applicant whose declared major
    # is outside that list may still qualify on the strength of an intended
    # STEM/licensure career. This field captures that alternate basis: which
    # majors count as qualifying, and whether a stated goal is sufficient on
    # its own, are open policy questions -- see docs/eligibility_rules.md.
    career_aspiration = schema.Text(
        title=_('Career aspirations / goals'),
        description=_(
            'Optional. If your major above is not itself a STEM field or a '
            'licensed profession, describe the STEM field or licensed '
            'profession you intend to pursue. CSTEP eligibility can be '
            'established either by major or by career goal.'
        ),
        required=False,
    )

    consent = schema.Bool(
        title=_('I confirm that the information provided is true and correct.'),
        constraint=must_be_true,
        required=True,
    )

    email_consent = schema.Bool(
        title=_(
            'I agree to receive emails about educational programs, special '
            'offers, events, and other promotional information from York '
            'College.'
        ),
        required=False,
    )

    @invariant
    def other_major_is_specified(data):
        if getattr(data, 'major', None) == 'other':
            if not (getattr(data, 'major_other', None) or '').strip():
                raise Invalid(
                    _('Please specify your major, since you selected “Other”.')
                )


ICstepApplication.setTaggedValue(
    'plone.autoform.widgets',
    {
        'classification': RadioFieldWidget,
        'degree_type': RadioFieldWidget,
    },
)


@implementer(ICstepApplication, IApplication)
class CstepApplication(Item):
    """A CSTEP application."""

    program = 'cstep'

    @property
    def title(self):
        return '{0}, {1}'.format(self.last_name or '', self.first_name or '')

    @title.setter
    def title(self, value):
        pass
