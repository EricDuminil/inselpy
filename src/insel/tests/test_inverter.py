import os
from pathlib import Path

from insel import EtaCurve, Inverter

from .constants import SCRIPT_DIR
from .custom_assertions import CustomAssertions

os.chdir(SCRIPT_DIR)

# Deye SUN600G3-EU-230 — micro-inverter, real-world example
DEYE_SUN600 = dict(
    manufacturer_name="Deye",
    name="Deye SUN600G3-EU-230",
    nominal_power=600,
    p_for_eta_max=0.40,
    eta_max=0.965,
    eta_euro=0.95,
)

# Fronius Symo 10k — real-world example
FRONIUS_SYMO = dict(
    manufacturer_name="Fronius",
    name="Symo 10k",
    nominal_power=10000,
    p_for_eta_max=0.50,
    eta_max=0.982,
    eta_euro=0.979,
    inverter_id="f100",
)


class TestEtaCurve(CustomAssertions):
    def test_find_params_returns_three_values(self):
        result = EtaCurve.find_params(pm=0.50, em=0.982, ee=0.979)
        self.assertEqual(len(result), 3)

    def test_eta_euro_round_trip(self):
        pm, em, ee = 0.50, 0.982, 0.979
        p_self, v_loss, r_loss = EtaCurve.find_params(pm, em, ee)
        ec = EtaCurve(pm=pm, eta_max=em, desired_eta_euro=ee)
        self.assertAlmostEqual(ec.eta_euro(r_loss), ee, places=4)

    def test_different_efficiencies_give_different_params(self):
        params_a = EtaCurve.find_params(0.50, 0.982, 0.979)
        params_b = EtaCurve.find_params(0.30, 0.975, 0.960)
        self.assertNotEqual(params_a, params_b)


class InverterChecks(CustomAssertions):
    """Parametric tests shared by all inverter fixtures."""
    __test__ = False
    inverter_params: dict

    @classmethod
    def setUpClass(cls):
        cls.inv = Inverter(**cls.inverter_params)

    def test_params_are_set(self):
        self.assertIn("p_self", self.inv.params)
        self.assertIn("v_loss", self.inv.params)
        self.assertIn("r_loss", self.inv.params)
        self.assertEqual(self.inv.params["nominal_power"], self.inv.nominal_power)

    def test_simulated_eta_euro_close_to_specified(self):
        self.assertAlmostEqual(self.inv.simulated_eta_euro, self.inv.eta_euro,
                               delta=self.inv.eta_euro * 0.01)

    def test_simulated_eta_max_close_to_specified(self):
        self.assertAlmostEqual(self.inv.simulated_eta_max, self.inv.eta_max,
                               delta=self.inv.eta_max * 0.001)

    def test_simulated_p_for_eta_max_close_to_specified(self):
        self.assertAlmostEqual(self.inv.simulated_p_for_eta_max, self.inv.p_for_eta_max,
                               delta=self.inv.p_for_eta_max * 0.001)

    def test_cec_efficiency_is_plausible(self):
        self.assertAlmostEqual(self.inv.simulated_eta_cec, self.inv.eta_euro,
                               delta=self.inv.eta_euro * 0.01)

    def test_plot_creates_output_file(self):
        output = Path("plots") / f"inverter_eta_curve_{self.inv.inverter_id}.txt"
        output.unlink(missing_ok=True)
        result = self.inv.plot()
        self.assertEqual(result, output)
        self.assertTrue(output.exists(), f"{output} should have been written by gnuplot")

    def test_report_runs_without_error(self):
        self.inv.report()


class TestFroniusSymo(InverterChecks):
    __test__ = True
    inverter_params = FRONIUS_SYMO

    def test_str(self):
        self.assertEqual(str(self.inv), "Symo 10k (10000 W)")


class TestDeyeSUN600(InverterChecks):
    __test__ = True
    inverter_params = DEYE_SUN600

    def test_str(self):
        self.assertEqual(str(self.inv), "Deye SUN600G3-EU-230 (600 W)")
