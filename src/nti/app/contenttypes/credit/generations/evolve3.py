#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
.. $Id$
"""

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

from nti.app.contenttypes.credit.generations.evolve2 import do_evolve

logger = __import__('logging').getLogger(__name__)

generation = 3

def evolve(context):
    """
    Evolve to generation 3 by trying more hard to install credit definition
    utility.
    """
    do_evolve(context, generation)
