A smart data pipeline that extracts news articles from multiple Indian sources and converts them into child-friendly content for three age groups (6-8, 9-11, 12-14 years) using Google Gemini 2.5 Flash Lite AI.
🌟 Features

Multi-Source Extraction: RSS feeds, web scraping, and Firecrawl API
Smart Filtering: Removes sensitive/violent content before processing
AI Simplification: Uses Google Gemini 2.5 Flash Lite to rewrite articles in child-friendly language
Age-Appropriate Content: Automatically adjusts content length for three age groups
Hybrid Processing: One AI call per article + Python-based truncation for efficiency
100% FREE: Uses free tier of Google Gemini API

📊 Supported News Sources
Current POC (3 Sources)
SourceMethodCategoryThe HinduRSS FeedNational NewsHindustan TimesWeb ScrapingNational NewsIndian ExpressFirecrawl APINational News
Planned Expansion (8-10 Sources)

Times of India
NDTV
The Wire
BBC News Asia
Al Jazeera Asia
The Guardian World
Reuters World

🏗️ Architecture

   News Sources  
  (RSS/Web/API)  

         │
         ▼

│   Extractors    │
│  - RSS Parser   │
│  - Web Scraper  │
│  - Firecrawl    │

         │
         ▼

│  Data Cleaner   │
│  - Deduplicate  │
│  - Filter Sensitive

         │
         ▼

│ Gemini 2.5 AI   │
│  Simplification │
└────────┬────────┘
         │
         ▼

│ Age-Based       │
│ Truncation      │
│  (6-8, 9-11,    │
│   12-14 years)  │

         │
         ▼

│  JSON Output    │
│  (Processed)    │

🚀 Quick Start
Prerequisites

Python 3.8+
Google Gemini API Key (FREE)
Firecrawl API Key (optional, for Indian Express)

Installation

Clone the repository

bash   git clone https://github.com/yourusername/childrens-news-app.git
   cd childrens-news-app

Create virtual environment

bash   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # Mac/Linux
   source venv/bin/activate

Install dependencies

bash   pip install -r requirements.txt

Set up environment variables
Create a .env file in the root directory:

bash   # Google Gemini 2.5 Flash Lite API Key (FREE)
   GOOGLE_API_KEY=AIzaSy...your-key-here
   
   # Firecrawl API Key (Optional)
   FIRECRAWL_API_KEY=fc-...your-key-here
   
   # Model Configuration (Optional - defaults to gemini-2.5-flash-lite)
   LITELLM_MODEL=gemini/gemini-2.5-flash-lite

Create data directory

bash   mkdir data
Usage
Step 1: Extract News Articles
bashpython src/extractors.py

Extracts 10 articles from each source
Saves to data/raw_articles.json
Handles rate limiting automatically

Step 2: Process with AI
bashpython src/processors.py

Filters sensitive content
Simplifies with Gemini 2.5 Flash Lite
Generates age-appropriate versions
Saves to data/processed_articles.json

Test Gemini Connection
bashpython src/test_gemini.py

Verifies API key is working
Tests different model names
Shows available Gemini models

🔑 API Keys Setup
Google Gemini API (FREE)

Visit Google AI Studio
Sign in with your Google account
Click "Create API Key"
Copy the key (starts with AIzaSy...)
Add to .env file

Free Tier Limits:

15 requests per minute
1 million tokens per minute
1,500 requests per day
Cost: $0.00 ✨

Firecrawl API (Optional)

Visit Firecrawl.dev
Sign up for free account
Get API key from dashboard
Add to .env file

📂 Project Structure
childrens-news-app/
├── src/
│   ├── config.py              # Configuration & settings
│   ├── extractors.py          # News extraction logic
│   ├── processors.py          # AI processing & simplification
│   └── data_pipeline.py       # Runs full pipeline
│   ├── raw_articles.json      # Extracted articles
│   ├── cleaned_articles.json  # Filtered & cleaned
│   └── processed_articles.json # Age-appropriate versions
├── .env                       # API keys (DO NOT COMMIT)
├── .gitignore                 # Git ignore file
├── requirements.txt           # Python dependencies
└── README.md                  # This file
🎯 Age Group Configuration
Age GroupMax WordsSentencesComplexity6-8 years503Very Simple9-11 years1005Simple12-14 years1508Moderate
🛡️ Sensitive Content Filtering
The system automatically filters articles containing:

Violence (murder, killed, attack, shooting, etc.)
Terrorism (terrorist, bomb, explosion, etc.)
Crime (rape, assault, kidnap, etc.)
Graphic content (blood, weapon, corpse, etc.)

19 articles filtered in latest run! ✅
🤖 AI Processing Workflow
Hybrid Approach (Efficient & Cost-Effective)

Filter Sensitive Content - Before AI processing
Simplify Language - One Gemini API call per article
Truncate by Age - Python-based word count truncation

Benefits:

✅ Only 1 API call per article (vs. 3)
✅ Consistent simplification across age groups
✅ 67% cost reduction
✅ Faster processing

📊 Sample Output
Original Article
Title: "Climate finance must be duty, not promise: India to developed countries"
Content: Financial support to developing countries for tackling climate change should be 
treated as a duty by developed countries...
For 6-8 Years (50 words)
India says rich countries should help poor countries fight climate change. 
They should give money because it is their job, not just a promise. 
Climate change makes the weather strange and hurts many people...
For 9-11 Years (100 words)
India told rich countries they must help poor countries deal with climate change. 
Rich countries promised to give money but often don't keep their promise. 
India says this money should be their duty, not just something they might do. 
Climate change is making weather patterns change. This causes problems like floods...
For 12-14 Years (150 words)
India has told developed nations that financial support for climate change should be 
considered a responsibility, not just a voluntary promise. At the G20 Environment 
Ministers' Meeting, India emphasized that wealthy countries must fulfill their 
commitments to help developing nations tackle climate challenges...
🔧 Configuration
Edit src/config.py to customize:

Age groups: Modify word limits and complexity levels
News sources: Add/remove sources
Sensitive keywords: Update filtering criteria
Model selection: Change Gemini model version
Rate limits: Adjust delays between requests

📈 Performance

Extraction Speed: ~30 articles in 2-3 minutes
Processing Speed: ~11 articles in 1-2 minutes
API Tokens: ~200-300 tokens per article
Success Rate: 95%+ (with rate limit handling)

🐛 Troubleshooting
Common Issues
1. API Key Not Found
bash❌ GOOGLE_API_KEY not found in environment
Solution: Check your .env file and ensure the key is correct
2. Rate Limit Exceeded
bash❌ Rate limit hit! Wait a moment.
Solution: Wait 60 seconds and retry. The script has automatic delays.
3. Model Not Found
bash❌ litellm.NotFoundError: GeminiException
Solution: Update model name to gemini/gemini-2.5-flash-lite in .env
4. No Articles Extracted
bash⚠️ No articles extracted!
Solution: Check the internet connection and the source URLs
Debug Mode
Enable verbose logging:
python# In processors.py
litellm.set_verbose = True  # Change to True
🚦 Rate Limiting
The pipeline includes smart rate limiting:

Between articles: 1 second delay
Between age groups: 0.5 second delay
Between sources: 2 second delay
Rate limit retry: Automatic 35-second wait

🔒 Security

✅ API keys stored in .env (not in code)
✅ .env added to .gitignore
✅ No sensitive data in commits
✅ Input validation and sanitization
✅ Error handling for API failures


Google Gemini - AI model for text simplification
Firecrawl - Web scraping API
LiteLLM - Unified LLM interface
BeautifulSoup - HTML parsing
Feedparser - RSS feed parsing


