import tempfile
import re
import os
from calendar import monthrange
from pathlib import Path
import insel
from insel import Insel, InselError
from .custom_assertions import CustomAssertions
from .constants import SCRIPT_DIR, IS_WINDOWS

os.chdir(SCRIPT_DIR)


class TestBasicTemplates(CustomAssertions):
    def test_a_times_b(self):
        self.assertAlmostEqual(insel.template('a_times_b'), 9, places=6)
        # NOTE: .insel can be included in template_name, but doesn't have to.
        self.assertAlmostEqual(insel.template(
            'a_times_b.insel', a=4), 12, places=6)
        # NOTE: template path can also be absolute.
        self.assertAlmostEqual(insel.template(SCRIPT_DIR / 'templates' / 'a_times_b.insel',
                                              a=4, b=5),
                               20, places=6)

    def test_array_parameter(self):
        self.assertRaisesRegex(AttributeError, "UndefinedValue for 'x'", insel.template,
                               'array_parameters')
        self.assertRaisesRegex(AttributeError, "'x' should be an array.", insel.template,
                               'array_parameters', x=3)
        self.assertEqual(6, insel.template('array_parameters', x=[1, 2, 3]))
        self.assertEqual(6, insel.template(
            'array_parameters', x={0: 1, 1: 3, 2: 2}))


class TestTemplatesWithConstants(CustomAssertions):
    def test_vseit_is_a_template(self):
        # A Vseit model should be a template with default values
        self.assertEqual(3, insel.run('templates/constants/x_plus_y.vseit'))
        self.assertEqual(3, insel.template('constants/x_plus_y.vseit'))

    def test_setting_constants_in_vseit(self):
        self.assertEqual(5, insel.template(
            'constants/x_plus_y.vseit', x=2, y=3))
        self.assertEqual(4, insel.template('constants/x_plus_y.vseit', x=2))
        self.assertEqual(4, insel.template('constants/x_plus_y.vseit', y=3))

    def test_setting_string_constants_in_vseit(self):
        self.assertListEqual([72, 109, 173, 227, 257, 279, 301, 270, 200, 132, 83, 74],
                             insel.template('constants/string_constant'))
        self.assertListEqual([326, 300, 250, 168, 122, 101, 107, 141, 198, 244, 302, 335],
                             insel.template('constants/string_constant', location_name='Perth'))
        self.assertRaisesRegex(InselError, 'Location not found', insel.template,
                               'constants/string_constant', location_name='NotACity')

    def test_example_vseit(self):
        # PV in Nurnberg:
        self.compareLists([3866, 3652],
                          insel.template('constants/nurnberg.vseit'), places=0)
        # PV in Phoenix
        self.compareLists([6560, 6260],
                          insel.template('constants/nurnberg.vseit',
                                         Latitude=33,
                                         Longitude=-112,
                                         Tilt=10,
                                         Timezone=-7),
                          places=-1)

    def test_placeholder_over_constant(self):
        self.assertEqual(12, insel.template('constants/both',
                                            placeholder_x=5,
                                            placeholder_y=7))
        self.assertEqual(12, insel.template('constants/both', placeholder_x=5, placeholder_y=7,
                                            constant_x=0, constant_y=0))
        self.assertEqual(5, insel.template('constants/conflict', x=3, y=5))

    def test_both_placeholder_and_constant(self):
        self.assertEqual(3.7, insel.template('constants/same', x=1.2))


