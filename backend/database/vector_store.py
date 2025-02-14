# Add this at the very top to verify installation
try:
    import langchain
except ImportError:
    raise ImportError("LangChain not installed! Run 'pip install langchain==0.1.0'")

from typing import Dict, List
import json
from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from backend.config import Config
import os
from backend.services.market_service import MarketService

class VectorStore:
    def __init__(self):
        try:
            # Initialize embeddings with correct parameter name
            self.embeddings = OpenAIEmbeddings(
                model=Config.EMBEDDING_MODEL,
                openai_api_key=Config.OPENAI_API_KEY,
                dimensions=1536  # Move dimensions to top-level parameter
            )
            self.vector_store = None
            
            # Try to load existing vector store with security override
            if os.path.exists(Config.VECTOR_STORE_PATH):
                self.load_from_disk(Config.VECTOR_STORE_PATH)
                
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAIEmbeddings: {str(e)}")

    def initialize_from_json(self, json_data: Dict):
        """Initialize vector store from client data"""
        try:
            texts = []
            metadatas = []
            
            for client in json_data.get("clients", []):
                # Create searchable text chunks with relevant client information
                client_info = client.get("clientInfo", {})
                portfolio_summary = client.get("portfolioSummary", {})
                asset_allocation = client.get("assetAllocation", {})
                
                client_text = (
                    f"Client {client_info.get('name')} (ID: {client_info.get('id')}) "
                    f"has a {client_info.get('accountType')} with a {client_info.get('riskProfile')} "
                    f"risk profile. Their portfolio value is ${portfolio_summary.get('totalValue', 0):,.2f}."
                )
                texts.append(client_text)
                metadatas.append({"client_id": client_info.get('id')})
                
                # Add detailed portfolio information
                portfolio_text = (
                    f"Portfolio details for {client_info.get('name')}: "
                    f"Asset allocation: Equities {asset_allocation.get('equities', {}).get('percentage')}%, "
                    f"Fixed Income {asset_allocation.get('fixedIncome', {}).get('percentage')}%, "
                    f"Alternatives {asset_allocation.get('alternatives', {}).get('percentage')}%, "
                    f"Cash {asset_allocation.get('cash', {}).get('percentage')}%."
                )
                texts.append(portfolio_text)
                metadatas.append({"client_id": client_info.get('id')})

            # Add market context embeddings
            market_text = MarketService.get_market_summary()
            texts.append(market_text)
            metadatas.append({"type": "market_context"})

            # Create new vector store
            self.vector_store = FAISS.from_texts(
                texts,
                self.embeddings,
                metadatas=metadatas
            )
            
            # Save to disk after initialization
            self.save_to_disk(Config.VECTOR_STORE_PATH)
            
        except Exception as e:
            raise ValueError(f"Failed to initialize vector store from JSON: {str(e)}")

    def search(self, query: str, k: int = 3) -> List[Dict]:
        """Search the vector store for relevant client information"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
            
        results = self.vector_store.similarity_search_with_score(query, k=k)
        return [(doc.page_content, doc.metadata, score) for doc, score in results]

    def save_to_disk(self, directory: str = "vector_store"):
        """Save the vector store to disk"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
        
        os.makedirs(directory, exist_ok=True)
        self.vector_store.save_local(directory)
        
    def load_from_disk(self, path: str):
        """Load vector store with explicit deserialization permission"""
        self.vector_store = FAISS.load_local(
            folder_path=path,
            embeddings=self.embeddings,
            allow_dangerous_deserialization=True  # Security override
        ) 