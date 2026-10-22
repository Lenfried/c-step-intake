# -*- coding: utf-8 -*-
"""Add and edit forms show every fieldset on one page, not as tabs."""
from c_step_intake.testing import C_STEP_INTAKE_INTEGRATION_TESTING
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from plone.dexterity.utils import createContentInContainer
from zope.component import getMultiAdapter
from zope.component import queryMultiAdapter

import unittest


class TestSinglePageForms(unittest.TestCase):

    layer = C_STEP_INTAKE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def test_add_forms_do_not_use_tabs(self):
        for type_name in ('step_application', 'cstep_application'):
            fti = self.portal.portal_types[type_name]
            view = queryMultiAdapter(
                (self.portal, self.request, fti), name=type_name)
            self.assertFalse(view.form_instance.enable_form_tabbing, type_name)

    def test_edit_forms_do_not_use_tabs(self):
        for type_name in ('step_application', 'cstep_application'):
            obj = createContentInContainer(
                self.portal, type_name, checkConstraints=False)
            view = getMultiAdapter((obj, self.request), name='edit')
            self.assertFalse(view.enable_form_tabbing, type_name)
