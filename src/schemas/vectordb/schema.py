from dataclasses import dataclass
from langchain_core.documents import Document

@dataclass
class Data:
    id: str
    vector: list[float]
    metadata: dict

    def __init__(self, id: str, vector: list[float], **metadata):
        self.id = id
        self.vector = vector
        self.metadata = metadata

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "vector": self.vector,
            **self.metadata,
        }