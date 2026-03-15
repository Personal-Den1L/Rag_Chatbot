import re

import bs4
import chromadb
from markdownify import markdownify as md
from langchain_community.document_loaders import SitemapLoader
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
    embedding_function=embedding_fn,
)

allow_patterns = [
    r"^https://daiict\.ac\.in/(about-us|founder|president|director|programs-of-study|btech.*|mtech.*|msc.*|mdes.*|phd.*|admissions.*|admission-.*|undergraduate-admissions.*|academic-calendar|policies|grievance-redressal-cell|internal-complaint-committee|infrastructure|resource-centre|halls-residence|food-court|medical-facility|sports-complex|placements|faculty.*|academic-areas|research-overview|deans-office|board-governors|academic-council|why-choose-da-iict)"
]


def custom_parsing(soup: bs4.BeautifulSoup) -> str:
    content = soup.find("main") or soup.find(class_="region-content")
    if content:
        return str(content)
    return ""


def run_web_ingestion() -> None:
    _ = re.compile(allow_patterns[0])

    loader = SitemapLoader(
        web_path="https://daiict.ac.in/sitemap.xml",
        filter_urls=allow_patterns,
        parsing_function=custom_parsing,
        is_local=False,
    )
    docs = loader.load()

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    header_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=600,
        chunk_overlap=100,
    )

    global_chunk_idx = 1

    for doc in docs:
        if not doc.page_content or not doc.page_content.strip():
            continue

        markdown_text = md(doc.page_content, heading_style="ATX")
        header_chunks = header_splitter.split_text(markdown_text)

        for header_chunk in header_chunks:
            smaller_chunks = text_splitter.split_text(header_chunk.page_content)

            for chunk_text in smaller_chunks:
                chunk_text = chunk_text.strip()
                if not chunk_text:
                    continue

                source_url = doc.metadata.get("source", "web")
                deterministic_id = f"{source_url.split('/')[-1]}_chunk_{global_chunk_idx}"
                enriched_text = f"Source URL: {source_url}\nText:\n{chunk_text}"
                chunk_metadata = {
                    "source": source_url,
                    "type": "web",
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


if __name__ == "__main__":
    run_web_ingestion()
