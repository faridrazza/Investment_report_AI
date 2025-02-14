from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
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
        
        # Create a chat prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a professional investment advisor assistant. 
            Use the available portfolio data to provide accurate, specific answers about the client's investments.
            Always be professional and precise in your responses."""),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # Create the runnable chain
        self.chain = self.prompt | self.model
        self.message_history = []

    async def process_message(self, message: str) -> str:
        """Process user message and return AI response"""
        try:
            # Search vector store for relevant context
            context_results = self.vector_store.search(message)
            context = "\n".join([content for content, _, _ in context_results])
            
            # Add context to the message
            enhanced_message = f"""
            Context: {context}
            
            Question: {message}
            """
            
            # Add message to history
            self.message_history.append(HumanMessage(content=enhanced_message))
            
            # Get response
            response = await self.model.ainvoke([
                *self.message_history,
                HumanMessage(content=enhanced_message)
            ])
            
            # Add response to history
            self.message_history.append(AIMessage(content=response.content))
            
            return response.content
            
        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return f"I apologize, but I encountered an error processing your request. Please try again."

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
            
            # Create a system message to guide the analysis
            system_msg = SystemMessage(content="""
            You are a professional investment analyst. Analyze the portfolio data and provide 
            a detailed report with the following sections:
            1. Executive Summary
            2. Performance Analysis
            3. Asset Allocation Analysis
            4. Key Observations
            5. Recommendations
            6. Holdings Analysis
            7. Historical Analysis
            
            Use clear section headers and provide detailed, data-driven insights.
            """)
            
            # Create the human message with the prompt
            human_msg = HumanMessage(content=prompt)
            
            # Get response from the model
            response = instance.model.invoke([system_msg, human_msg])
            content = response.content
            
            print("Raw AI Response:", content)  # Debug log
            
            # Parse sections
            sections = {}
            current_section = None
            current_content = []
            
            for line in content.split('\n'):
                line = line.strip()
                lower_line = line.lower()
                
                # Section detection logic
                if 'executive summary' in lower_line:
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'executive_summary'
                    current_content = []
                elif 'performance analysis' in lower_line:
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'performance_analysis'
                    current_content = []
                elif 'asset allocation analysis' in lower_line:
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'allocation_analysis'
                    current_content = []
                elif 'key observations' in lower_line:
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'key_observations'
                    current_content = []
                elif 'recommendations' in lower_line:
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'recommendations'
                    current_content = []
                elif 'holdings analysis' in lower_line:
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    current_section = 'holdings_analysis'
                    current_content = []
                elif 'historical analysis' in lower_line:
                    if current_section and current_content:
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
            return sections
            
        except Exception as e:
            print(f"Analysis generation error: {str(e)}")
            print(f"Full error details: {e.__class__.__name__}")
            raise 