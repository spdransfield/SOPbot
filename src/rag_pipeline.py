"""RAG pipeline for querying SOPs."""
import os
from typing import List, Dict
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv
from src.embeddings import EmbeddingGenerator

load_dotenv()


class SOPRAGPipeline:
     ## complete RAG pipeline for SOP queries. ##



    def __init__(self):
        ## Azure Search setup ##
        self.search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.search_key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

        self.search_client = SearchClient(
            endpoint=self.search_endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.search_key)
        )

        ## Embedding generator ##
        self.embedding_generator = EmbeddingGenerator()

        ## Azure OpenAI setup for GPT ##
        self.openai_client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")




    def retrieve_documents(self, query: str, top_k: int = 3) -> List[Dict]:
         ### Retrieve relevant documents using vector search ###

        ## Generate query embedding #
        query_vector = self.embedding_generator.generate_embedding(query)

        ### Create vector query ##
        vector_query = VectorizedQuery(
            vector=query_vector,
            k_nearest_neighbors=top_k,
            fields="content_vector"
        )

        ### Execute search ##
        results = self.search_client.search(
            search_text=query,
            vector_queries=[vector_query],
            select=["content", "sop_number", "title", "section_type"],
            top=top_k
        )

        ### Format results ##
        documents = []
        for result in results:
            documents.append({
                "content": result["content"],
                "sop_number": result.get("sop_number", "N/A"),
                "title": result.get("title", "N/A"),
                "section": result.get("section_type", "N/A"),
                "score": result.get("@search.score", 0)
            })

        return documents






    def generate_answer(self, query: str, context_docs: List[Dict]) -> str:
        """Generate answer using retrieved context."""

        ### Build context from retrieved documents ##
        context = "\n\n".join([
            f"[SOP {doc['sop_number']} - {doc['title']}]\n{doc['content']}"
            for doc in context_docs
        ])

        ### Create system message ##
        system_message = """You are a helpful assistant that answers questions about Clinical Research Enterprise (CRE) Standard Operating Procedures (SOPs).





Instructions:
- Answer based ONLY on the provided SOP context
- Cite the SOP number when providing information
- If the answer isn't in the context, say so clearly
- Be concise and specific
- Use bullet points for procedures/steps"""

        ## Create user message#
        user_message = f"""Context from SOPs:
{context}

Question: {query}

Please provide a clear, accurate answer based on the SOP context above."""

        ## Generate response ###
        response = self.openai_client.chat.completions.create(
            model=self.deployment_name,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0.3,
            max_tokens=1000
        )

        return response.choices[0].message.content




    def query(self, question: str, top_k: int = 3) -> Dict:
         ## Complete RAG query pipeline. ##

        ## Retrieve relevant documents ###
        print(f"Retrieving documents for: {question}")
        documents = self.retrieve_documents(question, top_k=top_k)

        if not documents:
            return {
                "answer": "I couldn't find relevant information in the SOPs to answer your question.",
                "sources": []
            }

        ## Generate answer #
        print("Generating answer...")
        answer = self.generate_answer(question, documents)

        ### Format sources #
        sources = [
            f"SOP {doc['sop_number']}: {doc['title']} ({doc['section']})"
            for doc in documents
        ]

        return {
            "answer": answer,
            "sources": sources,
            "retrieved_docs": documents
        }