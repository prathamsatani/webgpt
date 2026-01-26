# WebGPT

**WebGPT** is a comprehensive Retrieval-Augmented Generation (RAG) system designed to ingest website content, process it into vector embeddings, and serve it via a specialized AI agent. It enables users to have a conversation with a website's content, ensuring accurate, context-aware responses without hallucinations.

## 🚀 Features

*   **Web Ingestion Engine**: Crawls websites, identifying and filtering relevant content.
*   **Intelligent Processing**: Cleans HTML, converts it to Markdown, and splits text into semantic chunks for optimal retrieval.
*   **Vector Search**: Uses **ChromaDB** and **Sentence Transformers** (`all-MiniLM-L6-v2`) for efficient local similarity search.
*   **Metadata Tracking**: Stores detailed ingestion metadata in **PostgreSQL** to prevent duplicate work and track content lineage.
*   **RAG Agent**: A specialized **Google Gemini** powered agent that answers user queries using *only* the retrieved context ("Descriptive Bound" rule).
*   **API-First Design**: Built with **FastAPI**, creating a robust backend for ingestion and retrieval operations.
*   **Observability**: Integrated with **Arize Phoenix** and **OpenInference** for tracing and debugging AI workflows.

## 🛠 Tech Stack

*   **Language**: Python 3.12+
*   **Web Framework**: FastAPI
*   **Vector Database**: ChromaDB
*   **Relational Database**: PostgreSQL (AsyncPG, SQLAlchemy)
*   **LLM Provider**: Google Gen AI (Gemini 2.5 Flash)
*   **Embeddings**: Sentence Transformers (Local)
*   **Crawling**: Requests, BeautifulSoup4

## 📋 Prerequisites

Before running the project, ensure you have the following installed:

1.  **Python 3.12** or higher.
2.  **PostgreSQL** database based on `config.yaml` (default: `localhost:5432`, user: `postgres`, db: `webgpt`).
3.  **Google AI Studio API Key** (for the Gemini model).

## ⚙️ Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/yourusername/webgpt.git
    cd webgpt
    ```

2.  **Install dependencies**:
    This project uses `pyproject.toml`. You can install dependencies using `pip`:
    ```bash
    pip install .
    ```

3.  **Environment Setup**:
    Check `config.yaml` to ensure configuration matches your environment.
    You may also use a `.env` file to override specific settings like the API key or logging level.
    
    Example `.env`:
    ```env
    LOGGING_LEVEL=DEBUG
    ```
    
    Ensure your `config.yaml` has the correct Google API Key or handle it via environment variables if the code supports it (currently `config.yaml` hardcodes an example key, **replace this**).

4.  **Database Migration**:
    Initialize the PostgreSQL database table using Alembic:
    ```bash
    alembic upgrade head
    ```

## 🔧 Configuration

The primary configuration file is `config.yaml`.

```yaml
google:
  ai_studio:
    api_key: "YOUR_API_KEY" # Replace with your actual key
    ...
chromadb:
  path: "./vectordb_data/"
  collection_name: "webgpt_data"
postgres:
  user: "postgres"
  password: "postgres"
  host: "localhost"
  port: 5432
  database: "webgpt"
...
```

## 🚀 Usage

### Starting the Server

Run the FastAPI application:

```bash
fastapi dev main.py
```
Or
```bash
uvicorn main:app --reload
```

The server will start at `http://127.0.0.1:8000`.

### API Interface

Visit `http://127.0.0.1:8000/docs` for the interactive Swagger UI.

#### Ingest a Website
**POST** `/ingest/ingest_site/`
```json
{
  "url": "https://example.com/documentation",
  "max_pages": 10
}
```
*   Crawls the URL (up to `max_pages`).
*   Converts content to markdown -> chunks -> vectors.
*   Stores vectors in ChromaDB and metadata in Postgres.

#### Retrieve Context
**POST** `/retrieve/one`
```json
{
  "query": "How do I install the software?",
  "top_k": 5
}
```
Returns the top 5 most relevant document chunks.

**POST** `/retrieve/batch`
Retrieves documents for a list of queries.

### Run the Agent
To run the RAG agent interactively (programmatic usage example):
*   Logic is located in `src/agents/rag_agent/agent.py`.
*   It utilizes the `Retrieve` class to fetch context and prompts Gemini to answer based *only* on that context.

## 📂 Project Structure

```
├── alembic/              # Database migrations
├── config.yaml           # App configuration
├── main.py               # Application entry point
├── pyproject.toml        # Dependencies and metadata
├── src/
│   ├── agents/           # AI Agents (RAG Agent)
│   ├── app/              # Application logic
│   │   ├── ingest/       # Ingestion service & API
│   │   └── retrieve/     # Retrieval service & API
│   ├── models/           # SQLAlchemy Database Models
│   ├── schemas/          # Pydantic Schemas
│   └── utils/            # Utilities (DB, Crawler, Embedder)
└── vectordb_data/        # Persistent vector storage
```

## 🤝 Contributing
Contributions are welcome! Please open an issue or submit a pull request.

## 📄 License
[MIT](LICENSE)
