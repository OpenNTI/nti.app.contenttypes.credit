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

from zope.location.interfaces import ILocation

from nti.app.contenttypes.credit import USER_TRANSCRIPT_VIEW_NAME

from nti.app.contenttypes.credit.interfaces import IUserAwardedCredit

from nti.app.renderers.decorators import AbstractAuthenticatedRequestAwareDecorator

from nti.appserver.pyramid_renderers_edit_link_decorator import EditLinkDecorator

from nti.contenttypes.completion.interfaces import ICompletedItem

from nti.contenttypes.credit.interfaces import ICreditDefinition
from nti.contenttypes.credit.interfaces import ICreditTranscript

from nti.coremetadata.interfaces import IUser
from nti.coremetadata.interfaces import IDeletedObjectPlaceholder

from nti.dataserver.authorization import is_admin
from nti.dataserver.authorization import is_site_admin
from nti.dataserver.authorization import is_admin_or_site_admin
from nti.dataserver.authorization import is_admin_or_content_admin_or_site_admin

from nti.dataserver.interfaces import ISiteAdminUtility

from nti.externalization.interfaces import StandardExternalFields
from nti.externalization.interfaces import IExternalMappingDecorator

from nti.links.externalization import render_link

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
        if     not self._is_authenticated \
            or ICreditTranscript(user_context, None) is None:
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

        if is_admin_or_site_admin(self.remoteUser):
            # Admins can insert
            link = Link(context,
                        rel='add_credit',
                        method='PUT',
                        elements=('@@%s' % USER_TRANSCRIPT_VIEW_NAME,))
            _links.append(link)


@component.adapter(IUserAwardedCredit)
@interface.implementer(IExternalMappingDecorator)
class _UserAwardedCreditDecorator(EditLinkDecorator):
    """
    Decorates user awarded credit objects.
    """

    def _predicate(self, awarded_credit, unused_result):
        if not self._is_authenticated:
            return False
        user_context = IUser(awarded_credit)
        result = is_admin(self.remoteUser)
        if not result and is_site_admin(self.remoteUser):
            site_admin_utility = component.getUtility(ISiteAdminUtility)
            result = site_admin_utility.can_administer_user(self.remoteUser,
                                                            user_context)
        return result

    def _has_permission(self, unused_context):
        # Overriding parent class since we've validated access already
        return True

    def _get_edit_link(self, _links):
        for lnk in _links:
            if getattr(lnk, 'rel', None) == 'edit':
                return lnk

    def _do_decorate_external(self, context, result):
        super(_UserAwardedCreditDecorator, self)._do_decorate_external(context, result)
        _links = result.setdefault(LINKS, [])
        edit_link = self._get_edit_link(_links)
        if edit_link is not None:
            edit_ext = render_link(edit_link)
            delete_ext = dict(edit_ext)
            delete_ext['rel'] = 'delete'
            _links.append(delete_ext)


@component.adapter(ICreditDefinition)
@interface.implementer(IExternalMappingDecorator)
class _CreditDefinitionDecorator(AbstractAuthenticatedRequestAwareDecorator):
    """
    Decorates :class:`ICreditDefinition`.
    """

    def _do_decorate_external(self, context, result):
        result['deleted'] = IDeletedObjectPlaceholder.providedBy(context)


@component.adapter(ICreditDefinition)
@interface.implementer(IExternalMappingDecorator)
class _AdminCreditDefinitionLinkDecorator(AbstractAuthenticatedRequestAwareDecorator):
    """
    A decorator that provides admin course links.
    """

    def _predicate(self, unused_context, unused_result):
        return is_admin_or_content_admin_or_site_admin(self.remoteUser)

    def _do_decorate_external(self, context, result):
        _links = result.setdefault(LINKS, [])
        for rel in ('edit', 'delete'):
            link = Link(context, rel=rel)
            interface.alsoProvides(link, ILocation)
            link.__name__ = ''
            link.__parent__ = context
            _links.append(link)


@component.adapter(ICompletedItem)
@interface.implementer(IExternalMappingDecorator)
class _CompletedItemDecorator(AbstractAuthenticatedRequestAwareDecorator):
    """
    A decorator that provides awarded credits for a completed item, if
    applicable.
    """

    def _get_awarded_credits(self, completed_item):
        user = IUser(completed_item.Principal, None)
        item = completed_item.Item
        transcript = component.queryMultiAdapter((user, item),
                                                 ICreditTranscript)
        if transcript is not None:
            return tuple(transcript.iter_awarded_credits())

    def _do_decorate_external(self, context, result):
        awarded_credits = self._get_awarded_credits(context)
        if awarded_credits:
            result['awarded_credits'] = awarded_credits
