#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from pyramid import httpexceptions as hexc

from pyramid.threadlocal import get_current_request

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.container.contained import Contained

from zope.location.interfaces import LocationError

from zope.traversing.interfaces import IPathAdapter
from zope.traversing.interfaces import ITraversable

from nti.app.contenttypes.credit import MessageFactory as _

from nti.app.contenttypes.credit import CREDIT_PATH_NAME

from nti.app.externalization.error import raise_json_error

from nti.dataserver.authorization import ROLE_ADMIN

from nti.dataserver.authorization_acl import ace_allowing
from nti.dataserver.authorization_acl import acl_from_aces
from nti.dataserver.authorization_acl import ace_denying_all

from nti.dataserver.interfaces import ALL_PERMISSIONS

from nti.dataserver.interfaces import IUser

from nti.dataserver.users import User

from nti.links.links import Link

from nti.traversal.traversal import find_interface


def raise_error(data, tb=None,
                factory=hexc.HTTPUnprocessableEntity,
                request=None):
    request = request or get_current_request()
    raise_json_error(request, factory, data, tb)


@interface.implementer(IPathAdapter)
class CreditPathAdapter(Contained):

    __name__ = CREDIT_PATH_NAME

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.__parent__ = context
