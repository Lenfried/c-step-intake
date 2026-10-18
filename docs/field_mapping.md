# Plone → PostgreSQL field mapping

**Status:** reconciled against the live STEP schema (STEP), draft (CSTEP)
**Owners:** STEP/CSTEP dev team (mapping) · IT (the write itself)
**Source of truth:** [`src/c_step_intake/db/field_map.py`](../src/c_step_intake/db/field_map.py)

This document is the human-readable view of `field_map.py`. If the two ever
disagree, the code wins — but they shouldn't, because
`tests/test_schema_coverage.py` fails if a form field is added without a
mapping decision, and `tests/test_field_map.py` fails on duplicate or
program-mismatched columns.

---

## 1. Scope and ownership

We produce a row; IT writes it. Nothing in this add-on opens a database
connection.

```
applicant → Plone form → submit → eligibility rules → workflow state
                                        │
                                        └→ db.serializer.to_row(obj)
                                              │
                                              └→ { column: value, ... }  → IT
                                                 into field_map.table_for(program)
```

`to_row()` returns a plain dict keyed by the column names below. The same
values, keyed by Plone field name instead, are what the eligibility rules
evaluate — one mapping, two consumers, so the decision and the stored record
can never disagree.

Because each program now has its own table (§2), a row is only meaningful
alongside the table it belongs to. `field_map.table_for(program)` supplies
that; the row itself carries no program column.

**Open for IT:** how the row is handed over. We recommend IT **pulls** (we
expose a read endpoint per application, IT polls or reads on demand) rather
than Plone pushing. A pull is retry-safe, needs no database credentials
inside Plone, and a failed write can't silently lose an application. If push
is preferred, we'd want a durable outbox on our side so a failed write is
retried rather than dropped. This choice does not affect any column below.

---

## 2. Table structure

**One applications table per program, each shaped identically to that
program's students table.**

| Program | Applications table | Students table | Status |
|---|---|---|---|
| STEP | `step_applications` | (the schema we were sent) | reconciled |
| CSTEP | `cstep_applications` | — | not started |

Table names above need confirming — they weren't in the schema dump.

Two consequences worth being explicit about:

- **No `program` discriminator column.** The program is implied by which
  table the row lands in. `to_row()` therefore emits no `program` key, and
  `field_map.table_for(program)` is how the destination travels with the row.
- **Applications and students share a shape**, so promoting an accepted
  application into `students` is a straight copy rather than a column-by-column
  translation. `student_id` carries the Plone UID, so the identifier survives
  that promotion.

An applicant is still not a student: `students` should be populated **only on
the `accept` transition**, never at submit. The applications table is where
every submission lands, accepted or not.

CSTEP splitting into its own tables is what unblocks STEP shipping before
CSTEP development is authorised. The cost is that cross-program reporting —
which the NYSED interim report needs — becomes a `UNION` across two tables
rather than one query with a `WHERE program = …`. Worth confirming that's
acceptable to whoever writes that report.

---

## 3. Shared columns — both programs

| Plone field | Column | Type | PII |
|---|---|---|---|
| *(derived: Plone UID)* | `student_id` | `uuid` | |
| *(derived: creation date)* | `application_date` | `date` | |
| *(derived: creation date)* | `created_date` | `date` | |
| *(derived: modification date)* | `last_update` | `date` | |
| `first_name` | `first_name` | `text` | ● |
| `last_name` | `last_name` | `text` | ● |
| `date_of_birth` | `date_of_birth` | `date` | ● |
| `gender` | `gender` | `text` | |
| `ethnicity` | `ethnicity` | `text` | |
| `student_email` | `student_email` | `text` | ● |
| `student_phone_number` | `student_phone_number` | `text` | ● |
| `street_address` | `street_address` | `text` | ● |
| `apartment_number` | `apartment_number` | `text` | ● |
| `city` | `city` | `text` | |
| `state` | `state` | `character(2)` | |
| `zip_code` | `zip_code` | `text` | |
| `nys_resident` | `nys_resident` | `boolean` | |
| `household_size` | `household_size` | `integer` | |
| `household_income` | `household_income` | `integer` | ● |
| `other_economic_disadvantage` | `other_economic_disadvantage` | `text` | |

