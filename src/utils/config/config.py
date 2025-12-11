import yaml
from typing import Optional, Dict
class Config:
    def __init__(self):
        with open("config.yaml", "r") as file:
            self.config: Dict = yaml.safe_load(file)
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)    

if __name__ == "__main__":
    config = Config()
    print(config.get("milvus")["host"])  # Example usage