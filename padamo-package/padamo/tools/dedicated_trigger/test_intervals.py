import unittest
import numpy as np
from .triggering_parallel import find_intervals

class TestIntervals(unittest.TestCase):
    def test_noint(self):
        x = np.array([0,0,0,0,0,0]).astype(bool)
        res, n = find_intervals(x)
        self.assertFalse(res)
        self.assertEqual(len(n),1)

    def test_full(self):
        x = np.array([1,1,1,1,1,1]).astype(bool)
        res, n = find_intervals(x)
        self.assertEqual(len(res),1)
        self.assertFalse(n)

    def test_two_intervals(self):
        x = np.array([0, 1, 1, 0, 1, 1, 0]).astype(bool)
        res,n = find_intervals(x)
        self.assertEqual(len(res), 2)
        self.assertEqual(len(n),3)

    def test_edgecases(self):
        x = np.array([1,1,0,0, 1, 1, 0, 1, 1, 0,1]).astype(bool)
        res,n = find_intervals(x)
        self.assertEqual(len(res), 4)
        self.assertEqual(len(n),3)

    def test_singles(self):
        x = np.array([0,0, 1, 0, 0, 1, 1, 0]).astype(bool)
        res,n = find_intervals(x)
        self.assertEqual(len(res), 2)
        self.assertEqual(len(n),3)
        self.assertEqual(res[0][0], 2)
        self.assertEqual(res[0][1], 3)
