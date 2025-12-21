from src.schemas.vectordb import Data
from src.utils.markdowner import Markdowner
from src.utils.webcrawler import WebCrawler
from src.utils.vectordb import VectorDB
from src.utils.embedding.text import LocalTextEmbedder
from src.utils.postgresdb import PostgresDB
from src.models import EmbeddedMetadata
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
        self.postgresdb = PostgresDB()
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
        
        self.postgresdb.connect(
            user=self.config.get("postgres")["user"],
            password=self.config.get("postgres")["password"],
            host=self.config.get("postgres")["host"],
            port=self.config.get("postgres")["port"],
            database=self.config.get("postgres")["database"]
        )
        
        logging.info("Ingest instance created.")

    def convert_site_to_chunks(self, url: str, max_pages: int, exclude_pages: List[str]) -> Optional[List[Dict[str, any]]]:
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
            exclude_pages=exclude_pages
        )
        if not site_content:
            logging.warning("No site content available for ingestion.")
            return None

        markdowned_pages = []
        for page in site_content:
            markdowned_pages.append(
                {
                    "markdown": self.markdowner.convert_to_markdown(page["html"]),
                    "metadata": {
                        "source_url": page["url"],
                        "length": len(page["html"]),
                        "ingested_at": datetime.datetime.now(datetime.timezone.utc),
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

    async def get_ingested_urls(self, filter: EmbeddedMetadata) -> Optional[List[str]]:
        '''
        Retrieve ingested URLs based on the provided filter.
        
        :param self: Instance of the Ingest class
        :param base_url: Base URL to filter the ingested URLs
        :type base_url: str
        :return: List of ingested URLs or None if an error occurs
        :rtype: Optional[List[str]]
        '''
        try:
            retval = await self.postgresdb.fetch_all(filter)
            if retval:
                retval = [item.to_dict()["source_url"] for item in retval]
            
            return retval
        except Exception as e:
            print(f"Failed to fetch ingested metadata: {e}")

    async def save_ingested_metadata(self, metadata: List[EmbeddedMetadata]):
        '''
        Docstring for save_ingested_metadata
        
        :param self: Description
        :param metadata: Description
        :type metadata: List[EmbeddedMetadata]
        '''
        try:
            status = await self.postgresdb.insert(metadata)
            return status
        except Exception as e:
            print(f"Failed to save ingested metadata: {e}")

    async def ingest_site(self, url: str, max_pages: int) -> Optional[List[Dict[str, any]]]:
        ingested_metadata = await self.get_ingested_urls(EmbeddedMetadata(base_url=url))
        chunked_site = self.convert_site_to_chunks(url, max_pages, exclude_pages=ingested_metadata or [])
        if not chunked_site or len(chunked_site) == 0:
            logging.warning("No chunked site data available for ingestion.")
            return {
                "ingested_url": url,
                "total_pages": 0,
                "total_chunks": 0
            }
        data: list[Data] = []
        insert_metadata = []
        try:
            for page in chunked_site:
                embeddings = self.embedder.embed_texts(
                    [doc.page_content for doc in page["splits"]]
                )
                for idx, embedding in enumerate(embeddings):
                    if page["metadata"]["source_url"] not in ingested_metadata:
                        id = str(uuid4())
                        data.append(
                            Data(
                                id=id,
                                vector=embedding,
                                **{
                                    "source_url": page["metadata"]["source_url"],
                                    "ingested_at": page["metadata"]["ingested_at"].isoformat(),
                                    "text": page["splits"][idx].page_content,
                                    "chunk_length": len(page["splits"][idx].page_content),
                                }
                            )
                        )
                    
                insert_metadata.append({
                    "id": str(uuid4()),
                    "base_url": url,
                    "source_url": page["metadata"]["source_url"],
                    "number_of_chunks": len(page["splits"]),
                    "chunked_at": page["metadata"]["ingested_at"],
                    "page_length": page["metadata"]["length"],
                    "embedded_at": datetime.datetime.now(datetime.timezone.utc),
                })
                
        except Exception as e:
            logging.error(f"Failed while processing chunks for embedding: {page['metadata']['source_url']}, Error: {e}, Total Processed Chunks: {len(data)}")
        finally:
            logging.info(f"Total chunks prepared for upsert: {len(data)}")
            try:        
                retval = self.vectordb.upsert_vectors(
                    collection_name=self.config.get("milvus")["collection_name"],
                    data=[item.to_dict() for item in data]
                )
                if not retval:
                    logging.error("Upsert operation returned no result.")
                    return None
                logging.info("Vectors upserted successfully.")
            
                save_status = await self.save_ingested_metadata(
                    [EmbeddedMetadata(**metadata) for metadata in insert_metadata]
                )
                if save_status != True:
                    raise RuntimeError("Could not save ingested metadata. Aborting.")
            except Exception as e:
                logging.error(f"Failed to upsert vectors: {e}")
                return None
            
        return {
            "ingested_url": url,
            "total_pages": len(chunked_site),
            "total_chunks": len(data)
        }        
        
    async def terminate(self):
        '''
        Terminate the Ingest service and free up resources.
        
        :param self: Instance of Ingest
        '''
        logging.info("Terminating Ingest service and freeing resources.")
        self.embedder.terminate()
        self.vectordb.disconnect()
        await self.postgresdb.close()
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
        result = await service.ingest_site(url, max_pages)
        if result is None:
            raise HTTPException(status_code=500, detail="Ingestion failed.")
        return {"status": "success", "info": result}
    except Exception as e:
        logging.error(f"Error in ingestion endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))
