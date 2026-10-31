# -*- coding: utf-8 -*-
"""Submission emails.

- Staff get the new-application email on first submit only.
- The applicant gets a notice each time a submission comes back incomplete.
"""
from unittest import mock

from plone import api
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from c_step_intake.notifications import REGISTRY_KEY
from c_step_intake.testing import C_STEP_INTAKE_INTEGRATION_TESTING
from c_step_intake.tests.test_eligibility_rules import step_payload

import unittest

SEND = 'c_step_intake.notifications.api.portal.send_email'
STAFF = 'cstep-n8n@mailings.york.cuny.edu'


def sent_to(send, recipient):
    """Return the calls of the mocked send_email addressed to recipient."""
    return [c for c in send.call_args_list
            if c.kwargs['recipient'] == recipient]


class TestNotifications(unittest.TestCase):

    layer = C_STEP_INTAKE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        folder = api.content.create(
            container=self.portal, type='Folder', id='applications')
        self.application = createContentInContainer(
            folder, 'step_application', checkConstraints=False,
            **step_payload())

    def test_default_recipient_is_configured(self):
        self.assertEqual(
            'cstep-n8n@mailings.york.cuny.edu',
            api.portal.get_registry_record(REGISTRY_KEY))

    def test_submit_sends_one_email_without_applicant_details(self):
        with mock.patch(SEND) as send:
            api.content.transition(obj=self.application, transition='submit')
        self.assertEqual(1, send.call_count)
        kwargs = send.call_args.kwargs
        self.assertEqual('cstep-n8n@mailings.york.cuny.edu',
                         kwargs['recipient'])
        self.assertIn(self.application.absolute_url(), kwargs['body'])
        self.assertNotIn(self.application.first_name, kwargs['body'])
        self.assertNotIn(self.application.last_name, kwargs['body'])

    def test_resubmit_does_not_send(self):
        self.application.school_name = None
        with mock.patch(SEND) as send:
            api.content.transition(obj=self.application, transition='submit')
            self.application.school_name = 'York Early College Academy'
            api.content.transition(
                obj=self.application, transition='resubmit')
        self.assertEqual(1, len(sent_to(send, STAFF)))

    def test_empty_address_turns_notifications_off(self):
        api.portal.set_registry_record(REGISTRY_KEY, u'')
        with mock.patch(SEND) as send:
            api.content.transition(obj=self.application, transition='submit')
        send.assert_not_called()

    def test_mail_failure_does_not_block_submission(self):
        with mock.patch(SEND, side_effect=RuntimeError('smtp down')):
            api.content.transition(obj=self.application, transition='submit')
        self.assertEqual('manual_review',
                         api.content.get_state(self.application))


class TestIncompleteNotice(unittest.TestCase):

    layer = C_STEP_INTAKE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        folder = api.content.create(
            container=self.portal, type='Folder', id='applications')
        self.application = createContentInContainer(
            folder, 'step_application', checkConstraints=False,
            **step_payload())
        self.applicant = self.application.student_email

    def test_complete_submission_sends_the_applicant_nothing(self):
        with mock.patch(SEND) as send:
            api.content.transition(obj=self.application, transition='submit')
        self.assertEqual([], sent_to(send, self.applicant))
        self.assertEqual('manual_review',
                         api.content.get_state(self.application))

    def test_incomplete_submission_emails_the_applicant(self):
        self.application.school_name = None
        self.application.parent1_phone = ''
        with mock.patch(SEND) as send:
            api.content.transition(obj=self.application, transition='submit')
        self.assertEqual('request_more_info',
                         api.content.get_state(self.application))
        [call] = sent_to(send, self.applicant)
        body = call.kwargs['body']
        # Form labels, not field names, in schema order.
        self.assertIn('- School name\n- Parent / guardian phone', body)
        self.assertIn(self.application.absolute_url() + '/edit', body)
        self.assertIn('STEP', call.kwargs['subject'])

    def test_each_incomplete_resubmission_sends_another_notice(self):
        self.application.school_name = None
        with mock.patch(SEND) as send:
            api.content.transition(obj=self.application, transition='submit')
            api.content.transition(
                obj=self.application, transition='resubmit')
        self.assertEqual(2, len(sent_to(send, self.applicant)))

    def test_completed_resubmission_sends_no_notice(self):
        self.application.school_name = None
        with mock.patch(SEND) as send:
            api.content.transition(obj=self.application, transition='submit')
            self.application.school_name = 'York Early College Academy'
            api.content.transition(
                obj=self.application, transition='resubmit')
        self.assertEqual(1, len(sent_to(send, self.applicant)))
        self.assertEqual('manual_review',
                         api.content.get_state(self.application))

    def test_no_applicant_email_skips_the_notice(self):
        self.application.school_name = None
        self.application.student_email = None
        with mock.patch(SEND) as send:
            api.content.transition(obj=self.application, transition='submit')
        self.assertEqual([STAFF],
                         [c.kwargs['recipient'] for c in send.call_args_list])

    def test_mail_failure_does_not_block_sending_back(self):
        self.application.school_name = None
        with mock.patch(SEND, side_effect=RuntimeError('smtp down')):
            api.content.transition(obj=self.application, transition='submit')
        self.assertEqual('request_more_info',
                         api.content.get_state(self.application))
