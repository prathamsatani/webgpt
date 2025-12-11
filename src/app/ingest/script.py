from src.utils.markdowner import Markdowner
from src.utils.webcrawler import WebCrawler
from fastapi import APIRouter, HTTPException
from google import genai
from langchain_core.documents import Document
from typing import List, Dict, Optional
import logging
import os
import datetime
from src.utils.config import Config
from dotenv import load_dotenv
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

load_dotenv()

# --------------------------
# Logging Configuration
# --------------------------
logging.basicConfig(
    level=os.getenv("LOGGING_LEVEL", "DEBUG"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)


class Ingest:
    def __init__(self):
        self.config = Config()
        self.webcrawler = WebCrawler()
        self.markdowner = Markdowner()
        self.google_genai = genai.Client(
            api_key=self.config.get("google")["ai_studio"]["api_key"]
        
        )
        self.md_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[
                ("#", "Header 1"),
                ("##", "Header 2"),
                ("###", "Header 3"),
                ("####", "Header 4"),
            ],
        )
        
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.get("text_splitter")["chunk_size"],
            chunk_overlap=self.config.get("text_splitter")["chunk_overlap"],
            separators=self.config.get("text_splitter")["separators"],
        )
        
        logging.info("Ingest instance created.")

    def ingest_site(self, url: str, max_pages: int) -> Optional[List[Dict[str, any]]]:
        """
        Ingest a website by crawling, cleaning HTML, and converting to Markdown.

        :param self: Ingest instance
        :param url: URL of the website to ingest
        :type url: str
        :return: List of dictionaries containing markdown content and metadata
        :rtype: List[Dict[str, any]] | None
        """
        logging.info(f"Starting ingestion for site: {url}")

        site_content = self.webcrawler.get_website_content(
            url,
            exclude_tags=[
                "a",
                "img",
                "style",
                "script",
                "nav",
                "form",
                "header",
                "head",
            ],
            limit=max_pages,
        )
        if not site_content:
            logging.error("Failed to retrieve site content.")
            return None

        markdowned_pages = []
        for page in site_content:
            markdowned_pages.append(
                {
                    "markdown": self.markdowner.convert_to_markdown(page["html"]),
                    "metadata": {
                        "source_url": page["url"],
                        "length": len(page["html"]),
                        "ingested_at": datetime.datetime.now(
                            datetime.timezone.utc
                        ).isoformat(),
                    },
                }
            )

        splitted_pages = []
        for mp in markdowned_pages:
            md_splits = self.md_splitter.split_text(mp["markdown"])
            text_splits: list[Document] = self.text_splitter.split_documents(md_splits)
            mp["metadata"]["num_splits"] = len(text_splits)
            splitted_pages.append(
                {
                    "splits": text_splits,
                    "metadata": mp["metadata"],
                }
            )
        
        return splitted_pages

if __name__ == "__main__":
    ingest_instance = Ingest()
    test_url = "https://benhoyt.com/"
    result = ingest_instance.ingest_site(test_url, max_pages=5)
    if result:
        for page in result:
            logging.info(f"Ingested page metadata: {page['metadata']}")
    else:
        logging.error("Ingestion failed.")