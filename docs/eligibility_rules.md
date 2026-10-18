# Eligibility rules

**Status:** not yet defined. Nothing is auto-accepted or auto-rejected.
**Implementation:** [`src/c_step_intake/eligibility/rules.py`](../src/c_step_intake/eligibility/rules.py)
**Current version:** `0.1.0-completeness-only`

## What is implemented today

One rule: **completeness**. If a field in `REQUIRED_AT_SUBMIT` is blank, the
application returns to the applicant as `request_more_info`, with the missing
field names in the decision reason.

Everything else — every complete application, regardless of GPA or income —
goes to `manual_review` for a human decision. This is deliberate. Auto-reject
on criteria nobody has signed off is the one failure mode here that harms a
real applicant and is invisible until someone complains.

`test_eligibility_rules.py` contains a guard test asserting that no payload
can reach a `reject` outcome. Delete that test in the same commit that adds
the first reject rule.

## The intended rule set

From `ref/Decision Table.xlsx`, first match wins:

| # | Completeness | GPA | Income | Statement | → Decision |
|---|---|---|---|---|---|
| 1 | Missing | – | – | – | Request Info |
| 2 | Complete | Low | – | – | Reject |
| 3 | Complete | OK | Missing | No | Request Info |
| 4 | Complete | OK | Missing | Yes | Manual Review |
| 5 | Complete | OK | High | No | Reject |
| 6 | Complete | OK | High | Yes | Manual Review |
| 7 | Complete | OK | Eligible | – | Accept |

Rule 1 is what ships today. Rules 2–7 are blocked on the questions below.

Two columns in the source table — `Major` and `Enrolled Full-time` — are
listed as dimensions but blank in every row. `Major` now has a form field
behind it on the CSTEP side: an applicant whose declared major is not itself
a STEM field or licensed profession can instead complete `career_aspiration`
to describe the one they intend to pursue. CSTEP eligibility is meant to
accept either basis, but the table has no row that tests it, and neither
"which majors qualify" nor "does a stated career goal alone qualify an
applicant" is decided — see question 6 below. `Enrolled Full-time` still has
no corresponding form field. Drop it from the table or add the field.

## Blocking questions

These are duplicated in `docs/field_mapping.md` §9, where they sit alongside
their column implications.

1. **Does underrepresented-minority status establish eligibility on its own,
   independent of household income?** If yes, rule 5 as written is wrong.
2. **Do free/reduced lunch, public assistance, or foster care override the
   income test?** We believe NYSED says yes; the table doesn't reflect it.
3. **Is "Clarification Statement = No" an applicant answer or a staff
   judgment?** `support_statement` is required, so rules 3 and 5 are currently
   unreachable.
4. **What GPA floor applies, on what scale, per program?** High-school GPA
   scale is ambiguous today (0–100 vs 4.0).
5. **What are the income thresholds by household size, and for which program
   year?** Needed as a table keyed on `household_size` 1–9.
6. **Which majors count as a "STEM field or licensed profession" for CSTEP
   eligibility, and does a stated `career_aspiration` alone qualify an
   applicant whose major is not one of them?** The `MAJOR` vocabulary has no
   STEM/non-STEM classification today, and `career_aspiration` has no
   corresponding rule in `rules.py` yet — every CSTEP application still falls
   through to manual review regardless of major or stated career goal.

## Adding a rule

1. Write the test first, in `tests/test_eligibility_rules.py` — one test per
   decision-table row, using the `step_payload()` / `cstep_payload()` helpers.
2. Add the rule to `decide()`, above the manual-review fallthrough. Order
   matters: first match wins.
3. Bump `RULES_VERSION`. Past decisions record the version that produced
   them, so an auditor can always reconstruct which rules applied.
4. Note the change and its effective program year here.

`rules.py` imports nothing from Plone or Zope. Keep it that way — it is what
makes the whole rule set testable in milliseconds without a site fixture, and
what lets a student developer change a threshold with confidence.

## Version history

| Version | Date | Change |
|---|---|---|
| `0.1.0-completeness-only` | 2026-09-10 | Initial. Completeness check only; all complete applications route to manual review. |
