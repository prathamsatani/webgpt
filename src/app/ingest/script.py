from src.schemas.vectordb import Data
from src.utils.markdowner import Markdowner
from src.utils.webcrawler import WebCrawler
from src.utils.vectordb import VectorDB
from src.utils.embedding.text import LocalTextEmbedder
from fastapi import APIRouter, HTTPException, Request
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
from uuid import uuid4
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
        self.vectordb = VectorDB()
        self.embedder = LocalTextEmbedder()
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
        
        self.embedder.initialize(
            model_name=self.config.get("embedding")["local_model"]["embedding_model_name"],
            cache_dir=self.config.get("embedding")["local_model"]["embedding_model_cache_dir"],
            device=self.config.get("embedding")["local_model"]["device"],
        )
        
        self.vectordb.connect(
            host=self.config.get("milvus")["host"],
            port=self.config.get("milvus")["port"],
            db_name=self.config.get("milvus")["db_name"],
        )
        
        logging.info("Ingest instance created.")

    def convert_site_to_chunks(self, url: str, max_pages: int) -> Optional[List[Dict[str, any]]]:
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
                        "ingested_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
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

    def ingest_site(self, url: str, max_pages: int) -> Optional[List[Dict[str, any]]]:
        chunked_site = self.convert_site_to_chunks(url, max_pages)
        if not chunked_site:
            logging.error("Site conversion to chunks failed.")
            return None
        
        data: list[Data] = []
        insert_metadata = []
        try:
            for page in chunked_site:
                embeddings = self.embedder.embed_texts(
                    [doc.page_content for doc in page["splits"]]
                )
                for idx, embedding in enumerate(embeddings):
                    id = str(uuid4())
                    data.append(
                        Data(
                            id=id,
                            vector=embedding,
                            metadata={
                                "source_url": page["metadata"]["source_url"],
                                "ingested_at": page["metadata"]["ingested_at"],
                                "text": page["splits"][idx].page_content,
                                "chunk_length": len(page["splits"][idx].page_content),
                            }
                        )
                    )
                insert_metadata.append({
                    "source_url": page["metadata"]["source_url"],
                    "num_chunks": len(page["splits"]),
                    "chunked_at": page["metadata"]["ingested_at"],
                    "page_length": page["metadata"]["length"],
                    "embedded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                })
        except Exception as e:
            logging.error(f"Failed while processing chunks for embedding: {page['metadata']['source_url']}, Error: {e}, Total Processed Chunks: {len(data)}")
        finally:
            logging.info(f"Total chunks prepared for upsert: {len(data)}")
            try:        
                retval = self.vectordb.upsert_vectors(
                    collection_name=self.config.get("milvus")["collection_name"],
                    data=data
                )
                if not retval:
                    logging.error("Upsert operation returned no result.")
                    return None
                logging.info("Vectors upserted successfully.")
            except Exception as e:
                logging.error(f"Failed to upsert vectors: {e}")
                return None
            
        return {
            "ingested_url": url,
            "total_pages": len(chunked_site),
            "total_chunks": len(data)
        }        
        
    def terminate(self):
        '''
        Terminate the Ingest service and free up resources.
        
        :param self: Instance of Ingest
        '''
        logging.info("Terminating Ingest service and freeing resources.")
        self.embedder.terminate()
        self.vectordb.disconnect()
        self.webcrawler = None
        self.markdowner = None
        self.md_splitter = None
        self.text_splitter = None
        self.config = None

api_router = APIRouter()
@api_router.post("/ingest_site/")
async def ingest_site_endpoint(request: Request, url: str, max_pages: int | None = None):
    service: Ingest = request.app.state.ingest_service
    try:
        result = service.ingest_site(url, max_pages)
        if result is None:
            raise HTTPException(status_code=500, detail="Ingestion failed.")
        return {"status": "success", "info": result}
    except Exception as e:
        logging.error(f"Error in ingestion endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
