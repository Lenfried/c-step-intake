# -*- coding: utf-8 -*-
"""Integration tests for the application workflow and the eligibility handler.

The permission tests here are the FERPA-critical ones: they assert that an
applicant cannot edit a submitted application and cannot see anyone else's.
"""
import unittest

from AccessControl import getSecurityManager
from plone import api
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.dexterity.utils import createContentInContainer
from c_step_intake.interfaces import IEligibilityRecord
from c_step_intake.testing import C_STEP_INTAKE_INTEGRATION_TESTING
from c_step_intake.tests.test_eligibility_rules import step_payload
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent


class TestApplicationWorkflow(unittest.TestCase):

    layer = C_STEP_INTAKE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder = api.content.create(
            container=self.portal, type='Folder', id='applications')

    def _application(self, **overrides):
        return createContentInContainer(
            self.folder,
            'step_application',
            checkConstraints=False,
            **step_payload(**overrides)
        )

    def test_initial_state_is_draft(self):
        self.assertEqual('draft', api.content.get_state(self._application()))

    def test_workflow_is_bound_to_both_types(self):
        chain = self.portal.portal_workflow.getChainForPortalType
        for portal_type in ('step_application', 'cstep_application'):
            self.assertEqual(
                ('step-cstep-application',), chain(portal_type))

    def test_submit_routes_a_complete_application_to_manual_review(self):
        application = self._application()
        api.content.transition(obj=application, transition='submit')
        self.assertEqual('manual_review',
                         api.content.get_state(application))

    def test_submit_returns_an_incomplete_application_to_the_applicant(self):
        application = self._application(school_name=None)
        api.content.transition(obj=application, transition='submit')
        self.assertEqual('request_more_info',
                         api.content.get_state(application))

    def test_submit_records_the_decision(self):
        application = self._application()
        api.content.transition(obj=application, transition='submit')
        record = IEligibilityRecord(application)
        self.assertEqual(1, len(record.entries()))
        latest = record.latest()
        self.assertEqual('manual_review', latest['outcome'])
        self.assertTrue(latest['rules_version'])
        self.assertIsNotNone(latest['decided_at'])

    def test_resubmitting_appends_a_second_decision(self):
        application = self._application(school_name=None)
        api.content.transition(obj=application, transition='submit')
        application.school_name = 'York Early College Academy'
        api.content.transition(obj=application, transition='resubmit')
        self.assertEqual('manual_review',
                         api.content.get_state(application))
        # The first outcome is retained: an audit must be able to see that the
        # application was once incomplete.
        record = IEligibilityRecord(application)
        self.assertEqual(
            ['request_info', 'manual_review'],
            [entry['outcome'] for entry in record.entries()],
        )

    def test_handler_does_not_recurse(self):
        # The follow-on transition fired by the handler must not itself be
        # evaluated, or the decision would be recorded repeatedly.
        application = self._application()
        api.content.transition(obj=application, transition='submit')
        self.assertEqual(1, len(IEligibilityRecord(application).entries()))

    def test_saving_a_draft_does_not_produce_a_decision(self):
        # The handler is bound to the transition, not to modification. An
        # applicant part-way through the form must not trip a decision.
        application = self._application()
        notify(ObjectModifiedEvent(application))
        self.assertEqual('draft', api.content.get_state(application))
        self.assertEqual([], IEligibilityRecord(application).entries())


class TestApplicantPermissions(unittest.TestCase):

    layer = C_STEP_INTAKE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        self.folder = api.content.create(
            container=self.portal, type='Folder', id='applications')
        self.application = createContentInContainer(
            self.folder, 'step_application', checkConstraints=False,
            **step_payload())
        # Staff must be different people from the applicant. TEST_USER created
        # the application and therefore holds Owner on it permanently --
        # setRoles() changes portal roles and cannot take a local role away.
        # Standing that user in for staff silently grants every staff check
        # Owner's rights as well, which is what made a draft look visible to
        # staff and what let the 'staff may view a submission' check pass
        # without exercising the ProgramStaff grant at all.
        api.user.create(email='staffer@york.cuny.edu', username='staffer',
                        password='secret_staffer', roles=('ProgramStaff',))
        api.user.create(email='director@york.cuny.edu', username='director',
                        password='secret_director', roles=('ProgramDirector',))

    def _can(self, permission):
        return bool(
            getSecurityManager().checkPermission(permission, self.application))

    def test_applicant_may_edit_a_draft(self):
        setRoles(self.portal, TEST_USER_ID, ['Owner'])
        login(self.portal, TEST_USER_NAME)
        self.assertTrue(self._can('Modify portal content'))

    def test_applicant_may_not_edit_once_submitted(self):
        api.content.transition(obj=self.application, transition='submit')
        setRoles(self.portal, TEST_USER_ID, ['Owner'])
        login(self.portal, TEST_USER_NAME)
        self.assertFalse(self._can('Modify portal content'))

    def test_applicant_regains_edit_when_more_information_is_requested(self):
        api.content.transition(obj=self.application, transition='submit')
        if api.content.get_state(self.application) != 'request_more_info':
            api.content.transition(
                obj=self.application, transition='request_info')
        setRoles(self.portal, TEST_USER_ID, ['Owner'])
        login(self.portal, TEST_USER_NAME)
        self.assertTrue(self._can('Modify portal content'))

    def test_a_draft_is_not_visible_to_program_staff(self):
        login(self.portal, 'staffer')
        self.assertFalse(self._can('View'))

    def test_program_staff_may_view_a_submitted_application(self):
        api.content.transition(obj=self.application, transition='submit')
        login(self.portal, 'staffer')
        self.assertTrue(self._can('View'))

    def test_program_staff_may_not_decide(self):
        api.content.transition(obj=self.application, transition='submit')
        login(self.portal, 'staffer')
        self.assertFalse(self._can('c_step_intake: Decide Application'))

    def test_program_director_may_decide(self):
        api.content.transition(obj=self.application, transition='submit')
        login(self.portal, 'director')
        self.assertTrue(self._can('c_step_intake: Decide Application'))

    def test_anonymous_may_never_view_an_application(self):
        api.content.transition(obj=self.application, transition='submit')
        setRoles(self.portal, TEST_USER_ID, [])
        logout_roles = self.application.rolesOfPermission('View')
        granted = {
            entry['name'] for entry in logout_roles if entry['selected']}
        self.assertNotIn('Anonymous', granted)
        self.assertNotIn('Authenticated', granted)
