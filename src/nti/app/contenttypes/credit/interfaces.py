#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id:
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class

from zope import interface

from zope.container.constraints import contains
from zope.container.constraints import containers

from zope.container.interfaces import IContained
from zope.container.interfaces import IContainer

from nti.base.interfaces import ICreated
from nti.base.interfaces import ILastModified

from nti.contenttypes.credit.interfaces import ICreditDefinition

from nti.ntiids.schema import ValidNTIID

from nti.schema.field import Number
from nti.schema.field import Object
from nti.schema.field import DecodingValidTextLine as ValidTextLine


class IUserAwardedCreditTranscript(interface.Interface):
    pass
