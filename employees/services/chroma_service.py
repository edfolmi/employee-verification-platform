"""
ChromaDB service for storing and searching facial embeddings.
Simplified Windows-compatible version.
"""
import logging
from typing import Optional, List, Dict, Any
import chromadb
from django.conf import settings
import os

logger = logging.getLogger(__name__)


class ChromaService:
    """
    Service for managing facial embeddings in ChromaDB.
    Uses persistent storage with cosine similarity for searches.
    Simplified Windows-compatible version.
    """
    
    _client = None
    _collection = None
    
    @classmethod
    def _get_client(cls):
        """
        Get or create ChromaDB persistent client.
        
        Returns:
            ChromaDB client instance
        """
        if cls._client is None:
            logger.info(f"Initializing ChromaDB client at: {settings.CHROMA_PERSIST_DIRECTORY}")
            
            # Ensure the directory exists
            settings.CHROMA_PERSIST_DIRECTORY.mkdir(parents=True, exist_ok=True)
            
            try:
                # Simple client initialization without complex settings
                cls._client = chromadb.PersistentClient(
                    path=str(settings.CHROMA_PERSIST_DIRECTORY)
                )
                
                logger.info("ChromaDB client initialized successfully")
            except Exception as e:
                logger.error(f"Error initializing ChromaDB: {str(e)}")
                raise
        
        return cls._client
    
    @classmethod
    def _get_collection(cls):
        """
        Get or create the employee faces collection.
        
        Returns:
            ChromaDB collection instance
        """
        if cls._collection is None:
            try:
                client = cls._get_client()
                
                # Try to get existing collection first
                try:
                    cls._collection = client.get_collection(
                        name=settings.CHROMA_COLLECTION_NAME
                    )
                    logger.info(f"Retrieved existing collection '{settings.CHROMA_COLLECTION_NAME}'")
                except Exception:
                    # Create new collection if it doesn't exist
                    cls._collection = client.create_collection(
                        name=settings.CHROMA_COLLECTION_NAME,
                        metadata={"hnsw:space": "cosine"}
                    )
                    logger.info(f"Created new collection '{settings.CHROMA_COLLECTION_NAME}'")
                
            except Exception as e:
                logger.error(f"Error getting collection: {str(e)}")
                raise
        
        return cls._collection
    
    @classmethod
    def add_employee_embedding(
        cls,
        employee_uuid: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Add employee facial embedding to ChromaDB.
        
        Args:
            employee_uuid: Unique employee identifier
            embedding: Normalized facial embedding as list of floats
            metadata: Employee metadata (full_name, employer, reputation_score)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = cls._get_collection()
            
            # Convert UUID to string for ChromaDB
            doc_id = str(employee_uuid)
            
            # Clean metadata - remove any problematic characters
            clean_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, str):
                    # Remove null bytes and strip whitespace
                    clean_value = str(value).replace('\x00', '').replace('\r', '').replace('\n', ' ').strip()
                    clean_metadata[key] = clean_value
                elif isinstance(value, (int, float)):
                    # Convert numbers to strings for ChromaDB
                    clean_metadata[key] = str(value)
                else:
                    clean_metadata[key] = str(value)
            
            # Add to collection
            collection.add(
                ids=[doc_id],
                embeddings=[embedding],
                metadatas=[clean_metadata]
            )
            
            logger.info(f"Added embedding for employee: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding embedding to ChromaDB: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    @classmethod
    def search_embedding(
        cls,
        query_embedding: List[float],
        n_results: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Search for the closest matching employee embedding.
        
        Args:
            query_embedding: Query facial embedding as list of floats
            n_results: Number of results to return (default: 1)
            
        Returns:
            Dictionary containing match results or None if no results
        """
        try:
            collection = cls._get_collection()
            
            # Query the collection
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results
            )
            
            # Check if we have results
            if not results['ids'] or len(results['ids'][0]) == 0:
                logger.info("No matching embeddings found")
                return None
            
            # Extract the top result
            employee_id = results['ids'][0][0]
            distance = results['distances'][0][0]
            metadata = results['metadatas'][0][0] if results['metadatas'] else {}
            
            # Convert distance to similarity score
            # ChromaDB returns cosine distance (0 = identical, 2 = opposite)
            # Convert to similarity: 1 - (distance / 2)
            similarity = 1 - (distance / 2)
            
            result = {
                'id': employee_id,
                'distance': distance,
                'similarity': similarity,
                'metadata': metadata
            }
            
            logger.info(
                f"Found match - ID: {employee_id}, "
                f"Similarity: {similarity:.4f}, Distance: {distance:.4f}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching ChromaDB: {str(e)}")
            return None
    
    @classmethod
    def delete_employee_embedding(cls, employee_uuid: str) -> bool:
        """
        Delete employee embedding from ChromaDB.
        
        Args:
            employee_uuid: Employee UUID to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = cls._get_collection()
            doc_id = str(employee_uuid)
            
            collection.delete(ids=[doc_id])
            
            logger.info(f"Deleted embedding for employee: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting embedding from ChromaDB: {str(e)}")
            return False
    
    @classmethod
    def update_employee_embedding(
        cls,
        employee_uuid: str,
        embedding: List[float],
        metadata: Dict[str, Any]
    ) -> bool:
        """
        Update employee embedding in ChromaDB.
        
        Args:
            employee_uuid: Employee UUID
            embedding: New facial embedding
            metadata: Updated metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = cls._get_collection()
            doc_id = str(employee_uuid)
            
            # Clean metadata
            clean_metadata = {}
            for key, value in metadata.items():
                if isinstance(value, str):
                    clean_value = str(value).replace('\x00', '').replace('\r', '').replace('\n', ' ').strip()
                    clean_metadata[key] = clean_value
                elif isinstance(value, (int, float)):
                    clean_metadata[key] = str(value)
                else:
                    clean_metadata[key] = str(value)
            
            # Update in collection
            collection.update(
                ids=[doc_id],
                embeddings=[embedding],
                metadatas=[clean_metadata]
            )
            
            logger.info(f"Updated embedding for employee: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating embedding in ChromaDB: {str(e)}")
            return False
    
    @classmethod
    def get_collection_stats(cls) -> Dict[str, Any]:
        """
        Get statistics about the ChromaDB collection.
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            collection = cls._get_collection()
            count = collection.count()
            
            return {
                'collection_name': settings.CHROMA_COLLECTION_NAME,
                'total_embeddings': count,
                'status': 'healthy'
            }
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {str(e)}")
            return {
                'collection_name': settings.CHROMA_COLLECTION_NAME,
                'total_embeddings': 0,
                'status': 'error',
                'error': str(e)
            }
    
    @classmethod
    def reset_client(cls):
        """
        Reset the ChromaDB client and collection.
        Useful when changing settings or troubleshooting.
        """
        cls._client = None
        cls._collection = None
        logger.info("ChromaDB client and collection reset")
