#!/usr/bin/env python
"""Display clusto objects, recursively, with attributes, and/or in color."""

import sys
from itertools import chain

import clusto
from clusto import script_helper


class Colors(object):

    """ANSI color escape sequences class."""

    mapping = {'BRIGHT': '\033[1m',
               'GREEN': '\033[32m',
               'MAGENTA': '\033[35m',
               'YELLOW': '\033[33m',
               'RESET': '\033[0m'}

    def __init__(self, enabled=False):
        """Construct instance with color enabled or disabled."""
        # Could default to true if stdout is a tty and not on Windows,
        # but for now we don't try to guess.
        self.enabled = enabled

    def __getattr__(self, name):
        """Return ANSI color escape sequence if color is enabled."""
        if self.enabled:
            return self.mapping[name]
        else:
            assert name in self.mapping
            return ''


class Tree(script_helper.Script):

    """
    Display clusto objects, recursively, with attributes, and/or in color.

    This script queries for a specified clusto object and attributes and
    optionally also queries parent or contained objects, recursively.
    It displays a simple, human-readable indented tree, with different
    colors for clusto keys, subkeys, and values if color is enabled.
    """

    def print_obj(self, obj, attrs, indent=0, color=False):
        """Print indented object, optionally with attributes or in color."""
        colors = Colors(enabled=color)
        indent_txt = "\t" * indent

        # Clusto object name.
        txt = "{indent}* {name}".format(
            indent=indent_txt,
            name=colors.BRIGHT + obj.name + colors.RESET)

        # Clusto object attributes.
        if 'ALL' in attrs:
            attributes = obj.attrs()
        else:
            attributes = chain.from_iterable(obj.attrs(attr)
                                             for attr in attrs)
        for x in attributes:
            if x.subkey:
                subkey_txt = ".{subkey}".format(
                    subkey=colors.MAGENTA + str(x.subkey) + colors.RESET
                )
            else:
                subkey_txt = ""
            txt += "\n{indent}| {key}{subkey} = {value}".format(
                indent=indent_txt,
                key=colors.GREEN + str(x.key) + colors.RESET,
                subkey=subkey_txt,
                value=colors.YELLOW + str(x.value) + colors.RESET
            )

        print(txt)

    def print_tree(self, root, attrs, direction, indent=0, color=False):
        """Print parent or contained object attributes, recursively."""
        # Alternatively, we could call obj.attrs(merge_container_attrs=True),
        # and use the entity attribute of each clusto attribute to
        # recreate the tree.
        for parent in getattr(root, direction)():
            self.print_obj(parent, attrs, indent=indent, color=color)
            self.print_tree(parent, attrs, direction, indent=indent + 1,
                            color=color)

    def run(self, args):
        """Execute script, passing script arguments to methods."""
        obj = clusto.get_by_name(args.obj)
        attrs = args.attrs
        self.print_obj(obj, attrs, indent=0, color=args.color)
        if args.parents or args.contents:
            if args.parents:
                direction = 'parents'
            else:
                direction = 'contents'
            self.print_tree(obj, attrs, direction, indent=1,
                            color=args.color)

    def _add_arguments(self, parser):
        parser.add_argument('obj', metavar='object', help="clusto object")
        parser.add_argument('attrs', metavar='attributes', nargs='*',
                            help="clusto attribute keys, ALL for all")
        direction = parser.add_mutually_exclusive_group()
        direction.add_argument('-p', '--parents', action='store_true',
                               default=False,
                               help="query parent objects, recursively")
        direction.add_argument('-c', '--contents', action='store_true',
                               default=False,
                               help="query contained objects, recursively")
        parser.add_argument('-C', '--color', action='store_true',
                            default=False, help="enable color output")


def main():
    """Execute script with clusto script_helper."""
    attr, args = script_helper.init_arguments(Tree)
    return attr.run(args)

if __name__ == '__main__':
    sys.exit(main())
