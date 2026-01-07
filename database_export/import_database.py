#!/usr/bin/env python3
"""
Tahlil One - Database Import Script
====================================
This script imports all Tahlil One collections into your MongoDB server.

Usage:
    python import_database.py --mongo-url "mongodb://your-server:27017" --db-name "tahlil_one"

Requirements:
    pip install pymongo

Collections imported:
    - users (user accounts and subscriptions)
    - user_sessions (authentication sessions)
    - markets (market definitions)
    - assets (tradeable assets)
    - analyses (asset analysis content)
    - daily_analysis (Google Sheets synced data)
    - forecast_history (History of Success records)
"""

import json
import os
import argparse
from pymongo import MongoClient
from pathlib import Path

def import_collection(db, collection_name, json_file):
    """Import a single collection from JSON file."""
    if not os.path.exists(json_file):
        print(f"  ⚠️  File not found: {json_file}")
        return 0
    
    with open(json_file, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    if not documents:
        print(f"  ℹ️  No documents in {collection_name}")
        return 0
    
    # Clear existing data (optional - comment out to append)
    db[collection_name].delete_many({})
    
    # Insert documents
    result = db[collection_name].insert_many(documents)
    return len(result.inserted_ids)

def main():
    parser = argparse.ArgumentParser(description='Import Tahlil One database')
    parser.add_argument('--mongo-url', required=True, help='MongoDB connection URL')
    parser.add_argument('--db-name', default='tahlil_one', help='Database name (default: tahlil_one)')
    parser.add_argument('--data-dir', default='.', help='Directory containing JSON files (default: current directory)')
    args = parser.parse_args()
    
    # Connect to MongoDB
    print(f"\n🔌 Connecting to MongoDB: {args.mongo_url}")
    client = MongoClient(args.mongo_url)
    db = client[args.db_name]
    
    # Test connection
    try:
        client.admin.command('ping')
        print("✅ Connected successfully!\n")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return
    
    # Collections to import
    collections = [
        'users',
        'user_sessions', 
        'markets',
        'assets',
        'analyses',
        'daily_analysis',
        'forecast_history'
    ]
    
    print(f"📦 Importing to database: {args.db_name}\n")
    
    total_imported = 0
    for collection in collections:
        json_file = os.path.join(args.data_dir, f'{collection}.json')
        count = import_collection(db, collection, json_file)
        print(f"  ✅ {collection}: {count} documents imported")
        total_imported += count
    
    print(f"\n🎉 Import complete! Total: {total_imported} documents")
    print(f"\n📝 Update your backend/.env with:")
    print(f'   MONGO_URL="{args.mongo_url}"')
    print(f'   DB_NAME="{args.db_name}"')

if __name__ == '__main__':
    main()
