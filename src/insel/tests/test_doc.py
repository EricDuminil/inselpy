import unittest
from insel import Insel
from .constants import IMPORTANT_BLOCKS


class TestInselDoc(unittest.TestCase):
    def test_insel_pdfs(self):
        doc_dir = Insel.dirname / 'doc'
        for basename in ['Tutorial', 'BlockReference', 'UserBlockReference',
                         'GettingStarted', 'ProgrammersGuide']:
            pdf = doc_dir / f"insel{basename}_en.pdf"
            self.assertTrue(pdf.exists(), f"{pdf} should exist")
            self.assertTrue(pdf.stat().st_size > 100_000,
                            f"{pdf} should be large enough")

    def test_insel_block_pdfs(self):
        doc_dir = Insel.dirname / 'doc' / 'inselBlocks'
        for basename in IMPORTANT_BLOCKS:
            pdf = doc_dir / f"{basename}.pdf"
            self.assertTrue(pdf.exists(), f"{pdf} should exist")
            self.assertTrue(pdf.stat().st_size > 10_000,
                            f"{pdf} should be large enough")
