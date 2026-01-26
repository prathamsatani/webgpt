from chromadb import PersistentClient, ClientAPI, Search, K, Knn
from chromadb.config import Settings
from datetime import datetime as dt 
import datetime
import logging
import os
from dotenv import load_dotenv
from src.schemas.vectordb import Data

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOGGING_LEVEL", "DEBUG"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("VectorDB")


class VectorDB:
    def __init__(self):
        self.client: ClientAPI = None
        logger.info("VectorDB instance created.")
    
    def connect(self, path: str):
        '''
        Connects to the vector database server.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        :param path: Path to the vector database server
        :type path: str
        :return: None
        :rtype: None
        '''
        try:
            self.client = PersistentClient(path=path)
            logger.info("Connected to VectorDB successfully.")
        except Exception as e:
            logger.exception(f"Failed to connect to VectorDB: {e}")
        
    def create_collection(
        self, 
        collection_name: str, 
        dimension: int
    ) -> bool:
        '''
        Creates a collection in the vector database.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        :param collection_name: Name of the collection to be created
        :type collection_name: str
        :param dimension: Dimension of the vectors in the collection
        :type dimension: int
        :return: True if the collection was created successfully, False otherwise
        :rtype: bool
        '''
        if not self.client:
            logger.error("VectorDB client is not connected.")
            return False

        try:
            self.client.create_collection(
                name=collection_name,
                metadata={
                    "created_at": dt.now(datetime.timezone.utc).isoformat(),
                    "dimension": dimension, 
                }
            )
            logger.info(f"Collection '{collection_name}' created successfully.")
            return True
        except ValueError as e:
            logger.warning(f"Collection '{collection_name}' already exists: {e}")
            return True
        except Exception as e:
            logger.exception(f"Failed to create collection '{collection_name}': {e}")
            return False
    
    def upsert_vectors(
        self,  
        collection_name: str,
        data: list[Data],
    ) -> dict | bool:
        '''
        Upserts vectors into the specified collection.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        :param data: List of Data objects to be upserted
        :type data: list[Data]
        :return: True if the upsert was successful, False otherwise
        :rtype: bool
        '''
        if not self.client:
            logger.error("VectorDB client is not connected.")
            return False

        try:
            collection = self.client.get_collection(collection_name)
            ids = [item.id for item in data]
            vectors = [item.vector for item in data]
            metadata = [item.metadata for item in data]
            
            collection.upsert(
                ids=ids,
                embeddings=vectors,
                metadatas=metadata
            )
            logger.info(f"Vectors upserted successfully into collection '{collection_name}'.")
            return {
                "collection_name": collection_name,
                "upsert_count": len(data)
            }
        except Exception as e:
            logger.exception(f"Failed to upsert vectors into collection '{collection_name}': {e}")
            return False
    
    def similarity_search(
        self, 
        collection_name: str,
        query_vectors: list, 
        top_k: int = 10,
    ) -> list | bool:
        '''
        Searches for similar vectors in the specified collection.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        :param query_vectors: List of query vectors
        :type query_vectors: list
        :param top_k: Number of top similar vectors to retrieve
        :type top_k: int
        :return: List of search results if successful, False otherwise
        :rtype: list | bool
        '''
        if not self.client:
            logger.error("VectorDB client is not connected.")
            return False

        try:
            collection = self.client.get_collection(collection_name)
            
            results = collection.query(
                query_embeddings=query_vectors,
                n_results=top_k,
            )
            logger.info(f"Search completed successfully in collection '{collection_name}'.")
            return results
        except Exception as e:
            logger.exception(f"Failed to search vectors in collection '{collection_name}': {e}")
            return False
    
    def delete_collection(self, collection_name: str) -> bool:
        '''
        Deletes the specified collection from the vector database.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        :param collection_name: Name of the collection to be deleted
        :type collection_name: str
        :return: True if the collection was deleted successfully, False otherwise
        :rtype: bool
        '''
        if not self.client:
            logger.error("VectorDB client is not connected.")
            return False

        try:
            self.client.delete_collection(collection_name)
            logger.info(f"Collection '{collection_name}' deleted successfully.")
            return True
        except Exception as e:
            logger.exception(f"Failed to delete collection '{collection_name}': {e}")
            return False

    def disconnect(self):
        '''
        Disconnects from the vector database server.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        '''
        try:
            self.client = None
            logger.info("Disconnected from VectorDB successfully.")
        except Exception as e:
            logger.exception(f"Failed to disconnect from VectorDB: {e}")

if __name__ == "__main__":
    vectordb = VectorDB()
    vectordb.connect(path="./vectordb_data")
    vectordb.create_collection(collection_name="webgpt_data", dimension=384)
    # vectordb.delete_collection(collection_name="webgpt_data")
    vectordb.disconnect()