`household_income` is **nullable by design** — an applicant may establish
economic disadvantage categorically instead of disclosing a dollar figure.
The live column is `integer`, so cents are dropped at write; that's fine for
an annual household figure, but it is a decision rather than an accident.

`household_size` is an integer 1–9, where **9 means "9 or more"**.

`other_economic_disadvantage` stores `public_assistance` or `foster_care`.

`application_date` and `created_date` currently hold the same value (see Q8).

### Stored values are codes, not prose

The through-the-web form stored the entire option text as the field value —
`economically_disadvantaged` held a ~300-character paragraph. This version
stores short stable codes (`public_assistance`, `foster_care`,
`computer_science_bs`, `junior`, …) with the prose as the display label. Option
wording can then be reworded for applicants without invalidating stored rows
or breaking report queries. Full code lists are in
[`vocabularies.py`](../src/c_step_intake/vocabularies.py).

---

## 4. STEP-only columns (grades 7–12)

| Plone field | Column | Type | PII |
|---|---|---|---|
| `school_name` | `school_name` | `text` | |
| `current_grade` | `current_grade` | `text` | |
| `cumulative_gpa` | `cumulative_gpa` | `numeric` | |
| *(derived)* | `gpa_scale` | `text` | |
| `free_reduced_lunch` | `free_reduced_lunch` | `boolean` | |
| `parent1_first_name` | `parent1_first_name` | `text` | ● |
| `parent1_last_name` | `parent1_last_name` | `text` | ● |
| `parent1_email` | `parent1_email` | `text` | ● |
| `parent1_phone` | `parent1_phone` | `text` | ● |
| `parent2_first_name` | `parent2_first_name` | `text` | ● |
| `parent2_last_name` | `parent2_last_name` | `text` | ● |
| `parent2_email` | `parent2_email` | `text` | ● |
| `parent2_phone` | `parent2_phone` | `text` | ● |

Parent 1 is required, parent 2 optional. STEP applicants are minors, so
guardian contact is a legal requirement rather than a nice-to-have — worth
noting for retention and access-control decisions on these columns.

`cumulative_gpa` maps straight across now that STEP has its own table; there
is no longer any need for a shared `application_gpa` column aliasing STEP's
`cumulative_gpa` and CSTEP's `gpa` onto one name.

`current_grade` is stored as text (`'7'`…`'12'`) rather than an integer so it
can absorb non-numeric values later (e.g. `'ungraded'`) without a migration.
The live column is `integer` — see Q9.

---

## 5. CSTEP-only columns (college)

**Provisional.** The CSTEP tables do not exist yet — development on the CSTEP
side is not authorised — so none of these have been reconciled against a live
column. Expect the same treatment STEP got: the applications table mirrors a
CSTEP students table, and these column names may change to match whatever
that table turns out to look like.

| Plone field | Column | Type | PII |
|---|---|---|---|
| `emplid` | `empl_id` | `text` | ● |
| `classification` | `classification` | `text` | |
| `major` + `major_other` | `major_at_application` | `text` | |
| `degree_type` | `degree_type` | `text` | |
| `gpa` | `gpa` | `numeric` | |
| `support_statement` | `statement_support` | `text` | |
| `career_aspiration` | `career_aspiration` | `text` | |
| `consent` | `consent` | `boolean` | |
| `email_consent` | `email_consent` | `boolean` | |

`major_at_application` collapses two Plone fields: it holds `major`, or the
free-text `major_other` when `major = 'other'`. `major_other` is therefore
listed in `field_map.UNMAPPED` — deliberately not its own column.

