#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id:
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

# pylint: disable=inherit-non-class

from zope.container.constraints import contains

from nti.contenttypes.credit.interfaces import ICreditTranscript, IAwardedCredit


class IUserAwardedCredit(IAwardedCredit):
    """
    A :class:`IAwardedCredit` that was granted by another user.
    """


class IUserAwardedCreditTranscript(ICreditTranscript):
    """
    The storage container for :class:`IUserAwardedCredit`.
    """

    contains(IUserAwardedCredit)


