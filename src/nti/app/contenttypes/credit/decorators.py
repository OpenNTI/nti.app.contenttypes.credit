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

from nti.app.contenttypes.credit import USER_TRANSCRIPT_VIEW_NAME

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.contenttypes.credit.interfaces import ICreditDefinition

from nti.coremetadata.interfaces import IUser, IDeletedObjectPlaceholder

from nti.dataserver.authorization import is_admin
from nti.dataserver.authorization import is_site_admin

from nti.dataserver.interfaces import ISiteAdminUtility

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.links.links import Link

LINKS = StandardExternalFields.LINKS

logger = __import__('logging').getLogger(__name__)


@component.adapter(IUser)
@interface.implementer(IExternalMappingDecorator)
class _UserTranscriptDecorator(AbstractAuthenticatedRequestAwareDecorator):
    """
    Decorates a user with transcript link.
    """

    def _predicate(self, user_context, unused_result):
        if not self._is_authenticated:
            return False
        result = is_admin(self.remoteUser) or self.remoteUser == user_context
        if not result and is_site_admin(self.remoteUser):
            site_admin_utility = component.getUtility(ISiteAdminUtility)
            result = site_admin_utility.can_administer_user(self.remoteUser,
                                                            user_context)
        return result

    def _do_decorate_external(self, context, result):
        _links = result.setdefault(LINKS, [])
        link = Link(context,
                    rel=USER_TRANSCRIPT_VIEW_NAME,
                    elements=('@@%s' % USER_TRANSCRIPT_VIEW_NAME,))
        _links.append(link)


@component.adapter(ICreditDefinition)
@interface.implementer(IExternalMappingDecorator)
class _CreditDefinitionDecorator(AbstractAuthenticatedRequestAwareDecorator):
    """
    Decorates :class:`ICreditDefinition`.
    """

    def _do_decorate_external(self, context, result):
        result['deleted'] = IDeletedObjectPlaceholder.providedBy(context)
