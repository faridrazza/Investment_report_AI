import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64

class PortfolioVisualizer:
    @staticmethod
    def create_asset_allocation_pie(allocation_data):
        """Create pie chart for asset allocation"""
        plt.figure(figsize=(10, 8))
        labels = list(allocation_data.keys())
        sizes = [data['percentage'] for data in allocation_data.values()]
        colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99']
        
        plt.pie(sizes, labels=labels, colors=colors, autopct='%1.1f%%')
        plt.title('Asset Allocation')
        
        # Convert plot to base64 string
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode()

    @staticmethod
    def create_performance_chart(performance_data):
        """Create line graph for performance metrics"""
        plt.figure(figsize=(12, 6))
        periods = ['YTD', '1 Year', '3 Year', '5 Year', 'Since Inception']
        values = [
            performance_data['ytd'],
            performance_data['1year'],
            performance_data['3year'],
            performance_data['5year'],
            performance_data['sinceInception']
        ]
        
        plt.plot(periods, values, marker='o')
        plt.title('Performance History')
        plt.ylabel('Return (%)')
        plt.grid(True)
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode()

    @staticmethod
    def create_holdings_chart(holdings_data):
        """Create bar chart for top holdings"""
        plt.figure(figsize=(12, 6))
        securities = [holding['name'] for holding in holdings_data]
        weights = [holding['weight'] for holding in holdings_data]
        gains = [holding['gain'] for holding in holdings_data]
        
        x = range(len(securities))
        width = 0.35
        
        plt.bar(x, weights, width, label='Weight (%)')
        plt.bar([i + width for i in x], gains, width, label='Gain ($)')
        
        plt.xlabel('Securities')
        plt.title('Top Holdings Analysis')
        plt.xticks([i + width/2 for i in x], securities, rotation=45)
        plt.legend()
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_png = buffer.getvalue()
        buffer.close()
        plt.close()
        
        return base64.b64encode(image_png).decode() 