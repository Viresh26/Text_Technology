import os
from fastapi import FastAPI, HTTPException # Import HTTPException for proper error handling
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware for CORS
from pydantic import BaseModel
from typing import List, Dict
from sentence_transformers import SentenceTransformer
import torch

# --- Configuration ---
# Choose your BERT-based model.
# 'all-MiniLM-L6-v2' is fast and good for many tasks.
# 'all-mpnet-base-v2' offers higher quality but is larger/slower.
# 'intfloat/e5-small' is another strong option as mentioned in your PDF.
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2'

# CORS configuration
# You should update allow_origins with the actual domains that will access your API in production.
# For local development or broad access, you can use ["*"].
origins = [
    "http://localhost",
    "http://localhost:8000",
    # Add other origins where your frontend or clients will be hosted, e.g.:
    # "https://your-frontend-domain.com",
]

# FastAPI application initialization
app = FastAPI(
    title="BERT Document Embedding API",
    description=f"API to generate document embeddings using the {EMBEDDING_MODEL_NAME} model.",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # Allows specific origins or ["*"] for all
    allow_credentials=True, # Allow cookies to be included in cross-origin HTTP requests
    allow_methods=["*"], # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"], # Allow all headers
)

# Load the Sentence-BERT model once when the application starts
# This avoids reloading the model for every API request, which is crucial for performance.
try:
    # Check for GPU availability and use it if possible
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
    print(f"Successfully loaded model '{EMBEDDING_MODEL_NAME}' on device: {device}")
except Exception as e:
    print(f"Error loading model '{EMBEDDING_MODEL_NAME}': {e}")
    # In a production environment, you might want to raise an exception or exit
    # For now, we'll try to continue with a placeholder or handle gracefully.
    model = None # Indicate that model loading failed

# --- Pydantic Models for Request and Response ---

class TextInput(BaseModel):
    """
    Input schema for the embedding endpoint.
    text: The input text (e.g., an abstract, a full document).
    """
    text: str

class EmbeddingOutput(BaseModel):
    """
    Output schema for the embedding endpoint.
    embedding: A list of floats representing the document embedding.
    model_used: The name of the embedding model used.
    """
    embedding: List[float]
    model_used: str

class HealthCheck(BaseModel):
    """
    Schema for health check response.
    status: "ok" if the service is running and model is loaded.
    model_loaded: Boolean indicating if the model was loaded successfully.
    """
    status: str
    model_loaded: bool

# --- API Endpoints ---

@app.get("/health", response_model=HealthCheck, summary="Health Check")
async def health_check():
    """
    Checks the health of the API and if the embedding model is loaded.
    """
    model_status = model is not None
    return {"status": "ok", "model_loaded": model_status}

@app.post("/embed", response_model=EmbeddingOutput, summary="Generate Document Embedding")
async def get_document_embedding(input: TextInput):
    """
    Generates a BERT-based document embedding for the provided text.

    - **text**: The input text (e.g., research paper abstract, article content).
    """
    if model is None:
        # Handle case where model failed to load
        raise HTTPException(
            status_code=503,
            detail="Embedding model not loaded. Please check server logs."
        )

    # Generate the embedding
    # The .encode() method automatically handles tokenization and model inference.
    # It returns a numpy array, which needs to be converted to a list for JSON serialization.
    embedding = model.encode(input.text).tolist()

    return {
        "embedding": embedding,
        "model_used": EMBEDDING_MODEL_NAME
    }

# You can add more endpoints here, e.g., for similarity comparison,
# but for now, we'll focus on generating the embedding itself.
# If you wanted to do similarity, you'd load existing embeddings
# and compare the new input embedding to them using cosine similarity.

# Example of how you might extend for batch processing (optional)
class BatchTextInput(BaseModel):
    texts: List[str]

class BatchEmbeddingOutput(BaseModel):
    embeddings: List[List[float]]
    model_used: str

@app.post("/embed_batch", response_model=BatchEmbeddingOutput, summary="Generate Embeddings for Multiple Documents")
async def get_batch_document_embeddings(input: BatchTextInput):
    """
    Generates BERT-based document embeddings for a list of provided texts.
    This is more efficient for multiple inputs than individual calls.
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Embedding model not loaded. Please check server logs."
        )

    embeddings = model.encode(input.texts).tolist()

    return {
        "embeddings": embeddings,
        "model_used": EMBEDDING_MODEL_NAME
    }

# To run this API:
# 1. Save the code as, for example, `main.py`.
# 2. Make sure you have `fastapi`, `uvicorn`, and `sentence-transformers` installed:
#    `pip install fastapi uvicorn sentence-transformers torch`
# 3. Run the application from your terminal:
#    `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
# 4. Open your browser to `http://127.0.0.1:8000/docs` to see the interactive API documentation (Swagger UI).
