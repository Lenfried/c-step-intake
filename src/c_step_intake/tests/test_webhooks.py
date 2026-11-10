# -*- coding: utf-8 -*-
"""Staff decisions on applications are posted to n8n after commit."""
from unittest import mock

from Acquisition import aq_base
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from c_step_intake import webhooks
from c_step_intake.eligibility.decision import ACCEPT
from c_step_intake.eligibility.decision import Decision
from c_step_intake.testing import C_STEP_INTAKE_INTEGRATION_TESTING
from c_step_intake.tests.test_eligibility_rules import step_payload

import json
import os
import transaction
import unittest
import urllib.error

URL = 'https://n8n.example.edu/webhook/plone-application-decision'
TOKEN = 's3cret-token'
URLOPEN = 'c_step_intake.webhooks.urllib.request.urlopen'
SEND_EMAIL = 'c_step_intake.notifications.api.portal.send_email'


def queued_hooks():
    """The webhook hooks queued on the current transaction, as (args)."""
    return [args for hook, args, kwargs
            in transaction.get().getAfterCommitHooks()
            if hook is webhooks.post_webhook]


def queued_payloads():
    return [args[1] for args in queued_hooks()]


class TestStaffDecisionWebhook(unittest.TestCase):

    layer = C_STEP_INTAKE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        api.portal.set_registry_record(webhooks.URL_REGISTRY_KEY, URL)
        folder = api.content.create(
            container=self.portal, type='Folder', id='applications')
        self.application = createContentInContainer(
            folder, 'step_application', checkConstraints=False,
            **step_payload())
        with mock.patch(SEND_EMAIL):
            api.content.transition(obj=self.application, transition='submit')
        self.assertEqual('manual_review',
                         api.content.get_state(self.application))

    def transition(self, name, **kwargs):
        with mock.patch(SEND_EMAIL):
            api.content.transition(
                obj=self.application, transition=name, **kwargs)

    def test_url_record_is_installed(self):
        record = api.portal.get_registry_record(
            webhooks.URL_REGISTRY_KEY, default='missing')
        self.assertNotEqual('missing', record)

    def test_submit_alone_queues_nothing(self):
        self.assertEqual([], queued_payloads())

    def test_each_decision_posts_once_with_token(self):
        """Run the queued hooks as a commit would, for each decision."""
        for name in webhooks.STAFF_DECISIONS:
            with self.subTest(transition=name):
                before = len(queued_hooks())
                self.transition(name)
                new = queued_hooks()[before:]
                self.assertEqual(1, len(new))
                with mock.patch.dict(os.environ,
                                     {webhooks.TOKEN_ENV_VAR: TOKEN}), \
                        mock.patch(URLOPEN) as urlopen:
                    webhooks.post_webhook(True, *new[0])
                self.assertEqual(1, urlopen.call_count)
                request = urlopen.call_args.args[0]
                self.assertEqual(URL, request.full_url)
                self.assertEqual(TOKEN, request.get_header('X-step-token'))
                self.assertEqual('application/json',
                                 request.get_header('Content-type'))
                self.assertEqual('application.' + name,
                                 json.loads(request.data)['event'])
                # Back to manual review for the next decision.
                self.transition('reopen' if name != 'request_info'
                                else 'resubmit')

    def test_payload_fields_and_no_applicant_details(self):
        self.transition('request_info', comment='  Missing transcript  ')
        [payload] = queued_payloads()
        self.assertEqual({
            'event': 'application.request_info',
            'uid': self.application.UID(),
            'url': self.application.absolute_url(),
            'program': 'step',
            'comment': 'Missing transcript',
            'actor': TEST_USER_ID,
        }, payload)
        body = json.dumps(payload)
        self.assertNotIn(self.application.first_name, body)
        self.assertNotIn(self.application.student_email, body)

    def test_missing_comment_is_empty_string(self):
        self.transition('accept')
        self.assertEqual('', queued_payloads()[-1]['comment'])

    def test_long_comment_is_truncated(self):
        self.transition('reject', comment='x' * 2500)
        comment = queued_payloads()[-1]['comment']
        self.assertEqual(webhooks.MAX_COMMENT_LENGTH, len(comment))

    def test_reject_while_waiting_for_more_info_is_sent(self):
        """request_more_info -> reject is a staff decision too."""
        self.transition('request_info')
        self.transition('reject')
        self.assertEqual(
            ['application.request_info', 'application.reject'],
            [p['event'] for p in queued_payloads()])

    def test_other_transitions_queue_nothing(self):
        self.transition('accept')
        self.transition('reopen')
        self.transition('request_info')
        self.transition('resubmit')
        self.assertEqual(
            ['application.accept', 'application.request_info'],
            [p['event'] for p in queued_payloads()])

    def test_automatic_decision_is_not_queued(self):
        decision = Decision(outcome=ACCEPT, reason='test',
                            rules_version='test', missing_fields=(),
                            assessment=None)
        self.transition('request_info')
        before = len(queued_payloads())
        with mock.patch('c_step_intake.event_handlers.decide',
                        return_value=decision):
            self.transition('resubmit')
        self.assertEqual('accepted', api.content.get_state(self.application))
        self.assertEqual(before, len(queued_payloads()))

    def test_empty_url_turns_webhook_off(self):
        api.portal.set_registry_record(webhooks.URL_REGISTRY_KEY, u'')
        self.transition('accept')
        self.assertEqual([], queued_payloads())

    def test_invalid_payload_is_logged_not_queued(self):
        content_class = type(aq_base(self.application))
        with mock.patch.object(content_class, 'program', 'other'), \
                self.assertLogs('c_step_intake', 'ERROR') as logs:
            self.transition('accept')
        self.assertEqual([], queued_payloads())
        self.assertIn('unknown program', logs.output[0])
        self.assertEqual('accepted', api.content.get_state(self.application))


