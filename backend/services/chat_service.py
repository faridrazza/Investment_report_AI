from typing import Dict, List
from langchain_community.chat_models import ChatOpenAI
from langchain_community.chains import ConversationalRetrievalChain
from langchain_community.memory import ConversationBufferMemory
from langchain_core.messages import HumanMessage
from backend.config import Config
from backend.database.vector_store import VectorStore
from datetime import datetime
from dotenv import load_dotenv
from backend.services.market_service import MarketService

load_dotenv()

class ChatService:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        self.model = ChatOpenAI(
            model_name=Config.MODEL_NAME,
            openai_api_key=Config.OPENAI_API_KEY,
            temperature=0.7
        )
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.chain = ConversationalRetrievalChain.from_llm(
            llm=self.model,
            retriever=self.vector_store.vector_store.as_retriever(),
            memory=self.memory,
            verbose=True
        )

    async def process_message(self, message: str) -> str:
        """Process user message and return AI response"""
        response = await self.chain.ainvoke({
            "question": message,
            "chat_history": self.memory.chat_memory.messages
        })
        return response["answer"]

    async def get_stock_recommendation(self, symbol: str) -> Dict:
        """Generate stock recommendation with market data"""
        market_data = await MarketService().get_stock_data(symbol)
        prompt = f"""
        Analyze {symbol} with current data: {market_data}
        1. Current market conditions
        2. Historical performance
        3. Risk factors
        4. Market sentiment
        Provide buy/hold/sell recommendation with rationale.
        """
        response = await self.model.ainvoke(prompt)
        return {
            "symbol": symbol,
            "recommendation": response.content,
            "market_data": market_data,
            "timestamp": datetime.now().isoformat()
        }

    @classmethod
    def generate_analysis(cls, prompt: str, vector_store: VectorStore) -> Dict:
        """Generate investment analysis using OpenAI"""
        try:
            instance = cls(vector_store=vector_store)
            response = instance.model.invoke([HumanMessage(content=prompt)])
            content = response.content
            
            sections = {}
            current_section = None
            current_content = []
            
            print("Raw AI Response:", content)  # Debug log
            
            for line in content.split('\n'):
                line = line.strip()
                lower_line = line.lower()
                
                if 'executive summary:' in lower_line:
                    current_section = 'executive_summary'
                    current_content = []
                elif 'performance analysis:' in lower_line:
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'performance_analysis'
                    current_content = []
                elif 'asset allocation analysis:' in lower_line:
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'allocation_analysis'
                    current_content = []
                elif 'key observations:' in lower_line:
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'key_observations'
                    current_content = []
                elif 'recommendations:' in lower_line:
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'recommendations'
                    current_content = []
                elif 'holdings analysis:' in lower_line:
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'holdings_analysis'
                    current_content = []
                elif 'historical analysis:' in lower_line:
                    if current_section:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'historical_analysis'
                    current_content = []
                elif current_section and line:
                    current_content.append(line)
            
            # Add the last section
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Ensure all sections exist
            required_sections = [
                'executive_summary', 'performance_analysis', 'allocation_analysis',
                'key_observations', 'recommendations', 'holdings_analysis', 'historical_analysis'
            ]
            
            for section in required_sections:
                if section not in sections or not sections[section]:
                    sections[section] = f"Generating {section.replace('_', ' ')}..."
            
            print("Generated sections:", sections)  # Debug log
            
            # If no sections were parsed, create them from the full response
            if not sections:
                sections = {
                    'executive_summary': content,
                    'performance_analysis': content,
                    'allocation_analysis': content,
                    'key_observations': content,
                    'recommendations': content,
                    'holdings_analysis': content,
                    'historical_analysis': content
                }
            
            return sections
            
        except Exception as e:
            print(f"Analysis generation error: {str(e)}")
            print(f"Full error details: {e.__class__.__name__}")  # More debug info
            raise 