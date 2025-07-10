# Environment Setup Guide

This guide will help you set up the necessary environment variables and dependencies to fix the ChatOpenAI initialization error.

## 1. Create Environment File

Create a `.env` file in the project root directory with the following content:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Alpha Vantage API Configuration (for market data)
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_api_key_here

# Optional: OpenAI Organization ID
OPENAI_ORG_ID=your_organization_id_here

# Optional: Custom OpenAI API Base URL
OPENAI_API_BASE=https://api.openai.com/v1
```

## 2. Get Your API Keys

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in to your account
3. Click "Create new secret key"
4. Copy the key and replace `your_openai_api_key_here` in your `.env` file

### Alpha Vantage API Key
1. Go to [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Sign up for a free account
3. Get your API key from the dashboard
4. Replace `your_alpha_vantage_api_key_here` in your `.env` file

## 3. Update Dependencies

Run the following command to install the updated dependencies:

```bash
pip install -r requirements.txt
```

## 4. Verify Setup

Your `.env` file should look like this (with actual keys):

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ALPHA_VANTAGE_API_KEY=XXXXXXXXXXXXXXXX
```

## 5. Common Issues and Solutions

### Issue: "ChatOpenAI is not fully defined" Error
**Solution**: This is fixed by the updated code which includes:
- Proper Pydantic v2 compatibility
- Model rebuilding for ChatOpenAI
- Better error handling

### Issue: Missing dependencies
**Solution**: Run:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Issue: Import errors
**Solution**: Make sure you're in the correct directory and run:
```bash
python -m pip install langchain==0.3.18 langchain-openai==0.3.5 pydantic>=2.0.0
```

## 6. Test Your Setup

Run the application:
```bash
streamlit run main.py
```

If you see the application load without errors, your setup is successful!

## Security Note

Never commit your `.env` file to version control. The `.env` file is already included in `.gitignore` to prevent accidental commits. 