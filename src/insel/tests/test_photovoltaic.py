import shutil
import tempfile
from pathlib import Path

from insel import PhotovoltaicModuleModel

from .custom_assertions import CustomAssertions

# Typical 250 W crystalline silicon module
MODULE_PARAMS = dict(
    manufacturer_name="TestMfr",
    name="Test Module 250W",
    pv_id="t250",
    mpp=250.0,
    u_oc=37.5,
    i_sc=8.7,
    u_mpp=30.5,
    i_mpp=8.2,
    noct=47.0,
    alpha_u_percent=-0.32,
    alpha_i_percent=0.05,
    rows=6,
    columns=10,
    module_tolerance=3.0,
    height=1.65,
    width=0.995,
    mass=18.6,
    eta=15.3,
)


class TestPhotovoltaicModuleModel(CustomAssertions):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.module = PhotovoltaicModuleModel(**MODULE_PARAMS, output_folder=self.tmp)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_bp_file_is_created(self):
        self.assertTrue((self.tmp / "pvt250.bp").exists())

    def test_simulated_mpp_near_nameplate(self):
        self.assertAlmostEqual(self.module.simulated_mpp(), self.module.mpp,
                               delta=self.module.mpp * 0.05)

    def test_simulated_u_oc_near_nameplate(self):
        self.assertAlmostEqual(self.module.simulated_u_oc(), self.module.u_oc,
                               delta=self.module.u_oc * 0.05)

    def test_simulated_i_sc_near_nameplate(self):
        self.assertAlmostEqual(self.module.simulated_i_sc(), self.module.i_sc,
                               delta=self.module.i_sc * 0.05)

    def test_simulated_u_mpp_near_nameplate(self):
        self.assertAlmostEqual(self.module.simulated_u_mpp(), self.module.u_mpp,
                               delta=self.module.u_mpp * 0.05)

    def test_simulated_i_mpp_near_nameplate(self):
        self.assertAlmostEqual(self.module.simulated_i_mpp(), self.module.i_mpp,
                               delta=self.module.i_mpp * 0.05)

    def test_mpp_equals_u_mpp_times_i_mpp(self):
        self.assertAlmostEqual(
            self.module.simulated_mpp(),
            self.module.simulated_u_mpp() * self.module.simulated_i_mpp(),
            delta=self.module.mpp * 0.01,
        )

    def test_simulated_mpp_decreases_with_temperature(self):
        mpp_25 = self.module.simulated_mpp(temperature=25)
        mpp_50 = self.module.simulated_mpp(temperature=50)
        self.assertGreater(mpp_25, mpp_50)

    def test_simulated_mpp_increases_with_irradiance(self):
        mpp_500  = self.module.simulated_mpp(irradiance=500)
        mpp_1000 = self.module.simulated_mpp(irradiance=1000)
        self.assertGreater(mpp_1000, mpp_500)

    def test_derived_properties(self):
        self.assertEqual(self.module.cells_number, 60)
        self.assertEqual(self.module.serie, 60)
        self.assertAlmostEqual(self.module.area, 1.65 * 0.995, places=6)
        self.assertGreater(self.module.alpha_i, 0)
        self.assertLess(self.module.alpha_u, 0)

    def test_dmpp_dt_in_valid_range(self):
        self.assertLessEqual(self.module.dmpp_dt, -0.20)
        self.assertGreaterEqual(self.module.dmpp_dt, -0.60)

    def test_validation_rejects_wrong_alpha_i(self):
        self.assertRaises(ValueError, PhotovoltaicModuleModel,
                          **MODULE_PARAMS | {"alpha_i_percent": -0.05},
                          output_folder=self.tmp)

    def test_validation_rejects_wrong_alpha_u(self):
        self.assertRaises(ValueError, PhotovoltaicModuleModel,
                          **MODULE_PARAMS | {"alpha_u_percent": 0.32},
                          output_folder=self.tmp)
