from datetime import datetime
from typing import Dict
import jinja2
import pdfkit
import platform
from pathlib import Path
from backend.utils.visualization import PortfolioVisualizer
from backend.services.chat_service import ChatService
from backend.services.market_service import MarketService
from backend.database.vector_store import VectorStore

class ReportService:
    def __init__(self):
        self.visualizer = PortfolioVisualizer()
        self.template_loader = jinja2.FileSystemLoader(searchpath="./templates")
        self.template_env = jinja2.Environment(loader=self.template_loader)
        self.vector_store = VectorStore()  # Initialize VectorStore
        self.wkhtmltopdf_path = self._get_wkhtmltopdf_path()

    def _get_wkhtmltopdf_path(self):
        """Get correct wkhtmltopdf executable path based on OS"""
        if platform.system() == 'Windows':
            # Update this path to match your actual installation
            custom_path = r'C:\Users\mdfar\Downloads\wkhtmltox-0.12.6-1.mxe-cross-win64\wkhtmltox\bin\wkhtmltopdf.exe'
            if Path(custom_path).exists():
                return custom_path
        return pdfkit.configuration(wkhtmltopdf=pdfkit.configuration().wkhtmltopdf.decode('utf-8'))

    def generate_report(self, client_data: Dict) -> bytes:
        """Generate a comprehensive PDF report for a client"""
        try:
            # Initialize vector store
            self.vector_store.initialize_from_json({"clients": [client_data]})
            
            # Generate AI analysis
            analysis_prompt = f"""
            Please provide a detailed investment portfolio analysis with clear sections.
            Use the following data:

            Client: {client_data['clientInfo']['name']}
            Account Type: {client_data['clientInfo']['accountType']}
            Risk Profile: {client_data['clientInfo']['riskProfile']}
            Portfolio Value: ${client_data['portfolioSummary']['totalValue']:,.2f}
            YTD Return: {client_data['performance']['ytd']}%

            Please analyze and provide specific recommendations in these sections:
            1. Executive Summary
            2. Performance Analysis
            3. Asset Allocation Analysis
            4. Key Observations
            5. Recommendations
            6. Holdings Analysis
            7. Historical Analysis

            Use the provided data to make specific, data-driven observations and recommendations.
            """

            print("Sending prompt to AI:", analysis_prompt)  # Debug log
            ai_analysis = ChatService.generate_analysis(analysis_prompt, self.vector_store)
            print("Received AI analysis:", ai_analysis)  # Debug log
            
            # Generate visualizations
            asset_allocation_chart = self.visualizer.create_asset_allocation_pie(
                client_data['assetAllocation']
            )
            performance_chart = self.visualizer.create_performance_chart(
                client_data['performance']
            )
            holdings_chart = self.visualizer.create_holdings_chart(
                client_data['topHoldings']
            )

            # Prepare template data
            template_data = {
                'client': client_data['clientInfo'],
                'portfolio': {
                    **client_data['portfolioSummary'],
                    'ytd': client_data['performance']['ytd']
                },
                'charts': {
                    'asset_allocation': asset_allocation_chart,
                    'performance': performance_chart,
                    'holdings': holdings_chart
                },
                'generated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'ai_analysis': ai_analysis,
                'market_context': MarketService.get_market_summary(),
                'report_metadata': client_data.get('reportMetadata', {})
            }

            # Debug logging
            print("Template data prepared:", {
                k: v for k, v in template_data.items() 
                if k not in ['charts']  # Exclude binary chart data from log
            })

            # Render HTML template
            template = self.template_env.get_template('report_template.html')
            html_content = template.render(**template_data)

            # PDF options for better rendering
            pdf_options = {
                'page-size': 'Letter',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': 'UTF-8',
                'no-outline': None,
                'enable-local-file-access': None,
                'disable-smart-shrinking': None
            }

            # Convert HTML to PDF with explicit configuration
            config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)

            pdf_content = pdfkit.from_string(
                html_content, 
                False, 
                options=pdf_options, 
                configuration=config
            )

            return pdf_content
        except Exception as e:
            print(f"Report generation error: {str(e)}")
            print(f"Error type: {type(e)}")
            print(f"Error details: {e.__class__.__name__}")
            raise 