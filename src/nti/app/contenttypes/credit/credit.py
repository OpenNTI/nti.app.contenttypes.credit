#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import interface

from nti.app.contenttypes.credit.interfaces import IUserAwardedCredit

from nti.contenttypes.credit.credit import AwardedCredit

from nti.externalization.representation import WithRepr

logger = __import__('logging').getLogger(__name__)


@WithRepr
@interface.implementer(IUserAwardedCredit)
class UserAwardedCredit(AwardedCredit):

    __external_can_create__ = True

    mimeType = mime_type = "application/vnd.nextthought.credit.userawardedcredit"
