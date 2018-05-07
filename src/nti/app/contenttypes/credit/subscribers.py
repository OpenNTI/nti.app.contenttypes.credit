#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Event listeners.

.. $Id: subscribers.py 124417 2017-11-30 16:18:10Z carlos.sanchez $
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=E1101,E1121

from zope import component

from zope.site.interfaces import INewLocalSite

from nti.contenttypes.credit.credit import CreditDefinitionContainer

from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer

from nti.site.localutility import install_utility

from nti.site.interfaces import IHostPolicySiteManager

logger = __import__('logging').getLogger(__name__)


@component.adapter(IHostPolicySiteManager, INewLocalSite)
def on_site_created(site_manager, unused_event):
    logger.info('Installed credit definition container (%s)',
                site_manager.__parent__.__name__)
    install_utility(CreditDefinitionContainer(),
                    '++etc++nticreditdefinition',
                    ICreditDefinitionContainer,
                    site_manager)
