"""
Data Processing Module for Children's News App (Direct Google API)

Workflow:
1. Filter out sensitive articles FIRST
2. Simplify language once using Gemini (child-friendly rewrite)
3. Truncate simplified text by word count for each age group
"""

import re
import json
import os
import time
from datetime import datetime
from config import (
    SENSITIVE_KEYWORDS,
    AGE_GROUPS,
    CLEANED_DATA_PATH,
    PROCESSED_DATA_PATH,
    GEMINI_MODEL_NAME,  # <-- Renamed this variable
    GOOGLE_API_KEY
)

# Import Google Generative AI
try:
    import google.generativeai as genai
    from google.api_core.exceptions import ResourceExhausted, NotFound
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    print("⚠️  Warning: google-generativeai not installed. Install with: pip install google-generativeai")


class DataCleaner:
    """Clean and standardize extracted news data"""

    def __init__(self):
        self.sensitive_keywords = [kw.lower() for kw in SENSITIVE_KEYWORDS]

    def clean_all(self, articles):
        """Main cleaning pipeline"""
        print("\n" + "="*70)
        print("🧹 DATA CLEANING & DEDUPLICATION")
        print("="*70)

        print(f"\n📊 Input: {len(articles)} articles")

        # Step 1: Clean text
        print("  🔧 Step 1: Cleaning text...")
        cleaned = [self._clean_article(art) for art in articles]

        # Step 2: Remove duplicates
        print("  🔧 Step 2: Removing duplicates...")
        deduplicated = self._remove_duplicates(cleaned)
        print(f"  ✓ Removed {len(cleaned) - len(deduplicated)} duplicates")

        # Step 3: FILTER SENSITIVE CONTENT FIRST (before AI processing)
        print("  🔧 Step 3: Filtering sensitive content...")
        filtered = self._filter_sensitive(deduplicated)
        print(f"  ✓ Filtered out {len(deduplicated) - len(filtered)} sensitive articles")

        # Step 4: Add metadata
        print("  🔧 Step 4: Adding metadata...")
        final = [self._add_metadata(art) for art in filtered]

        print(f"\n✅ Output: {len(final)} clean articles (safe for children)")
        print("="*70)

        return final

    def _clean_article(self, article):
        """Clean individual article"""
        cleaned = article.copy()

        cleaned['title'] = self._clean_text(article.get('title', ''))
        cleaned['description'] = self._clean_text(article.get('description', ''))
        cleaned['raw_content'] = self._clean_text(article.get('raw_content', ''))

        if not cleaned['raw_content'] and cleaned['description']:
            cleaned['raw_content'] = cleaned['description']

        return cleaned

    def _clean_text(self, text):
        """Clean and normalize text"""
        if not text:
            return ""

        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\w\s.,!?;:\'\"-]', '', text)
        text = re.sub(r'([.,!?]){2,}', r'\1', text)
        text = text.strip()

        if text:
            text = text[0].upper() + text[1:]

        return text

    def _remove_duplicates(self, articles):
        """Remove duplicate articles"""
        seen_titles = set()
        unique_articles = []

        for article in articles:
            title = article.get('title', '').lower().strip()
            title_normalized = re.sub(r'[^\w\s]', '', title)

            if title_normalized and title_normalized not in seen_titles:
                seen_titles.add(title_normalized)
                unique_articles.append(article)

        return unique_articles

    def _filter_sensitive(self, articles):
        """Filter out articles with sensitive content - CRITICAL FOR CHILDREN'S APP"""
        safe_articles = []

        for article in articles:
            full_text = (
                article.get('title', '') + ' ' +
                article.get('description', '') + ' ' +
                article.get('raw_content', '')
            ).lower()

            # Check for ANY sensitive keyword
            is_sensitive = any(keyword in full_text for keyword in self.sensitive_keywords)

            if not is_sensitive:
                safe_articles.append(article)
            else:
                print(f"    ⚠️  Filtered: {article.get('title', '')[:50]}... (sensitive content)")

        return safe_articles

    def _add_metadata(self, article):
        """Add cleaning metadata"""
        article['cleaned_at'] = datetime.now().isoformat()
        article['word_count'] = len(article.get('raw_content', '').split())
        article['is_cleaned'] = True
        return article

    def save_cleaned_data(self, articles, filepath=CLEANED_DATA_PATH):
        """Save cleaned articles"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Cleaned data saved to: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error saving cleaned data: {str(e)}")
            return False


class GeminiHybridProcessor:
    """
    Hybrid AI Processing with Google Gemini (Direct API):
    1. Use Gemini once to simplify language (child-friendly rewrite)
    2. Manually truncate by word count for each age group
    """

    def __init__(self):
        self.age_groups = AGE_GROUPS
        # Use the model name from config
        self.model_name = GEMINI_MODEL_NAME # <-- Use the new variable
        self.model = None

        if not GOOGLE_API_AVAILABLE:
            raise ImportError("Google Generative AI SDK not installed. Run: pip install google-generativeai")

        # Check if GOOGLE_API_KEY exists
        if not GOOGLE_API_KEY:
            raise ValueError(
                "GOOGLE_API_KEY not found in config or environment!\n"
                "Add to .env file or config.py: GOOGLE_API_KEY='your-key-here'\n"
                "Get free key at: https://aistudio.google.com/app/apikey"
            )
        
        try:
            # Configure the Google API
            genai.configure(api_key=GOOGLE_API_KEY)
            
            # Set up the model configuration
            generation_config = {
                "temperature": 0.3,
                "top_p": 1,
                "top_k": 1,
                "max_output_tokens": 500, # Increased to get full rewrite
            }
            
            # Initialize the model
            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config
            )
            print(f"✅ Using Google Gemini (Direct Method): {self.model_name}")
        
        except Exception as e:
            print(f"❌ Error initializing Google Gemini model: {e}")
            raise

    def process_all(self, articles):
        """Process all articles using hybrid approach"""
        print("\n" + "="*70)
        print("🤖 AI PROCESSING - Gemini Direct Hybrid Approach")
        print("   Step 1: Simplify language once per article")
        print("   Step 2: Truncate by word count for age groups")
        print("="*70)

        processed_articles = []
        total_tokens_used = 0

        for idx, article in enumerate(articles, 1):
            print(f"\n📰 Article {idx}/{len(articles)}: {article['title'][:50]}...")

            # Step 1: Simplify language ONCE using Gemini
            simplified_base_text = ""
            try:
                print("  🎯 Simplifying with Gemini...", end=' ', flush=True)
                simplified_base_text, tokens = self._simplify_with_gemini(
                    article['title'],
                    article['raw_content']
                )
                total_tokens_used += tokens
                print(f"✓ ({len(simplified_base_text.split())} words, {tokens} tokens)")

                # Small delay to respect rate limits
                time.sleep(1)

            except Exception as e:
                print(f"❌ {str(e)[:50]}")
                # Fallback to original content
                simplified_base_text = article['raw_content']

            # Step 2: Create processed article structure
            processed = {
                'original': article,
                'source': article['source'],
                'title': article['title'],
                'url': article['url'],
                'published_date': article['published_date'],
                'category': article['category'],
                'simplified_base': simplified_base_text,  # Store the base simplified version
                'age_groups': {}
            }

            # Step 3: Truncate for each age group
            for group_key, group_info in self.age_groups.items():
                processed['age_groups'][group_key] = self._truncate_for_age_group(
                    simplified_base_text,
                    group_info
                )

            processed['processed_at'] = datetime.now().isoformat()
            processed_articles.append(processed)

        print(f"\n✅ Processed {len(processed_articles)} articles")
        print(f"📊 Total tokens used: {total_tokens_used:,}")
        print(f"💰 Cost: FREE (Google Gemini)")
        print("="*70)

        return processed_articles

    def _simplify_with_gemini(self, title, content):
        """
        Simplify article language once using Gemini
        Makes it child-friendly but doesn't truncate yet
        """
        
        if not self.model:
            raise Exception("Gemini model is not initialized.")

        # Truncate content if too long for API
        if len(content) > 2000:
            content = content[:2000] + "..."

        # Create prompt for language simplification (NOT truncation)
        prompt = f"""You are an expert at rewriting news articles for children. Your task is to rewrite this article in simple, child-friendly language.

