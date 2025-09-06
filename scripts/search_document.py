#!/usr/bin/env python
"""Simple script to search documents"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.database.database_manager import DocumentManager
from src.tools.searchDocuments import SearchDocumentsTool
import logging

async def main():
    # Get query from command line or use default
    if len(sys.argv) > 1:
        query = sys.argv[1]
    else:
        query = "API design"
    
    print(f"Searching for: {query}")
    
    # Initialize database
    db_path = "data/mydocs.db"
    db_manager = DocumentManager(db_path)
    await db_manager.initialize()
    
    # Setup logger
    logger = logging.getLogger(__name__)
    
    # Create search tool
    search_tool = SearchDocumentsTool(
        database_manager=db_manager,
        logger=logger
    )
    
    # Search documents
    result = await search_tool.execute({"query": query, "limit": 10})
    
    # Print result
    if not result.success:
        print(f"Error: {result.error_message}")
    else:
        data = result.data
        results = data.get('results', [])
        print(f"Found {len(results)} results:")
        for doc in results:
            print(f"\n- Document ID: {doc.get('document_id')}")
            print(f"  Title: {doc.get('title', 'N/A')}")
            print(f"  Path: {doc.get('file_path')}")
            print(f"  Score: {doc.get('score', 0):.2f}")
            print(f"  Preview: {doc.get('preview', '')[:100]}...")
    
    # Close database
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())