class TestTemplates(CustomAssertions):
    def test_empty_if(self):
        self.assertEqual(insel.template('empty_if'), [])

    def test_ifelsenan(self):
        odds_as_nans = insel.template('odds_as_nans')
        self.compareLists(odds_as_nans[::2], range(-10, 12, 2))
        for odd in odds_as_nans[1::2]:
            self.assertNaN(odd)

    def test_if(self):
        only_evens = insel.template('remove_odds')
        self.compareLists(only_evens, range(-10, 12, 2))

    def test_mtm_averages(self):
        # Those places used to have wrong averages
        places = ['Cambridge', 'Inuvik', 'Milagro',
                  'Naesgard', 'Nurnberg', 'Planes de Montecrist']
        for place in places:
            self.assertTrue(insel.template('weather/check_temperatures', location=place),
                            f'Wrong temperatures for {place}')

    def test_gengt_consistency(self):
        deviation = insel.template('weather/gengt_comparison')
        # NOTE: Depending on system, pseudo random values can vary very slightly.
        #       1e-4 really isn't any problem for °C or W/m²
        self.compareLists(deviation, [0, 0], places=4)

    def test_gengt_averages(self):
        irradiance_deviation, temperature_deviation = \
            insel.template('weather/gengt_monthly_averages')
        self.assertAlmostEqual(irradiance_deviation, 0, delta=5,
                               msg="Irradiance shouldnt vary by more than 5 W/m²")
        self.assertAlmostEqual(temperature_deviation, 0, delta=0.1,
                               msg="Temperature shouldnt vary by more than 0.1K")

    def test_aligned_screen_block(self):
        # Check that numbers displayed by SCREEN '*' are separated by at least one space
        # and that the decimal separators are aligned one above the other
        matrix = insel.template('expg')
        for i, row in zip(range(-20, 20), matrix):
            power = i / 2
            self.assertAlmostEqual(power, row[0], places=6)
            positive = 10 ** power
            negative = -10 ** (-power)
            self.assertAlmostEqual(positive, row[1], delta=positive / 1e6)
            self.assertAlmostEqual(negative, row[2], delta=-negative / 1e6)

        # Run again, this time checking the nicely formatted raw output.
        aligned = insel.raw_run('templates/expg.insel')
        output = [line for line in aligned.splitlines() if '    ' in line]
        self.assertTrue(len(output) > 30, 'Many lines should be returned.')

        dot_indices = set()
        columns = 5

        def indices(text, char):
            return [i for i, ltr in enumerate(text) if ltr == char]

        for line in output:
            dot_indices.update(indices(line, '.'))

        self.assertEqual(len(dot_indices), columns,
                         f"There should be {columns} nicely aligned decimal points")

    def test_updated_coordinates(self):
        v1_results = insel.template('photovoltaic/nurnberg_v1',
                                    latitude=49.5,
                                    old_longitude=-11.08,
                                    old_timezone=23
                                    )
        self.assertRegex(Insel.last_raw_output, '0 errors?, 4 warnings?')
        v2_results = insel.template('photovoltaic/nurnberg_v2',
                                    latitude=49.5,
                                    longitude=11.08,
                                    timezone=+1
                                    )
        self.compareLists(v1_results, [3865, 3645], places=-1)
        self.compareLists(v2_results, v1_results, places=2)

    def test_cumc(self):
        table = insel.template('conditional/sum')
        for month, (x, y) in zip(range(1, 13), table):
            _, days = monthrange(2021, month)
            self.assertAlmostEqual(month, x)
            self.assertAlmostEqual(days * (days + 1) / 2 * 24, y)

    def test_maxxc(self):
        table = insel.template('conditional/max')
        for month, (x, y) in zip(range(1, 13), table):
            _, days = monthrange(2021, month)
            self.assertAlmostEqual(month, x)
            self.assertAlmostEqual(days, y)

    def test_max_xy(self):
        table = insel.template('stats/max_xy')
        self.compareLists(table, [90, 1])
        self.assertEqual(insel.template('stats/max_xy_c'),
                         [[2020, 31], [2021, 31]])
        table = [v for r in insel.template('stats/max_xy_p') for v in r]
        self.compareLists(table, [90, 1, 360, 0], places=6)

    def test_min_xy(self):
        table = insel.template('stats/min_xy')
        self.compareLists(table, [270, -1])
        self.assertEqual(insel.template('stats/min_xy_c'),
                         [[2020, 29], [2021, 28]])
        table = [v for r in insel.template('stats/min_xy_p') for v in r]
        self.compareLists(table, [0, 0, 270, -1], places=6)

    def test_minnc(self):
        table = insel.template('conditional/min')
        for month, (x, y) in zip(range(1, 13), table):
            _, days = monthrange(2021, month)
            self.assertAlmostEqual(month, x)
            self.assertAlmostEqual(-days, y)

    def test_avec(self):
        table = insel.template('conditional/average')
        for month, (x, y) in zip(range(1, 13), table):
            _, days = monthrange(2021, month)
            self.assertAlmostEqual(month, x)
            self.assertAlmostEqual((days + 1) / 2, y)

    def test_parametric_average(self):
        self.assertEqual(1, insel.template('parametric/average'))

    def test_parametric_max(self):
        self.assertEqual(1, insel.template('parametric/max'))

    def test_parametric_min(self):
        self.assertEqual(1, insel.template('parametric/min'))

    def test_polyg(self):
        values = insel.template('mathematics/polyg')
        self.compareLists(values, [1, 1, 5, 4, -2, 0, 2, 4, 4, 4])

    def test_non_ascii_template(self):
        utf8_template = insel.Template('a_times_b_utf8', a=2, b=2)
        utf8_template.timeout = 5
        self.assertEqual(utf8_template.run(), 4)

        iso_template = insel.Template('a_times_b_iso8859', a=4, b=4)
        iso_template.timeout = 5
        self.assertEqual(iso_template.run(), 16)

    def test_sunpower_isc(self):
        self.assertRaisesRegex(AttributeError, "UndefinedValue", insel.template,
                               'photovoltaic/i_sc')  # Missing pv_id. STC by default
        self.assertIsNone(Insel.last_raw_output)
        spr_isc = insel.template('photovoltaic/i_sc', pv_id='008823')
        self.assertIsInstance(spr_isc, float)
        self.assertAlmostEqual(spr_isc, 5.87, places=2)

        self.assertAlmostEqual(insel.template('photovoltaic/i_sc', pv_id='003305'),
                               5.96, places=2)
        # TODO: More research is needed :)
        self.skipTest("""This spec fails, probably because of a too low
                'Temperature coeff of short-circuit current' in .bp files
                 .982E-7 in this example, instead of ~0.2E-3""")
        self.assertAlmostEqual(insel.template('photovoltaic/i_sc', pv_id='003305', temperature=70),
                               5.96 + (70 - 25) * 3.5e-3, places=2)

    def test_sunpower_uoc(self):
        # Missing pv_id. STC by default
        self.assertRaises(AttributeError, insel.template, 'photovoltaic/u_oc')
        self.assertAlmostEqual(insel.template('photovoltaic/u_oc', pv_id='003305'),
                               64.2, places=2)
        # TODO: More research is needed :)
        self.skipTest("Not sure about this calculation.")
        temp = 70
        self.assertAlmostEqual(insel.template('photovoltaic/u_oc', pv_id='003305',
                                              temperature=temp),
                               64.2 + (temp - 25) * (-0.1766), places=2)

    def test_sunpower_mpp(self):
        # Missing pv_id. STC by default
        self.assertRaises(AttributeError, insel.template, 'photovoltaic/mpp')
        self.assertAlmostEqual(insel.template('photovoltaic/mpp', pv_id='003305'),
                               305, places=0)
        temp = 70
        # TODO: Check with PVSYST or PVLIB. Is this the correct formula?
        # NOTE: -0.38%/K P_mpp, according to SPR 305 manual
        #       (https://www.pocosolar.com/wp-content/themes/twentyfifteen/pdfs/Sunpower%20Solar%20Panels/sunpower_305wht_spec_sheet.pdf)
        self.assertAlmostEqual(insel.template('photovoltaic/mpp', pv_id='003305', temperature=temp),
                               305 * (1 - 0.38 / 100) ** (temp - 25), places=0)

    def test_write_block(self):
        self._run_write_block()
        self._run_write_block(overwrite=0)
        self._run_write_block(overwrite=1)
        self._run_write_block(overwrite=2)

        self._run_write_block(basename='Ñüößç&txt.täxt€',
                              header='#ßeäöütµ§%&²³@°')

        self._run_write_block(basename='with a space.txt')
        self._run_write_block(basename='with_underscore.txt')

        self._run_write_block(fortran_format='(2F10.5)')

        self._run_write_block(header='#Some header here')

    def _run_write_block(self, basename='test.dat', **write_params):
        with tempfile.TemporaryDirectory() as tmpdirname:
            dat_file = Path(tmpdirname) / basename
            self.assertFalse(dat_file.exists())
            model = insel.Template(
                'io/write_params', dat_file=dat_file, **write_params)
            model.run()
            self.assertEqual(model.warnings, [])
            self.assertTrue(dat_file.exists(), "File should have been written")
            with open(dat_file) as out:
                if write_params.get('header'):
                    next(out)
                content = out.readlines()
                written = [float(line.split()[1]) for line in content]
                self.compareLists(
                    written, [x**2 for x in range(1, 11)], places=5)

    def test_write_block_relative_file_with_long_filename(self):
        """Template file is written in temp folder, in order for INSEL to run
        It means that relative files will be relative to temp folder"""
        dat_file = Path(tempfile.gettempdir(), 'a' * 50 + '.txt')
        dat_file.unlink(missing_ok=True)
        insel.template('io/write_params', dat_file=dat_file.name)
        self.assertTrue(dat_file.exists(),
                        f"{dat_file} should have been written")
        dat_file.unlink()

    def test_write_block_fails_if_folder_missing(self):
        filename = r'S:\\missing\\folder.txt' if IS_WINDOWS else '/not/here.txt'
        error_message = rf"(?m)^F05029 Block 00003: Cannot open file: {re.escape(filename)}$"

        self.assertRaisesRegex(InselError,
                               error_message,
                               insel.template, 'io/write_params',
                               dat_file=filename)

    def test_write_block_fails_if_read_only(self):
        if IS_WINDOWS:
            self.skipTest(
                "Docker tests for Windows are run as root, and ignore file permissions")
        with tempfile.TemporaryDirectory() as tmpdirname:
            dat_file = Path(tmpdirname) / 'read_only.dat'
            # Create read-only temp file:
            dat_file.touch()
            dat_file.chmod(mode=0o444)
            insel.template('io/write_params', dat_file=dat_file, overwrite=1)
            self.assertEqual(Insel.last_warnings, [
                'F05069 Block 00003: Unexpected write error - simulation terminated'])

    def test_read_simple_file(self):
        fourfivesix = insel.template('io/read_simple_file', ext='dat')
        self.compareLists(fourfivesix, [4, 5, 6])

    def test_read_missing_file(self):
        self.assertRaisesRegex(InselError, "(?m)^F05029 Block 00001: Cannot open file: .*not_here$",
                               insel.template, 'io/not_here')
        self.assertRegex(Insel.last_raw_output, '1 errors?, 0 warnings?')

    def test_read_too_many_lines(self):
        fourfivesix = insel.template('io/read_simple_file', ext='dat', lines=5)
        self.compareLists(fourfivesix, [4, 5, 6])
        self.assertEqual(Insel.last_warnings, [
                         'F05031 Block 00002: Unexpected end of file - simulation terminated'])

    def test_read_csv_like_as_normal_file(self):
        # READ block used to completely skip CSV files :-/
        # Now it just tries to read it as a normal file
        fourfivesix = insel.template('io/read_simple_file', ext='csv')
        self.compareLists(fourfivesix, [4, 5, 6])

    def test_read_epw_file(self):
        # Depending on extension, READ block will parse as normal file or EPW
        stuttgart_epw_average_temp = insel.template(
            'io/read_epw_file', ext='epw')
        self.assertAlmostEqual(stuttgart_epw_average_temp, 9.1, places=1)
        nothing_to_read = insel.template('io/read_epw_file', ext='txt')
        self.assertEqual(nothing_to_read, [])

    def test_weird_output(self):
        floats_and_lists = insel.template('io/weird_output')
        out = ';'.join(sorted(str(x) for x in floats_and_lists))
        self.assertEqual(
            out, '1.0;2.0;[1.0, 1.0, 1.0];[1.0, 1.0];[2.0, 2.0, 2.0];[2.0, 2.0]')