ORIGINAL ARTICLE:
Title: {title}
Content: {content}

INSTRUCTIONS:
1. Rewrite the ENTIRE article in simple English suitable for children aged 6-14
2. Use short sentences (8-12 words each)
3. Use simple everyday words - avoid complex vocabulary
4. Keep ALL the important facts accurate
5. Make it engaging and interesting for kids
6. DO NOT shorten or summarize - rewrite all content
7. Write in a friendly, conversational tone

Write ONLY the rewritten article (no explanations):"""

        try:
            # Send the prompt to Gemini
            response = self.model.generate_content(prompt)
            
            # Extract the simplified text
            simplified_text = response.text.strip()
            
            # Get token count
            tokens_used = response.usage_metadata.total_token_count
            
            return simplified_text, tokens_used

        except ResourceExhausted as e:
            raise Exception(f"Rate limit hit! Wait a moment. {e}")
        except NotFound as e:
            raise Exception(f"Model not found. Check: {self.model_name}. {e}")
        except Exception as e:
            # Catch other potential errors (e.g., safety settings)
            try:
                # Try to get more specific error from response
                error_info = f"Finish reason: {response.prompt_feedback}"
            except Exception:
                error_info = str(e)
            raise Exception(f"Gemini error: {error_info}")

    def _truncate_for_age_group(self, simplified_text, age_group_info):
        """
        Manually truncate simplified text based on word count for age group
        No AI call needed - just Python string manipulation
        """
        max_words = age_group_info['max_words']
        words = simplified_text.split()

        # Truncate if needed
        if len(words) <= max_words:
            final_text = simplified_text
        else:
            # Take first N words
            truncated_words = words[:max_words]
            final_text = ' '.join(truncated_words)

            # Add ellipsis if we truncated
            last_char = final_text[-1]
            if last_char not in '.!?':
                final_text += '...'

        # Calculate stats
        final_words = final_text.split()
        sentences = [s.strip() for s in re.split(r'[.!?]+', final_text) if s.strip()]

        return {
            'text': final_text,
            'word_count': len(final_words),
            'sentence_count': len(sentences),
            'complexity_level': age_group_info['complexity'],
            'age_group': age_group_info['name'],
            'model_used': self.model_name # Use the model name string
        }

    def save_processed_data(self, articles, filepath=PROCESSED_DATA_PATH):
        """Save processed articles"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(articles, f, indent=2, ensure_ascii=False)
            print(f"\n💾 Processed data saved to: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error saving processed data: {str(e)}")
            return False


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("\n🧪 Testing Data Processing with Google Gemini (Direct API)\n")

    # Load raw data
    try:
        with open('data/raw_articles.json', 'r', encoding='utf-8') as f:
            raw_articles = json.load(f)
        print(f"✅ Loaded {len(raw_articles)} raw articles")
    except Exception as e:
        print(f"❌ Error loading raw data: {str(e)}")
        print("   Run 'python src/extractors.py' first!")
        exit(1)

    # Step 1: Clean data and FILTER SENSITIVE CONTENT
    cleaner = DataCleaner()
    cleaned_articles = cleaner.clean_all(raw_articles)
    cleaner.save_cleaned_data(cleaned_articles)

    # Step 2: Process with Gemini (Hybrid Approach)
    if cleaned_articles:
        if GOOGLE_API_AVAILABLE and GOOGLE_API_KEY:
            try:
                processor = GeminiHybridProcessor()
                processed_articles = processor.process_all(cleaned_articles)
                processor.save_processed_data(processed_articles)

                # Show sample
                if processed_articles:
                    print("\n" + "="*70)
                    print("📊 SAMPLE OUTPUT")
                    print("="*70)
                    sample = processed_articles[0]
                    print(f"\nTitle: {sample['title']}")
                    print(f"Source: {sample['source']}")
                    print(f"\nAge Group Examples:")
                    for group_key, group_data in sample['age_groups'].items():
                        if 'error' not in group_data:
                            print(f"\n{group_data['age_group']} ({group_data['word_count']} words):")
                            print(f"{group_data['text'][:150]}...")
                    print("="*70)
            except Exception as e:
                print(f"\n❌ Error with Gemini processing: {str(e)}")
        else:
            if not GOOGLE_API_AVAILABLE:
                print("\n⚠️  google-generativeai not installed")
                print("   Install with: pip install google-generativeai")
            elif not GOOGLE_API_KEY:
                print("\n⚠️  GOOGLE_API_KEY not found in config or environment")
                print("   Add to .env file or config.py: GOOGLE_API_KEY='your-key-here'")
                print("   Get free key at: https://aistudio.google.com/app/apikey")
    else:
        print("\n⚠️  No cleaned articles to process")