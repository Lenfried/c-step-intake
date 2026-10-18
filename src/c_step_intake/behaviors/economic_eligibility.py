# -*- coding: utf-8 -*-
"""Household economic fields shared by STEP and CSTEP applications.

Income is optional by design: an applicant may establish economic disadvantage
through a categorical indicator instead of disclosing a dollar figure. Whether
those indicators override the income test is an open policy question -- see
docs/eligibility_rules.md, Q2.
"""
from decimal import Decimal

from plone.autoform.interfaces import IFormFieldProvider
from plone.supermodel import model
from c_step_intake import _
from c_step_intake.vocabularies import HOUSEHOLD_SIZE
from c_step_intake.vocabularies import OTHER_ECONOMIC_DISADVANTAGE
from z3c.form.browser.radio import RadioFieldWidget
from zope import schema
from zope.interface import provider


@provider(IFormFieldProvider)
class IEconomicEligibility(model.Schema):
    """Household size, income and categorical disadvantage indicators."""

    model.fieldset(
        'household',
        label=_('Household'),
        fields=[
            'household_size',
            'household_income',
            'other_economic_disadvantage',
        ],
    )

    household_size = schema.Choice(
        title=_('Household size'),
        description=_(
            'Number of people supported by your household income, including '
            'yourself.'
        ),
        vocabulary=HOUSEHOLD_SIZE,
        required=True,
    )

    household_income = schema.Decimal(
        title=_('Annual household income'),
        description=_(
            'Optional. Total annual income before taxes, in US dollars. You '
            'may leave this blank if you answer the question below instead.'
        ),
        min=Decimal('0'),
        required=False,
    )

    other_economic_disadvantage = schema.Choice(
        title=_('Do either of these apply to you?'),
        description=_('Optional. Select one if it applies.'),
        vocabulary=OTHER_ECONOMIC_DISADVANTAGE,
        required=False,
    )


IEconomicEligibility.setTaggedValue(
    'plone.autoform.widgets',
    {
        'household_size': RadioFieldWidget,
        'other_economic_disadvantage': RadioFieldWidget,
    },
)
