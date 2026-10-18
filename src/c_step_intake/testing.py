# -*- coding: utf-8 -*-
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import applyProfile
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer

import c_step_intake


class CStepIntakeLayer(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        self.loadZCML(package=c_step_intake)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'c_step_intake:default')


C_STEP_INTAKE_FIXTURE = CStepIntakeLayer()

C_STEP_INTAKE_INTEGRATION_TESTING = IntegrationTesting(
    bases=(C_STEP_INTAKE_FIXTURE,),
    name='CStepIntakeLayer:IntegrationTesting',
)

C_STEP_INTAKE_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(C_STEP_INTAKE_FIXTURE,),
    name='CStepIntakeLayer:FunctionalTesting',
)
