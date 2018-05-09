#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import is_not
from hamcrest import not_none
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
does_not = is_not

from zope import component

from nti.app.contenttypes.credit import CREDIT_DEFINITIONS_VIEW_NAME

from nti.app.contenttypes.credit.tests import CreditLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.contenttypes.credit.credit import CreditDefinition
from nti.contenttypes.credit.credit import CreditDefinitionContainer

from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer


class TestCreditDefinitions(CreditLayerTest):
    """
    Test the global workspace credit definition collection.
    """

    admin_user = u"sjohnson@nextthought.com"

    def setUp(self):
        self.container = CreditDefinitionContainer()
        component.getGlobalSiteManager().registerUtility(self.container,
                                                         ICreditDefinitionContainer)

    def tearDown(self):
        component.getGlobalSiteManager().unregisterUtility(self.container,
                                                           ICreditDefinitionContainer)

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_workspace(self):
        """
        Test the global workspace has a CreditDefinition collection.
        """

        service_url = '/dataserver2/service/'

        def _get_credit_collection(environ=None):
            service_res = self.testapp.get(service_url,
                                           extra_environ=environ)
            service_res = service_res.json_body
            workspaces = service_res['Items']
            global_ws = report_collection = None
            try:
                global_ws = next(x for x in workspaces if x['Title'] == 'Global')
            except StopIteration:
                pass
            assert_that(global_ws, not_none())
            try:
                report_collection = next(x for x in global_ws['Items']
                                         if x['Title'] == CREDIT_DEFINITIONS_VIEW_NAME)
            except StopIteration:
                pass
            assert_that(report_collection, not_none())
            return report_collection

        credit_collection = _get_credit_collection()
        credit_def_url = credit_collection['href']
        credit_res = self.testapp.get(credit_def_url)
        credit_res = credit_res.json_body
        credit_items = credit_res.get('Items')
        assert_that(credit_items, has_length(0))

        credit_def = {'MimeType': CreditDefinition.mime_type,
                      'credit_type': 'new_types',
                      'credit_units': 'new_units'}

        res = self.testapp.put_json(credit_def_url, credit_def)
        res = res.json_body
        original_ntiid = res['NTIID']
        def_href = res.get('href')
        assert_that(def_href, not_none())
        assert_that(res, has_entries('credit_units', is_('new_units'),
                                     'credit_type', is_('new_types'),
                                     'NTIID', not_none()))
        self.require_link_href_with_rel(res, 'edit')
        self.require_link_href_with_rel(res, 'delete')

        # De-duped if inserting same
        res = self.testapp.put_json(credit_def_url, credit_def)
        res = res.json_body
        assert_that(res, has_entries('credit_units', is_('new_units'),
                                     'credit_type', is_('new_types'),
                                     'deleted', is_(False),
                                     'NTIID', is_(original_ntiid)))

        # Edit
        new_units = 'new_new_units'
        new_type = 'new_new_type'
        res = self.testapp.put_json(def_href,
                                    {'credit_type': new_type,
                                     'credit_units': new_units})
        res = res.json_body
        assert_that(res['credit_type'], is_(new_type))
        assert_that(res['credit_units'], is_(new_units))

        # Get
        credit_res = self.testapp.get(credit_def_url)
        credit_res = credit_res.json_body
        credit_items = credit_res.get('Items')
        assert_that(credit_items, has_length(1))

        # Delete
        self.testapp.delete(def_href)

        credit_res = self.testapp.get(credit_def_url)
        credit_res = credit_res.json_body
        credit_items = credit_res.get('Items')
        assert_that(credit_items, has_length(0))

        # Fetch deleted too
        credit_res = self.testapp.get('%s?hide_deleted=False' % credit_def_url)
        credit_res = credit_res.json_body
        credit_items = credit_res.get('Items')
        assert_that(credit_items, has_length(1))
        assert_that(credit_items[0], has_entries('credit_units', is_(new_units),
                                                 'credit_type', is_(new_type),
                                                 'deleted', is_(True),
                                                 'NTIID', is_(original_ntiid)))

        # Recreate by posting some object to def container
        self.testapp.put_json(credit_def_url,
                              {'MimeType': CreditDefinition.mime_type,
                               'credit_type': new_type,
                               'credit_units': new_units})

        credit_res = self.testapp.get(credit_def_url)
        credit_res = credit_res.json_body
        credit_items = credit_res.get('Items')
        assert_that(credit_items, has_length(1))
        def_item = credit_items[0]
        assert_that(def_item['NTIID'], is_(original_ntiid))
        assert_that(def_item['deleted'], is_(False))
