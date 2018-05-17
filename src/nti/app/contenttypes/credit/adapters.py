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

from zope.annotation.interfaces import IAnnotations

from nti.app.contenttypes.credit.interfaces import IUserAwardedCredit
from nti.app.contenttypes.credit.interfaces import IUserAwardedCreditTranscript

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.contenttypes.credit.interfaces import ICreditTranscript

from nti.coremetadata.interfaces import IUser

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

from nti.traversal.traversal import find_interface

AWARDED_CREDIT_ANNOTATION_KEY = 'nti.app.contenttypes.credit.interfaces.IUserAwardedCreditTranscript'

logger = __import__('logging').getLogger(__name__)


@component.adapter(IUser)
@interface.implementer(ICreditTranscript)
def empty_user_credit_transcript(unused_user):
    """
    An empty :class:`ICreditTranscript` a site can use to disable credit
    features.
    """
    return None


@component.adapter(IUser)
@interface.implementer(ICreditTranscript)
class UserCreditTranscript(object):
    """
    A :class:`ICreditTranscript` that fetchs all awarded credit subscribers.
    """

    def __init__(self, user):
        self.context = user

    def iter_awarded_credits(self):
        awarded_credits = []
        transcripts = component.subscribers((self.context,), ICreditTranscript)
        for transcript in transcripts:
            awarded_credits.extend(transcript.iter_awarded_credits())
        return awarded_credits


@component.adapter(IUser)
@interface.implementer(IUserAwardedCreditTranscript)
class UserAwardedCreditTranscript(CaseInsensitiveCheckingLastModifiedBTreeContainer,
                                  SchemaConfigured):
    """
    Stores :class:`IAwardedCredit`.
    """
    createDirectFieldProperties(IUserAwardedCreditTranscript)

    def iter_awarded_credits(self):
        return iter(self.values())


def UserAwardedCreditTranscriptFactory(user):
    result = None
    annotations = IAnnotations(user)
    KEY = AWARDED_CREDIT_ANNOTATION_KEY
    try:
        result = annotations[KEY]
    except KeyError:
        result = UserAwardedCreditTranscript()
        annotations[KEY] = result
        result.__name__ = KEY
        result.__parent__ = user
        IConnection(user).add(result)
    return result


@component.adapter(IUserAwardedCredit)
@interface.implementer(IUser)
def awarded_credit_to_user(awarded_credit):
    return find_interface(awarded_credit, IUser)
