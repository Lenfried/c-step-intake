# -*- coding: utf-8 -*-
"""Tell n8n when staff decide an application, so it can email the student."""
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request

from plone import api
import transaction


logger = logging.getLogger('c_step_intake')

URL_REGISTRY_KEY = 'c_step_intake.n8n_webhook_url'
#: The shared secret lives in the environment, not the registry, so it is
#: never stored in the ZODB and site administrators cannot read it.
TOKEN_ENV_VAR = 'C_STEP_INTAKE_N8N_WEBHOOK_TOKEN'
#: Must match the header name of the n8n Header Auth credential.
TOKEN_HEADER = 'X-STEP-Token'
#: After-commit hooks run inside the staff member's request, so this is how
#: long their click can hang if n8n does not answer.
TIMEOUT_SECONDS = 5

STAFF_DECISIONS = ('accept', 'reject', 'request_info')
#: The eligibility handler fires the same transitions automatically, always
#: from these states and inside the submit/resubmit request, so an
#: application never rests in them. A decision taken from any other state
#: (manual_review, request_more_info) was made by staff.
AUTOMATIC_SOURCE_STATES = ('submitted', 'resubmitted')

#: n8n rejects a payload that breaks any of these rules.
EVENTS = tuple('application.' + t for t in STAFF_DECISIONS)
PROGRAMS = ('step', 'cstep')
MAX_COMMENT_LENGTH = 2000
UID_PATTERN = re.compile(r'^[0-9a-f]{32}$')


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Keep the shared secret on the configured endpoint."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def notify_n8n_on_staff_decision(obj, event):
    """Queue a webhook POST for a staff decision on an application.

    The POST runs after the transaction commits, so n8n never hears about a
    transition that was rolled back. Never raises.
    """
    if event.transition is None or event.transition.id not in STAFF_DECISIONS:
        return
    if event.old_state.id in AUTOMATIC_SOURCE_STATES:
        return
    path = obj.absolute_url_path()
    try:
        url = api.portal.get_registry_record(URL_REGISTRY_KEY, default=None)
        if not url:
            return
        payload = build_payload(obj, event)
        problem = payload_problem(payload)
        if problem:
            logger.error('n8n webhook not sent for %s (%s): %s',
                         path, event.transition.id, problem)
            return
        transaction.get().addAfterCommitHook(
            post_webhook, args=(url, payload, path))
    except Exception:
        logger.exception('Could not queue the n8n webhook for %s (%s)',
                         path, event.transition.id)


def build_payload(obj, event):
    """Omit applicant profile fields; n8n fetches them with its service account.

    Staff comments are included and must not contain sensitive information.
    """
    comment = str((event.kwargs or {}).get('comment') or '').strip()
    current = api.user.get_current()
    return {
        'event': 'application.' + event.transition.id,
        'uid': obj.UID(),
        'url': obj.absolute_url(),
        'program': obj.program,
        'comment': comment[:MAX_COMMENT_LENGTH],
        'actor': current.getId() if current else None,
    }


def payload_problem(payload):
    """Why n8n would reject this payload, or None if it is valid."""
    if payload['event'] not in EVENTS:
        return 'unknown event {0!r}'.format(payload['event'])
    if not UID_PATTERN.match(payload['uid'] or ''):
        return 'uid is not 32 hex characters'
    if payload['program'] not in PROGRAMS:
        return 'unknown program {0!r}'.format(payload['program'])
    if not payload['url'].startswith(('http://', 'https://')):
        return 'url is not http(s)'
    if len(payload['comment']) > MAX_COMMENT_LENGTH:
        return 'comment is longer than {0}'.format(MAX_COMMENT_LENGTH)
    return None


def post_webhook(committed, url, payload, path):
    """After-commit hook: POST the payload to n8n. Never raises.

    Logs name the object path and event only, never the token or applicant
    data. Application ids are not derived from names, so paths are safe.
    """
    if not committed:
        return
    token = os.environ.get(TOKEN_ENV_VAR)
    if not token:
        logger.warning('n8n webhook not sent for %s (%s): %s is not set',
                       path, payload['event'], TOKEN_ENV_VAR)
        return
    try:
        if urllib.parse.urlsplit(url).scheme != 'https':
            logger.error('n8n webhook not sent for %s (%s): URL must use HTTPS',
                         path, payload['event'])
            return
        request = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            method='POST',
            headers={'Content-Type': 'application/json', TOKEN_HEADER: token},
        )
        opener = urllib.request.build_opener(NoRedirectHandler())
        opener.open(request, timeout=TIMEOUT_SECONDS).close()
    except urllib.error.HTTPError as error:
        # urllib raises for every non-2xx response.
        logger.error('n8n webhook for %s (%s) was refused: HTTP %s',
                     path, payload['event'], error.code)
    except Exception:
        logger.exception('n8n webhook failed for %s (%s)',
                         path, payload['event'])
