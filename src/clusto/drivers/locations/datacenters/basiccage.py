# -*- coding: utf-8 -*-
#
# © 2012 Paul D. Lathrop
# Author: Paul Lathrop <paul@tertiusfamily.net>
#

"""Clusto driver to represent a cage in a datacenter."""

from clusto.drivers.base import Location

class BasicCage(Location):
    """
    Basic Cage driver.
    """

    _clusto_type = "cage"
    _driver_name = "basiccage"
