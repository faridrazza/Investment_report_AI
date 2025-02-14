from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    @staticmethod
    def get_env_variable(name: str, default: str = None) -> str:
        value = os.getenv(name, default)
        if value is None:
            raise ValueError(f"{name} environment variable is not set")
        return value

    # API Keys with validation
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    
    # Add Alpha Vantage API Key
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not ALPHA_VANTAGE_API_KEY:
        raise ValueError("ALPHA_VANTAGE_API_KEY environment variable is not set")
    
    # Model settings
    MODEL_NAME = "gpt-4-turbo-preview"
    EMBEDDING_MODEL = "text-embedding-3-small"
    
    # Vector store settings
    VECTOR_STORE_PATH = "vector_store"
    
    # Report generation settings
    REPORT_TEMPLATE_PATH = "templates/report_template.html"
    
    # Add debug mode
    DEBUG = True 