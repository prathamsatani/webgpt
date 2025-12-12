from src.utils.config import Config
from sentence_transformers import SentenceTransformer
from google import genai
import os

class LocalTextEmbedder:
    def __init__(self):
        self.config = Config()
        
        if not os.path.exists(self.config.get("embedding")["local_model"]["embedding_model_cache_dir"]):
            os.makedirs(self.config.get("embedding")["local_model"]["embedding_model_cache_dir"])
        
        self.model = SentenceTransformer(
            model_name_or_path=self.config.get("embedding")["local_model"]["embedding_model_name"],
            cache_folder=self.config.get("embedding")["local_model"]["embedding_model_cache_dir"],
            device=self.config.get("embedding")["local_model"]["device"],
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

class GeminiTextEmbedder:
    def __init__(self):
        self.config = Config()
        self.client = genai.Client(
            api_key=self.config.get("google")["ai_studio"]["api_key"]
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
        response = self.client.models.embed_content(
            model="gemini-1.5-flash-embed-text-001",
            contents=texts,
            config=genai.types.EmbedContentConfig(
                task_type=self.config.get("google")["ai_studio"]["embedding_task_type"],
                output_dimensionality=self.config.get("google")["ai_studio"]["embedding_output_dimensionality"]
            )
        )
        return [embedding.embedding for embedding in response.data]