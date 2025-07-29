import os
import time
import numpy as np
import mysql.connector
from lxml import etree
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from typing import List, Optional, Dict

# Load environment variables from .env file
load_dotenv()

# --- Database Configuration from Environment Variables ---
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_USER = os.getenv("MYSQL_USER", "arxiv_app_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "your_secure_password")
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "arxiv_papers")

# --- Sentence Transformer Model Loading ---
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2' # As specified in your PDF
embedding_model = None # Will be loaded on app startup

def load_embedding_model():
    """Loads the SentenceTransformer model, checking for GPU availability."""
    global embedding_model
    try:
        start_time = time.time()
        embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        # Check if CUDA (GPU) is available and move model
        if torch.cuda.is_available():
            embedding_model.to('cuda')
            print(f"Model '{EMBEDDING_MODEL_NAME}' loaded on GPU (CUDA) in {time.time() - start_time:.2f} seconds.")
        else:
            print(f"Model '{EMBEDDING_MODEL_NAME}' loaded on CPU in {time.time() - start_time:.2f} seconds.")
    except Exception as e:
        print(f"Error loading embedding model: {e}")
        embedding_model = None # Ensure it's None if loading fails

# --- FastAPI Application Setup ---
app = FastAPI(
    title="arXiv Document Embedding & Similarity API",
    description="API for generating BERT-based document embeddings and performing semantic search on arXiv papers.",
    version="1.0.0"
)

