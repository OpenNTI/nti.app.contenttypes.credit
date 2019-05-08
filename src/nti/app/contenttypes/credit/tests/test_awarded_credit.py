#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=protected-access,too-many-public-methods

import os
import fudge

from hamcrest import is_
from hamcrest import is_not
from hamcrest import calling
from hamcrest import raises
from hamcrest import contains
from hamcrest import not_none
from hamcrest import has_items
from hamcrest import has_entry
from hamcrest import has_length
from hamcrest import assert_that
from hamcrest import has_entries
from hamcrest import has_properties
from hamcrest import contains_inanyorder
does_not = is_not

from zope import component
from zope import interface

from zope.component.hooks import getSite

from zope.securitypolicy.interfaces import IPrincipalRoleManager

from nti.app.contenttypes.credit import USER_TRANSCRIPT_VIEW_NAME
from nti.app.contenttypes.credit import CREDIT_PATH_NAME
from nti.app.contenttypes.credit import CREDIT_DEFINITIONS_VIEW_NAME

from nti.app.contenttypes.credit.credit import UserAwardedCredit

from nti.app.contenttypes.credit.interfaces import IUserAwardedCreditTranscript

from nti.app.contenttypes.credit.tests import CreditLayerTest

from nti.app.contenttypes.credit.views import UserAwardedCreditBulkCreationView

from nti.app.testing.decorators import WithSharedApplicationMockDS

from nti.base._compat import text_

from nti.coremetadata.interfaces import IDeletedObjectPlaceholder

from nti.contenttypes.credit.credit import CreditDefinition
from nti.contenttypes.credit.credit import CreditDefinitionContainer

from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer

from nti.dataserver.authorization import ROLE_SITE_ADMIN

from nti.dataserver.tests import mock_dataserver

from nti.dataserver.users import User

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

        user_environ = self._make_extra_environ(user=non_admin_username)

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

        user_credits = self.testapp.get(user_transcript_url, extra_environ=user_environ).json_body
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
                       'credit_definition': credit_definition_obj['NTIID'],
                       'awarded_date': "2013-08-13T06:00:00+00:00",
                       'amount': amount}

        # Award credit to user
        self.testapp.put_json(user_transcript_url, awarded_def,
                              extra_environ=user_environ, status=403)
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
        awarded_def['awarded_date'] = "2013-08-14T06:00:00+00:00"
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
        awarded_def['awarded_date'] = "2013-08-15T06:00:00+00:00"
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

        # Cannot award zero amount credits get filtered out
        awarded_def['awarded_date'] = "2013-08-16T06:00:00+00:00"
        awarded_def['amount'] = 0
        self.testapp.put_json(user_transcript_url, awarded_def, status=422)

        # Edits
        self.testapp.put_json(awarded_credit_href,
                              {'amount': 10,
                               'title': 'new_title_1000'},
                              extra_environ=user_environ, status=403)
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

        user_credits = self.testapp.get('%s?definitionType=%s&definitionType=%s' % (user_transcript_url, 'new_types', 'new_types_dne'))
        user_credits = user_credits.json_body
        assert_that(user_credits, has_entries('Total', is_(3),
                                              'Items', has_length(3),
                                              'ItemCount', is_(3)))
        assert_that([x['NTIID'] for x in user_credits['Items']],
                    contains(awarded_credit_ntiid3, awarded_credit_ntiid2, awarded_credit_ntiid1))

        # Sorting
        user_credits = self.testapp.get('%s?sortOn=awarded_date&sortOrder=ASCENDING' % user_transcript_url)
        user_credits = user_credits.json_body
        assert_that(user_credits, has_entries('Total', is_(3),
                                              'Items', has_length(3),
                                              'ItemCount', is_(3)))
        assert_that([x['NTIID'] for x in user_credits['Items']],
                    contains(awarded_credit_ntiid1, awarded_credit_ntiid2, awarded_credit_ntiid3))

        user_credits = self.testapp.get('%s?sortOn=awarded_date&sortOrder=DESCENDING' % user_transcript_url)
        user_credits = user_credits.json_body
        assert_that(user_credits, has_entries('Total', is_(3),
                                              'Items', has_length(3),
                                              'ItemCount', is_(3)))
        assert_that([x['NTIID'] for x in user_credits['Items']],
                    contains(awarded_credit_ntiid3, awarded_credit_ntiid2, awarded_credit_ntiid1))

        user_credits = self.testapp.get('%s?sortOn=credit_definition&sortOrder=ASCENDING' % user_transcript_url)
        user_credits = user_credits.json_body
        assert_that(user_credits, has_entries('Total', is_(3),
                                              'Items', has_length(3),
                                              'ItemCount', is_(3)))
        assert_that([x['NTIID'] for x in user_credits['Items']],
                    contains_inanyorder(awarded_credit_ntiid1, awarded_credit_ntiid2, awarded_credit_ntiid3))

        # Delete
        self.testapp.delete(awarded_credit_href, extra_environ=user_environ, status=403)
        self.testapp.get(awarded_credit_href)
        self.testapp.delete(awarded_credit_href)
        self.testapp.get(awarded_credit_href, status=404)


