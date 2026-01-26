from src.utils.config import Config
from src.utils.vectordb import VectorDB
from src.utils.embedding import LocalTextEmbedder
from typing import List
from fastapi import APIRouter, HTTPException, Request

class Retrieve:
    def __init__(self):
        self.config = Config()
        self.vectordb = VectorDB()
        self.embedder = LocalTextEmbedder()
        
        self.vectordb.connect(
            path=self.config.get("chromadb")["path"],
        )
        
        self.embedder.initialize(
            model_name=self.config.get("embedding")["local_model"]["embedding_model_name"],
            cache_dir=self.config.get("embedding")["local_model"]["embedding_model_cache_dir"],
            device=self.config.get("embedding")["local_model"]["device"],
        )
    
    def retrieve(
        self, 
        query_vectors: List[List[float]], 
        top_k: int = 5, 

    ) -> List[dict]:
        results = self.vectordb.similarity_search(
            collection_name=self.config.get("chromadb")["collection_name"],
            query_vectors=query_vectors,
            top_k=top_k,
        )
        return results

    def embed_queries(self, queries: List[str]) -> List[List[float]]:
        return self.embedder.embed_texts(queries)
    
    def retrieve_by_queries(
        self, 
        queries: List[str], 
        top_k: int = 5, 
        filter: str = None, 
        search_params: dict = None,
        output_fields: List[str] = None
    ) -> List[dict]:
        query_vectors = self.embed_queries(queries)
        return self.retrieve(query_vectors, top_k=top_k)

    def terminate(self):
        self.vectordb.disconnect()   
        self.embedder.terminate()
        self.config = None

api_router = APIRouter()
@api_router.post("/one")
async def retrieve_documents(request: Request, query: str, top_k: int = 5):
    service: Retrieve = request.app.state.retrieve_service
    try:
        results = service.retrieve_by_queries([query], top_k=top_k, output_fields=["text"])
        print("Retrieve Results:", results)
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print full stack trace to console
        raise HTTPException(
            status_code=500, 
            detail=f"{type(e).__name__}: {e}"  # Include exception type
        )

@api_router.post("/batch")
async def retrieve_documents_batch(request: Request, queries: List[str], top_k: int = 5):
    """
    Retrieve relevant documents for a batch of queries.

    :param queries: A list of user's questions or query strings.
    :type queries: List[str]
    :param top_k: The number of top relevant documents to retrieve for each query.
    :type top_k: int
    :return: A list of lists containing retrieved documents for each query.
    :rtype: List[List[dict]]
    """
    service: Retrieve = request.app.state.retrieve_service
    try:
        results = service.retrieve_by_queries(queries, top_k=top_k, output_fields=["text"])
        return results 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))