`empl_id` is stored as text, not an integer: CUNY EMPLIDs are fixed-width
8-digit identifiers and leading zeros must survive.

`career_aspiration` is optional. CSTEP eligibility is not limited to
applicants already majoring in a STEM field or licensed profession — an
applicant whose major is outside that list may still qualify on the strength
of an intended STEM/licensure career, and this column captures that. Which
majors qualify, and whether a stated career goal is sufficient on its own,
are not yet decided — see Q7.

---

## 6. Decision and audit columns

| Source | Column | Type |
|---|---|---|
| Plone workflow state | `program_status` | `text` |
| date of the `accept` transition | `accepted_date` | `date` |
| decision reason | `decision_reason` | `text` |
| decision timestamp | `decided_at` | `timestamptz` |
| rule set version | `rules_version` | `text` |

`program_status` takes one of: `draft`, `submitted`, `request_more_info`,
`resubmitted`, `manual_review`, `accepted`, `rejected`. **Confirm with IT** —
on the students table this column looks like it means *enrolment* status
(`exit_date` sits beside it). If so, application status and enrolment status
must not share a column name across the two tables, or a report joining them
will silently compare different vocabularies. See Q10.

`accepted_date` is read from workflow history rather than recorded separately:
the transition is the event, and duplicating it into an annotation would give
two sources that can disagree.

`rules_version` is the reason this section exists. Income thresholds and GPA
floors will change between program years; without recording which rule set
produced a decision, a past outcome cannot be explained to an auditor. Full
decision history (including superseded decisions from before a resubmission)
stays in Plone annotations; these columns carry the current one.

`exit_date` exists on the table but this add-on never writes it — it belongs
to enrolment, after acceptance. It's listed in `field_map.NOT_POPULATED`.

---

## 7. Columns IT needs to add or change

Of the 33 columns in the STEP schema, **32 are already mapped**. Six columns
need adding and three need a type decision.

### Add (6)

| Column | Type | Why |
|---|---|---|
| `student_phone_number` | `text` | **The table has no student phone column at all.** The form requires a phone number of every applicant; today it has nowhere to go. |
| `apartment_number` | `text` | Without it the mailing address is incomplete for any applicant in an apartment building. |
| `gpa_scale` | `text` | `'4.0'` or `'100'`; makes `cumulative_gpa` interpretable. See Q4. |
| `decision_reason` | `text` | Why the application was decided as it was. |
| `decided_at` | `timestamptz` | When. |
| `rules_version` | `text` | Under which rule set. |

### Change (3)

| Column | Live type | Needs | Why |
|---|---|---|---|
| `zip_code` | `integer` | `text` | **Data loss today.** ZIP+4 (`11451-0001`) cannot be stored at all, and leading zeros are destroyed — NY's own `06390` becomes `6390`. A ZIP is an identifier, never an arithmetic operand. |
| `state` | `character` | `character(2)` | `information_schema` reports `character` for any `char(n)`, and bare `character` defaults to `char(1)`, which cannot hold `'NY'`. Confirm the length. |
| `current_grade` | `integer` | `text` | See Q9. |

---

## 8. PII and access control

Sixteen of the STEP table's columns are marked ● above;
`field_map.pii_columns()` returns the list programmatically so it can drive
IT's access review rather than being transcribed by hand.

Two notes for the database side:

- `student_id` is the Plone UID, which is opaque. It is safe as a join key
  and in URLs. We deliberately do **not** derive Plone object ids from
  applicant names, so applicant identity never appears in a URL, a web server
  log, or a referrer header.
- STEP rows contain minors' contact details plus their guardians'. If row-level
  security or a restricted reporting view is on the table, these are the rows
  that need it.

Note that only `student_id`, `first_name` and `last_name` are `NOT NULL`, so
the database enforces no completeness at all. `REQUIRED_AT_SUBMIT` in
[`rules.py`](../src/c_step_intake/eligibility/rules.py) is the only real gate.

