# -*- coding: utf-8 -*-
"""Declarative mapping from Plone fields to PostgreSQL columns.

This module is the single source of truth for the mapping. Our team owns it;
IT owns the write itself. It deliberately imports nothing from Plone so it can
be read, diffed and unit-tested as plain data -- values for derived columns are
supplied by ``serializer.DERIVED``.

Each program writes to its **own** applications table (see :data:`TABLES`),
shaped identically to that program's students table, so an accepted
application can be promoted into ``students`` as a straight copy rather than a
column-by-column translation. There is therefore no ``program`` discriminator
column: the program is implied by which table the row goes to, which is why
the hand-off needs ``table_for(program)`` alongside the row itself.

The STEP mappings below are reconciled against the live STEP students table.
The CSTEP ones are provisional -- that table does not exist yet.

``tests/test_field_map.py`` fails if a schema field is added without either a
mapping here or an explicit entry in :data:`UNMAPPED`, so the map cannot
silently fall behind the form.
"""
from dataclasses import dataclass
from typing import Optional
from typing import Tuple


STEP = 'step'
CSTEP = 'cstep'
BOTH = (STEP, CSTEP)

#: Applications table per program. Each mirrors that program's students table.
#: CONFIRM both names with IT -- they are not in the schema dump we were given.
TABLES = {
    STEP: 'step_applications',
    CSTEP: 'cstep_applications',
}


@dataclass(frozen=True)
class Mapping:
    """One Plone field (or derived value) mapped to one PostgreSQL column."""

    column: str
    pg_type: str
    programs: Tuple[str, ...]
    #: Plone field name, or None when the value is derived (see DERIVED).
    field: Optional[str] = None
    #: Plone field names a *derived* column's DERIVED function reads, when
    #: that isn't just ``field`` (e.g. major_at_application reads major).
    #: Declared here so mapped_fields() can still see these fields as
    #: accounted for, even though no single column maps to them directly.
    source_fields: Tuple[str, ...] = ()
    #: True when the column holds personally identifiable information.
    pii: bool = False
    note: str = ''


