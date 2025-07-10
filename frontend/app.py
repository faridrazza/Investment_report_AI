import streamlit as st
import asyncio
import json
from datetime import datetime
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Import with better error handling
try:
    from backend import ChatService, ReportService, MarketService, VectorStore
    from backend.models.portfolio import Portfolio
except ImportError as e:
    st.error(f"Import Error: {e}")
    st.error("Please ensure all dependencies are installed correctly.")
    st.stop()

import subprocess

def check_dependencies():
    try:
        import langchain_community
        import langchain_openai
        from langchain_core.caches import BaseCache
        # Force model rebuilding to fix Pydantic issues
        try:
            from langchain_openai import ChatOpenAI
            ChatOpenAI.model_rebuild()
        except Exception as e:
            print(f"Model rebuild warning: {e}")
    except ImportError:
        st.error("Missing required dependencies. Installing...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "langchain-community==0.3.17"])
            st.experimental_rerun()
        except Exception as e:
            st.error(f"Failed to install dependencies: {e}")
            st.stop()

# Custom CSS for better mobile responsiveness
def apply_custom_css():
    st.markdown("""
        <style>
        /* Removed element hiding rules that were causing content disappearance */
        
        /* Adjust header styling */
        h1, h2, h3 {
            margin-bottom: 1.5rem;
            padding-bottom: 0.5rem;
        }
        
        h1 {
            background: var(--primary-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800;
            margin: 0 !important;  /* Remove all margins */
            padding: 0 !important; /* Remove all padding */
            font-size: 2.7rem;
            line-height: 1 !important;  /* Prevent vertical spacing */
        }
        
        h2 {
            color: var(--text-primary);
            font-size: 1.8rem;
            font-weight: 600;
        }
        
        h3 {
            color: var(--text-primary);
            font-size: 1.4rem;
            font-weight: 600;
        }
        
        /* Modern color scheme and base styles */
        :root {
            --primary-color: #2C3E50;
            --secondary-color: #3498DB;
            --accent-color: #E74C3C;
            --background-light: #F8F9FA;
            --text-color: #2C3E50;
            --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            --gradient: linear-gradient(135deg, #2C3E50, #3498DB);
        }
        
        /* Adjust top spacing and font sizes */
        .main .block-container {
            max-width: 1200px;
            padding: 0 !important;  /* Remove all padding */
            margin: 0 !important;   /* Remove all margins */
            font-family: 'Inter', sans-serif;
            font-size: 1.1rem;
        }
        
        /* Adjusted header spacing */
        h1 {
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            margin: 0.5rem 0 1.5rem 0;  /* Reduced top margin */
            font-size: 2.7rem;  /* Slightly larger title */
        }
        
        /* Adjust subheader sizes */
        h2, .sidebar h2 {
            font-size: 1.8rem;  /* Slightly larger subheadings */
            margin-bottom: 1rem;
        }
        
        h3 {
            font-size: 1.4rem;  /* Slightly larger h3 */
        }
        
        /* Adjust text content size */
        p, .stMarkdown, .stText {
            font-size: 1.1rem;  /* Slightly larger regular text */
        }
        
        /* Enhanced typography */
        .main .block-container {
            max-width: 1200px;
            padding: 2rem;
            font-family: 'Inter', sans-serif;
        }
        
        /* Beautiful header styling */
        h1 {
            background: var(--gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 700;
            margin-bottom: 2rem;
            font-size: 2.5rem;
        }
        
        /* Enhanced tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 30px;
            padding: 15px 20px;
            background: var(--background-light);
            border-radius: 10px;
            box-shadow: var(--shadow);
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 12px 24px;
            font-weight: 500;
            background: white;
            border-radius: 8px;
            transition: all 0.3s ease;
            border: none;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            background: var(--secondary-color);
            color: white;
        }
        
        /* Enhanced client selector styling */
        .client-selector {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: var(--shadow);
            margin-bottom: 25px;
            border: 1px solid rgba(0,0,0,0.1);
        }
        
        /* Beautiful metrics display */
        .metric-container {
            background: transparent !important;
            box-shadow: none !important;
            padding: 0.5rem 0 !important;
            border: none !important;
            border-bottom: 2px solid var(--secondary-color) !important;
            border-radius: 0 !important;
            margin-bottom: 1.5rem;
        }
        
        .metric-value {
            color: var(--secondary-color);
            font-size: 1.8rem;
            font-weight: 700;
        }
        
        /* Enhanced dataframe styling */
        .dataframe-container {
            background: white;
            padding: 1rem;
            border-radius: 12px;
            box-shadow: var(--shadow);
            margin: 1rem 0;
        }
        
        .dataframe {
            border-radius: 8px;
            overflow: hidden;
        }
        
        /* Beautiful button styling */
        .stButton > button {
            background: var(--gradient);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
            width: 100%;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow);
        }
        
        /* Alert styling */
        .alert {
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }
        
        .alert-error {
            background-color: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        
        .alert-warning {
            background-color: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }
        
        .alert-success {
            background-color: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        </style>
    """, unsafe_allow_html=True)

class AssetManagementApp:
    def __init__(self):
        check_dependencies()
        try:
            # Ensure data directory exists
            if not os.path.exists('data'):
                os.makedirs('data')
                
            # Initialize vector store first
            self.vector_store = VectorStore()
            
            # Load client data
            data_path = os.path.join('data', 'clients.json')
            if not os.path.exists(data_path):
                raise FileNotFoundError(f"Client data file not found at {data_path}")
                
            with open(data_path, 'r', encoding='utf-8') as f:
                self.client_data = json.load(f)
                
            # Initialize vector store with data
            self.vector_store.initialize_from_json(self.client_data)
            
            # Initialize other services with proper error handling
            try:
                self.chat_service = ChatService(self.vector_store)
                self.report_service = ReportService()
                self.market_service = MarketService()
            except Exception as service_error:
                st.error(f"Service initialization error: {service_error}")
                st.error("This is likely due to missing or incorrect API keys.")
                st.error("Please check your .env file and ensure OPENAI_API_KEY and ALPHA_VANTAGE_API_KEY are set correctly.")
                st.stop()
                
        except FileNotFoundError as fe:
            st.error(f"File Error: {str(fe)}")
            st.error("Please ensure the client data file exists in the data/ directory.")
            st.stop()
        except Exception as e:
            st.error(f"Initialization Error: {str(e)}")
            st.error("This error is typically caused by:")
            st.error("1. Missing or incorrect OpenAI API key")
            st.error("2. Missing or incorrect Alpha Vantage API key") 
            st.error("3. Pydantic version compatibility issues")
            st.error("4. Missing data files")
            
            # Show detailed error information
            with st.expander("Show detailed error information"):
                st.code(str(e))
                
            # Provide helpful suggestions
            st.info("To fix this issue:")
            st.info("1. Create a .env file in the project root")
            st.info("2. Add your API keys: OPENAI_API_KEY=your_key_here")
            st.info("3. Add: ALPHA_VANTAGE_API_KEY=your_key_here")
            st.info("4. Ensure all dependencies are installed with: pip install -r requirements.txt")
            
            st.stop()  # Prevent further execution

    def run(self):
        st.set_page_config(
            page_title="Asset Management AI",
            layout="wide",
            initial_sidebar_state="collapsed"
        )
        
        apply_custom_css()
        
        st.title("Asset Management With AI")

        # Always visible client selector
        st.markdown('<div class="client-selector">', unsafe_allow_html=True)
        selected_client = st.selectbox(
            "Select Client",
            options=[client['clientInfo']['name'] for client in self.client_data['clients']],
            key="client_selector"
        )
        st.markdown('</div>', unsafe_allow_html=True)

        # Get selected client data
        client_info = next(
            client for client in self.client_data['clients'] 
            if client['clientInfo']['name'] == selected_client
        )

        # Tabs with improved spacing
        tab1, tab2, tab3 = st.tabs(["Portfolio", "Reports", "Chat"])

        with tab1:
            self.show_portfolio_overview(client_info)

        with tab2:
            self.show_report_generation(client_info)

        with tab3:
            self.show_chat_interface(client_info)

    def show_portfolio_overview(self, client_info):
        st.header("Portfolio Overview")
        
        # Responsive client information
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        if st.session_state.get('mobile_view', False):
            # Single column layout for mobile
            st.subheader("Client Information")
            st.write(f"Name: {client_info['clientInfo'].get('name', 'N/A')}")
            st.write(f"Account Type: {client_info['clientInfo'].get('accountType', 'N/A')}")
            st.write(f"Risk Profile: {client_info['clientInfo'].get('riskProfile', 'N/A')}")
            st.write(f"Investment Strategy: {client_info['clientInfo'].get('investmentStrategy', 'N/A')}")
            
            st.subheader("Portfolio Summary")
            total_value = client_info['portfolioSummary'].get('totalValue', 0)
            st.write(f"Total Value: ${total_value:,.2f}")
            st.write(f"YTD Return: {client_info['performance'].get('ytd', 0)}%")
            st.write(f"Since Inception: {client_info['performance'].get('sinceInception', 0)}%")
        else:
            # Two column layout for desktop
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Client Information")
                st.write(f"Name: {client_info['clientInfo'].get('name', 'N/A')}")
                st.write(f"Account Type: {client_info['clientInfo'].get('accountType', 'N/A')}")
                st.write(f"Risk Profile: {client_info['clientInfo'].get('riskProfile', 'N/A')}")
                st.write(f"Investment Strategy: {client_info['clientInfo'].get('investmentStrategy', 'N/A')}")

            with col2:
                st.subheader("Portfolio Summary")
                total_value = client_info['portfolioSummary'].get('totalValue', 0)
                st.write(f"Total Value: ${total_value:,.2f}")
                st.write(f"YTD Return: {client_info['performance'].get('ytd', 0)}%")
                st.write(f"Since Inception: {client_info['performance'].get('sinceInception', 0)}%")
        st.markdown('</div>', unsafe_allow_html=True)

        # Responsive asset allocation
        st.subheader("Asset Allocation")
        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        allocation_data = {
            "Asset Class": ["Equities", "Fixed Income", "Alternatives", "Cash"],
            "Current (%)": [
                client_info['assetAllocation']['equities']['percentage'],
                client_info['assetAllocation']['fixedIncome']['percentage'],
                client_info['assetAllocation']['alternatives']['percentage'],
                client_info['assetAllocation']['cash']['percentage']
            ],
            "Target (%)": [
                client_info['assetAllocation']['equities']['target'],
                client_info['assetAllocation']['fixedIncome']['target'],
                client_info['assetAllocation']['alternatives']['target'],
                client_info['assetAllocation']['cash']['target']
            ]
        }
        st.dataframe(allocation_data, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # Responsive holdings table
        st.subheader("Top Holdings")
        st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
        holdings_data = [
            {
                "Security": holding['name'],
                "Weight (%)": holding['weight'],
                "Value ($)": holding['value'],
                "Gain ($)": holding['gain']
            }
            for holding in client_info['topHoldings']
        ]
        st.dataframe(holdings_data, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    def show_report_generation(self, client_info):
        st.header("Report Generation")
        
        if st.button("Generate Report"):
            with st.spinner("Generating report..."):
                try:
                    pdf_content = self.report_service.generate_report(client_info)
                    st.download_button(
                        label="Download Report",
                        data=pdf_content,
                        file_name=f"portfolio_report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf"
                    )
                    st.success("Report generated successfully!")
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")

    def show_chat_interface(self, client_info):
        st.header("AI Assistant")
        
        # Set current client context
        self.chat_service.set_current_client(client_info)
        
        # Initialize chat history for the current client
        client_id = client_info['clientInfo']['id']
        if "chat_histories" not in st.session_state:
            st.session_state.chat_histories = {}
        if client_id not in st.session_state.chat_histories:
            st.session_state.chat_histories[client_id] = []
        
        # Display chat history for current client
        for message in st.session_state.chat_histories[client_id]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # Chat input
        if prompt := st.chat_input(f"Ask me anything about {client_info['clientInfo']['name']}'s portfolio..."):
            # Add user message to history
            st.session_state.chat_histories[client_id].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Process response
            with st.spinner("Analyzing..."):
                response = asyncio.run(self.chat_service.process_message(prompt))
            
            # Add assistant response to history
            with st.chat_message("assistant"):
                st.markdown(response)
            st.session_state.chat_histories[client_id].append({"role": "assistant", "content": response})

if __name__ == "__main__":
    app = AssetManagementApp()
    app.run() 
    