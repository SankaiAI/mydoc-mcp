#!/usr/bin/env python
"""Simple script to index a document"""

import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.database.database_manager import DocumentManager
from src.tools.indexDocument import IndexDocumentTool
from src.parsers.parser_factory import ParserFactory
import logging

async def main():
    # Get file path from command line or use default
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = "D:/AI_Agent_Practice/mydoc-mcp/sample_documents/api-design-guide.md"
    
    # Ensure absolute path
    file_path = os.path.abspath(file_path)
    
    print(f"Indexing document: {file_path}")
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return
    
    # Initialize database
    db_path = "data/mydocs.db"
    db_manager = DocumentManager(db_path)
    await db_manager.initialize()
    
    # Create parser factory
    parser_factory = ParserFactory()
    
    # Setup logger
    logger = logging.getLogger(__name__)
    
    # Create index tool
    index_tool = IndexDocumentTool(
        database_manager=db_manager,
        parser_factory=parser_factory,
        logger=logger
    )
    
    # Index the document
    result = await index_tool.execute({"file_path": file_path})
    
    # Print result
    if not result.success:
        print(f"Error: {result.error_message}")
    else:
        data = result.data
        print(f"Success: Document indexed")
        print(f"Document ID: {data.get('document_id', 'N/A')}")
        print(f"Title: {data.get('title', 'N/A')}")
        print(f"File path: {data.get('file_path', 'N/A')}")
        print(f"Size: {data.get('size', 0)} bytes")
        print(f"Chunks: {data.get('chunks', 0)}")
    
    # Close database
    await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())