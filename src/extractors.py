"""
Data Extraction Module for Children's News App

"""

import feedparser
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import json
import time
from config import NEWS_SOURCES, MAX_ARTICLES_PER_SOURCE, REQUEST_TIMEOUT, USER_AGENT, RAW_DATA_PATH, FIRECRAWL_API_KEY, FIRECRAWL_MAX_ARTICLES

# Import Firecrawl
try:
    from firecrawl import Firecrawl # type: ignore
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False
    print("⚠️  Warning: firecrawl-py not installed. Install with: pip install firecrawl-py")


class RSSExtractor:
    """Extract news articles from RSS feeds"""
    
    def __init__(self, source_config):
        self.source_name = source_config['name']
        self.url = source_config['url']
        self.category = source_config.get('category', 'general')
        self.headers = {'User-Agent': USER_AGENT}
        
    def extract(self):
        """Extract articles from RSS feed"""
        print(f"\n🔍 Extracting from {self.source_name} (RSS Feed)...")
        
        try:
            # Parse the RSS feed
            feed = feedparser.parse(self.url)
            
            if feed.bozo:
                print(f"⚠️  Warning: Feed parsing issue for {self.source_name}")
            
            articles = []
            total_to_fetch = min(len(feed.entries), MAX_ARTICLES_PER_SOURCE)
            
            # Extract articles
            for idx, entry in enumerate(feed.entries[:MAX_ARTICLES_PER_SOURCE], 1):
                print(f"  📄 Article {idx}/{total_to_fetch}: {entry.get('title', 'No Title')[:60]}...")
                
                # Get full article content
                full_content = self._fetch_full_article(entry.get('link', ''))
                
                article = {
                    'source': self.source_name,
                    'title': entry.get('title', 'No Title'),
                    'description': entry.get('summary', entry.get('description', '')),
                    'url': entry.get('link', ''),
                    'published_date': self._parse_date(entry),
                    'category': self.category,
                    'extraction_method': 'rss',
                    'raw_content': full_content if full_content else entry.get('summary', entry.get('description', '')),
                    'extracted_at': datetime.now().isoformat()
                }
                articles.append(article)
                
                # Small delay
                time.sleep(0.5)
            
            print(f"✅ Successfully extracted {len(articles)} articles from {self.source_name}")
            return articles
            
        except Exception as e:
            print(f"❌ Error extracting from {self.source_name}: {str(e)}")
            return []
    
    def _fetch_full_article(self, url):
        """Fetch full article content from URL"""
        if not url:
            return ""
        
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe']):
                element.decompose()
            
            # The Hindu specific
            if 'thehindu.com' in url:
                article_body = soup.find('div', class_='articlebodycontent') or soup.find('article')
                if article_body:
                    paragraphs = article_body.find_all('p')
                    content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                    return content[:2000]
            
            # Generic extraction
            article_body = soup.find('article') or soup.find('div', class_='article-body')
            if article_body:
                paragraphs = article_body.find_all('p')
                content = ' '.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                return content[:2000]
            
            return ""
            
        except:
            return ""
    
    def _parse_date(self, entry):
        """Parse and standardize date from RSS entry"""
        try:
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                return datetime(*entry.published_parsed[:6]).isoformat()
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                return datetime(*entry.updated_parsed[:6]).isoformat()
            else:
                return datetime.now().isoformat()
        except:
            return datetime.now().isoformat()


