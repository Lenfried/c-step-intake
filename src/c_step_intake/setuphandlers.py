# -*- coding: utf-8 -*-
from Products.CMFPlone.interfaces import INonInstallable
from zope.interface import implementer


@implementer(INonInstallable)
class HiddenProfiles(object):

    def getNonInstallableProfiles(self):
        """Hide the uninstall profile from site creation and quickinstaller."""
        return ['c_step_intake:uninstall']


def post_install(context):
    """Post install script."""


def uninstall(context):
    """Uninstall script."""
