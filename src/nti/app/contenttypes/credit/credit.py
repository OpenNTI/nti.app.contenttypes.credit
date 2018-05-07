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

from nti.contenttypes.credit.interfaces import ICreditDefinitionContainer

from nti.containers.containers import CaseInsensitiveCheckingLastModifiedBTreeContainer

from nti.coremetadata.interfaces import IUser

from nti.schema.fieldproperty import createDirectFieldProperties

from nti.schema.schema import SchemaConfigured

logger = __import__('logging').getLogger(__name__)
