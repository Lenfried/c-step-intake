# -*- coding: utf-8 -*-
"""Run the eligibility rules when an application is submitted."""
import logging

from plone import api
from c_step_intake.db.serializer import to_payload
from c_step_intake.eligibility.rules import decide
from c_step_intake.interfaces import IEligibilityRecord


logger = logging.getLogger('c_step_intake')

#: Only these transitions trigger an evaluation. This filter is also what
#: stops the handler recursing: the transition it fires below is not in the
#: set, so the resulting event is ignored.
EVALUATED_TRANSITIONS = ('submit', 'resubmit')


def evaluate_application(obj, event):
    """Evaluate eligibility and move the application to the decided state.

    Bound to the workflow transition rather than to IObjectModifiedEvent
    deliberately: modification fires on every draft save, and an applicant
    part-way through the form must not trip a decision.
    """
    if event.transition is None:
        # Fires on object creation as well as on real transitions.
        return
    if event.transition.id not in EVALUATED_TRANSITIONS:
        return

    payload = to_payload(obj)
    decision = decide(obj.program, payload)
    IEligibilityRecord(obj).record(decision, payload)

    # The applicant fired 'submit' and has no permission to accept, reject or
    # flag their own application, so the follow-on transition is elevated.
    with api.env.adopt_roles(['Manager']):
        api.content.transition(obj=obj, transition=decision.transition)

    logger.info(
        'Application %s (%s): %s via %s [rules %s]',
        obj.absolute_url_path(),
        obj.program,
        decision.outcome,
        decision.transition,
        decision.rules_version,
    )
