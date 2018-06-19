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

from nti.contenttypes.credit.internalization import CreditDefinitionNormalizationUpdater

from nti.externalization.interfaces import IInternalObjectUpdater

from nti.app.contenttypes.credit.interfaces import IUserAwardedCredit

logger = __import__('logging').getLogger(__name__)


@component.adapter(IUserAwardedCredit)
@interface.implementer(IInternalObjectUpdater)
class _UserAwardedCreditUpdater(CreditDefinitionNormalizationUpdater):

    _ext_iface_upper_bound = IUserAwardedCredit
