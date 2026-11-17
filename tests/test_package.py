"""Regression-contract and timing-measurement checks; no LTspice required."""
import copy,unittest
import numpy as np
from snspdtool.analysis import crossing,decay
from snspdtool.core import check,compare,references,selected

class PackageChecks(unittest.TestCase):
    def test_reference_coverage_and_model_hash(self):
        self.assertEqual(check()['reference_coverage'],'complete')

    def test_unknown_case_rejected(self):
        with self.assertRaises(ValueError):selected(['unknown_case'])

    def test_no_trigger_cannot_pass_as_detected_reset(self):
        ref=references()['geiger_c30_schematic_1V']
        result={'finite':True,'recovered':True,'event_count':0,'valid_pulse':False,
                'thermal_cap_hit':False,'kvl_integral_residual_fraction':0,
                'N':1,'deposited_relative_error':0}
        self.assertEqual(compare(result,ref),[])
        altered=copy.deepcopy(result);altered['valid_pulse']=True
        self.assertIn('unexpected trigger',compare(altered,ref))

    def test_nonfinite_results_rejected(self):
        self.assertEqual(compare({'finite':False},{}),['non-finite trace'])

    def test_missing_fall_crossing_is_not_zero_duration(self):
        t=np.linspace(0,1,100);y=np.ones_like(t)
        self.assertIsNone(decay(t,y,np.ones_like(t,dtype=bool)))

    def test_exponential_decay_has_expected_90_10_time(self):
        tau=2e-9
        t=np.linspace(0,1,10001)**1.3*12e-9
        y=np.exp(-t/tau)
        self.assertAlmostEqual(decay(t,y,np.ones_like(t,dtype=bool)),tau*np.log(9)*1e9,places=5)

    def test_crossing_uses_time_interpolation(self):
        self.assertAlmostEqual(crossing(np.array([0.,2.,5.]),np.array([10.,6.,0.]),5.,0,'down'),2.5)

if __name__=='__main__':unittest.main()