#: Target tables: one applications table per program, see TABLES.
#: `NEW COLUMN` marks a column absent from the live STEP students table.
APPLICATIONS = (
    # --- keys and provenance -------------------------------------------
    Mapping('student_id', 'uuid', BOTH,
            note='Plone UID; opaque by design. Named student_id to match the '
                 'students table so the id survives promotion on accept.'),
    Mapping('application_date', 'date', BOTH,
            note='Object creation date. See field_mapping.md Q8: arguably '
                 'should be the first-submit date instead.'),
    Mapping('created_date', 'date', BOTH,
            note='Object creation date; same value as application_date today.'),
    Mapping('last_update', 'date', BOTH, note='Object modification date.'),

    # --- identity -------------------------------------------------------
    Mapping('first_name', 'text', BOTH, field='first_name', pii=True),
    Mapping('last_name', 'text', BOTH, field='last_name', pii=True),
    Mapping('date_of_birth', 'date', BOTH, field='date_of_birth', pii=True),
    Mapping('gender', 'text', BOTH, field='gender'),
    Mapping('ethnicity', 'text', BOTH, field='ethnicity'),

    # --- contact --------------------------------------------------------
    Mapping('student_email', 'text', BOTH, field='student_email', pii=True),
    Mapping('student_phone_number', 'text', BOTH,
            field='student_phone_number', pii=True,
            note='NEW COLUMN. The live table has no student phone column at '
                 'all, though the form requires one of every applicant.'),
    Mapping('street_address', 'text', BOTH, field='street_address', pii=True),
    Mapping('apartment_number', 'text', BOTH, field='apartment_number',
            pii=True,
            note='NEW COLUMN. Without it the mailing address is incomplete '
                 'for any applicant in an apartment building.'),
    Mapping('city', 'text', BOTH, field='city'),
    Mapping('state', 'character(2)', BOTH, field='state',
            note='CONFIRM length. information_schema reports "character" for '
                 'any char(n), and bare character defaults to char(1), which '
                 'cannot hold "NY".'),
    Mapping('zip_code', 'text', BOTH, field='zip_code',
            note='LIVE COLUMN IS integer -- must change to text. ZIP+4 and '
                 'leading zeros (NY 06390) are unstorable as an integer, and '
                 'a ZIP is an identifier, never an arithmetic operand.'),
    Mapping('nys_resident', 'boolean', BOTH, field='nys_resident'),

    # --- household ------------------------------------------------------
    Mapping('household_size', 'integer', BOTH, field='household_size'),
    Mapping('household_income', 'integer', BOTH, field='household_income',
            pii=True,
            note='Nullable: applicant may use a categorical indicator '
                 'instead. Live column is integer, so cents are dropped at '
                 'write -- acceptable for annual household income.'),
    Mapping('other_economic_disadvantage', 'text', BOTH,
            field='other_economic_disadvantage',
            note='Stores public_assistance or foster_care.'),

    # --- STEP only ------------------------------------------------------
    Mapping('free_reduced_lunch', 'boolean', (STEP,),
            field='free_reduced_lunch'),
    Mapping('school_name', 'text', (STEP,), field='school_name'),
    Mapping('current_grade', 'text', (STEP,), field='current_grade',
            note='LIVE COLUMN IS integer. Text here so it can absorb '
                 'non-numeric values later (e.g. ungraded) without a '
                 'migration. See field_mapping.md Q9.'),
    Mapping('cumulative_gpa', 'numeric', (STEP,), field='cumulative_gpa',
            note='0-100 or 4.0 scale; ambiguous until gpa_scale is asked.'),
    Mapping('gpa_scale', 'text', (STEP,),
            note='NEW COLUMN. 4.0 or 100; see field_mapping.md Q4. Null '
                 'until the STEP form asks. CSTEP needs no such column.'),
    Mapping('parent1_first_name', 'text', (STEP,), field='parent1_first_name',
            pii=True),
    Mapping('parent1_last_name', 'text', (STEP,), field='parent1_last_name',
            pii=True),
    Mapping('parent1_email', 'text', (STEP,), field='parent1_email', pii=True),
    Mapping('parent1_phone', 'text', (STEP,), field='parent1_phone', pii=True),
    Mapping('parent2_first_name', 'text', (STEP,), field='parent2_first_name',
            pii=True),
    Mapping('parent2_last_name', 'text', (STEP,), field='parent2_last_name',
            pii=True),
    Mapping('parent2_email', 'text', (STEP,), field='parent2_email', pii=True),
    Mapping('parent2_phone', 'text', (STEP,), field='parent2_phone', pii=True),

    # --- CSTEP only -----------------------------------------------------
    # Provisional. The CSTEP tables do not exist yet -- development on the
    # CSTEP side is not authorised, so none of these have been reconciled
    # against a live column. Expect them to mirror a cstep students table the
    # same way the STEP block above mirrors its own.
    Mapping('empl_id', 'text', (CSTEP,), field='emplid', pii=True),
    Mapping('classification', 'text', (CSTEP,), field='classification'),
    Mapping('major_at_application', 'text', (CSTEP,),
            source_fields=('major',),
            note='major, or major_other when major is other.'),
    Mapping('degree_type', 'text', (CSTEP,), field='degree_type'),
    Mapping('gpa', 'numeric', (CSTEP,), field='gpa',
            note='4.0 scale; the CSTEP form constrains it, so no scale '
                 'column is needed.'),
    Mapping('statement_support', 'text', (CSTEP,), field='support_statement'),
    Mapping('career_aspiration', 'text', (CSTEP,), field='career_aspiration',
            note='Alternate eligibility basis for an applicant whose major is '
                 'not itself STEM/licensure; see docs/eligibility_rules.md.'),
    Mapping('consent', 'boolean', (CSTEP,), field='consent'),
    Mapping('email_consent', 'boolean', (CSTEP,), field='email_consent',
            note='Governs whether the program may email them.'),

    # --- decision and audit --------------------------------------------
    Mapping('program_status', 'text', BOTH,
            note='The Plone workflow state. CONFIRM: on the students table '
                 'this column appears to mean enrolment status instead, in '
                 'which case the two meanings must not share a column.'),
    Mapping('accepted_date', 'date', BOTH,
            note='Date of the accept transition; null until accepted.'),
    Mapping('decision_reason', 'text', BOTH, note='NEW COLUMN.'),
    Mapping('decided_at', 'timestamptz', BOTH, note='NEW COLUMN.'),
    Mapping('rules_version', 'text', BOTH,
            note='NEW COLUMN. Which rule set produced the decision.'),
)

#: Fields deliberately not written to PostgreSQL. Listing one here is a
#: decision, not an omission -- test_field_map.py requires every schema field
#: to appear either in APPLICATIONS or here.
UNMAPPED = {
    'major_other': 'Merged into major_at_application.',
}

#: Columns on the live table that this add-on never populates. They belong to
#: enrolment, which happens after acceptance and outside this add-on.
NOT_POPULATED = {
    'exit_date': 'Set when a student leaves the program; no application '
                 'analogue.',
}


def table_for(program):
    """Return the applications table ``program`` writes to."""
    return TABLES[program]


def columns_for(program):
    """Return the mappings that apply to ``program``, in column order."""
    return tuple(m for m in APPLICATIONS if program in m.programs)


def mapped_fields():
    """Return every Plone field name accounted for by some column.

    Includes both fields mapped directly (``field``) and fields a derived
    column's getter reads instead (``source_fields``) -- e.g.
    major_at_application has no ``field`` of its own but is derived from major.
    """
    direct = {m.field for m in APPLICATIONS if m.field}
    indirect = {name for m in APPLICATIONS for name in m.source_fields}
    return direct | indirect


def pii_columns():
    """Return the columns holding PII, for IT's access-control review."""
    return tuple(m.column for m in APPLICATIONS if m.pii)
