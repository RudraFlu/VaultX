
import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from docx import Document as DocxDocument
from pptx import Presentation
from openpyxl import Workbook
import fitz

from documents.search_engine import extract_document_text


class TextExtractionTests(SimpleTestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp_dir.name)
        self.addCleanup(self.temp_dir.cleanup)

    def test_extract_txt(self):
        path = self.directory / "test.txt"
        path.write_text("Hello VaultX", encoding="utf-8")

        result = extract_document_text(path)

        self.assertIn("Hello VaultX", result)

    def test_extract_csv(self):
        path = self.directory / "test.csv"
        path.write_text(
            "Name,Subject\nRudra,Python",
            encoding="utf-8"
        )

        result = extract_document_text(path)

        self.assertIn("Rudra", result)
        self.assertIn("Python", result)

    def test_extract_docx(self):
        path = self.directory / "test.docx"

        document = DocxDocument()
        document.add_paragraph("VaultX document text")
        document.save(path)

        result = extract_document_text(path)

        self.assertIn("VaultX document text", result)

    def test_extract_pdf(self):
        path = self.directory / "test.pdf"

        pdf = fitz.open()
        page = pdf.new_page()
        page.insert_text((50, 50), "VaultX PDF text")
        pdf.save(path)
        pdf.close()

        result = extract_document_text(path)

        self.assertIn("VaultX PDF text", result)

    def test_extract_pptx(self):
        path = self.directory / "test.pptx"

        presentation = Presentation()
        slide = presentation.slides.add_slide(
            presentation.slide_layouts[5]
        )
        slide.shapes.title.text = "VaultX Presentation"
        presentation.save(path)

        result = extract_document_text(path)

        self.assertIn("VaultX Presentation", result)

    def test_extract_xlsx(self):
        path = self.directory / "test.xlsx"

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Test Sheet"
        sheet["A1"] = "VaultX Spreadsheet"
        workbook.save(path)
        workbook.close()

        result = extract_document_text(path)

        self.assertIn("Test Sheet", result)
        self.assertIn("VaultX Spreadsheet", result)

    def test_unsupported_file_extension(self):
        path = self.directory / "test.exe"
        path.touch()

        with self.assertRaises(ValueError):
            extract_document_text(path)
