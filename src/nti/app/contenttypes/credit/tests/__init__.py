#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from persistent import Persistent

from zope.component.persistentregistry import PersistentComponents as Components

import zope.testing.cleanup

from zope import component

from nti.app.testing.application_webtest import ApplicationLayerTest

from nti.dataserver.tests.mock_dataserver import DSInjectorMixin

from nti.testing.base import AbstractTestBase

from nti.testing.layers import GCLayerMixin
from nti.testing.layers import ZopeComponentLayer
from nti.testing.layers import ConfiguringLayerMixin

from nti.contenttypes.credit.credit import CreditDefinitionContainer

from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.tests.mock_dataserver import WithMockDS


class SharedConfiguringTestLayer(ZopeComponentLayer,
                                 GCLayerMixin,
                                 ConfiguringLayerMixin,
                                 DSInjectorMixin):

    set_up_packages = ('nti.app.contenttypes.credit',)

    @classmethod
    def setUp(cls):
        cls.setUpPackages()

    @classmethod
    def tearDown(cls):
        cls.tearDownPackages()
        zope.testing.cleanup.cleanUp()

    @classmethod
    def testSetUp(cls):
        pass

    @classmethod
    def testTearDown(cls):
        pass


class CreditLayerTest(ApplicationLayerTest):

    get_configuration_package = AbstractTestBase.get_configuration_package.__func__

    set_up_packages = ('nti.app.contenttypes.credit',)

    def install_credit_definition_container(self):
        """
        Installs a credit definition container globally. This needs to be done
        in a transaction since it will be persisted once a definition is added.
        """
        with mock_dataserver.mock_db_trans(self.ds):
            self.container = CreditDefinitionContainer()
            con = mock_dataserver.current_transaction
            con.add(self.container)
            component.getGlobalSiteManager().registerUtility(self.container,
                                                             ICreditDefinitionContainer)
        return self.container

    def uninstall_credit_definition_container(self):
        with mock_dataserver.mock_db_trans(self.ds):
            component.getGlobalSiteManager().unregisterUtility(self.container,
                                                               ICreditDefinitionContainer)
