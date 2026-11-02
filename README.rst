=============
c-step-intake
=============

Plone 6 add-on providing the application intake for York College's STEP and
CSTEP programs. **Production ships STEP only**: CSTEP is off by default and
is turned on by applying a separate profile (see `Enabling CSTEP`_).

- ``step_application`` -- Science and Technology Entry Program, grades 7-12.
- ``cstep_application`` -- Collegiate Science and Technology Entry Program,
  enrolled college students.

Both types share the applicant identity and household fields through
behaviors, and both are bound to a single ``step-cstep-application`` workflow.


How it fits together
====================

::

    applicant fills form in Plone  (draft)
              |
              |  submits
              v
    event_handlers.evaluate_application
              |
              +-- db.serializer.to_payload(obj)     one payload
              |
              +-- eligibility.rules.decide(...)     pure Python, no Plone
              |
              +-- records the decision in annotations  (immutable audit trail)
              |
              +-- fires the resulting workflow transition
                        |
                        v
                  manual_review
                        |
                        v  (staff)
        request_more_info / accepted / rejected

The same payload feeds the eligibility rules and the PostgreSQL row, so the
rules and the database can never disagree about what an applicant answered.

Each program writes to its **own** table (``step_student``, and tentatively
``cstep_student``). A row is written only when an application is **accepted**;
undecided and rejected applications stay in Plone. After that the database owns
the row, including ``program_status`` (enrolment status), so the hand-off must
insert and never update. There is no ``program`` discriminator column -- the
program is implied by the table, which is why ``field_map.table_for(program)``
has to travel alongside the row.

Our team owns the field mapping (``src/c_step_intake/db/field_map.py`` and
``docs/field_mapping.md``). IT owns the write into PostgreSQL.


Current status
==============

Every submission goes to ``manual_review``: the rules never accept or reject
on their own. They record information for staff with each decision:

- **Completeness:** any missing required fields are listed.
- **STEP acceptance criteria:** ``eligibility/step_criteria.py`` records which
  conditions the answers meet (NYS residency, grade 7-12, economic need using
  the 2026-2027 NYSED income limits, STEM statement), with an overall
  conclusion. CSTEP criteria are not yet defined.

See ``docs/eligibility_rules.md`` for the criteria and open questions.

The STEP mapping is reconciled against the live STEP schema: 33 of its 34
columns are mapped (``exit_date`` is never written). Four columns that would
carry audit detail are deferred, because every application goes to manual
review for now. ``docs/field_mapping.md`` section 7 has the list, written for IT.

CSTEP exists on the Plone side but has no tables yet, because CSTEP database
development is not yet authorised. Its entries in ``field_map.py`` are
provisional and have not been checked against anything live.


New-application email
=====================

When an application is first submitted, the add-on emails the address in the
registry record ``c_step_intake.notification_email`` (default
``cstep-n8n@mailings.york.cuny.edu``; edit it in Site Setup -> Configuration
Registry, or empty it to turn notifications off). The message has a link and
the automatic check's outcome, and no applicant details. Resubmissions do not
send one, and a mail failure is logged rather than blocking the submission.

Plone must have SMTP configured (Site Setup -> Mail) for this to send.
Sites that already have the profile installed need the registry record
added by re-importing the ``registry`` step of ``c_step_intake:default``.


Enabling CSTEP
==============

Installing ``c_step_intake:default`` gives a site ``step_application`` only.
The ``cstep_application`` type, its workflow binding and its add permission
live in the ``c_step_intake:cstep`` profile, which is not applied by default.
The CSTEP code (schema, behaviors, field map entries, rules) stays in the
package so it keeps being tested, but a site cannot create a CSTEP
application until the profile is applied.

Do these **before** applying the profile in production:

1. **Get CSTEP database development authorised and the tables built.** There
   are no CSTEP tables today. Each program writes to its own applications
   table, shaped like that program's students table.
2. **Reconcile ``field_map.py`` against the live CSTEP schema.** Every CSTEP
   entry is provisional and unchecked. Update ``docs/field_mapping.md`` to
   match, and tell IT which columns need adding or retyping (as section 7 does
   for STEP).
3. **Have IT extend the PostgreSQL write to the CSTEP table.** The write must
   use ``field_map.table_for('cstep')``.
4. **Define the CSTEP eligibility criteria.** ``eligibility/rules.py``
   currently only checks completeness and sends every complete application
   to ``manual_review``. Record the CSTEP-specific questions and answers in
   ``docs/eligibility_rules.md``.
5. **Re-run the full suite** (``zope-testrunner --all --test-path=src``). The
   test layer applies both profiles, so CSTEP coverage is already included.
6. **Check the role map.** ``profiles/default/rolemap.xml`` already grants
   ``c_step_intake: Add CSTEP Application``. Confirm the roles are right for
   the CSTEP audience (enrolled college students rather than grades 7-12).

Then enable it on a site, either with ``portal_setup`` (Import tab, profile
"c_step_intake: CSTEP applications") or from a script::

    portal.portal_setup.runAllImportStepsFromProfile(
        'profile-c_step_intake:cstep')

The profile depends on ``c_step_intake:default``. There is no uninstall
profile for CSTEP: remove the type in ``portal_types`` only after deleting any
CSTEP applications. Once CSTEP is ready for everyone, move the three files
from ``profiles/cstep`` back into ``profiles/default`` and drop the profile.


Single-page forms
=================