class WebScraper:
    """Scrape news articles from websites"""
    
    def __init__(self, source_config):
        self.source_name = source_config['name']
        self.url = source_config['url']
        self.category = source_config.get('category', 'general')
        self.headers = {'User-Agent': USER_AGENT}
        
    def extract(self):
        """Extract articles by scraping the website"""
        print(f"\n🔍 Extracting from {self.source_name} (Web Scraping)...")
        
        try:
            # Fetch the page
            response = requests.get(self.url, headers=self.headers, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Route to appropriate scraper
            if 'hindustantimes.com' in self.url.lower():
                articles = self._scrape_hindustan_times(soup)
            elif 'ndtv.com' in self.url.lower():
                articles = self._scrape_ndtv(soup)
            elif 'thewire.in' in self.url.lower():
                articles = self._scrape_the_wire(soup)
            else:
                articles = self._scrape_generic(soup)
            
            print(f"✅ Successfully scraped {len(articles)} articles from {self.source_name}")
            return articles
            
        except Exception as e:
            print(f"❌ Error scraping {self.source_name}: {str(e)}")
            return []
    
    def _scrape_hindustan_times(self, soup):
        """Scraper for Hindustan Times - Enhanced with full content fetching"""
        articles = []
        print(f"  🔎 Searching for articles on page...")
        
        # HT uses 'cartHolder' and 'bigCart' classes
        article_containers = soup.find_all('div', class_=['cartHolder', 'bigCart', 'listView'])
        
        # Also try finding h3 tags with links
        if not article_containers:
            article_containers = soup.find_all('div', class_='media-box')
        
        # Fallback: find all article tags
        if not article_containers:
            article_containers = soup.find_all('article')
        
        print(f"  📦 Found {len(article_containers)} potential article containers")
        
        count = 0
        for container in article_containers:
            if count >= MAX_ARTICLES_PER_SOURCE:
                break
                
            try:
                # Find the link/title
                link_tag = container.find('a')
                if not link_tag:
                    continue
                
                # Get title - could be in the link text or in an h3/h2 tag
                title_tag = container.find(['h1', 'h2', 'h3', 'h4'])
                if title_tag:
                    title = title_tag.get_text(strip=True)
                else:
                    title = link_tag.get_text(strip=True)
                
                # Skip if title is too short
                if not title or len(title) < 15:
                    continue
                
                # Get URL
                url = link_tag.get('href', '')
                if url and not url.startswith('http'):
                    url = f"https://www.hindustantimes.com{url}"
                
                # Get description from listing page
                desc_tag = container.find('p')
                description = desc_tag.get_text(strip=True) if desc_tag else ''
                
                # IMPORTANT: Fetch full article content from the article page
                print(f"  📄 Fetching full content for: {title[:40]}...")
                full_content = self._fetch_ht_article(url) if url else description
                
                # Only add if we got substantial content
                if full_content and len(full_content) > 100:
                    article = {
                        'source': self.source_name,
                        'title': title,
                        'description': description if description else full_content[:200],
                        'url': url,
                        'published_date': datetime.now().isoformat(),
                        'category': self.category,
                        'extraction_method': 'scraper',
                        'raw_content': full_content,
                        'extracted_at': datetime.now().isoformat()
                    }
                    articles.append(article)
                    count += 1
                    print(f"  ✓ Article {count}: {title[:50]}... ({len(full_content)} chars)")
                else:
                    print(f"  ⚠️  Skipped (insufficient content): {title[:40]}...")
                
                # Delay between requests to be polite
                time.sleep(1)
                
            except Exception as e:
                print(f"  ⚠️  Error processing article: {str(e)}")
                continue
        
        return articles
    
    def _fetch_ht_article(self, url):
        """Fetch full article from Hindustan Times - Enhanced"""
        if not url:
            return ""
        
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for el in soup.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'noscript']):
                el.decompose()
            
            # Try multiple possible article content containers for HT
            article_body = None
            
            # Method 1: Look for common article content divs
            article_body = (
                soup.find('div', class_='detail') or
                soup.find('div', class_='storyDetails') or
                soup.find('div', class_='story-details') or
                soup.find('div', class_='contentbody') or
                soup.find('div', class_='story') or
                soup.find('article', class_='main-article')
            )
            
            # Method 2: Look for article tag
            if not article_body:
                article_body = soup.find('article')
            
            # Method 3: Look for div with 'article' in class name
            if not article_body:
                article_body = soup.find('div', class_=lambda x: x and 'article' in x.lower())
            
            if article_body:
                # Extract all paragraphs
                paragraphs = article_body.find_all('p')
                
                # Filter out very short paragraphs (likely ads or metadata)
                content_paragraphs = [
                    p.get_text(strip=True) 
                    for p in paragraphs 
                    if len(p.get_text(strip=True)) > 30  # Only paragraphs with 30+ chars
                ]
                
                if content_paragraphs:
                    content = ' '.join(content_paragraphs)
                    # Return first 2000 characters
                    return content[:2000] if len(content) > 2000 else content
            
            # Fallback: Try to get any substantial text
            all_paragraphs = soup.find_all('p')
            content_paragraphs = [
                p.get_text(strip=True) 
                for p in all_paragraphs 
                if len(p.get_text(strip=True)) > 50
            ]
            
            if content_paragraphs:
                content = ' '.join(content_paragraphs[:10])  # Take first 10 substantial paragraphs
                return content[:2000] if len(content) > 2000 else content
            
            return ""
            
        except Exception as e:
            print(f"      ⚠️  Could not fetch article: {str(e)[:50]}")
            return ""
    
    def _scrape_ndtv(self, soup):
        """Scraper for NDTV"""
        articles = []
        
        # NDTV patterns
        article_elements = (
            soup.find_all('div', class_='news_Itm') or
            soup.find_all('div', class_='new_storylising')
        )[:MAX_ARTICLES_PER_SOURCE]
        
        for element in article_elements:
            try:
                link_tag = element.find('a')
                if not link_tag:
                    continue
                
                title = link_tag.get_text(strip=True)
                url = link_tag.get('href', '')
                
                if url and not url.startswith('http'):
                    url = f"https://www.ndtv.com{url}"
                
                desc_tag = element.find('p')
                description = desc_tag.get_text(strip=True) if desc_tag else ''
                
                if title and len(title) > 10:
                    article = {
                        'source': self.source_name,
                        'title': title,
                        'description': description,
                        'url': url,
                        'published_date': datetime.now().isoformat(),
                        'category': self.category,
                        'extraction_method': 'scraper',
                        'raw_content': description,
                        'extracted_at': datetime.now().isoformat()
                    }
                    articles.append(article)
                    
            except:
                continue
        
        return articles
    
    def _scrape_the_wire(self, soup):
        """Scraper for The Wire"""
        articles = []
        
        article_elements = soup.find_all('article')[:MAX_ARTICLES_PER_SOURCE]
        
        for element in article_elements:
            try:
                title_tag = element.find(['h3', 'h2'])
                if not title_tag:
                    continue
                
                link_tag = title_tag.find('a')
                title = title_tag.get_text(strip=True)
                url = link_tag.get('href', '') if link_tag else ''
                
                if url and not url.startswith('http'):
                    url = f"https://thewire.in{url}"
                
                desc_tag = element.find('p')
                description = desc_tag.get_text(strip=True) if desc_tag else ''
                
                if title:
                    article = {
                        'source': self.source_name,
                        'title': title,
                        'description': description,
                        'url': url,
                        'published_date': datetime.now().isoformat(),
                        'category': self.category,
                        'extraction_method': 'scraper',
                        'raw_content': description,
                        'extracted_at': datetime.now().isoformat()
                    }
                    articles.append(article)
                    
            except:
                continue
        
        return articles
    
    def _scrape_generic(self, soup):
        """Generic fallback scraper"""
        articles = []
        
        # Try common patterns
        article_elements = (
            soup.find_all('article')[:MAX_ARTICLES_PER_SOURCE] or
            soup.find_all('div', class_=lambda x: x and 'article' in str(x).lower())[:MAX_ARTICLES_PER_SOURCE]
        )
        
        for element in article_elements:
            try:
                title_tag = element.find(['h1', 'h2', 'h3', 'h4'])
                if not title_tag:
                    continue
                
                title = title_tag.get_text(strip=True)
                link_tag = element.find('a')
                url = link_tag.get('href', '') if link_tag else ''
                
                desc_tag = element.find('p')
                description = desc_tag.get_text(strip=True) if desc_tag else ''
                
                if title and len(title) > 10:
                    article = {
                        'source': self.source_name,
                        'title': title,
                        'description': description,
                        'url': url,
                        'published_date': datetime.now().isoformat(),
                        'category': self.category,
                        'extraction_method': 'scraper',
                        'raw_content': description,
                        'extracted_at': datetime.now().isoformat()
                    }
                    articles.append(article)
                    
            except:
                continue
        
        return articles


