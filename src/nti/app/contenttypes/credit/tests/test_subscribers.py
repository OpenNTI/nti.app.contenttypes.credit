#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# disable: accessing protected members, too many methods
# pylint: disable=W0212,R0904

from hamcrest import none
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import assert_that
does_not = is_not

from zope.site.folder import Folder

from zope.site.site import LocalSiteManager

from nti.app.contenttypes.credit.subscribers import on_site_created

from nti.app.contenttypes.credit.tests import CreditLayerTest

from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer


class TestSubscribers(CreditLayerTest):

    def test_credit_container(self):
        site = Folder()
        site.__name__ = u'Site'
        sm = LocalSiteManager(site)
        site.setSiteManager(sm)
        assert_that(sm.queryUtility(ICreditDefinitionContainer),
                    none())

        on_site_created(sm, object())
        assert_that(sm.queryUtility(ICreditDefinitionContainer),
                    not_none())
