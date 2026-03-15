#./app/api/ingest.py:
import os
import gc
import tempfile
import chromadb
from app.api.pdf_parser import PDFProcessor
from app.api.split_pdf import should_split, split_into_temp_files
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)
from chromadb.utils import embedding_functions

embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)

client = chromadb.PersistentClient(path="/app/data/chroma")

collection = client.get_or_create_collection(
    name="daiict_knowledge",
    embedding_function=embedding_fn
)

def run_ingestion(raw_dir: str = "/app/data/raw") -> None:
    if not os.path.isdir(raw_dir):
        print(f"[!] Raw directory does not exist: {raw_dir}")
        return

    pdf_files = sorted(
        file_name
        for file_name in os.listdir(raw_dir)
        if file_name.lower().endswith(".pdf")
    )

    if not pdf_files:
        print(f"[!] No PDF files found in {raw_dir}")
        return

    processor = PDFProcessor()
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=headers_to_split_on
    )
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
    )

    print(f"[*] Found {len(pdf_files)} PDF files. Starting ingestion...")

    total_chunks = 0
    global_chunk_idx = 1
    for index, file_name in enumerate(pdf_files, start=1):
        file_path = os.path.join(raw_dir, file_name)
        print(f"\n[*] ({index}/{len(pdf_files)}) Processing: {file_name}")

        if should_split(file_path):
            with tempfile.TemporaryDirectory() as temp_dir:
                pdf_parts = split_into_temp_files(file_path, temp_dir, chunk_size=10)

                master_markdown = ""
                for part in pdf_parts:
                    result = processor.process_pdf(part)
                    if result:
                        master_markdown += result.document.export_to_markdown() + "\n\n"
                    gc.collect()

                if not master_markdown.strip():
                    print(f"[!] No parsed content returned for {file_name}. Skipping.")
                    continue

                header_chunks = header_splitter.split_text(master_markdown)
                print(f"[*] Header split into {len(header_chunks)} chunks")

                file_chunk_count = 0
                for header_chunk in header_chunks:
                    smaller_chunks = text_splitter.split_text(header_chunk.page_content)

                    for chunk_text in smaller_chunks:
                        chunk_text = chunk_text.strip()
                        if not chunk_text:
                            continue

                        enriched_text = f"Source Document: {file_name}\nText:\n{chunk_text}"
                        deterministic_id = f"{file_name}_chunk_{global_chunk_idx}"
                        chunk_metadata = {
                            "source": file_name,
                            "section": header_chunk.metadata.get("Header 1", "General"),
                            "subsection": header_chunk.metadata.get("Header 2", ""),
                            "subsubsection": header_chunk.metadata.get("Header 3", ""),
                        }

                        collection.upsert(
                            documents=[enriched_text],
                            metadatas=[chunk_metadata],
                            ids=[deterministic_id],
                        )
                        global_chunk_idx += 1
                        total_chunks += 1
                        file_chunk_count += 1

                print(f"[+] Upserted {file_chunk_count} chunks for {file_name}")
        else:
            pdf_parts = [file_path]

            master_markdown = ""
            for part in pdf_parts:
                result = processor.process_pdf(part)
                if result:
                    master_markdown += result.document.export_to_markdown() + "\n\n"
                gc.collect()

            if not master_markdown.strip():
                print(f"[!] No parsed content returned for {file_name}. Skipping.")
                continue

            header_chunks = header_splitter.split_text(master_markdown)
            print(f"[*] Header split into {len(header_chunks)} chunks")

            file_chunk_count = 0
            for header_chunk in header_chunks:
                smaller_chunks = text_splitter.split_text(header_chunk.page_content)

                for chunk_text in smaller_chunks:
                    chunk_text = chunk_text.strip()
                    if not chunk_text:
                        continue

                    enriched_text = f"Source Document: {file_name}\nText:\n{chunk_text}"
                    deterministic_id = f"{file_name}_chunk_{global_chunk_idx}"
                    chunk_metadata = {
                        "source": file_name,
                        "section": header_chunk.metadata.get("Header 1", "General"),
                        "subsection": header_chunk.metadata.get("Header 2", ""),
                        "subsubsection": header_chunk.metadata.get("Header 3", ""),
                    }

                    collection.upsert(
                        documents=[enriched_text],
                        metadatas=[chunk_metadata],
                        ids=[deterministic_id],
                    )
                    global_chunk_idx += 1
                    total_chunks += 1
                    file_chunk_count += 1

            print(f"[+] Upserted {file_chunk_count} chunks for {file_name}")

    print(f"\n[+] Ingestion complete. Total chunks upserted: {total_chunks}")


if __name__ == "__main__":
    run_ingestion()