# --- CORS Middleware ---
# Configure CORS to allow requests from specific origins
# In production, replace "*" with the actual domain(s) of your frontend application.
origins = [
    "*", # Allows all origins for development. Be specific in production!
    # "http://localhost",
    # "http://localhost:3000", # Example for a React frontend
    # "https://your-frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# --- Pydantic Models for Request/Response Validation ---

class TextInput(BaseModel):
    """Represents a single text input for embedding."""
    text: str = Field(..., example="This paper discusses novel deep learning architectures for natural language understanding.")

class EmbeddingOutput(BaseModel):
    """Represents the output for a single text embedding."""
    embedding: List[float] = Field(..., description="The BERT-based document embedding (list of floats).")
    model_used: str = Field(..., example=EMBEDDING_MODEL_NAME, description="The name of the Sentence-BERT model used.")

class BatchTextInput(BaseModel):
    """Represents multiple text inputs for batch embedding."""
    texts: List[str] = Field(..., example=["First text to embed.", "Second text for embedding."])

class BatchEmbeddingOutput(BaseModel):
    """Represents the output for batch text embeddings."""
    embeddings: List[List[float]] = Field(..., description="A list of BERT-based document embeddings.")
    model_used: str = Field(..., example=EMBEDDING_MODEL_NAME, description="The name of the Sentence-BERT model used.")

class HealthCheck(BaseModel):
    """Response model for the health check endpoint."""
    status: str = Field(..., example="ok")
    model_loaded: bool = Field(..., example=True)

class SimilarPaper(BaseModel):
    """Represents a similar paper found in the database."""
    arxiv_id: str
    title: str
    abstract: str
    primary_category: str
    published_date: str
    similarity_score: float

class SearchResults(BaseModel):
    """Response model for similarity search results."""
    query_embedding: List[float]
    results: List[SimilarPaper]
    model_used: str

# --- API Endpoints ---

@app.on_event("startup")
async def startup_event():
    """Event handler that runs when the FastAPI application starts up."""
    print("FastAPI application starting up. Loading embedding model...")
    load_embedding_model()

@app.get("/health", response_model=HealthCheck, summary="Health Check")
async def health_check():
    """
    Check the health of the API and whether the embedding model is loaded.
    """
    return {"status": "ok", "model_loaded": embedding_model is not None}

@app.post("/embed", response_model=EmbeddingOutput, summary="Generate Single Document Embedding")
async def embed_text(input: TextInput):
    """
    Generates a BERT-based document embedding for a single piece of text.
    """
    if embedding_model is None:
        raise HTTPException(status_code=503, detail="Embedding model not loaded. Please try again later.")
    
    try:
        embedding = embedding_model.encode(input.text)
        return {"embedding": embedding.tolist(), "model_used": EMBEDDING_MODEL_NAME}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")

@app.post("/embed_batch", response_model=BatchEmbeddingOutput, summary="Generate Batch Document Embeddings")
async def embed_texts_batch(input: BatchTextInput):
    """
    Generates BERT-based document embeddings for multiple pieces of text in a batch.
    This is more efficient for processing multiple inputs.
    """
    if embedding_model is None:
        raise HTTPException(status_code=503, detail="Embedding model not loaded. Please try again later.")
    
    try:
        embeddings = embedding_model.encode(input.texts)
        return {"embeddings": embeddings.tolist(), "model_used": EMBEDDING_MODEL_NAME}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating batch embeddings: {str(e)}")

@app.post("/search_similar_papers", response_model=SearchResults, summary="Search Similar Papers by Semantic Similarity")
async def search_similar_papers(
    query_text: str = Body(..., example="Explain deep learning techniques for natural language processing."),
    top_k: int = Body(10, ge=1, le=100) # Get top 10 results, min 1, max 100
):
    """
    Searches the locally stored arXiv papers for documents semantically similar to the `query_text`.
    Returns the `top_k` most similar papers along with their similarity scores.
    """
    if embedding_model is None:
        raise HTTPException(status_code=503, detail="Embedding model not loaded. Please try again later.")

    try:
        # 1. Generate embedding for the query text
        query_embedding = embedding_model.encode(query_text).tolist()

        # 2. Connect to MySQL and fetch all paper embeddings
        conn = None
        cursor = None
        try:
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DATABASE
            )
            cursor = conn.cursor(dictionary=True) # Get results as dictionaries

            # Fetch arxiv_id, title, abstract, primary_category, published_date, and embedding
            cursor.execute("""
                SELECT arxiv_id, title, abstract, authors, primary_category, published_date, embedding
                FROM papers
                WHERE embedding IS NOT NULL
            """)
            papers_from_db = cursor.fetchall()

        except mysql.connector.Error as err:
            raise HTTPException(status_code=500, detail=f"Database error: {err}")
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

        if not papers_from_db:
            return SearchResults(query_embedding=query_embedding, results=[], model_used=EMBEDDING_MODEL_NAME)

        # Prepare for similarity calculation
        db_embeddings = []
        paper_metadata = []
        for paper in papers_from_db:
            # Convert BLOB back to numpy array (assuming it was stored as float32 bytes)
            try:
                # Assuming the embedding was stored as numpy array bytes (e.g., from .tobytes())
                db_embeddings.append(np.frombuffer(paper['embedding'], dtype=np.float32))
                paper_metadata.append({
                    "arxiv_id": paper['arxiv_id'],
                    "title": paper['title'],
                    "abstract": paper['abstract'],
                    "authors": paper['authors'],
                    "primary_category": paper['primary_category'],
                    "published_date": str(paper['published_date']) # Convert date to string for Pydantic
                })
            except Exception as e:
                print(f"Error decoding embedding for paper {paper.get('arxiv_id')}: {e}")
                continue # Skip this paper if its embedding is corrupted

        if not db_embeddings:
            return SearchResults(query_embedding=query_embedding, results=[], model_used=EMBEDDING_MODEL_NAME)

        # Convert query embedding to numpy array for calculation
        query_embedding_np = np.array(query_embedding, dtype=np.float32)
        db_embeddings_np = np.array(db_embeddings, dtype=np.float32)

        # 3. Calculate Cosine Similarity
        # Cosine similarity formula: (A . B) / (||A|| * ||B||)
        # Reshape query_embedding_np to (1, embedding_dim) for dot product with a matrix
        similarities = np.dot(db_embeddings_np, query_embedding_np) / \
                       (np.linalg.norm(db_embeddings_np, axis=1) * np.linalg.norm(query_embedding_np))

        # 4. Get top_k results
        # Get indices that would sort 'similarities' in descending order
        sorted_indices = np.argsort(similarities)[::-1]

        top_results = []
        for i in sorted_indices[:top_k]:
            paper_info = paper_metadata[i]
            paper_info["similarity_score"] = float(similarities[i]) # Convert numpy float to Python float
            top_results.append(SimilarPaper(**paper_info)) # Use Pydantic model for validation

        return SearchResults(
            query_embedding=query_embedding,
            results=top_results,
            model_used=EMBEDDING_MODEL_NAME
        )

    except Exception as e:
        # Catch any other unexpected errors
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during search: {str(e)}")

# This `if __name__ == "__main__":` block is for direct testing/running,
# but when deployed with uvicorn, it's not strictly necessary.
if __name__ == "__main__":
    # You would typically run this via `uvicorn fastapi_app:app --reload`
    # For a minimal direct test, you could call load_embedding_model() here
    # but the @app.on_event("startup") handles it for the Uvicorn server.
    print("Run this file with: uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload")

