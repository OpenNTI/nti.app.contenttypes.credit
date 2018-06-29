#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generations for managing assesments.

.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from zope import component

from zope.component.hooks import site as current_site

from zope.generations.generations import SchemaManager

from nti.contenttypes.credit.credit import CreditDefinitionContainer

from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer

from nti.site.hostpolicy import get_all_host_sites

from nti.site.interfaces import IHostPolicyFolder

from nti.site.localutility import install_utility

from nti.traversal.traversal import find_interface

logger = __import__('logging').getLogger(__name__)

generation = 3


class _CreditSchemaManager(SchemaManager):
    """
    A schema manager that we can register as a utility in ZCML.
    """

    def __init__(self):
        super(_CreditSchemaManager, self).__init__(
            generation=generation,
            minimum_generation=generation,
            package_name='nti.app.contenttypes.credit.generations')


def evolve(context):
    install_credit_definition_container(context)


def install_credit_definition_container(context):
    conn = context.connection
    root = conn.root()
    ds_folder = root['nti.dataserver']
    with current_site(ds_folder):
        assert component.getSiteManager() == ds_folder.getSiteManager(), \
               "Hooks not installed?"

        for site in get_all_host_sites():
            with current_site(site):
                site_name = site.__name__
                site_registry = component.getSiteManager()
                credit_def_container = component.queryUtility(ICreditDefinitionContainer)
                container_site = find_interface(credit_def_container, IHostPolicyFolder, strict=False)
                if credit_def_container is None or container_site != site:
                    logger.info('Installed credit definition container (%s)',
                                site_name)
                    install_utility(CreditDefinitionContainer(),
                                    '++etc++nticreditdefinition',
                                    ICreditDefinitionContainer,
                                    site_registry)
