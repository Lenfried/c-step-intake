# -*- coding: utf-8 -*-
"""CSTEP is off unless the c_step_intake:cstep profile is applied."""
from c_step_intake.testing import STEP_ONLY_INTEGRATION_TESTING

import unittest


class TestCstepToggle(unittest.TestCase):

    layer = STEP_ONLY_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']

    def test_default_profile_installs_step_only(self):
        types = self.portal.portal_types
        self.assertIn('step_application', types.objectIds())
        self.assertNotIn('cstep_application', types.objectIds())

    def test_cstep_has_no_workflow_binding_by_default(self):
        chain = self.portal.portal_workflow.getChainForPortalType
        self.assertEqual(('step-cstep-application',),
                         chain('step_application'))
        self.assertNotIn('step-cstep-application', chain('cstep_application'))

    def test_cstep_profile_enables_the_type(self):
        self.portal.portal_setup.runAllImportStepsFromProfile(
            'profile-c_step_intake:cstep')
        self.assertIn('cstep_application', self.portal.portal_types.objectIds())
        self.assertEqual(
            ('step-cstep-application',),
            self.portal.portal_workflow.getChainForPortalType(
                'cstep_application'))
