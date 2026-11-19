import csv
import shutil
import subprocess
import tempfile
from pathlib import Path

import fitz
from docx import Document as DocxDocument
from pptx import Presentation
from openpyxl import load_workbook


def extract_pdf(path):
    text = []

    with fitz.open(str(path)) as pdf:
        for page in pdf:
            text.append(page.get_text())

    return "\n".join(text)


def extract_docx(path):
    document = DocxDocument(str(path))
    text = []

    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            text.append(paragraph.text)

    for table in document.tables:
        for row in table.rows:
            text.append(" ".join(cell.text for cell in row.cells))

    return "\n".join(text)



def extract_doc(path):
    """Extract text from legacy DOC files using LibreOffice."""

    executable = Path(
        r"C:\Program Files\LibreOffice\program\soffice.exe"
    )

    if not executable.exists():
        raise RuntimeError(
            "LibreOffice executable not found."
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        subprocess.run(
            [
                str(executable),
                "--headless",
                "--convert-to", "txt:Text",
                "--outdir", temp_dir,
                str(path),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )

        output_file = Path(temp_dir) / (path.stem + ".txt")

        if not output_file.exists():
            raise RuntimeError("DOC conversion failed.")

        return output_file.read_text(
            encoding="utf-8",
            errors="replace",
        )


def extract_pptx(path):
    presentation = Presentation(str(path))
    text = []

    for slide in presentation.slides:
        for shape in slide.shapes:
            if shape.has_text_frame:
                text.append(shape.text)

            if shape.has_table:
                for row in shape.table.rows:
                    text.append(
                        " ".join(cell.text for cell in row.cells)
                    )

    return "\n".join(text)


def extract_xlsx(path):
    workbook = load_workbook(
        filename=str(path),
        read_only=True,
        data_only=True,
    )

    text = []

    try:
        for sheet in workbook.worksheets:
            text.append(sheet.title)

            for row in sheet.iter_rows(values_only=True):
                values = [
                    str(value)
                    for value in row
                    if value is not None
                ]

                if values:
                    text.append(" ".join(values))
    finally:
        workbook.close()

    return "\n".join(text)


def extract_text(path):
    return path.read_text(encoding="utf-8", errors="replace")


def extract_csv(path):
    text = []

    with path.open(
        "r",
        encoding="utf-8-sig",
        errors="replace",
        newline="",
    ) as file:
        reader = csv.reader(file)

        for row in reader:
            text.append(" ".join(row))

    return "\n".join(text)


def extract_document_text(file_path):
    path = Path(file_path)
    extension = path.suffix.lower()

    extractors = {
        ".pdf": extract_pdf,
        ".docx": extract_docx,
        ".doc": extract_doc,
        ".pptx": extract_pptx,
        ".xlsx": extract_xlsx,
        ".txt": extract_text,
        ".csv": extract_csv,
    }

    extractor = extractors.get(extension)

    if extractor is None:
        raise ValueError(
            f"Unsupported file format: {extension}"
        )

    return extractor(path)
