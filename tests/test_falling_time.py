"""Independent checks of decay fitting and the experimental GL flux law."""
import unittest

import numpy as np
from scipy.optimize import brentq

from experiments.falling_time.run import fit_tail, flux


class FallingTimeChecks(unittest.TestCase):
    def test_offset_exponential_recovers_time_constant(self):
        t = np.linspace(0, 1, 2001)**2 * 15
        y = 2.3*np.exp(-t/1.7)-.05
        result = fit_tail(t, y)
        self.assertTrue(result['valid'])
        self.assertAlmostEqual(result['tau_ns'], 1.7, places=4)

    def test_flat_trace_has_no_falling_segment(self):
        self.assertIsNone(fit_tail(np.arange(10.), np.ones(10)))

    def test_gl_flux_derivative_matches_equilibrium_current_relation(self):
        lk, idep = 38e-9, 15.6e-6
        for ratio in [.1, .5, .8, .95]:
            q = brentq(lambda q: 3*np.sqrt(3)/2*q*(1-q*q)-ratio,
                       0, 1/np.sqrt(3))
            current, delta = ratio*idep, idep*1e-5
            derivative = (flux(current+delta, lk, idep)-flux(current-delta, lk, idep))/(2*delta)
            self.assertAlmostEqual(derivative/(lk/(1-3*q*q)), 1., places=7)

    def test_flux_is_odd_and_linear_at_small_current(self):
        lk, idep = 38e-9, 15.6e-6
        current = .7*idep
        self.assertEqual(flux(-current, lk, idep), -flux(current, lk, idep))
        self.assertAlmostEqual(float(flux(idep*1e-6, lk, idep)/(lk*idep*1e-6)), 1.)


if __name__ == '__main__':
    unittest.main()
