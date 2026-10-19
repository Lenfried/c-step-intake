# -*- coding: utf-8 -*-
"""Turn an application object into the payload the rest of the system consumes.

Two outputs, one mapping:

``to_payload`` keys values by Plone field name and feeds the eligibility rules.
``to_row`` keys the same values by PostgreSQL column name and is what IT reads.

Both derive from the same object, so the rules and the database row can never
disagree about what an applicant answered.

Each program has its own table (step_student / cstep_student), so a row is only meaningful
alongside the table it belongs to -- see ``field_map.table_for``.
"""
import uuid

from plone import api
from plone.dexterity.utils import iterSchemata
from plone.uuid.interfaces import IUUID
from c_step_intake.db import field_map
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


def format_student_id(plone_uid):
    """Return a Plone UID in the dashed form the table already uses.

    Plone stores a UID as 32 hex characters; step_student holds
    ``04e42317-bea7-44c6-964b-aa6944518988``. Same value, same randomness,
    only the dashes differ, and the result is stable for a given object.
    """
    if not plone_uid:
        return None
    try:
        return str(uuid.UUID(plone_uid))
    except ValueError:
        return plone_uid


def _student_id(obj):
    return format_student_id(IUUID(obj, None))


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


#: Column name -> how to compute it from the object.
DERIVED = {
    'student_id': _student_id,
    'application_date': _application_date,
    'created_date': _created_date,
    'last_update': _last_update,
    'major_at_application': _major_at_application,
    'accepted_date': _accepted_date,
}


def grade_to_int(value):
    return None if value in (None, '') else int(value)


#: Columns whose live type differs from the Plone value. Applied to directly
#: mapped fields only.
COERCE = {
    'current_grade': grade_to_int,
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
            value = getattr(obj, mapping.field, None)
            row[mapping.column] = COERCE.get(mapping.column, lambda v: v)(
                value)
        else:
            row[mapping.column] = DERIVED[mapping.column](obj)
    return row
