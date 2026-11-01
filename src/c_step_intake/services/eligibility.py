# -*- coding: utf-8 -*-
"""GET @eligibility: the latest eligibility decision, for program staff.

Only users with the review permission on the application get the decision.
Everyone else gets ``{"available": false}`` rather than an error, so the
Volto view can call this for any viewer and simply show nothing.

The payload snapshot stored with each decision is never returned: staff see
the answers on the application itself.
"""
from plone import api
from plone.restapi.services import Service
from c_step_intake.interfaces import IEligibilityRecord

REVIEW_PERMISSION = 'c_step_intake: Review Application'


def serialize_entry(entry):
    decided_at = entry.get('decided_at')
    return {
        'outcome': entry.get('outcome'),
        'reason': entry.get('reason'),
        'rules_version': entry.get('rules_version'),
        'missing_fields': list(entry.get('missing_fields') or []),
        # Decisions made before rules 0.3.0 have no assessment.
        'eligibility': entry.get('eligibility'),
        'decided_at': decided_at.isoformat() + 'Z' if decided_at else None,
    }


class EligibilityGet(Service):

    def reply(self):
        url = '{0}/@eligibility'.format(self.context.absolute_url())
        if not api.user.has_permission(REVIEW_PERMISSION, obj=self.context):
            return {'@id': url, 'available': False}
        entries = IEligibilityRecord(self.context).entries()
        return {
            '@id': url,
            'available': True,
            'latest': serialize_entry(entries[-1]) if entries else None,
            'decisions': len(entries),
        }
