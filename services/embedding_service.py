import json
import os
from pinecone import Pinecone, ServerlessSpec
from sentence_transformers import SentenceTransformer
import math
import sys

class EmbeddingsService:
    def __init__(self, pinecone_api_key: str, index_name: str):
        # Initialize Pinecone
        self.pc = Pinecone(api_key=pinecone_api_key)
        self.index_name = index_name
        self.index = self.pc.Index(index_name)
        
        # Initialize SentenceTransformer model
        self.model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    def generate_embeddings(self, sentences: list):
        """
        Generate embeddings for a list of sentences using the SentenceTransformer model.
        """
        embeddings = self.model.encode(sentences)
        print(f"Embedding length: {len(embeddings[0])}")  # This should print 384
        return embeddings

    def get_size_in_bytes(self, data):
        """
        Calculate the size of the data in bytes.
        """
        return sys.getsizeof(data) * 12

    def store_embeddings_in_pinecone(self, sentences: list):
        """
        Generate embeddings for sentences and store them in Pinecone with metadata in batches.
        
        Args:
            sentences (list): List of dictionaries containing "text" and metadata fields.
        """
        # Extract texts and metadata
        texts = [sentence["text"] for sentence in sentences]
        metadata_list = [
            {key: value for key, value in sentence.items() if key != "text"} 
            for sentence in sentences
        ]

        prefix_data = [sentence["company"] + '-' + sentence["type"] + '-' + sentence["source"] + '-' + str(sentence["page_number"]) for sentence in sentences]
        
        # Generate embeddings
        embeddings = self.generate_embeddings(texts)
        
        # Prepare data to store in Pinecone (vector, metadata)
        to_upsert = [
            {
                "id": prefix_data[i] + '-' + str(i),
                "values": embeddings[i].tolist(),
                "metadata": metadata_list[i]
            }
            for i in range(len(texts))
        ]

        # Batch and check size before sending to Pinecone
        current_batch = []
        current_size = 0
        batch_count = 0
        current_count = 0

        for vector in to_upsert:
            vector_size = self.get_size_in_bytes(vector)
            
            if current_size + vector_size > 3 * 1024 * 1024 or current_count > 990:  # 1.5MB limit
                # Send current batch
                self.index.upsert(vectors=current_batch)
                batch_count += 1
                print(f"Stored batch {batch_count} with {len(current_batch)} embeddings.")
                
                # Reset batch
                current_batch = []
                current_size = 0
                current_count = 0
            
            # Add vector to current batch
            current_batch.append(vector)
            current_size += vector_size
            current_count += 1

        # Send the last batch if not empty
        if current_batch:
            self.index.upsert(vectors=current_batch)
            batch_count += 1
            print(f"Stored batch {batch_count} with {len(current_batch)} embeddings.")

        print(f"Stored {len(sentences)} embeddings in Pinecone with metadata.")

'''
# Usage example:
# Initialize the service
pinecone_api_key = "pcsk_4kDbGF_TzcVnZwH9BiEFgAVkmwVCnQFZx2fcMS1QgZTcxJ53ZPbjLd34guwUYawgVvkDMw"
index_name = "documents"
embedding_service = EmbeddingsService(pinecone_api_key, index_name)

# Example sentences
sentences = [
    {
        "text": "This is an example sentence",
        "company": "ExampleCorp",
        "type": "Informational",
        "source": "ETimes",
        "url": "https://example.com/example-sentence",
        "page_number": 1
    },
    {
        "text": "Each sentence is converted",
        "company": "ConversionTech",
        "type": "Technical",
        "source": "Moneycontrol"
        "url": "https://conversiontech.com/sentence-conversion",
        "page_number": 2
    }
]
# Store embeddings in Pinecone
embedding_service.store_embeddings_in_pinecone(sentences)
'''

