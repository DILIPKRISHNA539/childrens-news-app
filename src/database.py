"""
Database Module for Children's News App

"""

import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH


class NewsDatabase:
    """SQLite database manager for news articles"""
    
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.conn = None
        self.cursor = None
    
    def connect(self):
        """Connect to database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row  # Access columns by name
            self.cursor = self.conn.cursor()
            print(f"✅ Connected to database: {self.db_path}")
            return True
        except Exception as e:
            print(f"❌ Database connection error: {str(e)}")
            return False
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✅ Database connection closed")
    
    def create_tables(self):
        """Create all necessary tables"""
        print("\n" + "="*70)
        print("🗄️  CREATING DATABASE SCHEMA")
        print("="*70)
        
        # Table 1: Raw Articles
        print("  📋 Creating table: raw_articles...")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT UNIQUE,
                published_date TEXT,
                category TEXT,
                extraction_method TEXT,
                raw_content TEXT,
                extracted_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Table 2: Cleaned Articles
        print("  📋 Creating table: cleaned_articles...")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cleaned_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_article_id INTEGER,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                url TEXT,
                published_date TEXT,
                category TEXT,
                raw_content TEXT,
                word_count INTEGER,
                is_cleaned BOOLEAN,
                cleaned_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (raw_article_id) REFERENCES raw_articles(id)
            )
        """)
        
        # Table 3: Processed Articles (Age-specific versions)
        print("  📋 Creating table: processed_articles...")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS processed_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cleaned_article_id INTEGER,
                source TEXT NOT NULL,
                title TEXT NOT NULL,
                url TEXT,
                published_date TEXT,
                category TEXT,
                age_group_key TEXT NOT NULL,
                age_group_name TEXT,
                simplified_text TEXT,
                word_count INTEGER,
                sentence_count INTEGER,
                complexity_level TEXT,
                processed_at TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (cleaned_article_id) REFERENCES cleaned_articles(id)
            )
        """)
        
        # Table 4: Metadata / Stats
        print("  📋 Creating table: extraction_stats...")
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS extraction_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                extraction_date TEXT,
                total_raw_articles INTEGER,
                total_cleaned_articles INTEGER,
                total_processed_articles INTEGER,
                sources_used TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        print("\n✅ Database schema created successfully!")
        print("="*70)
    
    def insert_raw_articles(self, articles):
        """Insert raw articles into database"""
        print(f"\n📥 Inserting {len(articles)} raw articles...")
        
        inserted = 0
        for article in articles:
            try:
                self.cursor.execute("""
                    INSERT OR IGNORE INTO raw_articles 
                    (source, title, description, url, published_date, category, 
                     extraction_method, raw_content, extracted_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article.get('source'),
                    article.get('title'),
                    article.get('description'),
                    article.get('url'),
                    article.get('published_date'),
                    article.get('category'),
                    article.get('extraction_method'),
                    article.get('raw_content'),
                    article.get('extracted_at')
                ))
                if self.cursor.rowcount > 0:
                    inserted += 1
            except Exception as e:
                print(f"  ⚠️  Error inserting article: {str(e)}")
        
        self.conn.commit()
        print(f"✅ Inserted {inserted} raw articles")
        return inserted
    
    def insert_cleaned_articles(self, articles):
        """Insert cleaned articles into database"""
        print(f"\n📥 Inserting {len(articles)} cleaned articles...")
        
        inserted = 0
        for article in articles:
            try:
                # Get raw_article_id based on URL
                self.cursor.execute(
                    "SELECT id FROM raw_articles WHERE url = ?",
                    (article.get('url'),)
                )
                result = self.cursor.fetchone()
                raw_article_id = result[0] if result else None
                
                self.cursor.execute("""
                    INSERT INTO cleaned_articles 
                    (raw_article_id, source, title, description, url, published_date, 
                     category, raw_content, word_count, is_cleaned, cleaned_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    raw_article_id,
                    article.get('source'),
                    article.get('title'),
                    article.get('description'),
                    article.get('url'),
                    article.get('published_date'),
                    article.get('category'),
                    article.get('raw_content'),
                    article.get('word_count'),
                    article.get('is_cleaned', True),
                    article.get('cleaned_at')
                ))
                inserted += 1
            except Exception as e:
                print(f"  ⚠️  Error inserting cleaned article: {str(e)}")
        
        self.conn.commit()
        print(f"✅ Inserted {inserted} cleaned articles")
        return inserted
    
    def insert_processed_articles(self, articles):
        """Insert processed (age-specific) articles into database"""
        print(f"\n📥 Inserting processed articles for multiple age groups...")
        
        inserted = 0
        for article in articles:
            try:
                # Get cleaned_article_id based on URL
                self.cursor.execute(
                    "SELECT id FROM cleaned_articles WHERE url = ?",
                    (article.get('url'),)
                )
                result = self.cursor.fetchone()
                cleaned_article_id = result[0] if result else None
                
                # Insert for each age group
                for age_group_key, age_data in article.get('age_groups', {}).items():
                    self.cursor.execute("""
                        INSERT INTO processed_articles 
                        (cleaned_article_id, source, title, url, published_date, category,
                         age_group_key, age_group_name, simplified_text, word_count, 
                         sentence_count, complexity_level, processed_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        cleaned_article_id,
                        article.get('source'),
                        article.get('title'),
                        article.get('url'),
                        article.get('published_date'),
                        article.get('category'),
                        age_group_key,
                        age_data.get('age_group'),
                        age_data.get('text'),
                        age_data.get('word_count'),
                        age_data.get('sentence_count'),
                        age_data.get('complexity_level'),
                        article.get('processed_at')
                    ))
                    inserted += 1
            except Exception as e:
                print(f"  ⚠️  Error inserting processed article: {str(e)}")
        
        self.conn.commit()
        print(f"✅ Inserted {inserted} processed article versions")
        return inserted
    
    def insert_stats(self, stats):
        """Insert extraction statistics"""
        try:
            self.cursor.execute("""
                INSERT INTO extraction_stats 
                (extraction_date, total_raw_articles, total_cleaned_articles, 
                 total_processed_articles, sources_used)
                VALUES (?, ?, ?, ?, ?)
            """, (
                stats.get('extraction_date'),
                stats.get('total_raw_articles'),
                stats.get('total_cleaned_articles'),
                stats.get('total_processed_articles'),
                stats.get('sources_used')
            ))
            self.conn.commit()
            print("✅ Statistics recorded")
        except Exception as e:
            print(f"❌ Error inserting stats: {str(e)}")
    
    def get_articles_by_age_group(self, age_group_key):
        """Retrieve articles for specific age group"""
        self.cursor.execute("""
            SELECT * FROM processed_articles 
            WHERE age_group_key = ?
            ORDER BY created_at DESC
        """, (age_group_key,))
        return self.cursor.fetchall()
    
    def get_article_count(self):
        """Get count of articles in each table"""
        counts = {}
        
        self.cursor.execute("SELECT COUNT(*) FROM raw_articles")
        counts['raw'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM cleaned_articles")
        counts['cleaned'] = self.cursor.fetchone()[0]
        
        self.cursor.execute("SELECT COUNT(*) FROM processed_articles")
        counts['processed'] = self.cursor.fetchone()[0]
        
        return counts
    
    def display_stats(self):
        """Display database statistics"""
        print("\n" + "="*70)
        print("📊 DATABASE STATISTICS")
        print("="*70)
        
        counts = self.get_article_count()
        
        print(f"  📰 Raw Articles: {counts['raw']}")
        print(f"  🧹 Cleaned Articles: {counts['cleaned']}")
        print(f"  🤖 Processed Articles (all age groups): {counts['processed']}")
        
        # Get article count by age group
        self.cursor.execute("""
            SELECT age_group_name, COUNT(*) as count 
            FROM processed_articles 
            GROUP BY age_group_name
        """)
        
        print(f"\n  Age Group Breakdown:")
        for row in self.cursor.fetchall():
            print(f"    • {row[0]}: {row[1]} articles")
        
        print("="*70)


# ============================================================
# MAIN EXECUTION FOR TESTING
# ============================================================
if __name__ == "__main__":
    print("\n🧪 Testing Database Module\n")
    
    # Initialize database
    db = NewsDatabase()
    
    if not db.connect():
        print("❌ Failed to connect to database")
        exit(1)
    
    # Create tables
    db.create_tables()
    
    # Load and insert data
    try:
        # Load raw articles
        print("\n📂 Loading data files...")
        with open('data/raw_articles.json', 'r', encoding='utf-8') as f:
            raw_articles = json.load(f)
        print(f"  ✓ Loaded raw_articles.json ({len(raw_articles)} articles)")
        
        # Load cleaned articles
        with open('data/cleaned_articles.json', 'r', encoding='utf-8') as f:
            cleaned_articles = json.load(f)
        print(f"  ✓ Loaded cleaned_articles.json ({len(cleaned_articles)} articles)")
        
        # Load processed articles
        with open('data/processed_articles.json', 'r', encoding='utf-8') as f:
            processed_articles = json.load(f)
        print(f"  ✓ Loaded processed_articles.json ({len(processed_articles)} articles)")
        
        # Insert into database
        db.insert_raw_articles(raw_articles)
        db.insert_cleaned_articles(cleaned_articles)
        db.insert_processed_articles(processed_articles)
        
        # Insert stats
        stats = {
            'extraction_date': datetime.now().isoformat(),
            'total_raw_articles': len(raw_articles),
            'total_cleaned_articles': len(cleaned_articles),
            'total_processed_articles': len(processed_articles),
            'sources_used': ', '.join(set([a['source'] for a in raw_articles]))
        }
        db.insert_stats(stats)
        
        # Display statistics
        db.display_stats()
        
        # Sample query
        print("\n" + "="*70)
        print("📖 SAMPLE: Articles for 6-8 years")
        print("="*70)
        articles_6_8 = db.get_articles_by_age_group('group_1')
        for idx, article in enumerate(articles_6_8[:3], 1):
            print(f"\n{idx}. {article['title']}")
            print(f"   {article['simplified_text'][:100]}...")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {str(e)}")
        print("   Make sure you've run extractors.py and processors.py first!")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    finally:
        db.close()
    
    print("\n✅ Database setup complete!")