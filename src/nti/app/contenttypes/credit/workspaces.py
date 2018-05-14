#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Service document and user workspaces support.

.. $Id: catalog.py 124952 2017-12-16 21:19:52Z josh.zuech $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component
from zope import interface

from zope.container.contained import Contained

from nti.app.authentication import get_remote_user

from nti.app.contenttypes.credit import CREDIT_DEFINITIONS_VIEW_NAME

from nti.appserver.workspaces.interfaces import IWorkspace
from nti.appserver.workspaces.interfaces import IGlobalCollection

from nti.contenttypes.credit.credit import CreditDefinition

from nti.externalization.interfaces import StandardExternalFields

from nti.property.property import alias
from nti.dataserver.authorization import is_admin_or_content_admin_or_site_admin

logger = __import__('logging').getLogger(__name__)

ITEMS = StandardExternalFields.ITEMS


@component.adapter(IWorkspace)
@interface.implementer(IGlobalCollection)
class CreditDefinitionCollectionFactory(Contained):
    """
    Return our credit definition collection.
    """

    name = CREDIT_DEFINITIONS_VIEW_NAME
    __name__ = name
    _workspace = alias('__parent__')

    links = ()

    def __init__(self, workspace):
        # DS folder
        self.__parent__ = workspace.__parent__

    @property
    def container(self):
        return ()

    @property
    def accepts(self):
        # Only admins can insert new definitions.
        result = ()
        user = get_remote_user()
        if is_admin_or_content_admin_or_site_admin(user):
            result = (CreditDefinition.mime_type,)
        return result