class FirecrawlExtractor:
    """Extract news articles using Firecrawl API"""
    
    def __init__(self, source_config):
        self.source_name = source_config['name']
        self.url = source_config['url']
        self.category = source_config.get('category', 'general')
        self.api_key = FIRECRAWL_API_KEY
        
        if not FIRECRAWL_AVAILABLE:
            raise ImportError("Firecrawl library not available. Install with: pip install firecrawl-py")
        
        if not self.api_key:
            raise ValueError("FIRECRAWL_API_KEY not found in environment variables")
        
        # Use the newer Firecrawl class instead of FirecrawlApp
        from firecrawl import Firecrawl
        self.app = Firecrawl(api_key=self.api_key)
    
    def extract(self):
        """Extract articles using Firecrawl API"""
        print(f"\n🔍 Extracting from {self.source_name} (Firecrawl API)...")
        
        try:
            # First, scrape the main page to get article links
            print(f"  🌐 Crawling main page: {self.url}")
            
            # Use Firecrawl's scrape endpoint to get the listing page
            main_page = self.app.scrape(self.url, formats=['markdown', 'html'])
            
            # Parse the HTML to find article links
            # Firecrawl returns a Document object with attributes
            html_content = getattr(main_page, 'html', '')
            soup = BeautifulSoup(html_content, 'html.parser')
            article_links = self._extract_article_links(soup)
            
            print(f"  📰 Found {len(article_links)} article links")
            
            # Limit to configured max articles
            article_links = article_links[:FIRECRAWL_MAX_ARTICLES]
            
            articles = []
            
            # Now scrape each article individually
            for idx, link in enumerate(article_links, 1):
                try:
                    print(f"  📄 Article {idx}/{len(article_links)}: Fetching {link[:60]}...")
                    
                    # Scrape individual article
                    article_data = self.app.scrape(link, formats=['markdown', 'html'])
                    
                    # Extract structured data
                    article = self._parse_article(article_data, link)
                    
                    if article:
                        articles.append(article)
                        print(f"  ✓ Extracted: {article['title'][:50]}... ({len(article['raw_content'])} chars)")
                    
                    # IMPORTANT: Rate limiting - wait between requests
                    # Firecrawl free tier: 10 requests/minute
                    # Wait 7 seconds between requests to stay under limit
                    if idx < len(article_links):  # Don't wait after last article
                        print(f"  ⏳ Waiting 7 seconds (rate limiting)...")
                        time.sleep(7)
                    
                except Exception as e:
                    error_msg = str(e)
                    if "Rate Limit" in error_msg:
                        print(f"  ⚠️  Rate limit hit! Waiting 35 seconds...")
                        time.sleep(35)
                        # Retry once
                        try:
                            article_data = self.app.scrape(link, formats=['markdown', 'html'])
                            article = self._parse_article(article_data, link)
                            if article:
                                articles.append(article)
                                print(f"  ✓ Retry successful: {article['title'][:50]}...")
                        except:
                            print(f"  ❌ Retry failed, skipping article")
                    else:
                        print(f"  ⚠️  Error fetching article {link}: {error_msg[:100]}")
                    continue
            
            print(f"✅ Successfully extracted {len(articles)} articles from {self.source_name} via Firecrawl")
            return articles
            
        except Exception as e:
            print(f"❌ Error with Firecrawl extraction from {self.source_name}: {str(e)}")
            return []
    
    def _extract_article_links(self, soup):
        """Extract article links from Indian Express listing page"""
        links = []
        
        # Indian Express specific patterns
        # Look for article links in common containers
        article_containers = soup.find_all('div', class_=['articles', 'ie-first-story', 'ie-story'])
        
        # Also try finding h2/h3 with links
        if not article_containers:
            article_containers = soup.find_all(['article', 'div'], class_=lambda x: x and 'story' in str(x).lower())
        
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
                if '/article/' in href or '/india/' in href or '/section/india/' in href:
                    if href not in links:
                        links.append(href)
        
        return links
    
    def _parse_article(self, article_data, url):
        """Parse article data from Firecrawl response (Document object)"""
        try:
            # Firecrawl returns a Document object with direct attributes
            markdown_content = getattr(article_data, 'markdown', '')
            metadata_obj = getattr(article_data, 'metadata', None)
            
            # Access metadata attributes directly (not as dict)
            # DocumentMetadata has attributes: title, description, language, etc.
            title = getattr(metadata_obj, 'title', '') if metadata_obj else ''
            
            if not title and markdown_content:
                # Fallback: extract from markdown
                lines = markdown_content.split('\n')
                for line in lines:
                    if line.strip() and not line.startswith('#') and len(line.strip()) > 15:
                        title = line.strip('# ').strip()
                        break
            
            # Extract description from metadata
            description = getattr(metadata_obj, 'description', '') if metadata_obj else ''
            if not description and markdown_content:
                # Use first paragraph as description
                paragraphs = [p.strip() for p in markdown_content.split('\n\n') if p.strip() and not p.startswith('#')]
                description = paragraphs[0][:200] if paragraphs else ''
            
            # Get publication date from metadata
            # Try multiple possible field names
            pub_date = datetime.now().isoformat()
            if metadata_obj:
                # Firecrawl uses various metadata fields for dates
                pub_date = (
                    getattr(metadata_obj, 'publishedTime', None) or 
                    getattr(metadata_obj, 'modifiedTime', None) or
                    getattr(metadata_obj, 'published_time', None) or 
                    getattr(metadata_obj, 'modified_time', None) or
                    datetime.now().isoformat()
                )
            
            # Clean up markdown content (remove headers, keep main text)
            content_lines = markdown_content.split('\n')
            clean_content = ' '.join([
                line.strip('# ').strip() 
                for line in content_lines 
                if line.strip() and not line.startswith('![') and not line.startswith('[')
            ])
            
            # Limit content length
            raw_content = clean_content[:2000] if len(clean_content) > 2000 else clean_content
            
            if not title or len(raw_content) < 100:
                return None
            
            return {
                'source': self.source_name,
                'title': title,
                'description': description,
                'url': url,
                'published_date': pub_date,
                'category': self.category,
                'extraction_method': 'firecrawl',
                'raw_content': raw_content,
                'extracted_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"    ⚠️  Error parsing article: {str(e)}")
            return None


class DataExtractor:
    """Main extractor class"""
    
    def __init__(self):
        self.sources = NEWS_SOURCES
        
    def extract_all(self):
        """Extract from all configured sources"""
        print("\n" + "="*70)
        print("🚀 CHILDREN'S NEWS APP - DATA EXTRACTION")
        print("="*70)
        
        all_articles = []
        
        for source_key, source_config in self.sources.items():
            print(f"\n📰 Processing: {source_config['name']} ({source_config['type'].upper()})")
            
            try:
                if source_config['type'] == 'rss':
                    extractor = RSSExtractor(source_config)
                elif source_config['type'] == 'scraper':
                    extractor = WebScraper(source_config)
                elif source_config['type'] == 'firecrawl':
                    extractor = FirecrawlExtractor(source_config)
                else:
                    print(f"⚠️  Unknown type: {source_config['type']}")
                    continue
                
                articles = extractor.extract()
                all_articles.extend(articles)
                
                # Be polite - delay between sources
                time.sleep(2)
                
            except Exception as e:
                print(f"❌ Error processing {source_config['name']}: {str(e)}")
                continue
        
        print("\n" + "="*70)
        print(f"✅ EXTRACTION COMPLETE!")
        print(f"📊 Total Articles Extracted: {len(all_articles)}")
        print("="*70)
        
        return all_articles
    
    def save_raw_data(self, articles, filepath=RAW_DATA_PATH):
        """Save extracted articles to JSON"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Raw data saved to: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error saving data: {str(e)}")
            return False


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("\n" + "🎯 Starting Data Extraction Module..." + "\n")
    
    # Create extractor
    extractor = DataExtractor()
    
    # Extract all articles
    articles = extractor.extract_all()
    
    # Save raw data
    if articles:
        extractor.save_raw_data(articles)
        
        # Show sample
        print("\n" + "="*70)
        print("📰 SAMPLE ARTICLE")
        print("="*70)
        sample = articles[0]
        print(f"Title: {sample['title']}")
        print(f"Source: {sample['source']}")
        print(f"Method: {sample['extraction_method']}")
        print(f"URL: {sample['url']}")
        print(f"Content Preview: {sample['raw_content'][:200]}...")
        print("="*70)
    else:
        print("\n❌ No articles extracted!")