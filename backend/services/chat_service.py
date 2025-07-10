from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Import Pydantic and ensure proper initialization
import pydantic
from pydantic import BaseModel

# Import LangChain components with proper order
from langchain_core.caches import BaseCache
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from backend.config import Config
from backend.database.vector_store import VectorStore
from datetime import datetime
from backend.services.market_service import MarketService

# Ensure ChatOpenAI is properly initialized with BaseCache
try:
    # Force Pydantic model rebuilding for compatibility
    ChatOpenAI.model_rebuild()
except Exception as e:
    print(f"Model rebuild warning: {e}")

class ChatService:
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store
        
        # Initialize ChatOpenAI with proper error handling
        try:
            self.model = ChatOpenAI(
                model=Config.MODEL_NAME,
                openai_api_key=Config.OPENAI_API_KEY,
                temperature=0.7
            )
        except Exception as e:
            print(f"Error initializing ChatOpenAI: {e}")
            print("Please ensure your OpenAI API key is correctly set.")
            raise ValueError(f"Failed to initialize ChatOpenAI: {str(e)}")
            
        self.current_client = None
        self.message_history = []
        
        # Create a chat prompt template with client context
        self.prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content="""You are a professional investment advisor assistant. 
            You are currently assisting with the portfolio of {client_name}.
            Only provide information about this client's portfolio.
            Use the available portfolio data to provide accurate, specific answers.
            Always be professional and precise in your responses."""),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{input}")
        ])
        
        # Create the runnable chain
        self.chain = self.prompt | self.model

    def set_current_client(self, client_data: Dict):
        """Set the current client context"""
        self.current_client = client_data
        self.message_history = []  # Reset history when switching clients
        
    async def process_message(self, message: str) -> str:
        """Process user message with client context"""
        try:
            if not self.current_client:
                return "Please select a client first."

            # Search vector store with client-specific context
            context_results = self.vector_store.search(
                query=message,
                client_id=self.current_client['clientInfo']['id'],
                k=3
            )
            
            # Combine context with priority for financial data
            financial_context = []
            general_context = []
            
            for content, metadata, score in context_results:
                if metadata.get('type') == 'financial':
                    financial_context.append(content)
                else:
                    general_context.append(content)
            
            # Construct enhanced message with client context
            enhanced_message = f"""
            Context: You are discussing the portfolio of {self.current_client['clientInfo']['name']}.
            
            Question: {message}
            
            Financial Information:
            {' '.join(financial_context)}
            
            Additional Context:
            {' '.join(general_context)}
            """
            
            # Get response with client context
            response = await self.model.ainvoke([
                SystemMessage(content=f"""You are assisting with {self.current_client['clientInfo']['name']}'s portfolio.
                Only provide information about this specific client."""),
                *self.message_history,
                HumanMessage(content=enhanced_message)
            ])
            
            # Update message history
            self.message_history.append(HumanMessage(content=message))
            self.message_history.append(AIMessage(content=response.content))
            
            # Limit history length to prevent token limits
            if len(self.message_history) > 10:
                self.message_history = self.message_history[-10:]
            
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
            Each section must start with its exact title (e.g., "Executive Summary").
            """)
            
            # Create the human message with the prompt
            human_msg = HumanMessage(content=prompt)
            
            # Get response from the model
            response = instance.model.invoke([system_msg, human_msg])
            content = response.content
            
            print("Raw AI Response:", content)  # Debug log
            
            # Parse sections with improved logic
            sections = {}
            current_section = None
            current_content = []
            
            # Define section markers with exact matches
            section_markers = {
                'executive summary': 'executive_summary',
                'performance analysis': 'performance_analysis',
                'asset allocation analysis': 'allocation_analysis',
                'key observations': 'key_observations',
                'recommendations': 'recommendations',
                'holdings analysis': 'holdings_analysis',
                'historical analysis': 'historical_analysis'
            }
            
            # Split content by ### to separate sections
            raw_sections = content.split('###')
            
            for section in raw_sections:
                if not section.strip():
                    continue
                    
                # Get the first line as the section title
                lines = section.strip().split('\n')
                title = lines[0].strip().lower()
                content = '\n'.join(lines[1:]).strip()
                
                # Match section title to our markers
                for marker, section_name in section_markers.items():
                    if marker in title:
                        sections[section_name] = content
                        break
            
            # Ensure all sections exist
            required_sections = [
                'executive_summary', 'performance_analysis', 'allocation_analysis',
                'key_observations', 'recommendations', 'holdings_analysis', 'historical_analysis'
            ]
            
            for section in required_sections:
                if section not in sections or not sections[section]:
                    sections[section] = "Analysis for this section is being generated..."
            
            print("Generated sections:", sections)  # Debug log
            return sections
            
        except Exception as e:
            print(f"Analysis generation error: {str(e)}")
            return {
                'executive_summary': f"Error generating analysis: {str(e)}",
                'performance_analysis': "Unable to generate performance analysis",
                'allocation_analysis': "Unable to generate allocation analysis", 
                'key_observations': "Unable to generate key observations",
                'recommendations': "Unable to generate recommendations",
                'holdings_analysis': "Unable to generate holdings analysis",
                'historical_analysis': "Unable to generate historical analysis"
            } 