The add and edit forms for both application types show every fieldset on
one page, each under its own heading, instead of as tabs.

- **Classic UI:** ``browser/forms.py`` sets ``enable_form_tabbing = False``.
- **Volto:** the classic setting does not reach Volto, which builds its forms
  from the ``@types`` schema and draws tabs whenever there is more than one
  fieldset. The Volto add-on in ``frontend/`` (``volto-c-step-intake-core``)
  rewrites the schema of these two types as it arrives: it merges the
  fieldsets into one and puts a read-only heading field at the start of each
  former fieldset. The backend schema is unchanged.

To use the Volto add-on, add ``volto-c-step-intake-core`` to the Volto
project's workspace and to its ``addons`` list. The type list is the setting
``config.settings.cStepIntakeSinglePageFormTypes``. Its tests are plain
vitest and need no Volto install::

    cd frontend
    npx vitest run


STEP school list
================

The STEP form's school field is a searchable pick-list, so the stored value
is always in NYSED reporting format: ``NAME  (COUNTY) BEDSCODE``, e.g.
``YORK EARLY COLLEGE ACADEMY  (QUEENS) 342800011284`` (two spaces before the
county, then the 12-digit BEDS code). Applicants see a readable title, e.g.
"YORK EARLY COLLEGE ACADEMY (Queens)".

- **List:** ``src/c_step_intake/data/step_schools.json``, NYSED IMF secondary
  schools (grades 7-12) for the five boroughs and Nassau County, 1,998
  schools. It is the vocabulary ``c_step_intake.StepSchools``
  (``vocabularies.step_schools``), keyed by BEDS code.
- **Not listed:** the first choice is "My school isn't listed". The applicant
  then types the name in ``school_name_other``, which is required in that case
  (form check and completeness rule). That value is written to the
  ``school_name`` column as typed, not in reporting format, so staff should
  correct it before accepting.
- **Updating the list:** replace the JSON file, keeping its structure. A test
  fails if any entry is not in the reporting format or a BEDS code repeats.
  Saved applications keep the value they were submitted with.


Pre-filled identity fields
==========================

When an applicant opens the add form, first name, last name and email are
pre-filled from their account, and so is CSTEP's EMPLID. ``account_defaults.py`` has
the functions, used as ``defaultFactory`` on those fields. They apply only
when the form opens, never overwrite a saved application, and leave a field
blank when the account has no value (anonymous visitors get blanks too).

What an account carries depends on the site. ``email`` and ``fullname`` are
standard Plone properties, so email and the first and last name (split from
``fullname``) work everywhere. ``first_name``, ``last_name`` and ``employeeID``
are not standard: they are used when the site's login setup (SSO, LDAP, a
custom member schema) provides them, and EMPLID is only pre-filled from
``employeeID`` if it is exactly 8 digits. STEP applicants may be minors using
a parent's account, so check the pre-filled STEP names before relying on them.


Eligibility panel
=================

Program staff see an **Eligibility check** panel at the top of each
submitted application in Volto. It shows the latest decision: the overall
conclusion, each STEP condition as met / not met / undetermined with the
answers behind it, any missing required answers, when it was checked, and
the rules version.

- **Backend:** ``GET <application>/@eligibility`` (``services/``) returns the
  latest decision to users with ``c_step_intake: Review Application``
  (Manager, Site Administrator, ProgramDirector, ProgramStaff; granted from
  submission onwards). Everyone else, including the applicant, gets
  ``{"available": false}``. It never answers 401, because Volto shows a
  site-wide error page on a 401. The answers snapshot stored with each
  decision is not returned.
- **Volto:** ``ApplicationView`` replaces the default view for both
  application types. It shows the panel, and the single-page schema's
  section headings, which the default view would render as empty fields.
  It also shows date-only fields such as date of birth as the day entered:
  Volto's default date display reads "2011-05-01" as midnight UTC and shows
  it a day early west of UTC (April 30 in New York).


Development
===========

Use **Python 3.11**. The add-on targets Plone 6.0, whose pinned dependency set
predates the newest interpreters: on Python 3.14 the ``RestrictedPython``
version that Plone 6.0 pins has no build, and the install fails outright.

::

    py -3.11 -m venv .venv
    .venv\Scripts\pip install -e ".[test]" -c constraints.txt

    # full suite -- 54 tests, including the in-memory Plone site fixture
    zope-testrunner --all --test-path=src

    # just the Plone-free tests: rules, field map, schema coverage
    python -m unittest c_step_intake.tests.test_eligibility_rules c_step_intake.tests.test_field_map c_step_intake.tests.test_schema_coverage

    flake8 src

The integration tests build a real Plone site in an in-memory ZODB, apply the
``c_step_intake:default`` profile and exercise the actual workflow, permissions
and event handler. Fixture setup costs a few seconds; the tests themselves run
in well under a second.

Known tooling gaps
------------------

``tox -e unit`` and ``tox -e lint`` both fail on current tooling, for reasons
unrelated to the code. Use the direct commands above until they are fixed.

- ``tox.ini`` sets ``deps = -cconstraints.txt``. tox runs the deps step as its
  own ``pip install -c constraints.txt`` with nothing to install, which pip
  rejects. Moving the constraint onto ``install_command`` fixes it.
- ``setup.cfg`` sets ``not_skip``, an isort 4 option that isort 5 refuses to
  start with. The tree is also still formatted to isort 4's conventions, so
  re-running a modern isort would rewrite most files.
