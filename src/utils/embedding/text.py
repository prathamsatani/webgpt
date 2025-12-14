from sentence_transformers import SentenceTransformer
from google import genai
import os

class LocalTextEmbedder:
    def __init__(self):
        self.model: SentenceTransformer = None
    
    def initialize(self, model_name: str, cache_dir: str, device: str):
        '''
        Initialize the embedder with a specific model.
        
        :param self: Instance of LocalTextEmbedder
        :param model_name: Name of the embedding model
        :type model_name: str
        :param cache_dir: Directory to cache the model
        :type cache_dir: str
        :param device: Device to run the model on (e.g., 'cpu', 'cuda')
        :type device: str
        '''
        if cache_dir and not os.path.exists(cache_dir):
            os.makedirs(cache_dir, exist_ok=True)
        
        self.model = SentenceTransformer(
            model_name_or_path=model_name,
            cache_folder=cache_dir,
            device=device,
        )

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        '''
        Embed a list of texts into vectors.
        
        :param self: Instance of LocalTextEmbedder
        :param texts: List of texts to be embedded
        :type texts: list[str]
        :return: List of embedded vectors
        :rtype: list[list[float]]
        '''
        return self.model.encode(texts).tolist()

    def terminate(self):
        '''
        Terminate the embedder and free up resources.
        
        :param self: Instance of LocalTextEmbedder
        '''
        self.model = None

class GeminiTextEmbedder:
    def __init__(self):
        self.client: genai.Client = None

    def initialize(self, api_key: str):
        self.client = genai.Client(api_key=api_key)
        
    def embed_texts(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT", output_dimensionality: int = 768) -> list[list[float]]:
        '''
        Embed a list of texts into vectors.
        
        :param self: Instance of LocalTextEmbedder
        :param texts: List of texts to be embedded
        :type texts: list[str]
        :return: List of embedded vectors
        :rtype: list[list[float]]
        '''
        response = self.client.models.embed_content(
            model="gemini-1.5-flash-embed-text-001",
            contents=texts,
            config=genai.types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=output_dimensionality
            )
        )
        return [embedding.embedding for embedding in response.data]
    
    def terminate(self):
        '''
        Terminate the embedder and free up resources.
        
        :param self: Instance of LocalTextEmbedder
        '''
        self.client = None