#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from datetime import datetime

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
from nti.app.contenttypes.credit import USER_TRANSCRIPT_VIEW_NAME
from nti.app.contenttypes.credit import CREDIT_DEFINITIONS_VIEW_NAME

from nti.app.contenttypes.credit.interfaces import IUserAwardedCredit
from nti.app.contenttypes.credit.interfaces import IUserAwardedCreditTranscript

from nti.app.externalization.error import raise_json_error

from nti.app.externalization.view_mixins import BatchingUtilsMixin
from nti.app.externalization.view_mixins import ModeledContentUploadRequestUtilsMixin

from nti.appserver.ugd_edit_views import UGDPutView
from nti.appserver.ugd_edit_views import UGDDeleteView

from nti.common.string import is_true

from nti.contenttypes.credit.interfaces import ICreditTranscript
from nti.contenttypes.credit.interfaces import ICreditDefinition
from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer

from nti.coremetadata.interfaces import IUser
from nti.coremetadata.interfaces import IDeletedObjectPlaceholder

from nti.dataserver.authorization import ACT_CONTENT_EDIT

from nti.dataserver.authorization import is_admin
from nti.dataserver.authorization import is_site_admin
from nti.dataserver.authorization import is_admin_or_content_admin_or_site_admin

from nti.dataserver.interfaces import ISiteAdminUtility
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
        return CaseInsensitiveDict(self.request.params)

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
    Allow creating a new credit definition to this pseudo-collection. If a
    duplicate definition exists, we raise a 409. If the duplicate is `deleted`,
    we restore it to a visible state.
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
        elif result != new_credit_definition:
            # Duplicate defs; raise a 409
            raise_error({'message': _(u"A credit definition of this type already exists."),
                         'code': 'DuplicateCreditDefinitionError'},
                        factory=hexc.HTTPConflict)
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


class UserAwardedCreditMixin(object):
    """
    A mixin that ensures only appropriate admins can grant credit.
    """

    @Lazy
    def user_context(self):
        return IUser(self.context)

    @Lazy
    def user_awarded_transcript(self):
        return IUserAwardedCreditTranscript(self.user_context)

    def check_access(self):
        result = is_admin(self.remoteUser)
        if not result and is_site_admin(self.remoteUser):
            site_admin_utility = component.getUtility(ISiteAdminUtility)
            result = site_admin_utility.can_administer_user(self.remoteUser,
                                                            self.user_context)
        if not result:
            raise hexc.HTTPForbidden(_('Must be an admin to award credit'))


class UserAwardedCreditFilterMixin(object):

    @Lazy
    def _params(self):
        return CaseInsensitiveDict(self.request.params)

    def _get_float_param(self, param_name):
        param_val = self._params.get(param_name)
        if param_val is None:
            return None
        try:
            result = float(param_val)
        except ValueError:
            raise_json_error(self.request,
                             hexc.HTTPUnprocessableEntity,
                             {
                                 'message': _(u'Invalid param.'),
                             },
                             None)
        return result

    def _get_date_param(self, param_name):
        result = self._get_float_param(param_name)
        if result is not None:
            return datetime.utcfromtimestamp(result)

    @Lazy
    def amount_filter(self):
        # Amount filter; defaults to zero.
        result = self._get_float_param('amount')
        if 'amount' not in self._params:
            result = 0
        return result

    @Lazy
    def definition_type_filter(self):
        return self._params.get('definitionType')

    @Lazy
    def definition_units_filter(self):
        return self._params.get('definitionUnits')

    @Lazy
    def not_before(self):
        return self._get_date_param("notBefore")

    @Lazy
    def not_after(self):
        return self._get_date_param("notAfter")

    def _include_item(self, awarded_credit):
        return  (  self.amount_filter is None \
                or self.amount_filter < awarded_credit.amount) \
            and (  self.definition_type_filter is None \
                or self.definition_type_filter == awarded_credit.credit_definition.credit_type) \
            and (  self.definition_units_filter is None \
                or self.definition_units_filter == awarded_credit.credit_definition.credit_units) \
            and (  self.not_before is None \
                or self.not_before < awarded_credit.awarded_date) \
            and (  self.not_after is None \
                or self.not_after > awarded_credit.awarded_date)

    def filter_credits(self, awarded_credits):
        return [x for x in awarded_credits if self._include_item(x)]

    @Lazy
    def sort_descending(self):
        sort_order = self._params.get('sortOrder')
        if sort_order:
            result = sort_order.lower() == 'descending'
        else:
            # Default to descending
            result = True
        return result

    @Lazy
    def sort_field(self):
        sort_on_field = self._params.get('sort') \
                     or self._params.get('sortOn')
        if not sort_on_field:
            sort_on_field = 'awarded_date'
        return sort_on_field

    def sort_key(self, awarded_credit):
        if self.sort_field == 'credit_definition':
            # Credit definition maps to the credit type
            return awarded_credit.credit_definition.credit_type
        return getattr(awarded_credit, self.sort_field, '')

    def sort_credits(self, awarded_credits):
        """
        Sort desc from most recently created.
        """
        return sorted(awarded_credits, key=self.sort_key, reverse=self.sort_descending)


