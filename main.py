import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

# Import and run the Streamlit app
from frontend.app import AssetManagementApp

if __name__ == "__main__":
    app = AssetManagementApp()
    app.run() 