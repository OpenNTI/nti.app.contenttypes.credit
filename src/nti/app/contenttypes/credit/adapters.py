#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from ZODB.interfaces import IConnection

from zope import component
from zope import interface

from zope.annotation import factory as an_factory

from nti.app.contenttypes.credit.interfaces import IUserAwardedCreditTranscript

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.coremetadata.interfaces import IUser

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

AWARDED_CREDIT_ANNOTATION_KEY = 'nti.app.contenttypes.credit.interfaces.IUserAwardedCreditTranscript'

logger = __import__('logging').getLogger(__name__)


@component.adapter(IUser)
@interface.implementer(IUserAwardedCreditTranscript)
class UserAwardedCreditTranscript(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                                  SchemaConfigured):
    """
    Stores :class:`IUserAwardedCredit`.
    """
    createDirectFieldProperties(IUserAwardedCreditTranscript)


_UserAwardedCreditTranscriptFactory = an_factory(UserAwardedCreditTranscript,
                                                AWARDED_CREDIT_ANNOTATION_KEY)


def _create_annotation(obj, factory):
    result = factory(obj)
    if IConnection(result, None) is None:
        try:
            # pylint: disable=too-many-function-args
            IConnection(obj).add(result)
        except (TypeError, AttributeError):  # pragma: no cover
            pass
    return result


def UserAwardedCreditTranscriptFactory(obj):
    return _create_annotation(obj, _UserAwardedCreditTranscriptFactory)