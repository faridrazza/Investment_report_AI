# Add this at the very top to verify installation
try:
    import langchain
except ImportError:
    raise ImportError("LangChain not installed! Run 'pip install langchain==0.3.18'")

from typing import Dict, List
import json
import os

# Import with proper error handling for Pydantic compatibility
try:
    from langchain_community.vectorstores import FAISS
    from langchain_openai import OpenAIEmbeddings
    from langchain_core.caches import BaseCache
    
    # Force model rebuilding for compatibility
    try:
        OpenAIEmbeddings.model_rebuild()
    except Exception as e:
        print(f"OpenAIEmbeddings model rebuild warning: {e}")
        
except ImportError as e:
    raise ImportError(f"Required LangChain components not available: {e}")

from backend.config import Config
from backend.services.market_service import MarketService

class VectorStore:
    def __init__(self):
        try:
            # Initialize embeddings with correct parameter name and error handling
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
            print(f"Vector store initialization error: {str(e)}")
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
                
                # Asset allocation details
                allocation_text = (
                    f"Asset allocation for {client_info.get('name')}: "
                    f"Equities {asset_allocation.get('equities', {}).get('percentage', 0)}% "
                    f"(${asset_allocation.get('equities', {}).get('value', 0):,.2f}), "
                    f"Fixed Income {asset_allocation.get('fixedIncome', {}).get('percentage', 0)}% "
                    f"(${asset_allocation.get('fixedIncome', {}).get('value', 0):,.2f}), "
                    f"Alternatives {asset_allocation.get('alternatives', {}).get('percentage', 0)}%, "
                    f"Cash {asset_allocation.get('cash', {}).get('percentage', 0)}%"
                )
                texts.append(allocation_text)
                metadatas.append({"client_id": client_info.get('id'), "type": "allocation"})
                
                # Holdings information  
                for holding in holdings:
                    holding_text = (
                        f"Top holding for {client_info.get('name')}: "
                        f"{holding.get('name')} ({holding.get('security')}) "
                        f"worth ${holding.get('value', 0):,.2f} "
                        f"({holding.get('weight', 0)}% of portfolio), "
                        f"gain: ${holding.get('gain', 0):,.2f}"
                    )
                    texts.append(holding_text)
                    metadatas.append({"client_id": client_info.get('id'), "type": "holding"})
            
            if texts:
                # Create vector store with error handling
                try:
                    self.vector_store = FAISS.from_texts(
                        texts=texts,
                        embedding=self.embeddings,
                        metadatas=metadatas
                    )
                    print(f"Successfully created vector store with {len(texts)} documents")
                except Exception as e:
                    print(f"Error creating FAISS vector store: {e}")
                    raise
            
        except Exception as e:
            print(f"Error in initialize_from_json: {str(e)}")
            raise ValueError(f"Failed to initialize vector store from JSON: {str(e)}")

    def search(self, query: str, client_id: str = None, k: int = 3) -> List[Dict]:
        """Search the vector store with optional client filtering"""
        if not self.vector_store:
            print("Vector store not initialized")
            return []
            
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
        
        try:
            os.makedirs(directory, exist_ok=True)
            self.vector_store.save_local(directory)
            print(f"Vector store saved to {directory}")
        except Exception as e:
            print(f"Error saving vector store: {e}")
            raise
        
    def load_from_disk(self, path: str):
        """Load vector store with explicit deserialization permission"""
        try:
            self.vector_store = FAISS.load_local(
                folder_path=path,
                embeddings=self.embeddings,
                allow_dangerous_deserialization=True  # Security override
            )
            print(f"Vector store loaded from {path}")
        except Exception as e:
            print(f"Error loading vector store from {path}: {e}")
            # Don't raise error here, just log it 