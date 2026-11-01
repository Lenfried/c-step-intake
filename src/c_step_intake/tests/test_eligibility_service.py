# -*- coding: utf-8 -*-
"""GET @eligibility shows staff the latest decision and nobody else."""
from plone import api
from plone.app.testing import setRoles
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from plone.testing.zope import Browser
from c_step_intake.testing import C_STEP_INTAKE_FUNCTIONAL_TESTING
from c_step_intake.tests.test_eligibility_rules import step_payload

import json
import transaction
import unittest

PASSWORD = 'secret-password-123'


class TestEligibilityService(unittest.TestCase):

    layer = C_STEP_INTAKE_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.application = createContentInContainer(
            self.portal, 'step_application', checkConstraints=False,
            **step_payload(other_economic_disadvantage='foster_care'))
        for username, roles in (('staff', ['ProgramStaff']),
                                ('applicant', ['Member'])):
            api.user.create(email='{0}@example.com'.format(username),
                            username=username, password=PASSWORD,
                            roles=roles)
        api.user.grant_roles(username='applicant', obj=self.application,
                             roles=['Owner'])
        transaction.commit()

    def get(self, username, password=PASSWORD):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False
        browser.addHeader('Accept', 'application/json')
        browser.addHeader('Authorization',
                          'Basic {0}:{1}'.format(username, password))
        browser.open(self.application.absolute_url() + '/@eligibility')
        return json.loads(browser.contents)

    def submit(self):
        api.content.transition(obj=self.application, transition='submit')
        transaction.commit()

    def test_staff_see_the_latest_decision(self):
        self.submit()
        data = self.get('staff')
        self.assertTrue(data['available'])
        self.assertEqual(1, data['decisions'])
        latest = data['latest']
        self.assertEqual('manual_review', latest['outcome'])
        self.assertEqual('meets the criteria (1, 2 and 3a)',
                         latest['eligibility']['overall'])
        self.assertEqual('met', latest['eligibility']['checks'][2]['status'])
        self.assertTrue(latest['decided_at'].endswith('Z'))

    def test_the_answers_snapshot_is_not_returned(self):
        self.submit()
        latest = self.get(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)['latest']
        self.assertNotIn('payload', latest)
        self.assertNotIn(self.application.first_name, json.dumps(latest))

    def test_applicant_gets_nothing_and_no_error(self):
        # Volto shows a site-wide error page on 401, so the applicant viewing
        # their own application must get a normal response.
        self.submit()
        self.assertEqual({'available': False},
                         {k: v for k, v in self.get('applicant').items()
                          if k != '@id'})

    def test_drafts_have_nothing_to_review(self):
        # The workflow grants the review permission to nobody in draft, so
        # not even a Manager gets a decision before submission.
        data = self.get(SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        self.assertFalse(data['available'])
