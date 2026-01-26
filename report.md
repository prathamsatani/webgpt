# WebGPT Project Report

## 1. Project Overview
**Name:** WebGPT
**Version:** 0.1.0
**Description:** A Retrieval-Augmented Generation (RAG) system designed to ingest website content, store it in a vector database, and provide a specialized knowledge assistant agent to answer queries based on the ingested content.
**Tech Stack:**
*   **Language:** Python 3.12+
*   **Web Framework:** FastAPI
*   **Vector Database:** ChromaDB
*   **Relational Database:** PostgreSQL (AsyncPG, SQLAlchemy)
*   **Embeddings:** Sentence Transformers (Local)
*   **LLM Integration:** Google Gen AI (Gemini), LangChain
*   **Observability:** Ariz Phoenix, OpenInference
*   **Web Crawling:** Beautiful Soup 4, Requests

## 2. Project Structure
The project follows a standard Python application structure:
*   `main.py`: The entry point for the FastAPI application.
*   `config.yaml`: Centralized configuration file.
*   `pyproject.toml`: Dependency management and project metadata.
*   `src/`: Contains the source code.
    *   `agents/`: Definitions for AI agents (e.g., `rag_agent`).
    *   `app/`: Core application logic, divided into `ingest` and `retrieve` modules.
    *   `models/`: SQLAlchemy data models (`models.py`).
    *   `schemas/`: Pydantic schemas (e.g., `vectordb`).
    *   `utils/`: Utility modules for configuration, vector DB, web crawling, embeddings, etc.
*   `tests/`: Test suite.
*   `alembic/`: Database migration scripts.

## 3. Configuration
Configuration is managed via `config.yaml` and environment variables. Key sections include:
*   **Google:** API key and model settings for Google AI Studio.
*   **Embedding:** Settings for the local embedding model (`all-MiniLM-L6-v2`) and cache directory.
*   **ChromaDB:** Path to the persistent data directory and collection name (`webgpt_data`).
*   **Text Splitter:** Chunk size (1000) and overlap (300) configuration.
*   **Postgres:** Database connection credentials.

## 4. Core Components

### 4.1 Ingestion System (`src/main/app/ingest`)
The ingestion process is handled by the `Ingest` class. It performs the following steps:
1.  **Web Crawling:** Uses `WebCrawler` to fetch HTML content from a given URL, respecting `robots.txt` and sitemaps. It filters out non-HTML assets.
2.  **HTML Cleaning:** Removes unwanted tags (scripts, styles, navs, etc.) using `BeautifulSoup`.
3.  **Markdown Conversion:** Converts cleaned HTML to Markdown using `Markdowner`.
4.  **Text Splitting:** Splits the Markdown content into chunks using `RecursiveCharacterTextSplitter` and `MarkdownHeaderTextSplitter`.
5.  **Embedding:** Generates embeddings for the text chunks using `LocalTextEmbedder` (Sentence Transformers).
6.  **Storage:** 
    *   Vectors and text chunks are stored in **ChromaDB**.
    *   Metadata (source URL, chunk count, timestamps) is stored in **PostgreSQL**.

### 4.2 Retrieval System (`src/main/app/retrieve`)
The retrieval process is handled by the `Retrieve` class:
*   **Query Embedding:** Converts user queries into vector embeddings using the same local model.
*   **Similarity Search:** Performs a k-nearest neighbor (k-NN) search in ChromaDB to find relevant text chunks.
*   **API:** Exposes endpoints to retrieve documents for single or batch queries.

### 4.3 RAG Agent (`src/agents/rag_agent`)
The project defines a `rag_agent` using `google.adk.agents.llm_agent.Agent`.
*   **Model:** `gemini-2.5-flash`
*   **Function:** Acts as a "High-Precision Knowledge Engine" that answers user queries strictly based on the retrieved context.
*   **Tools:** Uses a `get_retrieved_docs` tool which interfaces with the `Retrieve` service.
*   **Guardrails:** Explicitly instructed to avoid hallucination and refuse to answer if the context is insufficient.

### 4.4 Data Persistence
*   **VectorDB (`src/utils/vectordb`)**: Wraps the `chromadb` client for connection management, collection creation, and vector upsertion.
*   **PostgresDB (`src/utils/postgresdb`)**: Uses SQLAlchemy with `asyncpg` for asynchronous database operations. Manages `EmbeddedMetadata` records.

### 4.5 Web Crawler (`src/utils/webcrawler`)
A custom `WebCrawler` class handles HTTP requests and content parsing.
*   Checks for HTML content types.
*   Parses `robots.txt` to find sitemaps.
*   Cleans HTML by removing noise (ads, navigation, scripts).

## 5. API Endpoints
The FastAPI application (`main.py`) exposes the following endpoints:

*   **GET /health**: Returns the system status (`{"status": "healthy"}`).
*   **POST /retrieve/one**: Retrieve top-k documents for a single query.
*   **POST /retrieve/batch**: Retrieve top-k documents for a list of queries.
*   **(Inferred) /ingest**: Associated endpoints for triggering the ingestion process (via `src.app.ingest.api_router`).

## 6. Data Models
The `EmbeddedMetadata` SQL model tracks the ingestion history:
*   `id`: UUID
*   `base_url`: The root domain.
*   `source_url`: The specific page URL.
*   `number_of_chunks`: How many chunks were generated.
*   `chunked_at`: Timestamp of chunking.
*   `page_length`: Original length of the page.
*   `embedded_at`: Timestamp of embedding.
