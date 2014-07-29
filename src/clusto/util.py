"""Common utility functions for clusto"""
import itertools


def batch(iterable, size):
    """Returns an iterable of iterables that each yield size items."""
    assert size != 0, 'size must be nonzero'
    c = itertools.count()
    for _, g in itertools.groupby(iterable, lambda x: c.next()/size):
        yield g
