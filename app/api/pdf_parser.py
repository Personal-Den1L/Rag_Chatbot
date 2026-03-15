import os
import pypdf
from docling import (
    DocumentConverter,
    PdfFormatOption,
    InputFormat,
    PdfPipelineOptions,
    RapidOcrOptions,
)


def is_scanned(file_path: str, sample_pages: int = 3) -> bool:
    try:
        reader = pypdf.PdfReader(file_path)
        total_pages = len(reader.pages)
        text = ""
        for i in range(min(sample_pages, total_pages)):
            text += reader.pages[i].extract_text() or ""
        return len(text.strip()) < 100
    except Exception:
        return True


class PDFProcessor:
    def __init__(self):
        ocr_pipeline = PdfPipelineOptions()
        ocr_pipeline.do_ocr = True
        ocr_pipeline.ocr_options = RapidOcrOptions()

        no_ocr_pipeline = PdfPipelineOptions()
        no_ocr_pipeline.do_ocr = False

        self.converter_ocr = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=ocr_pipeline)
            }
        )
        self.converter_text = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(pipeline_options=no_ocr_pipeline)
            }
        )

    def process_pdf(self, file_path: str):
        try:
            if is_scanned(file_path):
                print(f"[*] Processing {os.path.basename(file_path)} with Docling [OCR]...")
                return self.converter_ocr.convert(file_path)

            print(f"[*] Processing {os.path.basename(file_path)} with Docling [no OCR]...")
            return self.converter_text.convert(file_path)
        except Exception as e:
            print(f"[!] Error processing {file_path}: {e}")
            return None