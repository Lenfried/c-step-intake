# -*- coding: utf-8 -*-
"""Email staff when a new application is submitted."""
import logging

from plone import api


logger = logging.getLogger('c_step_intake')

REGISTRY_KEY = 'c_step_intake.notification_email'

SUBJECT = 'New {program} application submitted'
BODY = """\
A new {program} application was submitted.

Review it: {url}
Outcome of the automatic check: {outcome}

This message deliberately contains no applicant details.
"""


def notify_new_application(obj, decision):
    """Email the configured address about a newly submitted application.

    Never raises: a mail failure must not roll back or block an applicant's
    submission. Failures are logged instead.
    """
    try:
        recipient = api.portal.get_registry_record(
            REGISTRY_KEY, default=None)
        if not recipient:
            return
        api.portal.send_email(
            recipient=recipient,
            subject=SUBJECT.format(program=obj.program.upper()),
            body=BODY.format(
                program=obj.program.upper(),
                url=obj.absolute_url(),
                outcome=decision.outcome,
            ),
        )
    except Exception:
        logger.exception(
            'Could not send the new-application notification for %s',
            obj.absolute_url_path())
