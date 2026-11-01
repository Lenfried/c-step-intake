# -*- coding: utf-8 -*-
"""Eligibility decision logic for STEP and CSTEP applications.

This module deliberately imports nothing from Plone, Zope or this add-on's
content types. It takes a plain dict (produced by ``db.serializer.to_payload``)
and returns a :class:`~c_step_intake.eligibility.decision.Decision`. Keeping it
free of framework dependencies means the whole rule set is unit-testable in
milliseconds with no Plone site fixture, which is what makes it safe for a
student developer to change a rule and what lets us show an auditor exactly
which inputs produced which outcome.

Every submission goes to staff review, complete or not, eligible or not:
the program decided that the rules never accept or reject on their own. What
the rules add is information for staff:

- the completeness check lists any missing required fields;
- for STEP, ``step_criteria.assess`` records which acceptance criteria the
  answers meet (``Decision.assessment``).

Incomplete applications go to staff review too, rather than back to the
applicant: the form already requires every answer the check needs, so an
incomplete one can only come from staff entry, an import or a later form
change, and staff are the ones to fix it.

See docs/eligibility_rules.md for the criteria and open policy questions.
"""
from c_step_intake.eligibility.decision import Decision
from c_step_intake.eligibility.decision import MANUAL_REVIEW
from c_step_intake.eligibility import step_criteria


#: Bump on every change to the logic below. Recorded on each application at
#: decision time so a past outcome can always be traced to the rules in force
#: when it was made.
RULES_VERSION = '0.3.0-step-criteria-2026-27'

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
        reason = (
            'Incomplete application, routed to staff review. Missing '
            'required fields: {0}.'.format(', '.join(missing))
        )
    else:
        reason = 'Application is complete, routed to staff review.'

    # STEP only: CSTEP's criteria are not defined yet.
    assessment = None
    if program == STEP:
        assessment = step_criteria.assess(payload)
        reason += ' STEP criteria: {0}.'.format(assessment.overall)

    return Decision(
        outcome=MANUAL_REVIEW,
        reason=reason,
        rules_version=RULES_VERSION,
        missing_fields=missing,
        assessment=assessment,
    )
