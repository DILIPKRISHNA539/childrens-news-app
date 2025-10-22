"""
Configuration file for Children's News App Data Pipeline

"""

import os
from dotenv import load_dotenv # type: ignore

# Load environment variables from .env file
load_dotenv()

# ============================================================
# API KEYS
# ============================================================
FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY', '')

# Google Gemini API - LiteLLM reads directly from GOOGLE_API_KEY environment variable
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')

# ============================================================
# LITELLM MODEL CONFIGURATION
# ============================================================
# Updated to Gemini 2.5 Flash (latest as of 2025, FREE tier)
# LITELLM_MODEL = os.getenv('LITELLM_MODEL', 'gemini-2.5-flash-lite')
GEMINI_MODEL_NAME = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-flash-lite')

# ============================================================
# MAIN NEWS SOURCES FOR POC (3 sources)
# ============================================================
NEWS_SOURCES = {
    'the_hindu': {
        'name': 'The Hindu',
        'type': 'rss',
        'url': 'https://www.thehindu.com/news/national/feeder/default.rss',
        'category': 'national',
        'language': 'english'
    },
    'hindustan_times': {
        'name': 'Hindustan Times',
        'type': 'scraper',
        'url': 'https://www.hindustantimes.com/india-news',
        'category': 'national',
        'language': 'english'
    },
    'indian_express': {
        'name': 'Indian Express',
        'type': 'firecrawl',
        'url': 'https://indianexpress.com/section/india/',
        'category': 'national',
        'language': 'english'
    }
}

# ============================================================
# ALL NEWS SOURCES (8-10 for documentation)
# ============================================================
ALL_NEWS_SOURCES = [
    {'name': 'The Hindu', 'url': 'https://www.thehindu.com/', 'type': 'RSS', 'country': 'India'},
    {'name': 'Hindustan Times', 'url': 'https://www.hindustantimes.com/', 'type': 'Scraper', 'country': 'India'},
    {'name': 'BBC News Asia', 'url': 'http://feeds.bbci.co.uk/news/world/asia/rss.xml', 'type': 'RSS', 'country': 'International'},
    {'name': 'Times of India', 'url': 'https://timesofindia.indiatimes.com/', 'type': 'RSS', 'country': 'India'},
    {'name': 'Indian Express', 'url': 'https://indianexpress.com/', 'type': 'Firecrawl', 'country': 'India'},
    {'name': 'NDTV', 'url': 'https://www.ndtv.com/', 'type': 'RSS', 'country': 'India'},
    {'name': 'The Wire', 'url': 'https://thewire.in/', 'type': 'Scraper', 'country': 'India'},
    {'name': 'Al Jazeera Asia', 'url': 'https://www.aljazeera.com/asia/', 'type': 'RSS', 'country': 'International'},
    {'name': 'The Guardian World', 'url': 'https://www.theguardian.com/world/rss', 'type': 'RSS', 'country': 'International'},
    {'name': 'Reuters World', 'url': 'https://www.reuters.com/', 'type': 'API/RSS', 'country': 'International'}
]

# ============================================================
# DATABASE CONFIGURATION
# ============================================================
DATABASE_PATH = 'news_database.db'
DATABASE_URL = f'sqlite:///{DATABASE_PATH}'

# ============================================================
# AGE GROUPS CONFIGURATION
# ============================================================
AGE_GROUPS = {
    'group_1': {
        'name': '6-8 years',
        'max_words': 50,
        'max_sentences': 3,
        'complexity': 'very_simple'
    },
    'group_2': {
        'name': '9-11 years',
        'max_words': 100,
        'max_sentences': 5,
        'complexity': 'simple'
    },
    'group_3': {
        'name': '12-14 years',
        'max_words': 150,
        'max_sentences': 8,
        'complexity': 'moderate'
    }
}

# ============================================================
# SENSITIVE KEYWORDS TO FILTER OUT
# ============================================================
SENSITIVE_KEYWORDS = [
    'murder', 'killed', 'death', 'violence', 'terrorist', 'bomb', 
    'rape', 'assault', 'abuse', 'suicide', 'war', 'shooting',
    'massacre', 'torture', 'kidnap', 'attack', 'wounded', 'injured',
    'blood', 'weapon', 'explosion', 'riot', 'dead', 'stabbed', 'shot dead',
    'corpse', 'brutal', 'slaughter', 'execution', 'hanging'
]

# ============================================================
# DATA EXTRACTION SETTINGS
# ============================================================
MAX_ARTICLES_PER_SOURCE = 10
FIRECRAWL_MAX_ARTICLES = 10
REQUEST_TIMEOUT = 30
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# ============================================================
# OUTPUT PATHS
# ============================================================
RAW_DATA_PATH = 'data/raw_articles.json'
CLEANED_DATA_PATH = 'data/cleaned_articles.json'
PROCESSED_DATA_PATH = 'data/processed_articles.json'