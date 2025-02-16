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

from backend import ChatService, ReportService, MarketService, VectorStore
from backend.models.portfolio import Portfolio
import subprocess

def check_dependencies():
    try:
        import langchain_community
    except ImportError:
        st.error("Missing required dependencies. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "langchain-community==0.0.10"])
        st.experimental_rerun()

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
        
        /* Chat interface enhancement */
        .stChatMessage {
            background: white;
            padding: 1rem;
            border-radius: 12px;
            margin: 1rem 0;
            box-shadow: var(--shadow);
        }
        
        /* Mobile-specific enhancements */
        @media (max-width: 768px) {
            /* Hide sidebar elements */
            section[data-testid="stSidebar"][aria-expanded="true"],
            section[data-testid="stSidebar"][aria-expanded="false"],
            button[kind="header"] {
                display: none !important;
            }
            
            /* Mobile client selector */
            .main-client-selector {
                display: block !important;
                position: sticky;
                top: 0;
                z-index: 999;
                background: white;
                padding: 15px;
                margin: -1rem -1rem 1rem -1rem;
                border-bottom: 1px solid rgba(0,0,0,0.1);
                box-shadow: var(--shadow);
            }
            
            /* Mobile-optimized metrics */
            .metric-container {
                padding: 1rem;
                margin-bottom: 1rem;
            }
            
            /* Mobile-friendly tabs */
            .stTabs [data-baseweb="tab"] {
                padding: 8px 16px;
                font-size: 14px;
            }
            
            /* Improved mobile spacing */
            .main .block-container {
                padding: 1rem;
            }
        }
        
        /* Desktop-specific enhancements */
        @media (min-width: 769px) {
            .main-client-selector {
                display: none !important;
            }
            
            section[data-testid="stSidebar"] {
                background: var(--background-light);
                border-right: 1px solid rgba(0,0,0,0.1);
            }
            
            /* Enhanced sidebar styling */
            .sidebar .sidebar-content {
                background: white;
                border-radius: 12px;
                margin: 1rem;
                padding: 1rem;
                box-shadow: var(--shadow);
            }
        }
        
        /* Animation effects */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .metric-container, .dataframe-container, .stChatMessage {
            animation: fadeIn 0.5s ease-out;
        }

        /* Remove space from Streamlit's root elements */
        .stApp {
            padding: 0 !important;
            margin: 0 !important;
        }

        .stTitle {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }

        /* Hide boxes under Asset Allocation and Top Holdings */
        h3:has(+ .element-container .dataframe-container) + .element-container {
            display: none !important;
        }

        /* Make Portfolio Summary box minimal */
        .metric-container {
            background: transparent !important;
            box-shadow: none !important;
            padding: 0.5rem 0 !important;
            border: none !important;
            border-bottom: 2px solid var(--secondary-color) !important;
            border-radius: 0 !important;
            margin-bottom: 1.5rem;
        }

        /* Keep client info box visible */
        .client-selector {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: var(--shadow);
            margin-bottom: 25px;
            border: 1px solid rgba(0,0,0,0.1);
        }

        /* Remove ALL boxes around the main title */
        .stTitle {
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            border: none !important;
            box-shadow: none !important;
        }

        /* Main title underline styling */
        .stTitle h1 {
            border-bottom: 3px solid #E74C3C !important;
            padding-bottom: 0.5rem;
            margin: 0 0 1rem 0 !important;
            display: block;
            width: 100%;
        }

        /* Remove Streamlit's default header container */
        div[data-testid="stHeader"] {
            display: none !important;
        }

        /* Remove parent container spacing */
        div[data-testid="stVerticalBlock"] > div:has(h1) {
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Remove existing underlines from metric container */
        .metric-container {
            border-bottom: none !important;
        }

        /* Unified header styling */
        h1, h2, h3 {
            border-bottom: 2px solid #E74C3C !important;
            padding-bottom: 0.5rem;
            margin: 0 0 1rem 0 !important;
            display: block;
            width: 100%;
            background: transparent !important;
            box-shadow: none !important;
        }

        /* Remove containers for all headers */
        .element-container:has(h1),
        .element-container:has(h2),
        .element-container:has(h3) {
            background: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
            box-shadow: none !important;
            border: none !important;
        }

        /* Remove dataframe containers */
        .dataframe-container {
            background: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
            border: none !important;
        }

        /* Remove metric container borders */
        .metric-container {
            border-bottom: none !important;
        }

        /* Restore main title styling */
        h1 {
            background: var(--gradient) !important;
            -webkit-background-clip: text !important;
            -webkit-text-fill-color: transparent !important;
            font-weight: 800;
            margin: 0 0 1rem 0 !important;
            padding: 0 !important;
            font-size: 2.7rem;
            border-bottom: none !important;  /* Remove red line */
        }

        /* Remove all header underlines */
        h2, h3 {
            border-bottom: none !important;
            padding-bottom: 0 !important;
            margin: 0 0 1rem 0 !important;
        }

        /* Remove all containers and boxes */
        .element-container:has(h1),
        .element-container:has(h2),
        .element-container:has(h3),
        .metric-container,
        .dataframe-container {
            background: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
            border: none !important;
        }

        /* Keep client selector box */
        .client-selector {
            background: white;
            padding: 20px;
            border-radius: 12px;
            box-shadow: var(--shadow);
            margin-bottom: 25px;
            border: 1px solid rgba(0,0,0,0.1);
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
            
            # Initialize other services
            self.chat_service = ChatService(self.vector_store)
            self.report_service = ReportService()
            self.market_service = MarketService()
                
        except Exception as e:
            st.error(f"Initialization Error: {str(e)}")
            st.error("Please check your OpenAI API key and data files")
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
    