import json
from datetime import datetime
import os
import time
from sqlalchemy import create_engine, Column, Integer, String, DateTime, JSON, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

# Database configuration
DB_URL = "mysql+mysqlconnector://product_user@localhost/product_translations"

# Create SQLAlchemy engine and base
engine = create_engine(DB_URL)
Base = declarative_base()

# Define the Translation model
class Translation(Base):
    __tablename__ = 'translation_cache'
    
    id = Column(Integer, primary_key=True)
    app = Column(String(50))
    catalog_number = Column(String(100))
    code = Column(String(100))
    status = Column(String(50))
    translated_obj = Column(JSON)
    hash_value = Column(String(32))
    pira_modified = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

# Create session factory
Session = sessionmaker(bind=engine)

@contextmanager
def get_session():
    """Context manager for database sessions"""
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def get_all_translations():
    """Get all translations from the database"""
    start_time = time.time()
    
    with get_session() as session:
        # Get cache statistics
        stats = session.query(
            func.count(Translation.id).label('total'),
            func.count(func.distinct(Translation.catalog_number)).label('unique_products'),
            func.max(Translation.pira_modified).label('latest_update')
        ).first()
        
        # Get all translations
        translations = session.query(Translation).order_by(Translation.pira_modified.desc()).all()
        
        # Convert to dictionary format
        results = [
            {
                'catalog_number': t.catalog_number,
                'translated_obj': t.translated_obj,
                'pira_modified': t.pira_modified,
                'hash_value': t.hash_value
            }
            for t in translations
        ]
    
    end_time = time.time()
    print(f"\nCache Statistics:")
    print(f"Total cached translations: {stats.total}")
    print(f"Unique products: {stats.unique_products}")
    print(f"Latest update: {stats.latest_update}")
    print(f"Query time: {(end_time - start_time):.3f} seconds")
    
    return results

def get_translation_by_catalog(catalog_number):
    """Get translation for a specific catalog number"""
    start_time = time.time()
    
    with get_session() as session:
        translation = session.query(Translation).filter_by(catalog_number=catalog_number).first()
        
        if translation:
            result = {
                'translated_obj': translation.translated_obj,
                'hash_value': translation.hash_value,
                'pira_modified': translation.pira_modified
            }
        else:
            result = None
    
    end_time = time.time()
    if result:
        print(f"\nCache hit for {catalog_number}")
        print(f"Hash value: {result['hash_value']}")
        print(f"Last modified: {result['pira_modified']}")
    else:
        print(f"\nCache miss for {catalog_number}")
    print(f"Query time: {(end_time - start_time):.3f} seconds")
    
    return result

def get_recent_translations(limit=10):
    """Get most recent translations"""
    start_time = time.time()
    
    with get_session() as session:
        translations = session.query(Translation).order_by(
            Translation.pira_modified.desc()
        ).limit(limit).all()
        
        results = [
            {
                'catalog_number': t.catalog_number,
                'translated_obj': t.translated_obj,
                'pira_modified': t.pira_modified,
                'hash_value': t.hash_value
            }
            for t in translations
        ]
    
    end_time = time.time()
    print(f"\nRetrieved {len(results)} recent translations")
    print(f"Query time: {(end_time - start_time):.3f} seconds")
    
    return results

def print_translation(translation):
    """Pretty print a translation result"""
    if not translation:
        print("No translation found")
        return
    
    if 'translated_obj' in translation:
        print("\nCatalog Number:", translation.get('catalog_number', 'N/A'))
        print("Modified:", translation.get('pira_modified', 'N/A'))
        print("Hash:", translation.get('hash_value', 'N/A'))
        print("\nTranslated Content:")
        print(json.dumps(translation['translated_obj'], indent=2, ensure_ascii=False))
    else:
        print(json.dumps(translation, indent=2, ensure_ascii=False))

def save_translations_to_file(translations, filename='translations.json'):
    """Save translations to a JSON file"""
    start_time = time.time()
    
    # Create translations directory if it doesn't exist
    os.makedirs('translations', exist_ok=True)
    filepath = os.path.join('translations', filename)
    
    # Convert datetime objects to strings
    processed_translations = []
    for trans in translations:
        trans_copy = trans.copy()
        if 'pira_modified' in trans_copy and isinstance(trans_copy['pira_modified'], datetime):
            trans_copy['pira_modified'] = trans_copy['pira_modified'].isoformat()
        processed_translations.append(trans_copy)
    
    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(processed_translations, f, indent=2, ensure_ascii=False)
    
    end_time = time.time()
    print(f"\nTranslations saved to {filepath}")
    print(f"Save time: {(end_time - start_time):.3f} seconds")

def save_single_translation_to_file(translation, filename=None):
    """Save a single translation to a JSON file"""
    if not translation:
        print("No translation to save")
        return
    
    start_time = time.time()
    
    # Create translations directory if it doesn't exist
    os.makedirs('translations', exist_ok=True)
    
    if filename is None:
        catalog = translation.get('catalog_number', 'unknown')
        filename = f'translation_{catalog}.json'
    
    filepath = os.path.join('translations', filename)
    
    # Process the translation
    trans_copy = translation.copy()
    if 'pira_modified' in trans_copy and isinstance(trans_copy['pira_modified'], datetime):
        trans_copy['pira_modified'] = trans_copy['pira_modified'].isoformat()
    
    # Save to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(trans_copy, f, indent=2, ensure_ascii=False)
    
    end_time = time.time()
    print(f"\nTranslation saved to {filepath}")
    print(f"Save time: {(end_time - start_time):.3f} seconds")

def main():
    """Main function to demonstrate usage"""
    print("\n=== Recent Translations ===")
    recent = get_recent_translations(5)
    for trans in recent:
        print_translation(trans)
        print("\n" + "="*50 + "\n")
    
    print("\n=== All Translations ===")
    all_trans = get_all_translations()
    print(f"Total translations: {len(all_trans)}")
    
    # Save all translations to a file
    save_translations_to_file(all_trans, 'all_translations.json')
    
    # Example of getting and saving a specific translation
    if all_trans:
        catalog = all_trans[0]['catalog_number']
        print(f"\n=== Translation for {catalog} ===")
        specific = get_translation_by_catalog(catalog)
        print_translation(specific)
        
        # Save the specific translation to a file
        save_single_translation_to_file(specific, f'translation_{catalog}.json')

if __name__ == "__main__":
    main() 