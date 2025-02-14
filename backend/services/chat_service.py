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
            Each section should start with its title in a new line.
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
            
            # Define section markers
            section_markers = {
                'executive summary': 'executive_summary',
                'performance analysis': 'performance_analysis',
                'asset allocation analysis': 'allocation_analysis',
                'key observations': 'key_observations',
                'recommendations': 'recommendations',
                'holdings analysis': 'holdings_analysis',
                'historical analysis': 'historical_analysis'
            }
            
            lines = content.split('\n')
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                lower_line = line.lower()
                
                # Check for section headers
                found_section = None
                for marker, section_name in section_markers.items():
                    if marker in lower_line:
                        if current_section and current_content:
                            sections[current_section] = '\n'.join(current_content).strip()
                        current_section = section_name
                        current_content = []
                        found_section = True
                        break
                
                if not found_section and current_section:
                    # Skip the section header line itself
                    if not (line.startswith('#') and 'conclusion' in lower_line):
                        current_content.append(line)
                
                i += 1
            
            # Add the last section
            if current_section and current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Extract executive summary from the beginning if not already captured
            if 'executive_summary' not in sections and content:
                summary_end = content.lower().find('performance analysis')
                if summary_end > 0:
                    summary = content[:summary_end].strip()
                    if summary:
                        sections['executive_summary'] = summary
            
            # Ensure all sections exist and have content
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