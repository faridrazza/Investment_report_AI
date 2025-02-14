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
        """Process user message with improved financial data handling"""
        try:
            # Search vector store for relevant context
            context_results = self.vector_store.search(message, k=3)  # Reduced from 5 to 3
            
            # Combine context with priority for financial data
            financial_context = []
            general_context = []
            
            for content, metadata, score in context_results:
                if metadata.get('type') == 'financial':
                    financial_context.append(content)
                else:
                    general_context.append(content)
            
            # Construct enhanced message with structured context
            enhanced_message = f"""
            Question: {message}
            
            Financial Information:
            {' '.join(financial_context)}
            
            Additional Context:
            {' '.join(general_context)}
            
            Provide a brief, focused answer using the available data. 
            Keep responses under 3-4 sentences unless specifically asked for detailed analysis.
            Focus on the most relevant information for the question asked.
            """
            
            # Add system message for concise responses
            system_message = SystemMessage(content="""
            You are a concise financial advisor assistant. When answering:
            1. Be brief and direct
            2. Focus on key metrics relevant to the question
            3. Only show calculations if specifically requested
            4. Limit responses to 3-4 sentences unless asked for more detail
            5. Use plain language and avoid unnecessary technical terms
            """)
            
            # Get response with enhanced context
            response = await self.model.ainvoke([
                system_message,
                *self.message_history,
                HumanMessage(content=enhanced_message)
            ])
            
            self.message_history.append(HumanMessage(content=message))
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
            print(f"Full error details: {e.__class__.__name__}")
            raise 