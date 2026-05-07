import os
import shutil
import tempfile
from pathlib import Path

from insel import Inverter

from .constants import SCRIPT_DIR
from .custom_assertions import CustomAssertions

os.chdir(SCRIPT_DIR)

# Deye SUN600G3-EU-230 — micro-inverter, real-world example
DEYE_SUN600 = dict(
    manufacturer_name="Deye",
    name="SUN600G3-EU-230",
    nominal_power=600,
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
    eta_euro=0.979
)


class InverterChecks:
    """Parametric tests shared by all inverter fixtures."""
    inverter_params: dict

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.inv = Inverter(**cls.inverter_params, output_folder=cls.tmp)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

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
        output = self.tmp / f"inverter_eta_curve_{self.inv.inverter_id}.txt"
        output.unlink(missing_ok=True)
        result = self.inv.plot(plots_folder=self.tmp)
        self.assertEqual(result, output)
        self.assertTrue(output.exists(), f"{output} should have been written by gnuplot")
        content = output.read_text()
        self.assertIn(self.inv.manufacturer_name, content)
        self.assertIn(self.inv.name, content)

    def test_report_runs_without_error(self):
        self.inv.report()
        self.assertTrue((self.inv.output_folder / f"inverter_{self.inv.inverter_id}_example.vseit").exists())


class TestFroniusSymo(InverterChecks, CustomAssertions):
    inverter_params = FRONIUS_SYMO

    def test_str(self):
        self.assertEqual(str(self.inv), "Fronius Symo 10k (10000 W)")
        self.assertEqual(self.inv.inverter_id, "s10")


class TestDeyeSUN600(InverterChecks, CustomAssertions):
    inverter_params = DEYE_SUN600

    def test_str(self):
        self.assertEqual(str(self.inv), "Deye SUN600G3-EU-230 (600 W)")
        self.assertEqual(self.inv.inverter_id, "s600")
