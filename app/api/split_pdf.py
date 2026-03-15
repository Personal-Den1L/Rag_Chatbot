import os
from pypdf import PdfReader, PdfWriter

def should_split(file_path: str, max_pages: int = 10, max_mb: float = 1.0) -> bool:
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    return size_mb > max_mb or len(PdfReader(file_path).pages) > max_pages


def split_into_temp_files(file_path: str, temp_dir: str, chunk_size: int = 10) -> list[str]:
    reader = PdfReader(file_path)
    total_pages = len(reader.pages)
    base_name = os.path.splitext(os.path.basename(file_path))[0]

    temp_paths: list[str] = []
    start = 0
    part = 1

    while start < total_pages:
        writer = PdfWriter()
        end = min(start + chunk_size, total_pages)

        for i in range(start, end):
            writer.add_page(reader.pages[i])

        out_path = os.path.join(temp_dir, f"{base_name}_part_{part}.pdf")
        with open(out_path, "wb") as out_f:
            writer.write(out_f)

        temp_paths.append(out_path)
        part += 1

        if end == total_pages:
            break

        start = end - 1

    return temp_paths
