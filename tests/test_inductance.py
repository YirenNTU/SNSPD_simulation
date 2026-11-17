"""Protect fixed-model compatibility and the opt-in nonlinear constitutive law."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
import numpy as np
from scipy.optimize import brentq
from snspdtool.core import ROOT, build, check_behavior, selected
from snspdtool.inductance import configure, flux_linkage, render_variant


class InductanceChecks(unittest.TestCase):
    def setUp(self):
        self.case = selected(['calorimetric_c30_b90_n10'])[0]
        self.source = (ROOT/'models/snspd_nbn_v5c.lib').read_text()

    def test_default_preserves_case_and_model_exactly(self):
        self.assertEqual(configure(self.case), self.case)
        self.assertEqual(render_variant(self.source, self.case), self.source)

    def test_gl_parameters_must_be_explicit_and_physical(self):
        for ratio, lk in [(None, 38), (1.2, None), (.8, 38), (float('nan'), 38), (1.2, -1)]:
            with self.assertRaises(ValueError):
                configure(self.case, 'gl', ratio, lk)

    def test_fixed_model_rejects_silently_ignored_gl_parameters(self):
        with self.assertRaises(ValueError):
            configure(self.case, 'fixed', 1.2, 38)

    def test_only_electrical_inductor_changes(self):
        c=configure(self.case, 'gl', 1.2, 38)
        active=lambda s:[x for x in s.splitlines() if x.strip() and not x.lstrip().startswith('*')]
        old,new=active(self.source),active(render_variant(self.source,c))
        self.assertEqual(len(old),len(new))
        changed=[(a,b) for a,b in zip(old,new) if a!=b]
        self.assertEqual(len(changed),1)
        self.assertTrue(changed[0][0].startswith('L_NBN4 '))
        self.assertIn(' Flux=',changed[0][1])

    def test_rebuild_fixed_clears_previous_variant_metadata(self):
        with TemporaryDirectory() as temporary:
            output = Path(temporary)
            opamp = output/'opamp.sub'
            build(configure(self.case, 'gl', 1.2, 38), output, opamp)
            directory = build(self.case, output, opamp)
            self.assertFalse((directory/'model_variant.json').exists())
            self.assertFalse((directory/'detector_gl.lib').exists())
            self.assertIn('snspd_nbn_v5c.lib', (directory/'case.cir').read_text())

    def test_flux_derivative_matches_gl_equilibrium(self):
        c=configure(self.case,'gl',1.2,38)
        idep=c['depairing_ratio']*c['Isw']
        for fraction in [.1,.5,.8,.95]:
            q=brentq(lambda q:3*np.sqrt(3)/2*q*(1-q*q)-fraction,0,1/np.sqrt(3))
            delta=idep*1e-5; current=fraction*idep
            actual=(flux_linkage(current+delta,c)-flux_linkage(current-delta,c))/(2*delta)
            self.assertAlmostEqual(actual/(38e-9/(1-3*q*q)),1,places=7)

    def test_behavior_check_rejects_an_inductance_guard_hit(self):
        ref={'recovered':True,'event_count':1}
        result={'finite':True,'recovered':True,'event_count':1,'valid_pulse':True,
                'thermal_cap_hit':False,'inductance_guard_hit':True,
                'kvl_integral_residual_fraction':0.,'N':10,'deposited_relative_error':0.}
        self.assertIn('inductance current guard reached',check_behavior(result,ref))


if __name__=='__main__':
    unittest.main()
