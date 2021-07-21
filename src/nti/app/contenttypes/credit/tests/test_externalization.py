#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods,arguments-differ

from hamcrest import is_
from hamcrest import none
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_property
from hamcrest import same_instance

import fudge
import unittest

from datetime import datetime
from datetime import timedelta

from zope import component

from zc.intid import IIntIds

from nti.app.contenttypes.credit.credit import AwardedCredit

from nti.contenttypes.credit.credit import CreditDefinition
from nti.contenttypes.credit.credit import CreditDefinitionContainer

from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer

from nti.contenttypes.credit.tests import SharedConfiguringTestLayer

from nti.externalization.externalization import to_external_object

from nti.externalization.interfaces import StandardExternalFields

from nti.externalization.internalization import find_factory_for

from nti.intid.common import add_intid

CLASS = StandardExternalFields.CLASS
MIMETYPE = StandardExternalFields.MIMETYPE
CREATED_TIME = StandardExternalFields.CREATED_TIME
LAST_MODIFIED = StandardExternalFields.LAST_MODIFIED


class TestExternalization(unittest.TestCase):

    layer = SharedConfiguringTestLayer

    def setUp(self):
        self.container = CreditDefinitionContainer()
        component.getGlobalSiteManager().registerUtility(self.container,
                                                         ICreditDefinitionContainer)

    def tearDown(self):
        component.getGlobalSiteManager().unregisterUtility(self.container,
                                                           ICreditDefinitionContainer)

    def test_awarded_credit(self):
        credit_definition = CreditDefinition(credit_type=u'Credit',
                                             credit_units=u'Hours')
        intids = fudge.Fake().provides('getObject').returns(credit_definition)
        intids.provides('getId').returns(10)
        component.getGlobalSiteManager().registerUtility(intids, IIntIds)
        add_intid(credit_definition)
        yesterday = datetime.utcnow() - timedelta(days=1)
        awarded_credit = AwardedCredit(title=u'Credit conference',
                                       description=u'desc',
                                       amount=42,
                                       credit_definition=credit_definition,
                                       issuer=u'my issuer',
                                       awarded_date=yesterday)

        ext_obj = to_external_object(awarded_credit)
        assert_that(ext_obj[CLASS], is_('AwardedCredit'))
        assert_that(ext_obj[MIMETYPE],
                    is_(AwardedCredit.mime_type))
        assert_that(ext_obj[CREATED_TIME], not_none())
        assert_that(ext_obj[LAST_MODIFIED], not_none())
        assert_that(ext_obj['amount'], is_(42))
        assert_that(ext_obj['title'], is_(u'Credit conference'))
        assert_that(ext_obj['description'], is_(u'desc'))
        assert_that(ext_obj['issuer'], is_(u'my issuer'))
        assert_that(ext_obj['awarded_date'], not_none())
        assert_that(ext_obj['credit_definition']['credit_type'], is_(u'Credit'))
        assert_that(ext_obj['credit_definition']['credit_units'], is_(u'Hours'))

        factory = find_factory_for(ext_obj)
        assert_that(factory, none())
        