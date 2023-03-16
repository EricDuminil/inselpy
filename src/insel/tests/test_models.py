# coding=utf8
from pathlib import Path
import insel
from insel import Insel, InselError
from .custom_assertions import CustomAssertions
from .constants import SCRIPT_DIR, cwd


class TestExistingModel(CustomAssertions):
    def test_one_to_ten(self):
        self.compareLists(
            insel.run('templates/one_to_ten.insel'), range(1, 11))

    def test_screen(self):
        self.compareLists(insel.run('templates/io/screen.insel'), [1, 2, 3])
        header_content = insel.raw_run('templates/io/screen_header.insel')
        self.assertTrue('# HASHTAG' in header_content)
        self.assertTrue('! EXCLAMATION' in header_content)

    def test_screen1g(self):
        self.compareLists(insel.run('templates/io/screen1g.insel'), [])

    def test_add_negative_inputs(self):
        # Little known feature. Could be deleted.
        self.assertEqual(insel.template('add_negative_inputs.insel'), -8)

    def test_nonexisting_model(self):
        self.assertRaisesRegex(InselError, "File not found",
                               insel.run, 'templates/not_here.insel')
        self.assertRaisesRegex(InselError, "File not found",
                               insel.run, 'not_here/model.insel')

    def test_not_an_insel_file(self):
        self.assertRaisesRegex(InselError, "Invalid INSEL model file extension",
                               insel.run, 'data/gengt_comparison.dat')
        self.assertRaisesRegex(InselError, "Invalid INSEL model file extension",
                               insel.run, 'not_even_a_file.csv')

    def test_insel_constants(self):
        self.assertEqual(insel.run('templates/insel_constants.insel'), 3)

    def test_insel_duplicate_constant(self):
        self.assertEqual(
            insel.run('templates/duplicate_constant.insel'), 12345)
        self.assertEqual(Insel.last_warnings,
                         ['W04024 Redefinition of constant TEST skipped'])

    def test_insel_empty_constant(self):
        self.assertEqual(insel.run('templates/empty_constant.insel'), 12345)
        self.assertRegex(Insel.last_raw_output,
                         ("W05313 Stray constant definition detected at line 00003"
                          " of file .*empty_constant.insel"))

    def test_insel_include(self):
        self.assertEqual(insel.run('templates/insel_include.insel'), 3)

    def test_merging_two_loops(self):
        self.assertRaisesRegex(InselError, "Please try to merge 2 & 3", insel.run,
                               'templates/merge_distinct_loops.insel')

    def test_read_relative_file_when_in_correct_folder(self):
        with cwd(SCRIPT_DIR / 'templates'):
            deviation = insel.run('io/read_relative_file.insel')
            self.compareLists(deviation, [0, 0], places=4)

    def test_read_relative_file_when_in_another_folder(self):
        with cwd(SCRIPT_DIR):
            deviation = insel.run('templates/io/read_relative_file.insel')
            self.compareLists(deviation, [0, 0], places=4)

    def test_can_read_relative_file_with_absolute_path(self):
        with cwd(Path.home()):
            deviation = insel.run(
                SCRIPT_DIR / 'templates' / 'io' / 'read_relative_file.insel')
            self.compareLists(deviation, [0, 0], places=4)

    def test_string_parameter_in_vseit_should_not_be_cut(self):
        for model in ['short_string.vseit', 'long_string.vseit']:
            insel_model = insel.raw_run('-m', 'templates/io/' + model)
            string_params = [
                p for p in insel_model.split() if p.count("'") == 2]
            self.assertEqual(len(string_params), 2,
                             f"2 string parameters should be found in {model}")

    def test_screen_headline_should_be_displayed(self):
        for model in ['short_string.vseit', 'long_string.vseit']:
            out = insel.raw_run('templates/io/' + model)
            lines = out.splitlines()
            headline = next(line for line in lines if 'String' in line)
            self.assertTrue(len(headline) < 100,
                            f"Headline '{headline}' shouldn't be too long")

    def test_screen_utf8_header_should_be_displayed(self):
        out = insel.raw_run('templates/io/utf_headline.insel')
        self.assertTrue('T€st 12345' in out,
                        "Headline should be allowed to be in UTF-8")

    def test_mpp_without_top_of_loop(self):
        self.assertRaisesRegex(InselError, "No TOL-block", insel.run,
                               'templates/photovoltaic/mpp_without_top_of_loop.vseit')

    def test_mpp_with_top_of_loop(self):
        out = insel.raw_run('templates/photovoltaic/mpp_with_top_of_loop.vseit')
        self.assertRegex(out, r'Maximum at 17\.3 Volt and 52\.6 Watt')

    def test_algebraic_loop(self):
        self.assertRaisesRegex(InselError, "Algebraic loop detected", insel.run,
                               'templates/engine/sum_sum_do.insel')

    def test_algebraic_loop_with_do_do(self):
        self.skipTest("templates/engine/do_do.insel fails with SIGSEGV")

    def test_algebraic_loop_with_sum_sum(self):
        self.skipTest("templates/engine/sum_sum.insel fails with SIGSEGV")
