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

from zope.component.hooks import setHooks

from nti.app.contenttypes.credit.generations.install import install_credit_definition_container

from nti.dataserver.interfaces import IDataserver
from nti.dataserver.interfaces import IOIDResolver

logger = __import__('logging').getLogger(__name__)

generation = 2


@interface.implementer(IDataserver)
class MockDataserver(object):

    root = None

    def get_by_oid(self, oid, ignore_creator=False):
        resolver = component.queryUtility(IOIDResolver)
        if resolver is None:
            logger.warn("Using dataserver without a proper ISiteManager.")
        else:
            return resolver.get_object_by_oid(oid, ignore_creator=ignore_creator)
        return None


def do_evolve(context, generation=generation):
    logger.info("Credit evolution %s started", generation)

    setHooks()
    conn = context.connection
    ds_folder = conn.root()['nti.dataserver']

    mock_ds = MockDataserver()
    mock_ds.root = ds_folder
    component.provideUtility(mock_ds, IDataserver)
    install_credit_definition_container(context)
    component.getGlobalSiteManager().unregisterUtility(mock_ds, IDataserver)
    logger.info('Credit evolution %s done.', generation)


def evolve(context):
    """
    Evolve to generation 32 by making sure assessment items are registered
    correctly (mainly around IRandomizedQuestionSets, which should just
    be registered as IQuestionSets).
    """
    do_evolve(context)
