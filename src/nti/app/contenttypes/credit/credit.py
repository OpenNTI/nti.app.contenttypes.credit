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

from nti.app.contenttypes.credit.interfaces import IUserAwardedCredit

from nti.contenttypes.credit.credit import AwardedCredit

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.coremetadata.interfaces import IUser

from nti.externalization.representation import WithRepr

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)


@WithRepr
@interface.implementer(IUserAwardedCredit)
class UserAwardedCredit(AwardedCredit):

    __external_can_create__ = True

    mimeType = mime_type = "application/vnd.nextthought.credit.userawardedcredit"
