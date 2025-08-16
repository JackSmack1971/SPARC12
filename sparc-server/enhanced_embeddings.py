"""
enhanced_embeddings.py
======================

Optional enhancement to the SPARC Context Portal that upgrades from TF-IDF
to modern sentence transformers for better semantic search capabilities.

This module provides a drop-in replacement for the semantic search functionality
with the option to use either:
1. TF-IDF (fast, no external dependencies, good for keywords)
2. Sentence Transformers (slower, requires downloading models, excellent for semantics)
3. OpenAI Embeddings (requires API key, best quality, costs money)
"""

import json
import sqlite3
import numpy as np
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from abc import ABC, abstractmethod

# Optional imports - gracefully degrade if not available
try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


@dataclass
class SearchResult:
    """Enhanced search result with similarity score and metadata."""
    item_id: int
    item_type: str
    content: Dict[str, Any]
    similarity_score: float
    phase_name: Optional[str] = None
    timestamp: Optional[str] = None


class EmbeddingProvider(ABC):
    """Abstract base class for different embedding providers."""
    
    @abstractmethod
    def encode(self, texts: List[str]) -> np.ndarray:
        """Encode a list of texts into embeddings."""
        pass
    
    @abstractmethod
    def get_dimension(self) -> int:
        """Get the dimension of embeddings produced by this provider."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Get the name of this embedding provider."""
        pass


class TFIDFEmbeddingProvider(EmbeddingProvider):
    """TF-IDF based embedding provider (original implementation)."""
    
    def __init__(self, max_features: int = 5000):
        self.vectorizer = TfidfVectorizer(
            stop_words='english', 
            max_features=max_features,
            ngram_range=(1, 2)  # Include bigrams for better context
        )
        self._fitted = False
        self._dimension = max_features
    
    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        
        if not self._fitted:
            # First time - fit the vectorizer
            matrix = self.vectorizer.fit_transform(texts)
            self._fitted = True
            self._dimension = matrix.shape[1]
        else:
            # Subsequent times - just transform
            matrix = self.vectorizer.transform(texts)
        
        return matrix.toarray()
    
    def get_dimension(self) -> int:
        return self._dimension
    
    @property
    def name(self) -> str:
        return "tfidf"


