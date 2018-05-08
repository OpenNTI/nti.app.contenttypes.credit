#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import six
import collections

from zope import component
from zope import interface

from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer

from nti.externalization.datastructures import InterfaceObjectIO

from nti.externalization.interfaces import IInternalObjectUpdater

from nti.app.contenttypes.credit.interfaces import IUserAwardedCredit

logger = __import__('logging').getLogger(__name__)


@component.adapter(IUserAwardedCredit)
@interface.implementer(IInternalObjectUpdater)
class _UserAwardedCreditUpdater(object):

    __slots__ = ('obj',)

    def __init__(self, obj):
        self.obj = obj

    def updateFromExternalObject(self, parsed, *unused_args, **unused_kwargs):
        """
        Normalize our credit definition.
        """
        credit_definition = parsed.get('credit_definition')
        if credit_definition is not None:
            if isinstance(credit_definition, six.string_types):
                credit_definition_ntiid = credit_definition
            elif isinstance(credit_definition, collections.Mapping):
                credit_definition_ntiid = credit_definition['ntiid']
            else:
                credit_definition_ntiid = getattr(credit_definition, 'ntiid', '')
            if credit_definition_ntiid:
                container = component.getUtility(ICreditDefinitionContainer)
                credit_definition_obj = container.get_credit_definition(credit_definition_ntiid)
                parsed['credit_definition'] = credit_definition_obj
        result = InterfaceObjectIO(self.obj,
                                   IUserAwardedCredit).updateFromExternalObject(parsed)
        return result
