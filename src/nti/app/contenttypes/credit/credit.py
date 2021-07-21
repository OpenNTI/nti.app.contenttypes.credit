#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.component.hooks import getSite

from zope.cachedescriptors.property import Lazy

from nti.app.contenttypes.credit.interfaces import IUserAwardedCredit

from nti.appserver.interfaces import IPreferredAppHostnameProvider

from nti.contenttypes.credit.common import generate_awarded_credit_ntiid

from nti.contenttypes.credit.interfaces import IAwardedCredit

from nti.dublincore.time_mixins import PersistentCreatedAndModifiedTimeObject

from nti.externalization.representation import WithRepr

from nti.property.property import alias

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.wref.interfaces import IWeakRef

logger = __import__('logging').getLogger(__name__)


@WithRepr
@interface.implementer(IAwardedCredit)
class AwardedCredit(PersistentCreatedAndModifiedTimeObject,
                    SchemaConfigured):

    createDirectFieldProperties(IAwardedCredit)
    __external_can_create__ = False

    __name__ = None
    __parent__ = None
    _credit_definition = None
    creator = None
    NTIID = alias('ntiid')

    mimeType = mime_type = "application/vnd.nextthought.credit.awardedcredit"

    @property
    def credit_definition(self):
        result = None
        if self._credit_definition is not None:
            result = self._credit_definition()
        return result

    @credit_definition.setter
    def credit_definition(self, value):
        self._credit_definition = IWeakRef(value)

    @Lazy
    def ntiid(self):
        return generate_awarded_credit_ntiid()

    @Lazy
    def issuer(self):
        """
        Default to site name
        """
        result = None
        site = getSite()
        if site is not None:
            host_utility = component.queryUtility(IPreferredAppHostnameProvider)
            if host_utility:
                result = host_utility.get_preferred_hostname(result)
        return result

    @Lazy
    def awarded_date(self):
        return self.created
    

@WithRepr
@interface.implementer(IUserAwardedCredit)
class UserAwardedCredit(AwardedCredit):

    __external_can_create__ = True

    mimeType = mime_type = "application/vnd.nextthought.credit.userawardedcredit"
