class CharacterTextSplitter:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 0, separator: str = "\n"):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator
    
    def split_text(self, text: str) -> list:
        '''
        Docstring for split_text
        
        :param self: Description
        :param text: Description
        :type text: str
        :return: Description
        :rtype: list
        '''
        non_overlapping_chunks = []
        for i in range(stop=len(text), step=self.chunk_size):
            non_overlapping_chunks.append()