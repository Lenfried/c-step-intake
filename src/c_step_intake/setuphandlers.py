# -*- coding: utf-8 -*-
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
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


def upgrade_webhook_registry(context):
    """Import webhook configuration while preserving the notification address."""
    registry = getUtility(IRegistry)
    key = 'c_step_intake.notification_email'
    existed = key in registry
    value = registry[key] if existed else None
    try:
        context.runImportStepFromProfile(
            'profile-c_step_intake:default', 'plone.app.registry')
    finally:
        if existed:
            registry[key] = value
