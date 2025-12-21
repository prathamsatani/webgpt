from src.utils.config import Config
from src.utils.vectordb import VectorDB
from src.utils.embedding import LocalTextEmbedder
from typing import List

class Retrieve:
    def __init__(self):
        self.config = Config()
        self.vectordb = VectorDB()
        self.embedder = LocalTextEmbedder()
        
        self.vectordb.connect(
            host=self.config.get("milvus")["host"],
            port=self.config.get("milvus")["port"],
            db_name=self.config.get("milvus")["db_name"],
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
        filter: str = None, 
        search_params: dict = None,
        output_fields: List[str] = None
    ) -> List[dict]:
        results = self.vectordb.search_vectors(
            collection_name=self.config.get("milvus")["collection_name"],
            query_vectors=query_vectors,
            top_k=top_k,
            filter=filter,
            search_params=search_params,
            output_fields=output_fields
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
        return self.retrieve(query_vectors, top_k=top_k, filter=filter, search_params=search_params, output_fields=output_fields)

if __name__ == "__main__":
    import json
    retriever = Retrieve()
    sample_queries = ["What is the __slots__ method in Python?"]
    retrieved_results = retriever.retrieve_by_queries(sample_queries, top_k=10, output_fields=["source_url","text"])
    print(retrieved_results)