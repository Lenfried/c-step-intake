# -*- coding: utf-8 -*-
"""Emails sent when an application is submitted.

- Staff get one email per new application.
- The applicant gets one each time a submission is sent back as incomplete.
"""
import logging

from plone import api
from plone.dexterity.utils import iterSchemata
from zope.schema import getFields


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


INCOMPLETE_SUBJECT = 'Your {program} application needs more information'
INCOMPLETE_BODY = """\
Thank you for applying to {program}.

Your application could not be reviewed yet because these questions were not
answered:

{missing}

Please answer them and submit your application again:
{url}
"""


def field_titles(obj, names):
    """Return the form labels of ``names``, in the order given."""
    titles = {}
    for schemata in iterSchemata(obj):
        for name, field in getFields(schemata).items():
            titles.setdefault(name, str(field.title))
    return [titles.get(name, name) for name in names]


def notify_incomplete_application(obj, decision):
    """Email the applicant the questions their submission is missing.

    Sent to the applicant's own email address. Never raises, for the same
    reason as notify_new_application.
    """
    try:
        recipient = getattr(obj, 'student_email', None)
        if not recipient:
            logger.warning(
                'No applicant email on %s; incomplete-application notice '
                'not sent', obj.absolute_url_path())
            return
        missing = '\n'.join(
            '- {0}'.format(title)
            for title in field_titles(obj, decision.missing_fields))
        api.portal.send_email(
            recipient=recipient,
            subject=INCOMPLETE_SUBJECT.format(program=obj.program.upper()),
            body=INCOMPLETE_BODY.format(
                program=obj.program.upper(),
                missing=missing,
                url='{0}/edit'.format(obj.absolute_url()),
            ),
        )
    except Exception:
        logger.exception(
            'Could not send the incomplete-application notice for %s',
            obj.absolute_url_path())