class SentenceTransformerProvider(EmbeddingProvider):
    """Sentence transformer based embedding provider."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        if not HAS_SENTENCE_TRANSFORMERS:
            raise ImportError("sentence-transformers not installed. Run: pip install sentence-transformers")
        
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
    
    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        return self.model.encode(texts)
    
    def get_dimension(self) -> int:
        return self.model.get_sentence_embedding_dimension()
    
    @property
    def name(self) -> str:
        return f"sentence_transformer_{self.model_name}"


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""
    
    def __init__(self, model: str = "text-embedding-3-small", api_key: Optional[str] = None):
        if not HAS_OPENAI:
            raise ImportError("openai not installed. Run: pip install openai")
        
        if api_key:
            openai.api_key = api_key
        
        self.model = model
        self._dimension = 1536 if "3-small" in model else 3072  # Approximate
    
    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.array([])
        
        response = openai.embeddings.create(
            model=self.model,
            input=texts
        )
        
        embeddings = [item.embedding for item in response.data]
        return np.array(embeddings)
    
    def get_dimension(self) -> int:
        return self._dimension
    
    @property
    def name(self) -> str:
        return f"openai_{self.model}"


class EnhancedSPARCSearch:
    """Enhanced search functionality for SPARC Context Portal."""
    
    def __init__(self, db_connection: sqlite3.Connection, embedding_provider: EmbeddingProvider):
        self.conn = db_connection
        self.provider = embedding_provider
        self._setup_vector_tables()
    
    def _setup_vector_tables(self):
        """Set up tables for storing vector embeddings."""
        c = self.conn.cursor()
        
        # Create embeddings table
        c.execute("""
            CREATE TABLE IF NOT EXISTS item_embeddings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_type TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                embedding BLOB NOT NULL,
                text_content TEXT NOT NULL,
                embedding_model TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(item_type, item_id, embedding_model)
            )
        """)
        
        # Index for faster lookups
        c.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_type_id 
            ON item_embeddings(item_type, item_id)
        """)
        
        self.conn.commit()
    
    def _get_item_text_content(self, item_type: str, item_id: int) -> Optional[str]:
        """Extract text content from an item for embedding."""
        c = self.conn.cursor()
        
        if item_type == "decisions":
            row = c.execute(
                "SELECT summary, rationale FROM decisions WHERE id = ?", 
                (item_id,)
            ).fetchone()
            if row:
                return f"{row['summary']}. {row['rationale']}"
        
        elif item_type == "progress":
            row = c.execute(
                "SELECT description FROM progress WHERE id = ?", 
                (item_id,)
            ).fetchone()
            if row:
                return row["description"]
        
        elif item_type == "system_patterns":
            row = c.execute(
                "SELECT name, description FROM system_patterns WHERE id = ?", 
                (item_id,)
            ).fetchone()
            if row:
                return f"{row['name']}. {row['description']}"
        
        elif item_type == "custom_data":
            row = c.execute(
                "SELECT category, key, value FROM custom_data WHERE id = ?", 
                (item_id,)
            ).fetchone()
            if row:
                try:
                    value_str = json.loads(row["value"])
                    if not isinstance(value_str, str):
                        value_str = json.dumps(value_str)
                except:
                    value_str = row["value"]
                return f"{row['category']}/{row['key']}: {value_str}"
        
        return None
    
    def update_embeddings(self, item_type: str, item_ids: Optional[List[int]] = None):
        """Update embeddings for specific items or all items of a type."""
        c = self.conn.cursor()
        
        # Get items to update
        if item_ids:
            placeholders = ",".join("?" * len(item_ids))
            if item_type == "decisions":
                rows = c.execute(
                    f"SELECT id FROM decisions WHERE id IN ({placeholders})", 
                    item_ids
                ).fetchall()
            elif item_type == "progress":
                rows = c.execute(
                    f"SELECT id FROM progress WHERE id IN ({placeholders})", 
                    item_ids
                ).fetchall()
            elif item_type == "system_patterns":
                rows = c.execute(
                    f"SELECT id FROM system_patterns WHERE id IN ({placeholders})", 
                    item_ids
                ).fetchall()
            elif item_type == "custom_data":
                rows = c.execute(
                    f"SELECT id FROM custom_data WHERE id IN ({placeholders})", 
                    item_ids
                ).fetchall()
            else:
                return
        else:
            # Update all items of this type
            if item_type == "decisions":
                rows = c.execute("SELECT id FROM decisions").fetchall()
            elif item_type == "progress":
                rows = c.execute("SELECT id FROM progress").fetchall()
            elif item_type == "system_patterns":
                rows = c.execute("SELECT id FROM system_patterns").fetchall()
            elif item_type == "custom_data":
                rows = c.execute("SELECT id FROM custom_data").fetchall()
            else:
                return
        
        # Collect texts and IDs
        texts = []
        ids = []
        for row in rows:
            text_content = self._get_item_text_content(item_type, row["id"])
            if text_content:
                texts.append(text_content)
                ids.append(row["id"])
        
        if not texts:
            return
        
        # Generate embeddings
        embeddings = self.provider.encode(texts)
        
        # Store embeddings
        from datetime import datetime
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        for i, (item_id, text_content) in enumerate(zip(ids, texts)):
            embedding_blob = embeddings[i].tobytes()
            
            c.execute("""
                INSERT OR REPLACE INTO item_embeddings 
                (item_type, item_id, embedding, text_content, embedding_model, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                item_type, 
                item_id, 
                embedding_blob, 
                text_content, 
                self.provider.name, 
                timestamp
            ))
        
        self.conn.commit()
    
    def semantic_search(
        self, 
        query: str, 
        top_k: int = 5, 
        filter_item_types: Optional[List[str]] = None,
        min_similarity: float = 0.1
    ) -> List[SearchResult]:
        """Perform enhanced semantic search using stored embeddings."""
        
        # Generate query embedding
        query_embedding = self.provider.encode([query])[0]
        
        # Retrieve stored embeddings
        c = self.conn.cursor()
        
        conditions = ["embedding_model = ?"]
        params = [self.provider.name]
        
        if filter_item_types:
            placeholders = ",".join("?" * len(filter_item_types))
            conditions.append(f"item_type IN ({placeholders})")
            params.extend(filter_item_types)
        
        query_sql = f"""
            SELECT item_type, item_id, embedding, text_content
            FROM item_embeddings 
            WHERE {" AND ".join(conditions)}
        """
        
        rows = c.execute(query_sql, params).fetchall()
        
        # Calculate similarities
        results = []
        for row in rows:
            stored_embedding = np.frombuffer(row["embedding"], dtype=np.float64)
            
            # Reshape if needed
            if stored_embedding.shape != query_embedding.shape:
                continue
            
            # Calculate cosine similarity
            similarity = np.dot(query_embedding, stored_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(stored_embedding)
            )
            
            if similarity >= min_similarity:
                # Get full item data
                item_data = self._get_full_item_data(row["item_type"], row["item_id"])
                if item_data:
                    results.append(SearchResult(
                        item_id=row["item_id"],
                        item_type=row["item_type"],
                        content=item_data,
                        similarity_score=float(similarity),
                        phase_name=item_data.get("phase_name"),
                        timestamp=item_data.get("timestamp")
                    ))
        
        # Sort by similarity and return top_k
        results.sort(key=lambda x: x.similarity_score, reverse=True)
        return results[:top_k]
    
    def _get_full_item_data(self, item_type: str, item_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve full item data from the database."""
        c = self.conn.cursor()
        
        if item_type == "decisions":
            row = c.execute("SELECT * FROM decisions WHERE id = ?", (item_id,)).fetchone()
        elif item_type == "progress":
            row = c.execute("SELECT * FROM progress WHERE id = ?", (item_id,)).fetchone()
        elif item_type == "system_patterns":
            row = c.execute("SELECT * FROM system_patterns WHERE id = ?", (item_id,)).fetchone()
        elif item_type == "custom_data":
            row = c.execute("SELECT * FROM custom_data WHERE id = ?", (item_id,)).fetchone()
            if row:
                row = dict(row)
                row["value"] = json.loads(row["value"])
        else:
            return None
        
        return dict(row) if row else None
    
    def rebuild_all_embeddings(self):
        """Rebuild embeddings for all items."""
        for item_type in ["decisions", "progress", "system_patterns", "custom_data"]:
            print(f"Rebuilding embeddings for {item_type}...")
            self.update_embeddings(item_type)
        print("All embeddings rebuilt!")


# Integration with the original ContextPortalSPARCServer
class EnhancedContextPortalSPARCServer:
    """Enhanced version of ContextPortalSPARCServer with better semantic search."""
    
    def __init__(self, workspace_dir: str, embedding_type: str = "tfidf", **embedding_kwargs):
        # Import and initialize the original server
        from specialized_mcp_server import ContextPortalSPARCServer
        self.base_server = ContextPortalSPARCServer(workspace_dir)
        
        # Set up enhanced search
        self.embedding_provider = self._create_embedding_provider(embedding_type, **embedding_kwargs)
        self.enhanced_search = EnhancedSPARCSearch(self.base_server._conn, self.embedding_provider)
        
        # Hook into the base server's methods to auto-update embeddings
        self._setup_embedding_hooks()
    
    def _create_embedding_provider(self, embedding_type: str, **kwargs) -> EmbeddingProvider:
        """Create the specified embedding provider."""
        if embedding_type == "tfidf":
            return TFIDFEmbeddingProvider(**kwargs)
        elif embedding_type == "sentence_transformer":
            return SentenceTransformerProvider(**kwargs)
        elif embedding_type == "openai":
            return OpenAIEmbeddingProvider(**kwargs)
        else:
            raise ValueError(f"Unknown embedding type: {embedding_type}")
    
    def _setup_embedding_hooks(self):
        """Set up hooks to automatically update embeddings when items are modified."""
        original_log_decision = self.base_server.log_decision
        original_log_progress = self.base_server.log_progress
        original_log_system_pattern = self.base_server.log_system_pattern
        original_log_custom_data = self.base_server.log_custom_data
        
        def hooked_log_decision(*args, **kwargs):
            decision_id = original_log_decision(*args, **kwargs)
            self.enhanced_search.update_embeddings("decisions", [decision_id])
            return decision_id
        
        def hooked_log_progress(*args, **kwargs):
            progress_id = original_log_progress(*args, **kwargs)
            self.enhanced_search.update_embeddings("progress", [progress_id])
            return progress_id
        
        def hooked_log_system_pattern(*args, **kwargs):
            pattern_id = original_log_system_pattern(*args, **kwargs)
            self.enhanced_search.update_embeddings("system_patterns", [pattern_id])
            return pattern_id
        
        def hooked_log_custom_data(*args, **kwargs):
            data_id = original_log_custom_data(*args, **kwargs)
            self.enhanced_search.update_embeddings("custom_data", [data_id])
            return data_id
        
        # Replace methods with hooked versions
        self.base_server.log_decision = hooked_log_decision
        self.base_server.log_progress = hooked_log_progress
        self.base_server.log_system_pattern = hooked_log_system_pattern
        self.base_server.log_custom_data = hooked_log_custom_data
    
    def semantic_search(self, query: str, **kwargs) -> List[SearchResult]:
        """Enhanced semantic search using the configured embedding provider."""
        return self.enhanced_search.semantic_search(query, **kwargs)
    
    def rebuild_embeddings(self):
        """Rebuild all embeddings."""
        self.enhanced_search.rebuild_all_embeddings()
    
    def __getattr__(self, name):
        """Delegate all other methods to the base server."""
        return getattr(self.base_server, name)


# Example usage
if __name__ == "__main__":
    # Example with different embedding providers
    
    # Using TF-IDF (fast, no dependencies)
    server_tfidf = EnhancedContextPortalSPARCServer(
        workspace_dir="/path/to/workspace",
        embedding_type="tfidf"
    )
    
    # Using Sentence Transformers (better semantic understanding)
    if HAS_SENTENCE_TRANSFORMERS:
        server_st = EnhancedContextPortalSPARCServer(
            workspace_dir="/path/to/workspace",
            embedding_type="sentence_transformer",
            model_name="all-MiniLM-L6-v2"  # Fast and good quality
        )
    
    # Using OpenAI embeddings (best quality, requires API key)
    if HAS_OPENAI:
        server_openai = EnhancedContextPortalSPARCServer(
            workspace_dir="/path/to/workspace",
            embedding_type="openai",
            model="text-embedding-3-small",
            api_key="your-openai-api-key"
        )
    
    # Example search
    results = server_tfidf.semantic_search("authentication patterns")
    for result in results:
        print(f"Score: {result.similarity_score:.3f}")
        print(f"Type: {result.item_type}")
        print(f"Content: {result.content}")
        print("---")
