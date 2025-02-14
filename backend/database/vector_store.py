# Add this at the very top to verify installation
try:
    import langchain
except ImportError:
    raise ImportError("LangChain not installed! Run 'pip install langchain==0.1.0'")

from typing import Dict, List
import json
from langchain_community.vectorstores import FAISS
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
        """Initialize vector store from client data with detailed financial information"""
        try:
            texts = []
            metadatas = []
            
            for client in json_data.get("clients", []):
                client_info = client.get("clientInfo", {})
                portfolio = client.get("portfolioSummary", {})
                holdings = client.get("topHoldings", [])
                asset_allocation = client.get("assetAllocation", {})
                
                # Basic client information
                client_text = (
                    f"Client {client_info.get('name')} (ID: {client_info.get('id')}) "
                    f"has a {client_info.get('accountType')} with a {client_info.get('riskProfile')} "
                    f"risk profile. Their portfolio value is ${portfolio.get('totalValue', 0):,.2f}."
                )
                texts.append(client_text)
                metadatas.append({"client_id": client_info.get('id')})
                
                # Detailed financial information
                financial_text = (
                    f"Financial details for {client_info.get('name')}: "
                    f"Total Value: ${portfolio.get('totalValue', 0):,.2f}, "
                    f"Beginning Balance: ${portfolio.get('beginningBalance', 0):,.2f}, "
                    f"Realized Gains: ${portfolio.get('realizedGains', 0):,.2f}, "
                    f"Unrealized Gains: ${portfolio.get('unrealizedGains', 0):,.2f}, "
                    f"Income Earned: ${portfolio.get('incomeEarned', 0):,.2f}, "
                    f"Total Gains: ${portfolio.get('realizedGains', 0) + portfolio.get('unrealizedGains', 0):,.2f}"
                )
                texts.append(financial_text)
                metadatas.append({"client_id": client_info.get('id'), "type": "financial"})
                
                # Holdings information with improved formatting
                if holdings:
                    holdings_text = f"Top holdings for {client_info.get('name')}:\n"
                    for holding in holdings:
                        holdings_text += (
                            f"- {holding.get('name')} ({holding.get('security')})\n"
                            f"  Value: ${holding.get('value', 0):,.2f}\n"
                            f"  Portfolio Weight: {holding.get('weight')}%\n"
                            f"  Gain: ${holding.get('gain', 0):,.2f}\n"
                        )
                    texts.append(holdings_text)
                    metadatas.append({"client_id": client_info.get('id'), "type": "holdings"})
                
                # Asset allocation information
                allocation_text = (
                    f"Asset allocation for {client_info.get('name')}: "
                    f"Equities: {asset_allocation.get('equities', {}).get('percentage')}%, "
                    f"Fixed Income: {asset_allocation.get('fixedIncome', {}).get('percentage')}%, "
                    f"Alternatives: {asset_allocation.get('alternatives', {}).get('percentage')}%, "
                    f"Cash: {asset_allocation.get('cash', {}).get('percentage')}%"
                )
                texts.append(allocation_text)
                metadatas.append({"client_id": client_info.get('id'), "type": "allocation"})

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

    def search(self, query: str, client_id: str = None, k: int = 3) -> List[Dict]:
        """Search the vector store with optional client filtering"""
        if not self.vector_store:
            raise ValueError("Vector store not initialized")
            
        try:
            # Clean and prepare the query
            query = query.lower().strip()
            
            # Get search results
            results = self.vector_store.similarity_search_with_score(query, k=k)
            
            # Filter results by client_id if provided
            if client_id:
                filtered_results = [
                    (doc, score) for doc, score in results
                    if doc.metadata.get('client_id') == client_id
                ]
                results = filtered_results if filtered_results else results[:1]
            
            return [(doc.page_content, doc.metadata, score) for doc, score in results]
            
        except Exception as e:
            print(f"Search error: {str(e)}")
            return []

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