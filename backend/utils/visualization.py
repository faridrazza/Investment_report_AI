import matplotlib.pyplot as plt
import io
import base64

class PortfolioVisualizer:
    def __init__(self):
        # Use a built-in style that's clean and modern
        plt.style.use('fivethirtyeight')
        
    def create_asset_allocation_pie(self, allocation_data):
        """Create pie chart for asset allocation"""
        try:
            # Clear any existing plots
            plt.clf()
            
            # Create figure with specific size and DPI
            plt.figure(figsize=(10, 8), dpi=100, facecolor='white')
            
            # Extract data
            labels = []
            sizes = []
            colors = ['#FF9999', '#66B2FF', '#99FF99', '#FFCC99']
            
            for asset_type, data in allocation_data.items():
                labels.append(asset_type.title())
                sizes.append(data['percentage'])
            
            # Create pie chart with improved styling
            plt.pie(sizes, 
                   labels=labels,
                   colors=colors,
                   autopct='%1.1f%%',
                   startangle=90,
                   pctdistance=0.85,
                   textprops={'fontsize': 12, 'color': 'black'},
                   wedgeprops={'width': 0.7, 'edgecolor': 'white'})
            
            plt.title('Asset Allocation', pad=20, fontsize=14, fontweight='bold', color='black')
            
            # Ensure the pie is drawn as a circle
            plt.axis('equal')
            
            # Add padding
            plt.tight_layout(pad=3.0)
            
            # Save to buffer with white background
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight', 
                       facecolor='white', edgecolor='none',
                       transparent=False)
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            plt.close()
            
            return base64.b64encode(image_png).decode()
            
        except Exception as e:
            print(f"Error creating pie chart: {str(e)}")
            return ""

    def create_performance_chart(self, performance_data):
        """Create line graph for performance metrics"""
        try:
            plt.clf()
            plt.figure(figsize=(12, 6), dpi=100, facecolor='white')
            
            # Define periods and values
            periods = ['YTD', '1 Year', '3 Year', '5 Year', 'Since Inception']
            values = [
                performance_data['ytd'],
                performance_data['1year'],
                performance_data['3year'],
                performance_data['5year'],
                performance_data['sinceInception']
            ]
            
            # Create line plot with markers
            plt.plot(periods, values, marker='o', linewidth=2, markersize=8, 
                    color='#2c5282', label='Return')
            
            # Add value labels above points
            for i, value in enumerate(values):
                plt.text(i, value + 0.5, f'{value:.1f}%', 
                        ha='center', va='bottom', fontsize=10, color='black')
            
            # Customize the plot
            plt.title('Performance History', pad=20, fontsize=14, fontweight='bold', color='black')
            plt.ylabel('Return (%)', fontsize=12, color='black')
            plt.grid(True, alpha=0.3, linestyle='--')
            
            # Customize axes
            plt.xticks(range(len(periods)), periods, rotation=45, ha='right', fontsize=10, color='black')
            plt.yticks(color='black')
            
            # Add light background grid
            plt.grid(True, linestyle='--', alpha=0.3)
            
            # Add padding and ensure proper layout
            plt.tight_layout(pad=3.0)
            
            # Save to buffer
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                       facecolor='white', edgecolor='none',
                       transparent=False,
                       dpi=100)
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            plt.close()
            
            return base64.b64encode(image_png).decode()
            
        except Exception as e:
            print(f"Error creating performance chart: {str(e)}")
            print(f"Performance data received: {performance_data}")  # Debug log
            return ""

    def create_holdings_chart(self, holdings_data):
        """Create bar chart for top holdings"""
        try:
            plt.clf()
            plt.figure(figsize=(10, 6), dpi=100, facecolor='white')
            
            securities = [holding['name'] for holding in holdings_data]
            weights = [holding['weight'] for holding in holdings_data]
            gains = [holding['gain'] for holding in holdings_data]
            
            x = range(len(securities))
            width = 0.35
            
            # Create bars with better colors
            plt.bar(x, weights, width, label='Weight (%)', color='#4299E1')
            plt.bar([i + width for i in x], gains, width, label='Gain ($)', color='#48BB78')
            
            plt.xlabel('Securities', fontsize=12, color='black')
            plt.title('Top Holdings Analysis', pad=20, fontsize=14, fontweight='bold', color='black')
            plt.xticks([i + width/2 for i in x], securities, rotation=45, ha='right', fontsize=10, color='black')
            plt.yticks(color='black')
            plt.legend(fontsize=10)
            
            plt.tight_layout(pad=3.0)
            
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight',
                       facecolor='white', edgecolor='none',
                       transparent=False)
            buffer.seek(0)
            image_png = buffer.getvalue()
            buffer.close()
            plt.close()
            
            return base64.b64encode(image_png).decode()
            
        except Exception as e:
            print(f"Error creating holdings chart: {str(e)}")
            return "" 