class TestBulkAwardedCreditView(CreditLayerTest):

    admin_user = u"sjohnson@nextthought.com"

    def setUp(self):
        self.url = '/dataserver2/Credit/@@bulk_awarded_credit'
        self.source_info = ('source', os.path.join(os.path.dirname(__file__), 'resources/bulk_awarded_credit.csv'))

        self.container = CreditDefinitionContainer()
        component.getGlobalSiteManager().registerUtility(self.container,
                                                         ICreditDefinitionContainer)

    def tearDown(self):
        component.getGlobalSiteManager().unregisterUtility(self.container,
                                                           ICreditDefinitionContainer)

    def _f(self, file_info, content=None):
        return file_info if content is None else (file_info[0], file_info[1], str(content))

    def _upload_file(self, file_info, content=None, status=200, username=u'sjohnson@nextthought.com'):
        return self.testapp.post(self.url,
                                 upload_files=(self._f(file_info, content),),
                                 status=status,
                                 extra_environ=self._make_extra_environ(username=username))

    def _make_csv_content(self, header='username,title,description,issuer,date,value,type,units', rows=[]):
        data = []
        if header is not None:
            data.append(header)
        data.extend(rows)
        return '\n'.join(data)

    @WithSharedApplicationMockDS(testapp=True, users=True)
    @fudge.patch('nti.appserver.timezone.DisplayableTimeProvider.get_timezone_display_name')
    def test_adjust_date_time(self, mock_timezone):
        with mock_dataserver.mock_db_trans(self.ds):
            user = self._create_user(u'user001')

            view = UserAwardedCreditBulkCreationView(self.request)
            view.remoteUser = None
            mock_timezone.is_callable().returns('US/Central')
            assert_that(view._adjust_date_time("2018-09-20T00:00:00Z").strftime("%Y-%m-%d %H:%M:%S"), is_("2018-09-20 00:00:00"))
            assert_that(view._adjust_date_time("2018-09-20T00:00:00").strftime("%Y-%m-%d %H:%M:%S"), is_("2018-09-20 00:00:00"))

            view = UserAwardedCreditBulkCreationView(self.request)
            view.remoteUser = user
            mock_timezone.is_callable().returns('US/Central')
            assert_that(view._adjust_date_time("2018-09-20T00:00:00Z").strftime("%Y-%m-%d %H:%M:%S"), is_("2018-09-20 00:00:00"))
            assert_that(view._adjust_date_time("2018-09-20T00:00:00").strftime("%Y-%m-%d %H:%M:%S"), is_("2018-09-20 05:00:00"))

            view = UserAwardedCreditBulkCreationView(self.request)
            view.remoteUser = user
            mock_timezone.is_callable().returns(None)
            assert_that(view._adjust_date_time("2018-09-20T00:00:00Z").strftime("%Y-%m-%d %H:%M:%S"), is_("2018-09-20 00:00:00"))
            assert_that(view._adjust_date_time("2018-09-20T00:00:00").strftime("%Y-%m-%d %H:%M:%S"), is_("2018-09-20 00:00:00"))

            assert_that(calling(view._adjust_date_time).with_args("2018-09-20"), raises(Exception))

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_credit_definition_container_required(self):
        content = self._make_csv_content()
        self._upload_file(self.source_info, content=content, status=200)

        component.getGlobalSiteManager().unregisterUtility(self.container, ICreditDefinitionContainer)

        result = self._upload_file(self.source_info, content=content, status=422).json_body
        assert_that(result, has_entries({'message': 'Credit definition container not setup for site.'}))

    @WithSharedApplicationMockDS(testapp=True, users=True)
    @fudge.patch('nti.app.users.utils.admin.SiteAdminUtility.can_administer_user',
                 'nti.app.contenttypes.credit.views.UserAwardedCreditBulkCreationView._is_user_in_current_site')
    def test_bulk_awarded_credit(self, mock_can_administer, mock_in_site):
        """
        Test bulk create awarded credit to users. only nt and site admin could access.
        """
        mock_can_administer.is_callable().returns(False)
        mock_in_site.is_callable().returns(True)

        with mock_dataserver.mock_db_trans(self.ds):
            for username in (u'user001', u'user002', u'user003'):
                self._create_user(username)

        # No source file uploaded.
        result = self.testapp.post(self.url, upload_files=(), status=422, extra_environ=self._make_extra_environ(username=self.admin_user)).json_body
        assert_that(result, has_entries({"code": "MissingCSVFileError",
                                         "message": "No csv source file found."}))

        # bad csv formater: no content.
        result = self._upload_file(self.source_info, content='', status=422).json_body
        assert_that(result, has_entries({'code': 'InvalidCSVFileCodeError',
                                         'message': 'Please use tab or comma as csv delimiters.'}))

        # bad csv formater: mixed delimiters.
        content = self._make_csv_content(rows=['\t'.join(['user001', 'Math', 'gift', 'nextthought', '2018-09-20T00', '100', 'Course', 'points'])])
        result = self._upload_file(self.source_info, content=content, status=422).json_body
        assert_that(result, has_entries({'code': 'InvalidCSVFileCodeError',
                                         'message': 'Please use tab or comma as csv delimiters.'}))

        # required columns is missing.
        content = self._make_csv_content(header='title,description,issuer,date,value,type,units')
        result = self._upload_file(self.source_info, content=content, status=422).json_body
        assert_that(result, has_entries({'code': 'InvalidCSVFileCodeError',
                                         'message': 'Please provide missing columns: username.'}))

        content = self._make_csv_content(header='description,unknown')
        result = self._upload_file(self.source_info, content=content, status=422).json_body
        assert_that(result, has_entries({'code': 'InvalidCSVFileCodeError',
                                         'message': 'Please provide missing columns: username, title, value, date, units, type.'}))

        # invalid data, missing value for required columns
        content = self._make_csv_content(rows=[', , , , , , ,'])
        result = self._upload_file(self.source_info, content=content, status=422).json_body
        assert_that(result, has_entries({'code': 'InvalidRowsError',
                                         'message': 'No credits were applied. There was a problem importing the data.',
                                         'InvalidRows': has_length(1)}))
        assert_that(result['InvalidRows'][0], has_entries({'RowNumber': 1,
                                                           'username': 'No user (username=) found.',
                                                           'credit_definition': 'No credit definition (type=, units=) found.',
                                                           'title': 'Please use at least 2 characters.',
                                                           'date': 'Please use an iso8601 format date.',
                                                           'value': 'Please provide a number.'}))

        # invalid data, non-existing user, bad title, bad date format, non-existing credit_definition
        content = self._make_csv_content(rows=['non-user, d, , , 2018-09-20, xyz, Grade,points'])
        result = self._upload_file(self.source_info, content=content, status=422).json_body
        assert_that(result, has_entries({'code': 'InvalidRowsError',
                                         'message': 'No credits were applied. There was a problem importing the data.',
                                         'InvalidRows': has_length(1)}))
        assert_that(result['InvalidRows'][0], has_entries({'RowNumber': 1,
                                                           'username': 'No user (username=non-user) found.',
                                                           'credit_definition': 'No credit definition (type=Grade, units=points) found.',
                                                           'title': 'Please use at least 2 characters.',
                                                           'date': 'Please use an iso8601 format date.',
                                                           'value': 'Please provide a number.'}))

        # add credit_definition
        with mock_dataserver.mock_db_trans(self.ds):
            mock_dataserver.current_transaction.add(self.container)
            self.container.add_credit_definition(CreditDefinition(credit_type=u'grade', credit_units=u'points'))
            self.container.add_credit_definition(CreditDefinition(credit_type=u'sport', credit_units=u'rewards'))
            self.container.add_credit_definition(CreditDefinition(credit_type=u'sport', credit_units=u'scores'))
            self.container.add_credit_definition(CreditDefinition(credit_type=text_('成绩'), credit_units=text_('分')))

            deleted_credit_def = self.container.add_credit_definition(CreditDefinition(credit_type=u'match', credit_units=u'inches'))
            interface.alsoProvides(deleted_credit_def, IDeletedObjectPlaceholder)
            assert_that(self.container.get_credit_definition_by('match', 'inches'))

        # invalid data, both rows are invalid
        content = self._make_csv_content(rows=['user001, d, , , 2018-09-20T00, 52, Grade,points',
                                               'user001, "dd", , , 2018-09-20T00, 0, Grade,points',
                                               'user001, dd, , , 2018-09-02T00, 52, match, inches'])
        result = self._upload_file(self.source_info, content=content, status=422).json_body
        assert_that(result, has_entries({'code': 'InvalidRowsError',
                                         'message': 'No credits were applied. There was a problem importing the data.',
                                         'InvalidRows': has_length(3)}))
        assert_that(result['InvalidRows'], has_items(has_entries({'RowNumber': 1, 'title': 'Please use at least 2 characters.'}),
                                                     has_entries({'RowNumber': 2, 'value': 'Please use a number no less than 0.1.'}),
                                                     has_entries({'RowNumber': 3, 'credit_definition': 'No credit definition (type=match, units=inches) found.'})))

        content = """username,title,description,issuer,date,value,type,units
user001,"d\nd","a\na","s\ns",2018-09-10,you,k,z
user001,dd, dd,dd,2018-09-20T00:00:00Z,3,grade,points"""
        result = self._upload_file(self.source_info, content=content, status=422).json_body
        assert_that(result['InvalidRows'], has_length(1))
        assert_that(result['InvalidRows'][0], has_entries({'RowNumber': 1,
                                                           'description': u'Description can not contain newline character.',
                                                           'title': u'Title can not contain newline character.',
                                                           'value': u'Please provide a number.',
                                                           'date': u'Please use an iso8601 format date.',
                                                           'credit_definition': u'No credit definition (type=k, units=z) found.',
                                                           'issuer': u'Issuer can not contain newline character.'}))

        with mock_dataserver.mock_db_trans(self.ds):
            interface.noLongerProvides(deleted_credit_def, IDeletedObjectPlaceholder)

        # any invalid row would cause error.
        content = self._make_csv_content(rows=['user001, d, , , 2018-09-20T00, 52, inches,inches',
                                               'user001, dd, , , 2018-09-20T00, 52, match,inches'])
        result = self._upload_file(self.source_info, content=content, status=422).json_body
        assert_that(result, has_entries({'code': 'InvalidRowsError',
                                         'message': 'No credits were applied. There was a problem importing the data.',
                                         'InvalidRows': has_length(1)}))
        assert_that(result['InvalidRows'], has_items(has_entries({'RowNumber': 1, 'title': 'Please use at least 2 characters.'})))

        # all rows are valid
        result = self._upload_file(self.source_info, status=200).json_body
        assert_that(result, has_entries({'Items': has_length(5)}))
        assert_that(result['Items'][0], has_entries({'MimeType': 'application/vnd.nextthought.credit.userawardedcredit',
                                                     'title': 'Math',
                                                     'description': 'final test',
                                                     'issuer': 'MathClass',
                                                     'awarded_date': '2018-10-29T00:00:00Z',
                                                     'amount': 100,
                                                     'credit_definition': has_entries({'MimeType': u'application/vnd.nextthought.credit.creditdefinition',
                                                                                       'credit_type': 'grade',
                                                                                       'credit_units': 'points'})})
                                                )

        with mock_dataserver.mock_db_trans(self.ds):
            transcript = IUserAwardedCreditTranscript(User.get_user('user001'))
            awarded_credits = sorted([x for x in transcript.iter_awarded_credits()], key=lambda x: x.amount)
            assert_that(awarded_credits, has_length(3))
            assert_that(awarded_credits[0], has_properties({'title': 'English',
                                                            'amount': 50,
                                                            'credit_definition': has_properties({'credit_type': 'sport', 'credit_units': 'rewards'})}))
            assert_that(awarded_credits[1], has_properties({'title': text_('夏令营'),
                                                            'description': text_('数学竞赛'),
                                                            'issuer': text_('美国'),
                                                            'amount': 90,
                                                            'credit_definition': has_properties({'credit_type': text_('成绩'), 'credit_units': text_('分')})}))
            assert_that(awarded_credits[2], has_properties({'title': 'Math',
                                                            'amount': 100,
                                                            'credit_definition': has_properties({'credit_type': 'grade', 'credit_units': 'points'})}))

            transcript = IUserAwardedCreditTranscript(User.get_user('user002'))
            awarded_credits = [x for x in transcript.iter_awarded_credits()]
            assert_that(awarded_credits, has_length(1))
            assert_that(awarded_credits[0], has_properties({'title': 'Tennis',
                                                            'amount': 20,
                                                            'credit_definition': has_properties({'credit_type': 'sport', 'credit_units': 'rewards'})}))

            transcript = IUserAwardedCreditTranscript(User.get_user('user003'))
            awarded_credits = [x for x in transcript.iter_awarded_credits()]
            assert_that(awarded_credits, has_length(1))
            assert_that(awarded_credits[0], has_properties({'title': 'Golf',
                                                            'amount': 0.1,
                                                            'credit_definition': has_properties({'credit_type': 'sport', 'credit_units': 'scores'})}))

        # only contains required columns
        content = self._make_csv_content(header='username,title,date,value,type,units',
                                         rows=['user002, "math", 2018-09-20T00, 52, Grade,points'])
        result = self._upload_file(self.source_info, content=content, status=200).json_body
        assert_that(result['Items'][0], has_entries({'title': 'math',
                                                     'issuer': None,
                                                     'description': None,
                                                     'amount': 52,
                                                     'user': not_none(),
                                                     'MimeType': 'application/vnd.nextthought.credit.userawardedcredit'}))
        assert_that(result['Items'][0]['user']['Username'], is_('user002'))

        # authentication, only nextthought and site admins could access this view.
        mock_can_administer.is_callable().returns(True)

        self.testapp.post(self.url, upload_files=(), status=401, extra_environ=self._make_extra_environ(username=None))
        self.testapp.post(self.url, upload_files=(), status=403, extra_environ=self._make_extra_environ(username=u'user001'))

        with mock_dataserver.mock_db_trans(self.ds):
            srm = IPrincipalRoleManager(getSite(), None)
            srm.assignRoleToPrincipal(ROLE_SITE_ADMIN.id, 'user001')

        result = self._upload_file(self.source_info, status=200, username=u'user001').json_body
        assert_that(result, has_entries({'Items': has_length(5)}))

        with mock_dataserver.mock_db_trans(self.ds):
            srm = IPrincipalRoleManager(getSite(), None)
            srm.removeRoleFromPrincipal(ROLE_SITE_ADMIN.id, 'user001')

    @WithSharedApplicationMockDS(testapp=True, users=True)
    def test_credit_collection(self):
        result = self.testapp.get('/dataserver2/service/').json_body['Items']
        global_ws = None
        credit_collection = None
        try:
            global_ws = next(x for x in result if x['Title'] == 'Global')
            credit_collection = next(x for x in global_ws['Items'] if x['Title'] == CREDIT_PATH_NAME)
        except StopIteration:
            pass
        assert_that(global_ws, not_none())
        assert_that(credit_collection, not_none())

        link = self.require_link_href_with_rel(credit_collection, 'bulk_awarded_credit')
        assert_that(link, is_("/dataserver2/Credit/@@bulk_awarded_credit"))
