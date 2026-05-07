import os
import shutil
import tempfile
from pathlib import Path

from insel import PhotovoltaicModuleModel

from .constants import SCRIPT_DIR
from .custom_assertions import CustomAssertions

os.chdir(SCRIPT_DIR)

# JA Solar JAM54D40 460W (monocrystalline bifacial, 18×6 cells, half-cells)
JA_SOLAR_460 = dict(
    manufacturer_name="JASolar",
    name="JAM54D40 460W",
    module_technology="monocrystalline bifacial",
    pv_id="j460",
    mpp=460.0,
    u_oc=39.70,
    i_sc=14.64,
    u_mpp=33.17,
    i_mpp=13.87,
    noct=45.0,
    alpha_u_percent=-0.25,
    alpha_i_percent=0.045,
    rows=18,
    columns=6,
    module_tolerance=3.0,
    height=1.762,
    width=1.134,
    mass=22.0,
    eta=23.0,
    parallel=2,
)

# Trina Vertex TSM-DEG19C.20 410W (monocrystalline, 5×24 cells, half-cells, 2 parallel strings)
TRINA_VERTEX_410 = dict(
    manufacturer_name="Trina",
    name="Vertex TSM 410",
    mpp=410.0,
    u_oc=41.6,
    i_sc=12.40,
    u_mpp=34.6,
    i_mpp=11.85,
    noct=43.0,
    alpha_u_percent=-0.25,
    alpha_i_percent=0.04,
    rows=5,
    columns=24,
    height=1.754,
    width=1.096,
    eta=21.3,
    parallel=2,
)

# Sunpower SPR-X21-345 (monocrystalline, 8×12 cells)
SPR_345 = dict(
    manufacturer_name="Sunpower",
    name="SPR-X21-345",
    mpp=345.0,
    u_oc=68.2,
    i_sc=6.39,
    u_mpp=57.3,
    i_mpp=6.02,
    noct=45.0,
    alpha_u_percent=-0.1674 / 68.2 * 100,
    alpha_i_percent=0.0035 / 6.39 * 100,
    rows=8,
    columns=12,
    module_tolerance=3.0,
    height=1.558,
    width=1.046,
    mass=18.6,
    eta=21.5,
    parallel=1,
)


class PhotovoltaicModuleChecks:
    """Parametric tests shared by all PV module fixtures."""
    module_params: dict

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.module = PhotovoltaicModuleModel(**cls.module_params, output_folder=cls.tmp)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp)

    def _delta(self, value, percent=0.25):
        return abs(value) * percent / 100

    def test_bp_file_is_created(self):
        self.assertTrue((self.tmp / f"pv{self.module.pv_id}.bp").exists())

    def test_simulated_mpp(self):
        self.assertAlmostEqual(self.module.simulated_mpp(), self.module.mpp,
                               delta=self._delta(self.module.mpp))

    def test_simulated_u_oc(self):
        self.assertAlmostEqual(self.module.simulated_u_oc(), self.module.u_oc,
                               delta=self._delta(self.module.u_oc))

    def test_simulated_i_sc(self):
        self.assertAlmostEqual(self.module.simulated_i_sc(), self.module.i_sc,
                               delta=self._delta(self.module.i_sc))

    def test_simulated_u_mpp(self):
        self.assertAlmostEqual(self.module.simulated_u_mpp(), self.module.u_mpp,
                               delta=self._delta(self.module.u_mpp))

    def test_simulated_i_mpp(self):
        self.assertAlmostEqual(self.module.simulated_i_mpp(), self.module.i_mpp,
                               delta=self._delta(self.module.i_mpp))

    def test_mpp_equals_u_times_i(self):
        self.assertAlmostEqual(
            self.module.simulated_mpp(),
            self.module.simulated_u_mpp() * self.module.simulated_i_mpp(),
            delta=self._delta(self.module.mpp),
        )

    def test_simulated_mpp_decreases_with_temperature(self):
        self.assertGreater(self.module.simulated_mpp(temperature=25),
                           self.module.simulated_mpp(temperature=50))

    def test_simulated_mpp_increases_with_irradiance(self):
        self.assertGreater(self.module.simulated_mpp(irradiance=1000),
                           self.module.simulated_mpp(irradiance=500))

    def test_dmpp_dt_in_valid_range(self):
        self.assertLessEqual(self.module.dmpp_dt, -0.20)
        self.assertGreaterEqual(self.module.dmpp_dt, -0.60)

    def test_derived_properties(self):
        p = self.module_params
        self.assertEqual(self.module.cells_number, p["rows"] * p["columns"])
        self.assertEqual(self.module.serie, self.module.cells_number // p["parallel"])
        self.assertAlmostEqual(self.module.area, p["height"] * p["width"], places=6)
        self.assertGreater(self.module.alpha_i, 0)
        self.assertLess(self.module.alpha_u, 0)

    def test_plot_creates_output_file(self):
        output = self.tmp / f"iv_curve_{self.module.pv_id}.txt"
        output.unlink(missing_ok=True)
        self.assertEqual(self.module.plot(plots_folder=self.tmp), output)
        self.assertTrue(output.exists())
        self.assertIn(self.module.name, output.read_text())

    def test_simulated_fill_factor(self):
        self.assertAlmostEqual(self.module.simulated_fill_factor(), 80, delta=1)

    def test_report_runs_without_error(self):
        self.module.report()
        self.assertTrue((self.tmp / f"pv{self.module.pv_id}_example.insel").exists())


class TestJASolar460(PhotovoltaicModuleChecks, CustomAssertions):
    module_params = JA_SOLAR_460

    def test_cells_in_series(self):
        self.assertEqual(self.module.serie, 54)  # 108 cells / 2 parallel strings


class TestSPR345(PhotovoltaicModuleChecks, CustomAssertions):
    module_params = SPR_345

    def test_cells_in_series(self):
        self.assertEqual(self.module.serie, 96)
        self.assertEqual(self.module.pv_id, "s345")


class TestTrinaVertex410(PhotovoltaicModuleChecks, CustomAssertions):
    module_params = TRINA_VERTEX_410

    def _delta(self, value, percent=0.4):
        return abs(value) * percent / 100

    def test_cells_in_series(self):
        self.assertEqual(self.module.serie, 60)  # 120 cells / 2 parallel strings
