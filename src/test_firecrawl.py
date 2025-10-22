"""
Standalone Firecrawl Test Script
Tests the Firecrawl API integration for Indian Express

"""

import os
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from datetime import datetime
import time
import json

# Load environment variables
load_dotenv()

# Configuration
FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY', '')
FIRECRAWL_MAX_ARTICLES = 10

# Import Firecrawl
try:
    from firecrawl import Firecrawl
    print("✅ Firecrawl library imported successfully")
except ImportError:
    print("❌ Firecrawl library not found. Install with: pip install firecrawl-py")
    exit(1)

# Check API key
if not FIRECRAWL_API_KEY:
    print("❌ FIRECRAWL_API_KEY not found in .env file")
    print("Please add: FIRECRAWL_API_KEY=your_api_key_here")
    exit(1)
else:
    print(f"✅ API Key found: {FIRECRAWL_API_KEY[:10]}...")


def test_firecrawl():
    """Test Firecrawl extraction for Indian Express"""
    
    print("\n" + "="*70)
    print("🔥 FIRECRAWL TEST - INDIAN EXPRESS")
    print("="*70)
    
    # Initialize Firecrawl
    try:
        app = Firecrawl(api_key=FIRECRAWL_API_KEY)
        print("✅ Firecrawl client initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Firecrawl: {str(e)}")
        return
    
    # Test URL
    url = "https://indianexpress.com/section/india/"
    print(f"\n📰 Target URL: {url}")
    
    # Step 1: Scrape the main listing page
    print("\n" + "-"*70)
    print("STEP 1: Scraping main listing page...")
    print("-"*70)
    
    try:
        print("  🌐 Calling Firecrawl API...")
        main_page_result = app.scrape(url, formats=['markdown', 'html'])
        print("  ✅ API call successful!")
        
        # Debug: Check response type
        print(f"  📦 Response type: {type(main_page_result)}")
        print(f"  📦 Response attributes: {dir(main_page_result)}")
        
        # Access the data from the response
        if hasattr(main_page_result, 'data'):
            main_page = main_page_result.data
            print("  ✅ Extracted data from response.data")
        else:
            main_page = main_page_result
            print("  ✅ Using response directly")
        
        # Debug: Check data type
        print(f"  📦 Data type: {type(main_page)}")
        
        # Get HTML content
        if isinstance(main_page, dict):
            html_content = main_page.get('html', '')
            markdown_content = main_page.get('markdown', '')
        else:
            html_content = getattr(main_page, 'html', '')
            markdown_content = getattr(main_page, 'markdown', '')
        
        print(f"  📄 HTML length: {len(html_content)} characters")
        print(f"  📄 Markdown length: {len(markdown_content)} characters")
        
        # Save raw HTML for inspection
        with open('debug_main_page.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("  💾 Saved raw HTML to debug_main_page.html")
        
    except Exception as e:
        print(f"  ❌ Error scraping main page: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 2: Extract article links
    print("\n" + "-"*70)
    print("STEP 2: Extracting article links...")
    print("-"*70)
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        print("  ✅ HTML parsed with BeautifulSoup")
        
        # Find article links
        article_links = []
        
        # Method 1: Look for article containers
        article_containers = soup.find_all('div', class_=['articles', 'ie-first-story', 'ie-story'])
        print(f"  🔍 Found {len(article_containers)} article containers (method 1)")
        
        # Method 2: Look for any story divs
        if not article_containers:
            article_containers = soup.find_all(['article', 'div'], class_=lambda x: x and 'story' in str(x).lower())
            print(f"  🔍 Found {len(article_containers)} article containers (method 2)")
        
        # Method 3: Just find all links in the page
        if not article_containers:
            print("  🔍 Using fallback method - finding all links...")
            all_links = soup.find_all('a', href=True)
            print(f"  🔍 Found {len(all_links)} total links")
        
        # Extract links
        for container in article_containers:
            link_tag = container.find('a', href=True)
            if link_tag:
                href = link_tag['href']
                
                # Make sure it's a full URL
                if href.startswith('/'):
                    href = f"https://indianexpress.com{href}"
                elif not href.startswith('http'):
                    continue
                
                # Filter out non-article links
                if '/article/' in href or '/india/' in href:
                    if href not in article_links:
                        article_links.append(href)
        
        # Fallback: try to find article links from all links
        if not article_links:
            print("  ⚠️  No article links found in containers, trying all links...")
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                if href.startswith('/'):
                    href = f"https://indianexpress.com{href}"
                if 'indianexpress.com' in href and any(x in href for x in ['/article/', '/india/', '/section/india/']):
                    if href not in article_links and len(article_links) < 20:
                        article_links.append(href)
        
        print(f"  ✅ Extracted {len(article_links)} article links")
        
        # Show first few links
        print("\n  📋 Sample article links:")
        for i, link in enumerate(article_links[:5], 1):
            print(f"    {i}. {link}")
        
    except Exception as e:
        print(f"  ❌ Error extracting links: {str(e)}")
        import traceback
        traceback.print_exc()
        return
    
    # Step 3: Scrape individual articles
    print("\n" + "-"*70)
    print("STEP 3: Scraping individual articles...")
    print("-"*70)
    
    articles = []
    max_to_scrape = min(3, len(article_links))  # Test with 3 articles first
    
    for idx, link in enumerate(article_links[:max_to_scrape], 1):
        try:
            print(f"\n  📄 Article {idx}/{max_to_scrape}")
            print(f"    URL: {link[:70]}...")
            
            # Scrape the article
            article_result = app.scrape(link, formats=['markdown', 'html'])
            
            # Access the data
            if hasattr(article_result, 'data'):
                article_data = article_result.data
            else:
                article_data = article_result
            
            # Extract content
            if isinstance(article_data, dict):
                markdown = article_data.get('markdown', '')
                metadata = article_data.get('metadata', {})
            else:
                markdown = getattr(article_data, 'markdown', '')
                metadata = getattr(article_data, 'metadata', {})
            
            # Convert metadata to dict if needed
            if not isinstance(metadata, dict):
                metadata = vars(metadata) if hasattr(metadata, '__dict__') else {}
            
            # Get title
            title = metadata.get('title', 'No Title')
            
            # Get description
            description = metadata.get('description', '')
            
            # Clean content
            if markdown:
                lines = [line.strip() for line in markdown.split('\n') if line.strip()]
                content = ' '.join(lines[:20])  # First 20 lines
            else:
                content = ''
            
            print(f"    ✅ Title: {title[:60]}...")
            print(f"    📝 Content length: {len(content)} chars")
            print(f"    📊 Metadata keys: {list(metadata.keys())}")
            
            article = {
                'source': 'Indian Express',
                'title': title,
                'description': description,
                'url': link,
                'published_date': metadata.get('publishedTime', datetime.now().isoformat()),
                'category': 'national',
                'extraction_method': 'firecrawl',
                'raw_content': content[:2000],
                'extracted_at': datetime.now().isoformat()
            }
            
            articles.append(article)
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            print(f"    ❌ Error: {str(e)}")
            continue
    
    # Step 4: Show results
    print("\n" + "="*70)
    print("📊 EXTRACTION RESULTS")
    print("="*70)
    print(f"✅ Successfully extracted {len(articles)} articles")
    
    if articles:
        print("\n" + "-"*70)
        print("📰 SAMPLE ARTICLE")
        print("-"*70)
        sample = articles[0]
        print(f"Title: {sample['title']}")
        print(f"URL: {sample['url']}")
        print(f"Description: {sample['description'][:100]}...")
        print(f"Content preview: {sample['raw_content'][:200]}...")
        
        # Save to JSON
        with open('test_firecrawl_results.json', 'w', encoding='utf-8') as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)
        print("\n💾 Results saved to test_firecrawl_results.json")
    
    print("\n" + "="*70)
    print("✅ FIRECRAWL TEST COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    test_firecrawl()