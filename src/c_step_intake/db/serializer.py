# -*- coding: utf-8 -*-
"""Turn an application object into the payload the rest of the system consumes.

Two outputs, one mapping:

``to_payload`` keys values by Plone field name and feeds the eligibility rules.
``to_row`` keys the same values by PostgreSQL column name and is what IT reads.

Both derive from the same object, so the rules and the database row can never
disagree about what an applicant answered.

Each program has its own applications table, so a row is only meaningful
alongside the table it belongs to -- see ``field_map.table_for``.
"""
from plone import api
from plone.dexterity.utils import iterSchemata
from plone.uuid.interfaces import IUUID
from c_step_intake.db import field_map
from c_step_intake.interfaces import IEligibilityRecord
from zope.schema import getFieldsInOrder


def to_payload(obj):
    """Return every schema field value on ``obj``, keyed by field name.

    Behaviour fields are included, so adding a field to a shared behavior
    reaches the eligibility rules without touching this function.
    """
    payload = {}
    for schemata in iterSchemata(obj):
        for name, _field in getFieldsInOrder(schemata):
            payload[name] = getattr(obj, name, None)
    return payload


def _major_at_application(obj):
    major = getattr(obj, 'major', None)
    if major == 'other':
        return getattr(obj, 'major_other', None)
    return major


def _gpa_scale(obj):
    # STEP accepts either a 4.0 GPA or a 100-point average and cannot tell
    # them apart, because the form does not ask. Null until it does -- see
    # docs/field_mapping.md Q4. CSTEP has no such column: always 4.0.
    return None


def _application_date(obj):
    return obj.created().asdatetime().date()


def _created_date(obj):
    return obj.created().asdatetime().date()


def _last_update(obj):
    return obj.modified().asdatetime().date()


def _accepted_date(obj):
    """Date of the accept transition, or None if never accepted.

    Read from workflow history rather than recorded separately: the
    transition is the event, and duplicating it into an annotation would give
    two sources that can disagree.
    """
    workflow = api.portal.get_tool('portal_workflow')
    history = workflow.getInfoFor(obj, 'review_history', ()) or ()
    for entry in reversed(history):
        if entry.get('action') == 'accept':
            when = entry.get('time')
            return when.asdatetime().date() if when else None
    return None


def _decision(obj, key):
    latest = IEligibilityRecord(obj).latest()
    if latest is None:
        return None
    return latest.get(key)


#: Column name -> how to compute it from the object.
DERIVED = {
    'student_id': IUUID,
    'application_date': _application_date,
    'created_date': _created_date,
    'last_update': _last_update,
    'major_at_application': _major_at_application,
    'gpa_scale': _gpa_scale,
    'program_status': lambda obj: api.content.get_state(obj=obj, default=None),
    'accepted_date': _accepted_date,
    'decision_reason': lambda obj: _decision(obj, 'reason'),
    'decided_at': lambda obj: _decision(obj, 'decided_at'),
    'rules_version': lambda obj: _decision(obj, 'rules_version'),
}


def to_row(obj):
    """Return the PostgreSQL row for ``obj``, keyed by column name.

    The table it belongs to is ``field_map.table_for(obj.program)`` -- the row
    carries no program discriminator of its own, because each program has its
    own table.
    """
    row = {}
    for mapping in field_map.columns_for(obj.program):
        if mapping.field:
            row[mapping.column] = getattr(obj, mapping.field, None)
        else:
            row[mapping.column] = DERIVED[mapping.column](obj)
    return row
