# -*- coding: utf-8 -*-
"""The decision value returned by the eligibility engine.

No Plone imports here or anywhere else in this package -- see rules.py.
"""
from dataclasses import dataclass
from dataclasses import field
from typing import Tuple


ACCEPT = 'accept'
REJECT = 'reject'
MANUAL_REVIEW = 'manual_review'
REQUEST_INFO = 'request_info'

#: Outcome -> the workflow transition the event handler should fire.
TRANSITION_BY_OUTCOME = {
    ACCEPT: 'accept',
    REJECT: 'reject',
    MANUAL_REVIEW: 'flag_for_review',
    REQUEST_INFO: 'request_info',
}


@dataclass(frozen=True)
class Decision:
    """The outcome of evaluating one application against the rule set."""

    outcome: str
    reason: str
    rules_version: str
    missing_fields: Tuple[str, ...] = field(default=())

    @property
    def transition(self):
        return TRANSITION_BY_OUTCOME[self.outcome]
