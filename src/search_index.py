 ## Azure AI Search index setup and management. ###
import os
from typing import List, Dict
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
)
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()





class AzureSearchIndexManager:
    ## Manage Azure AI Search index for SOPs.##

    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.key = os.getenv("AZURE_SEARCH_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX_NAME")

        self.credential = AzureKeyCredential(self.key)
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )



    def create_index(self, embedding_dimensions: int = 1536):
         ### Create search index with vector search capability. ###

        # Define fields
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="content", type=SearchFieldDataType.String),
            SearchableField(name="sop_number", type=SearchFieldDataType.String, filterable=True),
            SearchableField(name="title", type=SearchFieldDataType.String),
            SearchableField(name="section_type", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="version", type=SearchFieldDataType.String),
            SimpleField(name="filename", type=SearchFieldDataType.String),
            SimpleField(name="effective_date", type=SearchFieldDataType.String),
            SearchField(
                name="content_vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=embedding_dimensions,
                vector_search_profile_name="default-vector-profile"
            ),
        ]

        ## Configure vector search ##
        vector_search = VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="default-vector-profile",
                    algorithm_configuration_name="hnsw-config"
                )
            ],
            algorithms=[
                HnswAlgorithmConfiguration(name="hnsw-config")
            ]
        )

        #### Create index ###
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            vector_search=vector_search
        )

        result = self.index_client.create_or_update_index(index)
        print(f"Index '{result.name}' created successfully")
        return result





    def upload_documents(self, documents: List[Dict]):
         ### Upload documents to the search index.###
        search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )

        result = search_client.upload_documents(documents=documents)
        print(f"Uploaded {len(documents)} documents")
        return result


    def delete_index(self):
         ### Delete the index if it exists. ####
        try:
            self.index_client.delete_index(self.index_name)
            print(f"Index '{self.index_name}' deleted")
        except Exception as e:
            print(f"Could not delete index: {e}")