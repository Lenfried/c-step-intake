# Eligibility rules

**Status:** not yet defined. Nothing is auto-accepted or auto-rejected.
**Implementation:** [`src/c_step_intake/eligibility/rules.py`](../src/c_step_intake/eligibility/rules.py)
**Current version:** `0.2.0-incomplete-to-staff`

## What is implemented today

One rule: **completeness**. If a field in `REQUIRED_AT_SUBMIT` is blank, the
missing field names are recorded in the decision reason and the decision's
`missing_fields`. The application still goes to `manual_review`; it is **not**
sent back to the applicant. The form already requires every one of these
answers, and applicants cannot save a partial draft, so an incomplete
application can only come from staff entry, an import or a later form change.
Staff are the ones to fix it. They can still use "Request info" to send any
application back to its applicant.

Everything else — every complete application, regardless of GPA or income —
also goes to `manual_review` for a human decision. **Program decision
(2026-10-31):** this stays true even once the eligibility criteria below are
implemented. Complete applications go to staff review whether or not they
look eligible; the rules may annotate the decision, but never accept or
reject on their own. This is deliberate. Auto-reject
on criteria nobody has signed off is the one failure mode here that harms a
real applicant and is invisible until someone complains.

`test_eligibility_rules.py` contains a guard test asserting that no payload
can reach a `reject` outcome. Delete that test in the same commit that adds
the first reject rule.

## STEP acceptance criteria

ELIGIBLE = Condition 1 **and** Condition 2 **and** Condition 3 (3a **or** 3b).

| Condition | Rule | Form field(s) |
|---|---|---|
| 1 | Resides in New York State | `nys_resident` |
| 2 | Enrolled in grades 7–12 | `current_grade` (offers only 7–12) |
| 3a | Economically disadvantaged — any one of: free/reduced lunch (verified by school); Family Assistance / Safety Net; Family Day-Care payments; foster care with no money from natural parents; ward of the State or a county; family income at or below the 2022–28 STEP threshold | `free_reduced_lunch`, `other_economic_disadvantage`, `household_income` + `household_size` |
| 3b | Needs, or would greatly benefit from, STEM enrichment or support — judged by program staff from the student's written statement | `stem_statement` (optional; not stored in `step_student`) |

A student who is not economically disadvantaged can still be eligible on 3b
alone, and one with no statement can still be eligible on 3a alone, so
`stem_statement` is optional and an application without it is complete.

Not yet implemented in `rules.py`. Still missing: the 2022–28 income table by
household size, and a "ward of the State or a county" option in
`OTHER_ECONOMIC_DISADVANTAGE`. 3b is a staff judgment and cannot be automated.

## The intended rule set

From `ref/Decision Table.xlsx`, first match wins:

| # | Completeness | GPA | Income | Statement | → Decision |
|---|---|---|---|---|---|
| 1 | Missing | – | – | – | Request Info (superseded: now Manual Review, see above) |
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
| `0.2.0-incomplete-to-staff` | 2026-10-31 | Incomplete applications route to manual review with their missing fields listed, instead of back to the applicant. |
