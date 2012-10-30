#!/usr/bin/env python
# -*- mode: python; sh-basic-offset: 4; indent-tabs-mode: nil; coding: utf-8 -*-
# vim: tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8

import argparse
import sys

import clusto
from clusto import drivers
from clusto import script_helper


class ListPool(script_helper.Script):
    '''
    Lists servers that are part of two given pools.
    '''

    def __init__(self):
        script_helper.Script.__init__(self)

    def _add_arguments(self, parser):
        parser.add_argument('--names', default=False, action='store_true',
            help='Print names instead of ip addresses (defaults to False)')
        parser.add_argument('--recursive', default=False, action='store_true',
            help='Search resursively on both pools (defaults to False)')
        parser.add_argument('pool', nargs='+', metavar='pool',
            help='Pool(s) to query (1 required, 2 maximum)')

    def run(self, args):
        if len(args.pool) > 2:
            self.warn('Specified more than 2 pools, using only first 2')
        self.debug('Querying for pools %s' % args.pool)
        self.debug('Recursive search = %s' % args.recursive)
        serverset = clusto.get_from_pools(args.pool[:2],
            clusto_types=[drivers.servers.BasicServer],
            search_children=args.recursive)
        for server in serverset:
            if args.names:
                print server.name
            else:
                try:
                    ip = server.get_ips()
                except Exception, e:
                    self.debug(e)
                    ip = None
                if ip:
                    print ip[0]
                else:
                    print server.name


def main():
    lp, args = script_helper.init_arguments(ListPool)
    return(lp.run(args))

if __name__ == '__main__':
    sys.exit(main())