@view_config(route_name='objects.generic.traversal',
             context=IUser,
             request_method='GET',
             name=USER_TRANSCRIPT_VIEW_NAME,
             renderer='rest')
class UserTranscriptView(AbstractAuthenticatedView,
                         UserAwardedCreditMixin,
                         UserAwardedCreditFilterMixin,
                         BatchingUtilsMixin):
    """
    Allow fetching a user's transcript.
    """

    _DEFAULT_BATCH_SIZE = None
    _DEFAULT_BATCH_START = 0

    def check_access(self):
        return self.remoteUser == self.context \
            or super(UserTranscriptView, self).check_access()

    def get_awarded_credits(self):
        user_transcript = ICreditTranscript(self.context, None)
        result = ()
        if user_transcript is not None:
            result = user_transcript.iter_awarded_credits()
        return result

    def __call__(self):
        self.check_access()
        awarded_credits = self.get_awarded_credits()
        included_credits = self.filter_credits(awarded_credits)
        included_credits = self.sort_credits(included_credits)

        result = LocatedExternalDict()
        result[ITEMS] = included_credits
        result[TOTAL] = len(awarded_credits)
        result[ITEM_COUNT] = len(included_credits)
        self._batch_items_iterable(result, included_credits)
        return result


@view_config(route_name='objects.generic.traversal',
             context=IUser,
             request_method='PUT',
             name=USER_TRANSCRIPT_VIEW_NAME,
             renderer='rest')
class UserAwardedCreditInsertView(AbstractAuthenticatedView,
                                  ModeledContentUploadRequestUtilsMixin,
                                  UserAwardedCreditMixin):
    """
    Allow creating a new credit definition to this pseudo-collection.
    """

    def _do_call(self):
        self.check_access()
        new_awarded_credit = self.readCreateUpdateContentObject(self.remoteUser)
        container = self.user_awarded_transcript
        container[new_awarded_credit.ntiid] = new_awarded_credit
        logger.info('Granted credit to user (%s) (remote_user=%s)',
                    self.user_context, self.remoteUser)
        return new_awarded_credit


@view_config(route_name='objects.generic.traversal',
             context=IUserAwardedCredit,
             request_method='PUT',
             renderer='rest')
class UserAwardedCreditPutView(UGDPutView,
                               UserAwardedCreditMixin):
    """
    Allow editing of a :class:`ICreditDefinition`.
    """

    def __call__(self):
        self.check_access()
        return super(UserAwardedCreditPutView, self).__call__()


@view_config(route_name='objects.generic.traversal',
             context=IUserAwardedCredit,
             request_method='DELETE',
             renderer='rest')
class UserAwardedCreditDeleteView(UGDDeleteView,
                                  UserAwardedCreditMixin):
    """
    Allow editing of a :class:`ICreditDefinition`.
    """

    def _do_delete_object(self, awarded_credit):
        try:
            del self.user_awarded_transcript[awarded_credit.ntiid]
        except KeyError:
            pass
        logger.info('Deleted credit granted to user (%s) (remote_user=%s)',
                    self.user_context, self.remoteUser)
        return awarded_credit

    def __call__(self):
        self.check_access()
        return super(UserAwardedCreditDeleteView, self).__call__()
