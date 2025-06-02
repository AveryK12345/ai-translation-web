import asyncio
import hashlib
import json
import mysql.connector
from datetime import datetime
import aiohttp
import os
from translatable_fields import TRANSLATABLE_FIELDS

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'product_user',
    'password': '',  # Empty password
    'database': 'product_translations'
}

def _load_api_key():
    """Load API key from possible locations."""
    key_paths = [
        "api-development.key",  # Current directory
        "../api-development.key",  # Parent directory
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "api-development.key")
    ]
    
    for path in key_paths:
        try:
            with open(path, "r") as f:
                return f.read().strip()
        except FileNotFoundError:
            continue
    
    raise FileNotFoundError("api-development.key not found in current or parent directory")

async def translate_text(text, target_lang):
    """Translate text using Intento API"""
    api_key = _load_api_key()
    headers = {
        'apikey': api_key,
        'Content-Type': 'application/json',
        'User-Agent': 'Intento.Integration.python/1.0'
    }
    
    payload = {
        "context": {
            "text": [text],
            "to": target_lang,
            "from": "en"
        },
        "service": {
            "provider": "ai.text.translate.openai.gpt-4.translate",
            "model": "openai/gpt-4"
        }
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            'https://api.inten.to/ai/text/translate',
            headers=headers,
            json=payload
        ) as response:
            result = await response.json()
            
            if 'results' in result:
                return result['results'][0]
            elif 'response' in result and result['response']:
                translation_data = result['response'][0]
                return translation_data.get('results', [''])[0]
            else:
                raise Exception("No translation results found in response")

def calculate_hash(content):
    """Calculate hash of the content for caching"""
    return hashlib.md5(json.dumps(content, sort_keys=True).encode()).hexdigest()

def get_db_connection():
    """Create database connection"""
    return mysql.connector.connect(**DB_CONFIG)

def init_database():
    """Initialize database and create table if not exists"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS translation_cache (
            id INT AUTO_INCREMENT PRIMARY KEY,
            app VARCHAR(50),
            catalog_number VARCHAR(100),
            code VARCHAR(100),
            status VARCHAR(50),
            translated_obj JSON,
            hash_value VARCHAR(32),
            pira_modified DATETIME,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_hash (hash_value),
            INDEX idx_catalog (catalog_number)
        )
    """)
    
    conn.commit()
    cursor.close()
    conn.close()

async def translate_product(product_json, picked_fields=None, target_lang='es'):
    """Translate selected fields of a product to target language"""
    if picked_fields is None:
        picked_fields = TRANSLATABLE_FIELDS
    
    translated_product = product_json.copy()
    
    # Handle array fields
    for field in picked_fields:
        if field == "names":
            for name_obj in translated_product.get("names", []):
                if name_obj["isocode"] == "en":
                    translated_text = await translate_text(name_obj["value"], target_lang)
                    translated_product["names"].append({
                        "value": translated_text,
                        "isocode": target_lang
                    })
        
        elif field == "technicalDescription":
            for desc_obj in translated_product.get("technicalDescription", []):
                if desc_obj["isocode"] == "en":
                    translated_text = await translate_text(desc_obj["value"], target_lang)
                    translated_product["technicalDescription"].append({
                        "value": translated_text,
                        "isocode": target_lang
                    })
        
        elif field == "commercialDescription":
            for desc_obj in translated_product.get("commercialDescription", []):
                if desc_obj["isocode"] == "en":
                    translated_text = await translate_text(desc_obj["value"], target_lang)
                    translated_product["commercialDescription"].append({
                        "value": translated_text,
                        "isocode": target_lang
                    })
        
        elif field == "categoryList.name":
            for category in translated_product.get("categoryList", []):
                if "name" in category:
                    category["name"] = await translate_text(category["name"], target_lang)
        
        elif field == "categoryList.path":
            for category in translated_product.get("categoryList", []):
                if "path" in category:
                    category["path"] = await translate_text(category["path"], target_lang)
        
        # Handle simple string fields
        elif field in translated_product and translated_product[field]:
            translated_product[field] = await translate_text(translated_product[field], target_lang)
    
    return translated_product

async def cache_translation(product_json, translated_json, picked_fields):
    """Cache the translation in MySQL database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Calculate hash of the original content
    content_to_hash = {field: product_json.get(field) for field in picked_fields if field in product_json}
    hash_value = calculate_hash(content_to_hash)
    
    # Check if translation already exists
    cursor.execute("""
        SELECT translated_obj FROM translation_cache 
        WHERE hash_value = %s AND app = %s AND catalog_number = %s
    """, (hash_value, product_json["app"], product_json["catalogNumber"]))
    
    result = cursor.fetchone()
    
    if not result:
        # Insert new translation
        cursor.execute("""
            INSERT INTO translation_cache 
            (app, catalog_number, code, status, translated_obj, hash_value, pira_modified)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            product_json["app"],
            product_json["catalogNumber"],
            product_json["code"],
            product_json.get("productLifeCycleStatus", "UNKNOWN"),
            json.dumps(translated_json),
            hash_value,
            datetime.strptime(product_json["pira_modified"], "%Y-%m-%dT%H:%M:%S")
        ))
        
        conn.commit()
    
    cursor.close()
    conn.close()

async def get_cached_translation(product_json, picked_fields):
    """Retrieve cached translation from database"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    content_to_hash = {field: product_json.get(field) for field in picked_fields if field in product_json}
    hash_value = calculate_hash(content_to_hash)
    
    cursor.execute("""
        SELECT translated_obj FROM translation_cache 
        WHERE hash_value = %s AND app = %s AND catalog_number = %s
    """, (hash_value, product_json["app"], product_json["catalogNumber"]))
    
    result = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    return json.loads(result["translated_obj"]) if result else None

async def main():
    # Initialize database
    init_database()
    
    # Example: Fetch 10 products from API
    async with aiohttp.ClientSession() as session:
        async with session.get(
            'https://api-qa.rockwellautomation.com/ra-eapi-cx-public-dashboard-vpcqa/api/v1/productExperience/products',
            params={
                'startIndex': 0,
                    'noOfResults': 2,
                'app': 'RA',
                'lastModifiedDate': '2000-07-02 18:50:32'
            },
            headers={
                'client_id': 'e63aece91025460ab5159495269fe381',
                'client_secret': 'f1dA7Fac0916411690a0360Ba2B9b6F5',
                'correlation_id': 'dwei_test_dev_1748876809'
            }
        ) as response:
            products_data = await response.json()
            
            for product in products_data["data"]["dataList"]:
                # Check cache first
                cached_translation = await get_cached_translation(product, TRANSLATABLE_FIELDS)
                
                if cached_translation:
                    print(f"Using cached translation for product {product['catalogNumber']}")
                    continue
                
                # Translate if not in cache
                translated_product = await translate_product(product, TRANSLATABLE_FIELDS, 'es')
                await cache_translation(product, translated_product, TRANSLATABLE_FIELDS)
                print(f"Translated and cached product {product['catalogNumber']}")

if __name__ == "__main__":
    asyncio.run(main()) 