import streamlit as st
import asyncio
import json
from datetime import datetime
from backend import ChatService, ReportService, MarketService, VectorStore
from backend.models.portfolio import Portfolio
import os
import sys
import subprocess

def check_dependencies():
    try:
        import langchain_community
    except ImportError:
        st.error("Missing required dependencies. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "langchain-community==0.0.10"])
        st.experimental_rerun()

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
        st.set_page_config(page_title="Asset Management AI", layout="wide")
        st.title("Asset Management AI Platform")

        # Sidebar for client selection
        st.sidebar.title("Client Selection")
        selected_client = st.sidebar.selectbox(
            "Select Client",
            options=[client['clientInfo']['name'] for client in self.client_data['clients']],
            key="client_selector"
        )

        # Get selected client data
        client_info = next(
            client for client in self.client_data['clients'] 
            if client['clientInfo']['name'] == selected_client
        )

        # Main content area with tabs
        tab1, tab2, tab3 = st.tabs(["Portfolio Overview", "Report Generation", "Chat Assistant"])

        with tab1:
            self.show_portfolio_overview(client_info)

        with tab2:
            self.show_report_generation(client_info)

        with tab3:
            self.show_chat_interface(client_info)

    def show_portfolio_overview(self, client_info):
        st.header("Portfolio Overview")
        
        # Client Information
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Client Information")
            st.write(f"Name: {client_info['clientInfo']['name']}")
            st.write(f"Account Type: {client_info['clientInfo']['accountType']}")
            st.write(f"Risk Profile: {client_info['clientInfo']['riskProfile']}")
            st.write(f"Investment Strategy: {client_info['clientInfo']['investmentStrategy']}")

        with col2:
            st.subheader("Portfolio Summary")
            st.write(f"Total Value: ${client_info['portfolioSummary']['totalValue']:,.2f}")
            st.write(f"YTD Return: {client_info['performance']['ytd']}%")
            st.write(f"Since Inception: {client_info['performance']['sinceInception']}%")

        # Asset Allocation
        st.subheader("Asset Allocation")
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
        st.dataframe(allocation_data)

        # Top Holdings
        st.subheader("Top Holdings")
        holdings_data = [
            {
                "Security": holding['name'],
                "Weight (%)": holding['weight'],
                "Value ($)": holding['value'],
                "Gain ($)": holding['gain']
            }
            for holding in client_info['topHoldings']
        ]
        st.dataframe(holdings_data)

    def show_report_generation(self, client_info):
        st.header("Report Generation")
        
        report_type = st.selectbox(
            "Select Report Type",
            ["Comprehensive Portfolio Report", "Performance Summary", "Holdings Analysis"]
        )
        
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