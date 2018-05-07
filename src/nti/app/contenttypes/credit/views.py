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

from pyramid.view import view_config

from requests.structures import CaseInsensitiveDict

from zope import component
from zope import interface

from zope.cachedescriptors.property import Lazy

from zope.container.contained import Contained

from zope.traversing.interfaces import IPathAdapter

from nti.app.base.abstract_views import AbstractAuthenticatedView

from nti.app.contenttypes.credit import MessageFactory as _

from nti.app.contenttypes.credit import CREDIT_PATH_NAME
from nti.app.contenttypes.credit import CREDIT_DEFINITIONS_VIEW_NAME

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.appserver.ugd_edit_views import UGDPutView
from nti.appserver.ugd_edit_views import UGDDeleteView

from nti.common.string import is_true

from nti.contenttypes.credit.interfaces import ICreditDefinition
from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer

from nti.coremetadata.interfaces import IDeletedObjectPlaceholder

from nti.dataserver.authorization import ACT_CONTENT_EDIT

from nti.dataserver.authorization import is_admin_or_content_admin_or_site_admin

from nti.dataserver.interfaces import IDataserverFolder

from nti.externalization.interfaces import LocatedExternalDict
from nti.externalization.interfaces import StandardExternalFields

ITEMS = StandardExternalFields.ITEMS
TOTAL = StandardExternalFields.TOTAL
ITEM_COUNT = StandardExternalFields.ITEM_COUNT

logger = __import__('logging').getLogger(__name__)


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


@view_config(route_name='objects.generic.traversal',
             renderer='rest',
             name=CREDIT_DEFINITIONS_VIEW_NAME,
             request_method='GET',
             context=IDataserverFolder)
class CreditDefinitionView(AbstractAuthenticatedView):
    """
    A view/collection to fetch all credit definition objects.
    """

    @Lazy
    def _params(self):
        result = {}
        request = get_current_request()
        if request is not None:
            values = request.params
            result = CaseInsensitiveDict(values)
        return result

    @Lazy
    def hide_deleted(self):
        """
        By default, hide all deleted credit definitions.
        """
        result = True
        param = self._params.get('hide_deleted')
        if param is not None:
            result = is_true(param)
        return result

    @Lazy
    def credit_definitions(self):
        """
        Return externalized reports for the :class:`IDataserverFolder`.
        """
        result = []
        credit_definition_utility = component.queryUtility(ICreditDefinitionContainer)
        if credit_definition_utility is not None:
            for credit_definition in credit_definition_utility.values():
                if      self.hide_deleted \
                    and IDeletedObjectPlaceholder.providedBy(credit_definition):
                    continue
                result.append(credit_definition)
        return result

    def __call__(self):
        result = LocatedExternalDict()
        result[ITEMS] = items = self.credit_definitions
        result[ITEM_COUNT] = result[TOTAL] = len(items)
        return result


@view_config(route_name='objects.generic.traversal',
             context=IDataserverFolder,
             request_method='PUT',
             name=CREDIT_DEFINITIONS_VIEW_NAME,
             renderer='rest')
class CreditDefinitionInsertView(AbstractAuthenticatedView,
                                 ModeledContentUploadRequestUtilsMixin):
    """
    Allow creating a new credit definition to this pseudo-collection.
    """

    def check_access(self):
        if not is_admin_or_content_admin_or_site_admin(self.remoteUser):
            raise hexc.HTTPForbidden(_('Must be an admin'))

    def _do_call(self):
        self.check_access()
        definition_container = component.queryUtility(ICreditDefinitionContainer)
        if definition_container is None:
            logger.warn('Credit definition container not setup for site')
            raise_error({'message': _(u"Credit definition container not setup for site"),
                         'code': 'InvalidSiteCreditDefinitionContainerError'})
        new_credit_definition = self.readCreateUpdateContentObject(self.remoteUser)
        result = definition_container.add_credit_definition(new_credit_definition)
        if IDeletedObjectPlaceholder.providedBy(result):
            # If we normalize to an existing, deleted object, restore it.
            logger.info('Restoring credit definition (%s)', result)
            interface.noLongerProvides(result, IDeletedObjectPlaceholder)
        else:
            logger.info('Created credit definition (%s)', result)
        return result


@view_config(route_name='objects.generic.traversal',
             context=ICreditDefinition,
             request_method='PUT',
             permission=ACT_CONTENT_EDIT,
             renderer='rest')
class CreditDefinitionPutView(UGDPutView):
    """
    Allow editing of a :class:`ICreditDefinition`.
    """

@view_config(route_name='objects.generic.traversal',
             context=ICreditDefinition,
             request_method='DELETE',
             permission=ACT_CONTENT_EDIT,
             renderer='rest')
class CreditDefinitionDeleteView(UGDDeleteView):
    """
    Allow editing of a :class:`ICreditDefinition`.
    """

    def _do_delete_object(self, theObject):
        if not IDeletedObjectPlaceholder.providedBy(theObject):
            interface.alsoProvides(theObject, IDeletedObjectPlaceholder)
        return theObject
