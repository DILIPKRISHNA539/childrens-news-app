"""
Main Data Pipeline for Children's News App

"""

import sys
import json
from datetime import datetime
from extractors import DataExtractor
from processors import DataCleaner, GeminiHybridProcessor
from database import NewsDatabase
from config import (
    RAW_DATA_PATH,
    CLEANED_DATA_PATH,
    PROCESSED_DATA_PATH,
    GOOGLE_API_KEY,
    GEMINI_MODEL_NAME  # <-- Use our new config variable
)


class NewsPipeline:
    """Main pipeline orchestrator"""

    def __init__(self):
        self.extractor = DataExtractor()
        self.cleaner = DataCleaner()
        
        # ✅ Updated check for Direct Google API
        if not GEMINI_MODEL_NAME or not GOOGLE_API_KEY:
            raise RuntimeError(
                "Gemini processor requires GEMINI_MODEL_NAME and GOOGLE_API_KEY.\n"
                "Check your config.py and .env file."
            )
        
        # This now works because your processors.py is correctly updated
        self.processor = GeminiHybridProcessor()
        self.db = NewsDatabase()

        self.raw_articles = []
        self.cleaned_articles = []
        self.processed_articles = []

    def run_complete_pipeline(self):
        """Run the complete end-to-end pipeline"""
        print("\n" + "=" * 70)
        print("🚀 CHILDREN'S NEWS APP - COMPLETE DATA PIPELINE")
        print("=" * 70)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)

        try:
            # Step 1: Data Extraction
            print("\n📡 STEP 1: DATA EXTRACTION")
            print("-" * 70)
            self.raw_articles = self.extractor.extract_all()

            if not self.raw_articles:
                print("❌ No articles extracted. Pipeline stopped.")
                return False

            self.extractor.save_raw_data(self.raw_articles, RAW_DATA_PATH)

            # Step 2: Data Cleaning & Sensitive Filtering
            print("\n🧹 STEP 2: DATA CLEANING & SENSITIVE CONTENT FILTERING")
            print("-" * 70)
            self.cleaned_articles = self.cleaner.clean_all(self.raw_articles)

            if not self.cleaned_articles:
                print("❌ No articles passed cleaning/filtering. Pipeline stopped.")
                return False

            self.cleaner.save_cleaned_data(self.cleaned_articles, CLEANED_DATA_PATH)

            # Step 3: AI Processing with Gemini (Hybrid)
            print("\n🤖 STEP 3: GEMINI HYBRID AI PROCESSING")
            print("-" * 70)
            self.processed_articles = self.processor.process_all(self.cleaned_articles)
            self.processor.save_processed_data(self.processed_articles, PROCESSED_DATA_PATH)

            # Step 4: Database Storage
            print("\n🗄️  STEP 4: DATABASE STORAGE")
            print("-" * 70)
            if not self.db.connect():
                print("❌ Database connection failed. Skipping storage.")
                return False

            self.db.create_tables()
            self.db.insert_raw_articles(self.raw_articles)
            self.db.insert_cleaned_articles(self.cleaned_articles)
            self.db.insert_processed_articles(self.processed_articles)

            # Insert statistics
            stats = {
                'extraction_date': datetime.now().isoformat(),
                'total_raw_articles': len(self.raw_articles),
                'total_cleaned_articles': len(self.cleaned_articles),
                'total_processed_articles': len(self.processed_articles),
                'sources_used': ', '.join(set([a['source'] for a in self.raw_articles]))
            }
            self.db.insert_stats(stats)

            # Step 5: Summary
            print("\n📊 STEP 5: PIPELINE SUMMARY")
            print("-" * 70)
            self.display_summary()
            self.db.display_stats()
            self.db.close()

            print("\n" + "=" * 70)
            print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
            print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 70)

            return True

        except Exception as e:
            print(f"\n❌ PIPELINE ERROR: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def display_summary(self):
        """Display pipeline execution summary"""
        print("\n📈 EXECUTION SUMMARY:")
        print(f"  • Raw Articles Extracted: {len(self.raw_articles)}")
        print(f"  • Articles After Cleaning & Filtering: {len(self.cleaned_articles)}")
        print(f"  • Articles Filtered Out (Sensitive/Duplicates): {len(self.raw_articles) - len(self.cleaned_articles)}")
        print(f"  • Final Processed Articles: {len(self.processed_articles)}")
        print(f"  • Total Age-Group Versions: {len(self.processed_articles) * 3}")

        # Source breakdown
        sources = {}
        for article in self.raw_articles:
            source = article.get('source', 'Unknown')
            sources[source] = sources.get(source, 0) + 1

        print(f"\n📰 SOURCES USED:")
        for source, count in sources.items():
            print(f"  • {source}: {count} articles")

        # Age group info
        print(f"\n👶 AGE GROUP TARGETS:")
        from config import AGE_GROUPS
        for group in AGE_GROUPS.values():
            print(f"  • {group['name']}: ≤{group['max_words']} words")

    def display_sample_articles(self):
        """Display sample processed articles"""
        if not self.processed_articles:
            return

        print("\n" + "=" * 70)
        print("📰 SAMPLE PROCESSED ARTICLES (CHILD-FRIENDLY)")
        print("=" * 70)

        sample = self.processed_articles[0]
        print(f"\nTitle: {sample['title']}")
        print(f"Source: {sample['source']}")
        print(f"URL: {sample['url']}\n")

        for group_key, group_data in sample['age_groups'].items():
            print(f"{group_data['age_group']} ({group_data['word_count']} words):")
            print(f"  {group_data['text']}\n")

        print("=" * 70)


# ======================
# Standalone Functions
# ======================

def run_extraction_only():
    extractor = DataExtractor()
    articles = extractor.extract_all()
    extractor.save_raw_data(articles, RAW_DATA_PATH)
    return articles


def run_processing_only():
    try:
        with open(RAW_DATA_PATH, 'r', encoding='utf-8') as f:
            raw_articles = json.load(f)

        cleaner = DataCleaner()
        cleaned_articles = cleaner.clean_all(raw_articles)
        cleaner.save_cleaned_data(cleaned_articles, CLEANED_DATA_PATH)

        # Use real processor
        processor = GeminiHybridProcessor()
        processed_articles = processor.process_all(cleaned_articles)
        processor.save_processed_data(processed_articles, PROCESSED_DATA_PATH)

        return processed_articles

    except FileNotFoundError:
        print("❌ Raw articles file not found. Run extraction first!")
        return []


def run_database_only():
    try:
        with open(RAW_DATA_PATH, 'r', encoding='utf-8') as f:
            raw_articles = json.load(f)
        with open(CLEANED_DATA_PATH, 'r', encoding='utf-8') as f:
            cleaned_articles = json.load(f)
        with open(PROCESSED_DATA_PATH, 'r', encoding='utf-8') as f:
            processed_articles = json.load(f)

        db = NewsDatabase()
        db.connect()
        db.create_tables()
        db.insert_raw_articles(raw_articles)
        db.insert_cleaned_articles(cleaned_articles)
        db.insert_processed_articles(processed_articles)
        db.display_stats()
        db.close()
        return True

    except FileNotFoundError as e:
        print(f"❌ Data file not found: {str(e)}")
        return False


# ======================
# Main Execution
# ======================

if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("   CHILDREN'S NEWS APP - DATA PIPELINE (Gemini Direct API)")
    print("=" * 70)

    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "extract":
            run_extraction_only()
        elif mode == "process":
            run_processing_only()
        elif mode == "database":
            run_database_only()
        elif mode == "full":
            pipeline = NewsPipeline()
            success = pipeline.run_complete_pipeline()
            if success:
                pipeline.display_sample_articles()
            sys.exit(0 if success else 1)
        else:
            print("\n❌ Invalid mode. Use: extract, process, database, or full")
            print("\nUsage:")
            print("  python src/data_pipeline.py full      - Run complete pipeline")
            print("  python src/data_pipeline.py extract   - Run extraction only")
            print("  python src/data_pipeline.py process   - Run processing only")
            print("  python src/data_pipeline.py database  - Run database storage only")
    else:
        print("\n▶️  Running COMPLETE PIPELINE (default)")
        pipeline = NewsPipeline()
        success = pipeline.run_complete_pipeline()
        if success:
            pipeline.display_sample_articles()
        sys.exit(0 if success else 1)