class TestPostWebhook(unittest.TestCase):

    payload = {'event': 'application.accept', 'uid': 'a' * 32}
    path = '/plone/applications/step_application'

    def setUp(self):
        patcher = mock.patch.dict(os.environ, {webhooks.TOKEN_ENV_VAR: TOKEN})
        patcher.start()
        self.addCleanup(patcher.stop)

    def post(self, committed=True):
        webhooks.post_webhook(committed, URL, self.payload, self.path)

    def test_posts_json_with_token_and_timeout(self):
        with mock.patch(URLOPEN) as urlopen:
            self.post()
        request = urlopen.call_args.args[0]
        self.assertEqual('POST', request.get_method())
        self.assertEqual(self.payload, json.loads(request.data))
        self.assertEqual(webhooks.TIMEOUT_SECONDS,
                         urlopen.call_args.kwargs['timeout'])

    def test_aborted_transaction_sends_nothing(self):
        with mock.patch(URLOPEN) as urlopen:
            self.post(committed=False)
        urlopen.assert_not_called()

    def test_missing_token_logs_warning_and_sends_nothing(self):
        del os.environ[webhooks.TOKEN_ENV_VAR]
        with mock.patch(URLOPEN) as urlopen, \
                self.assertLogs('c_step_intake', 'WARNING') as logs:
            self.post()
        urlopen.assert_not_called()
        self.assertIn(webhooks.TOKEN_ENV_VAR, logs.output[0])

    def test_non_2xx_is_logged_with_status_and_no_token(self):
        error = urllib.error.HTTPError(URL, 403, 'Forbidden', {}, None)
        with mock.patch(URLOPEN, side_effect=error), \
                self.assertLogs('c_step_intake', 'ERROR') as logs:
            self.post()
        output = '\n'.join(logs.output)
        self.assertIn('HTTP 403', output)
        self.assertIn(self.path, output)
        self.assertIn('application.accept', output)
        self.assertNotIn(TOKEN, output)

    def test_network_error_is_logged_and_does_not_raise(self):
        with mock.patch(URLOPEN, side_effect=OSError('n8n down')), \
                self.assertLogs('c_step_intake', 'ERROR') as logs:
            self.post()
        output = '\n'.join(logs.output)
        self.assertIn(self.path, output)
        self.assertNotIn(TOKEN, output)
