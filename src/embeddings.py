### generate embeddings ##
import os
from typing import List
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()




class EmbeddingGenerator:

    def __init__(self):
        ## Use the embedding-specific endpoint ##
        load_dotenv()

        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_EMBEDDING_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_EMBEDDING_ENDPOINT")
        )
        self.deployment = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT")


    def generate_embedding(self, text: str) -> List[float]:
        response = self.client.embeddings.create(
            input=text,
            model=self.deployment
        )
        return response.data[0].embedding




    def generate_batch_embeddings(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = self.client.embeddings.create(
                input=batch,
                model=self.deployment
            )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

            print(f"Processed {min(i + batch_size, len(texts))}/{len(texts)} embeddings")

        return embeddings