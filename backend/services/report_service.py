from datetime import datetime
from typing import Dict
import jinja2
import pdfkit
import platform
from pathlib import Path
from backend.utils.visualization import PortfolioVisualizer
from backend.services.chat_service import ChatService
from backend.services.market_service import MarketService

class ReportService:
    def __init__(self):
        self.visualizer = PortfolioVisualizer()
        self.template_loader = jinja2.FileSystemLoader(searchpath="./templates")
        self.template_env = jinja2.Environment(loader=self.template_loader)
        
        # Configure wkhtmltopdf path
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

        # Generate AI-powered insights
        analysis_prompt = f"""
        Generate a professional investment analysis report for {client_data['clientInfo']['name']} with:
        1. Executive summary of portfolio performance
        2. Market context analysis for the reporting period
        3. Key observations about asset allocation
        4. Recommendations for portfolio adjustments
        5. Risk assessment and mitigation strategies
        
        Portfolio Details:
        - Total Value: ${client_data['portfolioSummary']['totalValue']:,.2f}
        - Top Holdings: {[h['name'] for h in client_data['topHoldings']]}
        - Risk Profile: {client_data['clientInfo']['riskProfile']}
        """
        
        try:
            ai_analysis = ChatService.generate_analysis(analysis_prompt)
        except Exception as e:
            ai_analysis = "AI analysis unavailable at this time"

        # Prepare template data
        template_data = {
            'client': client_data['clientInfo'],
            'portfolio': client_data['portfolioSummary'],
            'charts': {
                'asset_allocation': asset_allocation_chart,
                'performance': performance_chart,
                'holdings': holdings_chart
            },
            'generated_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'ai_analysis': ai_analysis,
            'market_context': MarketService.get_market_summary()
        }

        # Render HTML template
        template = self.template_env.get_template('report_template.html')
        html_content = template.render(**template_data)

        # Convert HTML to PDF
        pdf_options = {
            'page-size': 'Letter',
            'margin-top': '0.75in',
            'margin-right': '0.75in',
            'margin-bottom': '0.75in',
            'margin-left': '0.75in',
            'encoding': 'UTF-8'
        }
        
        # Convert HTML to PDF with explicit configuration
        config = pdfkit.configuration(wkhtmltopdf=self.wkhtmltopdf_path)
        
        try:
            pdf_content = pdfkit.from_string(
                html_content, 
                False, 
                options=pdf_options, 
                configuration=config
            )
        except OSError as e:
            raise RuntimeError(
                f"Failed to generate PDF. Verify wkhtmltopdf installation at: {self.wkhtmltopdf_path}"
            ) from e

        return pdf_content 