import unittest
import clusto.util


class TestUtil(unittest.TestCase):
    def test_batch_against_iterable(self):
        i = clusto.util.batch(xrange(100), 10)
        first_batch = None
        last_batch = None
        num_batches = 0
        for batch_iter in i:
            num_batches += 1
            if first_batch is None:
                first_batch = list(batch_iter)
            last_batch = list(batch_iter)

        self.assertEqual(num_batches, 10)
        self.assertEqual(len(first_batch), 10)
        self.assertEqual(len(last_batch), 10)
        self.assertEqual(first_batch,
                         [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(last_batch,
                         [90, 91, 92, 93, 94, 95, 96, 97, 98, 99])

    def test_batch_unequal_lengths(self):
        i = clusto.util.batch(xrange(97), 10)
        first_batch = None
        last_batch = None
        num_batches = 0
        for batch_iter in i:
            num_batches += 1
            if first_batch is None:
                first_batch = list(batch_iter)
            last_batch = list(batch_iter)

        self.assertEqual(num_batches, 10)
        self.assertEqual(len(first_batch), 10)
        self.assertEqual(len(last_batch), 7)
        self.assertEqual(first_batch,
                         [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        self.assertEqual(last_batch,
                         [90, 91, 92, 93, 94, 95, 96])

    def test_batch_empty_list(self):
        i = clusto.util.batch([], 10)
        num_batches = 0
        for batch_iter in i:
            num_batches += 1
        self.assertEqual(num_batches, 0)

    def test_batch_zero_batch_length(self):
        i = clusto.util.batch(xrange(100), 0)
        with self.assertRaises(AssertionError):
            for g in i:
                pass
