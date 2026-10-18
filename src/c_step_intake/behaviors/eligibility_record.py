# -*- coding: utf-8 -*-
"""Append-only storage for eligibility decisions.

Decisions live in annotations rather than schema fields for two reasons: they
must never appear on the applicant's edit form, and they must not be editable
by anyone once written. Adding a schema field would give both away.
"""
from datetime import datetime

from persistent.dict import PersistentDict
from persistent.list import PersistentList
from c_step_intake.interfaces import IEligibilityRecord
from c_step_intake.interfaces import IEligibilityRecordMarker
from zope.annotation.interfaces import IAnnotations
from zope.component import adapter
from zope.interface import implementer


KEY = 'c_step_intake.eligibility_record'


@implementer(IEligibilityRecord)
@adapter(IEligibilityRecordMarker)
class EligibilityRecord(object):

    def __init__(self, context):
        self.context = context
        annotations = IAnnotations(context)
        if KEY not in annotations:
            annotations[KEY] = PersistentList()
        self.storage = annotations[KEY]

    def record(self, decision, payload):
        self.storage.append(PersistentDict({
            'outcome': decision.outcome,
            'reason': decision.reason,
            'rules_version': decision.rules_version,
            'missing_fields': list(decision.missing_fields),
            'decided_at': datetime.utcnow(),
            'payload': PersistentDict(payload),
        }))

    def entries(self):
        return list(self.storage)

    def latest(self):
        if not self.storage:
            return None
        return self.storage[-1]
