"""Common utility functions for clusto"""
import itertools


def batch(iterable, size):
    """Returns an iterable of iterables that each yield size items."""
    if size == 0:
        raise ValueError('size cannot be 0')
    c = itertools.count()
    for _, g in itertools.groupby(iterable, lambda x: c.next()/size):
        yield g
