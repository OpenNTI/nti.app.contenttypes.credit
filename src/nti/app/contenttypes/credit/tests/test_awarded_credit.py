#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

from hamcrest import is_
from hamcrest import is_not
from hamcrest import contains
from hamcrest import not_none
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
does_not = is_not

from zope import component

from nti.app.contenttypes.credit import USER_TRANSCRIPT_VIEW_NAME
from nti.app.contenttypes.credit import CREDIT_DEFINITIONS_VIEW_NAME

from nti.app.contenttypes.credit.credit import UserAwardedCredit

from nti.app.contenttypes.credit.tests import CreditLayerTest

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.contenttypes.credit.credit import CreditDefinition
from nti.contenttypes.credit.credit import CreditDefinitionContainer

from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer

from nti.dataserver.tests import mock_dataserver


class TestAwardedCredit(CreditLayerTest):
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

    def _create_credit_def(self):
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

        credit_def = {'MimeType': CreditDefinition.mime_type,
                      'credit_type': 'new_types',
                      'credit_units': 'new_units'}

        res = self.testapp.put_json(credit_def_url, credit_def)
        return res.json_body

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_awarding_credit(self):
        """
        Test awarded credit to a user and editing.
        """
        non_admin_username = 'non_admin'
        with mock_dataserver.mock_db_trans(self.ds):
            self._create_user(non_admin_username)

        resolve_href = '/dataserver2/ResolveUser/%s?filter_by_site_community=False' % non_admin_username
        user_ext = self.testapp.get(resolve_href).json_body
        user_ext = user_ext['Items'][0]
        user_transcript_url = self.require_link_href_with_rel(user_ext,
                                                              USER_TRANSCRIPT_VIEW_NAME)

        # Get transcript
        user_credits = self.testapp.get(user_transcript_url).json_body
        assert_that(user_credits, has_entries('Total', is_(0),
                                              'Items', has_length(0),
                                              'ItemCount', is_(0)))

        credit_definition_obj = self._create_credit_def()
        credit_definition_ntiid = credit_definition_obj['NTIID']
        title = u'awarded credit title'
        desc = u'awarded credit desc'
        amount = 3
        awarded_def = {'MimeType': UserAwardedCredit.mime_type,
                       'title': title,
                       'description': desc,
                       'credit_definition': credit_definition_obj,
                       'amount': amount}

        # Award credit to user
        res = self.testapp.put_json(user_transcript_url, awarded_def)
        res = res.json_body
        awarded_credit_ntiid1 = res.get('NTIID')
        assert_that(res, has_entries('title', is_(title),
                                     'description', is_(desc),
                                     'credit_definition', has_entry('NTIID', credit_definition_ntiid),
                                     'amount', is_(amount),
                                     'NTIID', not_none()))
        self.require_link_href_with_rel(res, 'edit')
        self.require_link_href_with_rel(res, 'delete')

        user_credits = self.testapp.get(user_transcript_url).json_body
        assert_that(user_credits, has_entries('Total', is_(1),
                                              'Items', has_length(1),
                                              'ItemCount', is_(1)))

        # Credit definition normalization #1
        awarded_def['credit_definition'] = {'ntiid': credit_definition_ntiid}
        res = self.testapp.put_json(user_transcript_url, awarded_def)
        res = res.json_body
        awarded_credit_ntiid2 = res.get('NTIID')
        assert_that(res, has_entries('title', is_(title),
                                     'description', is_(desc),
                                     'credit_definition', has_entry('NTIID', credit_definition_ntiid),
                                     'amount', is_(amount),
                                     'NTIID', not_none()))

        # Credit definition normalization #2
        awarded_def['credit_definition'] = credit_definition_ntiid
        res = self.testapp.put_json(user_transcript_url, awarded_def)
        res = res.json_body
        awarded_credit_ntiid3 = res.get('NTIID')
        awarded_credit_href = res.get('href')
        assert_that(awarded_credit_href, not_none())
        assert_that(res, has_entries('title', is_(title),
                                     'description', is_(desc),
                                     'credit_definition', has_entry('NTIID', credit_definition_ntiid),
                                     'amount', is_(amount),
                                     'NTIID', not_none()))

        # Edits
        res = self.testapp.put_json(awarded_credit_href, {'amount': 10,
                                                          'title': 'new_title_1000'})
        res = res.json_body
        assert_that(res, has_entries('title', is_('new_title_1000'),
                                     'description', is_(desc),
                                     'credit_definition', has_entry('NTIID', credit_definition_ntiid),
                                     'amount', is_(10),
                                     'NTIID', not_none()))

        # Get with filters and batching
        user_credits = self.testapp.get(user_transcript_url).json_body
        assert_that(user_credits, has_entries('Total', is_(3),
                                              'Items', has_length(3),
                                              'ItemCount', is_(3)))

        user_credits = self.testapp.get('%s?batchSize=1' % user_transcript_url).json_body
        assert_that(user_credits, has_entries('Total', is_(3),
                                              'Items', has_length(1),
                                              'ItemCount', is_(1)))
        assert_that(user_credits['Items'][0],
                    has_entry('NTIID', is_(awarded_credit_ntiid3)))

        user_credits = self.testapp.get('%s?definitionType=%s&definitionUnits=%s' % (user_transcript_url, 'new_types', 'new_units'))
        user_credits = user_credits.json_body
        assert_that(user_credits, has_entries('Total', is_(3),
                                              'Items', has_length(3),
                                              'ItemCount', is_(3)))
        assert_that([x['NTIID'] for x in user_credits['Items']],
                    contains(awarded_credit_ntiid3, awarded_credit_ntiid2, awarded_credit_ntiid1))

        # Delete
        self.testapp.get(awarded_credit_href)
        self.testapp.delete(awarded_credit_href)
        self.testapp.get(awarded_credit_href, status=404)

        # FIXME test permissions
