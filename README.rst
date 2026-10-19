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
        request_more_info / manual_review / accepted / rejected

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

The program's automated accept/reject criteria are **not yet defined**. Until
they are, ``eligibility/rules.py`` implements only the completeness check and
routes every complete application to ``manual_review``. Nothing is
auto-rejected. See ``docs/eligibility_rules.md`` for the open questions.

The STEP mapping is reconciled against the live STEP schema: 33 of its 34
columns are mapped (``exit_date`` is never written). IT must change
``zip_code`` from integer to text before go-live; four columns that would
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
