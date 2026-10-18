# -*- coding: utf-8 -*-
"""Eligibility decision logic for STEP and CSTEP applications.

This module deliberately imports nothing from Plone, Zope or this add-on's
content types. It takes a plain dict (produced by ``db.serializer.to_payload``)
and returns a :class:`~c_step_intake.eligibility.decision.Decision`. Keeping it
free of framework dependencies means the whole rule set is unit-testable in
milliseconds with no Plone site fixture, which is what makes it safe for a
student developer to change a rule and what lets us show an auditor exactly
which inputs produced which outcome.

Current status: the program's automated accept/reject criteria are NOT yet
defined. Until they are, this module implements only the completeness check
and routes every complete application to human review. That is the safe
default -- no applicant is auto-rejected by rules nobody has signed off on.

See docs/eligibility_rules.md for the open policy questions blocking the rest.
"""
from c_step_intake.eligibility.decision import Decision
from c_step_intake.eligibility.decision import MANUAL_REVIEW
from c_step_intake.eligibility.decision import REQUEST_INFO


#: Bump on every change to the logic below. Recorded on each application at
#: decision time so a past outcome can always be traced to the rules in force
#: when it was made.
RULES_VERSION = '0.1.0-completeness-only'

STEP = 'step'
CSTEP = 'cstep'

#: Fields that must be answered before an application can be evaluated.
#: Schema-level ``required=True`` already guards the add form; this is the
#: submit-time gate for records created by other paths (staff entry, import,
#: restapi) and the single place the completeness rule is defined.
_SHARED_REQUIRED = (
    'first_name',
    'last_name',
    'student_email',
    'student_phone_number',
    'street_address',
    'city',
    'state',
    'zip_code',
    'nys_resident',
    'household_size',
)

REQUIRED_AT_SUBMIT = {
    STEP: _SHARED_REQUIRED + (
        'date_of_birth',
        'school_name',
        'current_grade',
        'cumulative_gpa',
        'parent1_first_name',
        'parent1_last_name',
        'parent1_email',
        'parent1_phone',
    ),
    CSTEP: _SHARED_REQUIRED + (
        'emplid',
        'classification',
        'major',
        'gpa',
        'degree_type',
        'support_statement',
        'consent',
    ),
}


def missing_fields(program, payload):
    """Return the required fields that are absent or blank, in schema order."""
    required = REQUIRED_AT_SUBMIT[program]
    missing = []
    for name in required:
        value = payload.get(name)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(name)
    return tuple(missing)


def decide(program, payload):
    """Evaluate one application and return a :class:`Decision`.

    :param program: ``'step'`` or ``'cstep'``.
    :param payload: field name -> value, from ``db.serializer.to_payload``.
    """
    if program not in REQUIRED_AT_SUBMIT:
        raise ValueError('Unknown program: {0!r}'.format(program))

    missing = missing_fields(program, payload)
    if missing:
        return Decision(
            outcome=REQUEST_INFO,
            reason='Missing required fields: {0}'.format(', '.join(missing)),
            rules_version=RULES_VERSION,
            missing_fields=missing,
        )

    # TODO(program policy): the GPA and household-income rules go here, ahead
    # of the fallthrough below. Four questions must be answered first --
    # they change the outcome, not just the wording. See
    # docs/eligibility_rules.md:
    #   1. Does underrepresented-minority status satisfy eligibility on its
    #      own, independent of household income?
    #   2. Do the economic-disadvantage indicators (free/reduced lunch, public
    #      assistance, foster care) override the income test?
    #   3. What GPA floor applies, on what scale, per program?
    #   4. What are the income thresholds by household size, and for which
    #      program year?
    return Decision(
        outcome=MANUAL_REVIEW,
        reason=(
            'Application is complete. Automated eligibility criteria are not '
            'yet defined, so every complete application is routed to staff '
            'review.'
        ),
        rules_version=RULES_VERSION,
    )
