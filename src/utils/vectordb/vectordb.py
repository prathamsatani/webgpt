from pymilvus import MilvusClient
import logging
import os
from utils.config import Config
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOGGING_LEVEL", "DEBUG"),
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
)
logger = logging.getLogger("VectorDB")


class VectorDB:
    def __init__(self, host: str, port: str):
        self.config = Config()  
        self.client = MilvusClient(
            host=self.config.get("milvus")["host"], 
            port=self.config.get("milvus")["port"]
        )
        logger.info("VectorDB instance created.")
        
    def create_collection(
        self, 
        collection_name: str, 
        schema: dict, 
        dimension: int
    ) -> bool:
        '''
        Creates a collection in the vector database.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        :param collection_name: Name of the collection to be created
        :type collection_name: str
        :param schema: schema of the collection
        :type schema: dict
        :param dimension: Dimension of the vectors in the collection
        :type dimension: int
        :return: True if the collection was created successfully, False otherwise
        :rtype: bool
        '''
        if self.client.has_collection(collection_name):
            logger.info(f"Collection '{collection_name}' already exists.")
            return True
        
        try:
            self.client.create_collection(
                collection_name=collection_name,
                schema=schema,
                dimension=dimension
            )
            logger.info(f"Collection '{collection_name}' created successfully.")
            return True
        except Exception as e:
            logger.exception(f"Failed to create collection '{collection_name}': {e}")
            return False
    
    def upsert_vectors(
        self, 
        collection_name: str, 
        vectors: list, 
        ids: list = None,
        **metadata
    ) -> dict | bool:
        '''
        Upserts vectors into the specified collection.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        :param collection_name: Name of the collection to upsert vectors into
        :type collection_name: str
        :param vectors: List of vectors to be upserted
        :type vectors: list
        :param ids: Optional list of IDs for the vectors
        :type ids: list, optional
        :return: True if the upsert was successful, False otherwise
        :rtype: bool
        '''
        if not self.client.has_collection(collection_name):
            logger.error(f"Collection '{collection_name}' does not exist.")
            return False
        try:
            self.client.upsert(
                collection_name=collection_name,
                vectors=vectors,
                ids=ids,
                **metadata
            )
            logger.info(f"Vectors upserted successfully into collection '{collection_name}'.")
            return {
                "collection_name": collection_name,
                "num_vectors_upserted": len(vectors)
            }
        except Exception as e:
            logger.exception(f"Failed to upsert vectors into collection '{collection_name}': {e}")
            return False
    
    def insert_vectors(
        self, 
        collection_name: str, 
        vectors: list, 
        ids: list = None,
        **metadata
    ) -> dict | bool:
        '''
        Inserts vectors into the specified collection.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        :param collection_name: Name of the collection to insert vectors into
        :type collection_name: str
        :param vectors: List of vectors to be inserted
        :type vectors: list
        :param ids: Optional list of IDs for the vectors
        :type ids: list, optional
        :return: True if the insert was successful, False otherwise
        :rtype: bool
        '''
        if not self.client.has_collection(collection_name):
            logger.error(f"Collection '{collection_name}' does not exist.")
            return False
        try:
            self.client.insert(
                collection_name=collection_name,
                vectors=vectors,
                ids=ids,
                **metadata
            )
            logger.info(f"Vectors inserted successfully into collection '{collection_name}'.")
            return {
                "collection_name": collection_name,
                "num_vectors_inserted": len(vectors)
            }
        except Exception as e:
            logger.exception(f"Failed to insert vectors into collection '{collection_name}': {e}")
            return False
    
    def search_vectors(
        self, 
        collection_name: str, 
        query_vectors: list, 
        top_k: int = 10,
        **search_params
    ) -> list | bool:
        '''
        Searches for similar vectors in the specified collection.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        :param collection_name: Name of the collection to search in
        :type collection_name: str
        :param query_vectors: List of query vectors
        :type query_vectors: list
        :param top_k: Number of top similar vectors to retrieve
        :type top_k: int
        :return: List of search results if successful, False otherwise
        :rtype: list | bool
        '''
        if not self.client.has_collection(collection_name):
            logger.error(f"Collection '{collection_name}' does not exist.")
            return False
        try:
            results = self.client.search(
                collection_name=collection_name,
                data=query_vectors,
                limit=top_k,
                **search_params
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
        if not self.client.has_collection(collection_name):
            logger.error(f"Collection '{collection_name}' does not exist.")
            return False
        try:
            self.client.drop_collection(collection_name)
            logger.info(f"Collection '{collection_name}' deleted successfully.")
            return True
        except Exception as e:
            logger.exception(f"Failed to delete collection '{collection_name}': {e}")
            return False
    
    def collection_exists(self, collection_name: str) -> bool:
        '''
        Checks if the specified collection exists in the vector database.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        :param collection_name: Name of the collection to check
        :type collection_name: str
        :return: True if the collection exists, False otherwise
        :rtype: bool
        '''
        try:
            exists = self.client.has_collection(collection_name)
            logger.info(f"Collection '{collection_name}' existence check: {exists}.")
            return exists
        except Exception as e:
            logger.exception(f"Failed to check existence of collection '{collection_name}': {e}")
            return False
    
    def get_collection_stats(self, collection_name: str) -> dict | bool:
        '''
        Retrieves statistics for the specified collection.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        :param collection_name: Name of the collection to get statistics for
        :type collection_name: str
        :return: Dictionary of collection statistics if successful, False otherwise
        :rtype: dict | bool
        '''
        if not self.client.has_collection(collection_name):
            logger.error(f"Collection '{collection_name}' does not exist.")
            return False
        try:
            stats = self.client.get_collection_stats(collection_name)
            logger.info(f"Retrieved stats for collection '{collection_name}'.")
            return stats
        except Exception as e:
            logger.exception(f"Failed to get stats for collection '{collection_name}': {e}")
            return False
    
    def close(self):
        '''
        Closes the connection to the vector database.
        
        :param self: Instance of the VectorDB class
        :type self: VectorDB
        '''
        try:
            self.client.close()
            logger.info("Connection to VectorDB closed successfully.")
        except Exception as e:
            logger.exception(f"Failed to close connection to VectorDB: {e}")