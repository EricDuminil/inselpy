import os

import insel

from .constants import SCRIPT_DIR
from .custom_assertions import CustomAssertions

os.chdir(SCRIPT_DIR)


class TestModelsWithDifferentEncoding(CustomAssertions):
    def test_non_ascii_template(self):
        utf8_template = insel.Template("encoding/a_times_b_utf8", a=2, b=2)
        utf8_template.timeout = 5
        self.assertEqual(utf8_template.run(), 4)

        iso_template = insel.Template("encoding/a_times_b_iso8859", a=4, b=4)
        iso_template.timeout = 5
        self.assertEqual(iso_template.run(), 16)

    def test_non_ascii_template_name(self):
        template = insel.Template("encoding/ä_tïm€ß_b", a=3, b=2)
        self.assertEqual(template.run(), 6)

    def test_space_in_template_name(self):
        template = insel.Template("encoding/space in folder/a times b", a=617, b=2)
        self.assertEqual(template.run(), 1234)

    def test_non_ascii_in_template_folder(self):
        template = insel.Template("encoding/Ëñçödìñg/a times b", a=2, b=2)
        self.assertEqual(template.run(), 4)

        template = insel.Template("encoding/Ëñçödìñg/x_plus_y.vseit", x=1200, y=34)
        self.assertEqual(template.run(), 1234)

        direct_run = insel.run("templates/encoding/Ëñçödìñg/x_plus_y.vseit")
        self.assertEqual(direct_run, 123)

    def test_full_unicode(self):
        insel.run("templates/encoding/Ëñçödìñg/💎.vseit")
        insel.run("templates/encoding/Ëñçödìñg/こんにちは.vseit")

    def test_read_file_in_non_ascii_folder(self):
        direct_run = insel.run("templates/encoding/Ëñçödìñg/read_file.insel")
        self.assertEqual(direct_run, 55)
