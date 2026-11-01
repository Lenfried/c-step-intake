# -*- coding: utf-8 -*-
"""Form defaults come from the logged-in user's account, and are never junk."""
from unittest import mock

from plone.app.testing import logout
from plone.app.testing import setRoles
from plone.app.testing import TEST_USER_ID
from c_step_intake import defaults
from c_step_intake.behaviors.applicant_identity import IApplicantIdentity
from c_step_intake.content.cstep_application import ICstepApplication
from c_step_intake.testing import C_STEP_INTAKE_INTEGRATION_TESTING

import unittest

USER = 'c_step_intake.defaults.api.user.get_current'


class FakeUser(object):
    """An account carrying whatever properties a test gives it.

    The test site only has the standard properties (fullname, email);
    first_name, last_name and employeeID exist where SSO or LDAP fills them.
    """

    def __init__(self, **properties):
        self.properties = properties

    def getProperty(self, name, default=None):
        return self.properties.get(name, default)


def as_user(**properties):
    return mock.patch(USER, return_value=FakeUser(**properties))


ALL = {
    'first_name': 'Grace', 'last_name': 'Hopper',
    'email': 'grace@example.edu', 'employeeID': '12345678',
}
FUNCTIONS = (defaults.first_name, defaults.last_name,
             defaults.email, defaults.emplid)


class TestDefaults(unittest.TestCase):

    layer = C_STEP_INTAKE_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        setRoles(self.portal, TEST_USER_ID, ['Member'])

    def test_names_email_and_emplid_come_from_the_account(self):
        with as_user(**ALL):
            self.assertEqual('Grace', defaults.first_name())
            self.assertEqual('Hopper', defaults.last_name())
            self.assertEqual('grace@example.edu', defaults.email())
            self.assertEqual('12345678', defaults.emplid())

    def test_name_falls_back_to_the_full_name(self):
        with as_user(fullname='Ada King Lovelace'):
            self.assertEqual('Ada', defaults.first_name())
            self.assertEqual('King Lovelace', defaults.last_name())

    def test_missing_values_are_none_not_a_string(self):
        with as_user():
            for default in FUNCTIONS:
                self.assertIsNone(default())
        with as_user(first_name=None, email='', employeeID='  '):
            for default in FUNCTIONS:
                self.assertIsNone(default())

    def test_an_invalid_emplid_is_not_prefilled(self):
        for bad in ('1234567', '123456789', 'abcd1234'):
            with as_user(employeeID=bad):
                self.assertIsNone(defaults.emplid(), bad)

    def test_the_real_test_user_works_with_standard_properties(self):
        # No mocking: the site's own account, which has no custom properties.
        for default in FUNCTIONS:
            default()

    def test_anonymous_visitors_get_blanks(self):
        logout()
        for default in FUNCTIONS:
            self.assertIsNone(default())

    def test_the_form_fields_use_these_defaults(self):
        with as_user(**ALL):
            identity = IApplicantIdentity
            self.assertEqual('Grace', identity['first_name'].bind(None).default)
            self.assertEqual('Hopper', identity['last_name'].bind(None).default)
            self.assertEqual('grace@example.edu',
                             identity['student_email'].bind(None).default)
            self.assertEqual('12345678',
                             ICstepApplication['emplid'].bind(None).default)

    def test_a_blank_email_default_does_not_break_the_form(self):
        # The Email field rejects '' as an invalid address, so a missing value
        # must come back as None. This is what opening the form does.
        with as_user():
            self.assertIsNone(
                IApplicantIdentity['student_email'].bind(None).default)
