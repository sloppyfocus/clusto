#!/usr/bin/env python
# -*- mode: python; sh-basic-offset: 4; indent-tabs-mode: nil; coding: utf-8 -*-
# vim: tabstop=4 softtabstop=4 expandtab shiftwidth=4 fileencoding=utf-8

import argparse
import sys

import clusto
from clusto import script_helper

class Rename(script_helper.Script):
    '''
    This will rename a given entity
    '''

    def __init__(self):
        script_helper.Script.__init__(self)

    def _add_arguments(self, parser):
        parser.add_argument('oldname', nargs=1,
            help='Name of an entity')
        parser.add_argument('newname', nargs=1,
            help='New name for the given entity')

    def run(self, args):
        try:
            obj = clusto.get_by_name(args.oldname[0])
        except LookupError, e:
            self.debug(e)
            self.error('"%s" does not exist' % args.oldname[0])
            return -1

        try:
            obj = clusto.get_by_name(args.newname[0])
            if obj:
                self.error('There is already an object named "%s"' %
                    args.newname[0])
        except LookupError, e:
            pass

        clusto.rename(obj.name, args.newname[0])
        return


def main():
    rename = Rename()
    parent_parser = script_helper.setup_base_parser()
    this_parser = argparse.ArgumentParser(parents=[parent_parser],
        description=rename._get_description())
    rename._add_arguments(this_parser)
    args = this_parser.parse_args()
    rename.init_script(args=args, logger=script_helper.get_logger(args.loglevel))
    return(rename.run(args))


if __name__ == '__main__':
    sys.exit(main())