---

## 9. Open questions

Q1–Q3 and Q7 change the *rules*; Q4–Q6 and Q8–Q10 change the *columns*.

**Q1 — Does underrepresented-minority status establish eligibility on its
own?** CSTEP eligibility is normally "historically underrepresented minority
**or** economically disadvantaged." The decision table only tests income, so
as written it would reject a URM applicant whose household income is above
threshold. Needs the program director's answer before any reject rule ships.

**Q2 — Do the categorical indicators override the income test?** If an
applicant reports free/reduced lunch, public assistance, or foster care, does
that establish economic disadvantage regardless of the income figure? Under
NYSED rules we believe yes. As the decision table stands, an applicant on
SNAP who also reports gross income would be rejected by the "income too high"
rule.

**Q3 — Is "Clarification Statement = No" an applicant answer or a staff
judgment?** `support_statement` is required on the form, so it can never be
absent — meaning decision-table rows 3 and 5 can never fire and every such
applicant lands in Manual Review instead. Either the field becomes optional,
or "No" means *staff judged the statement inadequate*, which makes it a
reviewer input rather than an applicant field.

**Q4 — What scale is a high-school GPA on?** NYC high schools commonly report
a 0–100 average; others report 4.0. The form currently accepts 0–100 to avoid
rejecting valid input, which means `cumulative_gpa` alone is ambiguous and
any GPA rule is unsafe. Either add a `gpa_scale` question to the STEP form
(our recommendation, and the reason the column is in the mapping) or require
one scale and state it on the form.

**Q5 — Should race and ethnicity be separate questions?** Federal and NYSED
reporting treats Hispanic/Latino ethnicity as a separate question from race,
and race as multi-select. The current single combined field cannot produce
those two report fields, and changing it later is a data migration. Cheap to
fix now; expensive after the first cohort.

**Q6 — Retention.** How long are rejected applications kept, and is there a
purge requirement? This affects whether the mapping needs a
`retention_expires_at` column.

**Q7 — Which majors count as a STEM field or licensed profession, and is
`career_aspiration` sufficient on its own?** CSTEP eligibility is normally
available either through a qualifying major or an applicant's stated intent
to pursue one. The `MAJOR` vocabulary has no STEM/non-STEM classification
today, and `career_aspiration` has no corresponding rule in
`eligibility/rules.py`. Needs the program director's list of qualifying
majors/professions before any major-based rule ships.

**Q8 — What should `application_date` actually mean?** It currently holds the
object's creation date, which is when the applicant *started a draft*, not
when they applied — and `created_date` holds the same value, so one of the two
is redundant. We'd suggest `application_date` = first `submit` transition,
`created_date` = row/object creation. Both are `date`, so same-day
applications cannot be ordered; if a waitlist ever needs that, one of them
should be `timestamptz`.

**Q9 — Should `current_grade` be text or integer?** The live column is
`integer`. We store text so the column can absorb `'ungraded'`, transfer
students, or non-US grade labels later without a migration. If the program is
confident grades are always 7–12 numerics, integer is fine and we'll match it.

**Q10 — Does `program_status` mean application status or enrolment status?**
On the students table, sitting next to `exit_date`, it reads as enrolment
status (`active`/`exited`/`graduated`). On the applications table we want it
to hold the Plone workflow state (`draft`…`accepted`/`rejected`). Same name,
two vocabularies, two tables — workable, but only if it's deliberate and
documented, or the application one gets its own name.

---

## 10. Changing this mapping

1. Edit `field_map.py` — it is plain data, no Plone imports.
2. Run `tox -e unit`. `test_schema_coverage.py` will fail if a form field has
   no mapping decision; `test_field_map.py` will fail on duplicates or
   program mismatches.
3. Update this document.
4. Send IT the diff of section 7 if columns changed.
