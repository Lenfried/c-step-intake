=============
c-step-intake
=============

Plone 6 add-on providing the application intake for York College's STEP and
CSTEP programs.

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

Each program writes to its **own** applications table, shaped identically to
that program's students table so an accepted application can be promoted with
a straight copy rather than a column-by-column translation. There is no
``program`` discriminator column -- the program is implied by the table, which
is why ``field_map.table_for(program)`` has to travel alongside the row.

Our team owns the field mapping (``src/c_step_intake/db/field_map.py`` and
``docs/field_mapping.md``). IT owns the write into PostgreSQL.


Current status
==============

The program's automated accept/reject criteria are **not yet defined**. Until
they are, ``eligibility/rules.py`` implements only the completeness check and
routes every complete application to ``manual_review``. Nothing is
auto-rejected. See ``docs/eligibility_rules.md`` for the open questions.

The STEP mapping is reconciled against the live STEP schema: 32 of its 33
columns are mapped, six more need adding and three need a type decision.
``docs/field_mapping.md`` section 7 is that list, written for IT.

CSTEP exists on the Plone side but has no tables yet, because CSTEP database
development is not yet authorised. Its entries in ``field_map.py`` are
provisional and have not been checked against anything live.


Development
===========

Use **Python 3.11**. The add-on targets Plone 6.0, whose pinned dependency set
predates the newest interpreters: on Python 3.14 the ``RestrictedPython``
version that Plone 6.0 pins has no build, and the install fails outright.

::

    py -3.11 -m venv .venv
    .venv\Scripts\pip install -e ".[test]" -c constraints.txt

    # full suite -- 51 tests, including the in-memory Plone site fixture
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
