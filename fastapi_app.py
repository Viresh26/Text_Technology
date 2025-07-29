import os
import time
import numpy as np
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from typing import List, Optional, Dict

# Load environment variables from .env file
load_dotenv()

# --- XML File Configuration ---
XML_FILE_PATH = os.getenv("ARXIV_XML_PATH", "Text_Technology/arxiv_papers_response.xml")

# --- Sentence Transformer Model Loading ---
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2' # As specified in your PDF
embedding_model = None # Will be loaded on app startup

def load_embedding_model():
    """Loads the SentenceTransformer model, checking for GPU availability."""
    global embedding_model
    try:
        import torch
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
origins = [
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Models for Request/Response Validation ---
class TextInput(BaseModel):
    text: str = Field(..., example="This paper discusses novel deep learning architectures for natural language understanding.")

class EmbeddingOutput(BaseModel):
    embedding: List[float] = Field(..., description="The BERT-based document embedding (list of floats).")
    model_used: str = Field(..., example=EMBEDDING_MODEL_NAME, description="The name of the Sentence-BERT model used.")

class BatchTextInput(BaseModel):
    texts: List[str] = Field(..., example=["First text to embed.", "Second text for embedding."])

class BatchEmbeddingOutput(BaseModel):
    embeddings: List[List[float]] = Field(..., description="A list of BERT-based document embeddings.")
    model_used: str = Field(..., example=EMBEDDING_MODEL_NAME, description="The name of the Sentence-BERT model used.")

class HealthCheck(BaseModel):
    status: str = Field(..., example="ok")
    model_loaded: bool = Field(..., example=True)

class SimilarPaper(BaseModel):
    title: str
    abstract: str
    primary_category: str
    published_date: str
    similarity_score: float

class SearchResults(BaseModel):
    query_embedding: List[float]
    results: List[SimilarPaper]
    model_used: str

# --- XML Parsing Helper ---
def parse_arxiv_xml(xml_path: str):
    """Parse the XML file and return a list of papers with title, abstract, category, published date."""
    namespaces = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    papers = []
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        for entry in root.findall('atom:entry', namespaces):
            title = entry.find('atom:title', namespaces)
            abstract = entry.find('atom:summary', namespaces)
            published = entry.find('atom:published', namespaces)
            primary_category = entry.find('arxiv:primary_category', namespaces)
            papers.append({
                "title": title.text if title is not None else "N/A",
                "abstract": abstract.text if abstract is not None else "N/A",
                "primary_category": primary_category.get('term') if primary_category is not None else "N/A",
                "published_date": published.text if published is not None else "N/A"
            })
    except Exception as e:
        print(f"Error parsing XML: {e}")
    return papers

# --- API Endpoints ---
@app.on_event("startup")
async def startup_event():
    print("FastAPI application starting up. Loading embedding model...")
    load_embedding_model()

@app.get("/health", response_model=HealthCheck, summary="Health Check")
async def health_check():
    return {"status": "ok", "model_loaded": embedding_model is not None}

@app.post("/embed", response_model=EmbeddingOutput, summary="Generate Single Document Embedding")
async def embed_text(input: TextInput):
    if embedding_model is None:
        raise HTTPException(status_code=503, detail="Embedding model not loaded. Please try again later.")
    try:
        embedding = embedding_model.encode(input.text)
        return {"embedding": embedding.tolist(), "model_used": EMBEDDING_MODEL_NAME}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")

@app.post("/embed_batch", response_model=BatchEmbeddingOutput, summary="Generate Batch Document Embeddings")
async def embed_texts_batch(input: BatchTextInput):
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
    top_k: int = Body(10, ge=1, le=100)
):
    if embedding_model is None:
        raise HTTPException(status_code=503, detail="Embedding model not loaded. Please try again later.")
    try:
        # 1. Generate embedding for the query text
        query_embedding = embedding_model.encode(query_text)

        # 2. Read papers from XML
        papers = parse_arxiv_xml(XML_FILE_PATH)
        if not papers:
            return SearchResults(query_embedding=query_embedding.tolist(), results=[], model_used=EMBEDDING_MODEL_NAME)

        # 3. Generate embeddings for all abstracts
        abstracts = [p['abstract'] for p in papers]
        db_embeddings = embedding_model.encode(abstracts)

        # 4. Calculate cosine similarity
        query_embedding_np = np.array(query_embedding, dtype=np.float32)
        db_embeddings_np = np.array(db_embeddings, dtype=np.float32)
        similarities = np.dot(db_embeddings_np, query_embedding_np) / (
            np.linalg.norm(db_embeddings_np, axis=1) * np.linalg.norm(query_embedding_np)
        )

        # 5. Get top_k results
        sorted_indices = np.argsort(similarities)[::-1]
        top_results = []
        for i in sorted_indices[:top_k]:
            paper = papers[i]
            top_results.append(SimilarPaper(
                title=paper['title'],
                abstract=paper['abstract'],
                primary_category=paper['primary_category'],
                published_date=paper['published_date'],
                similarity_score=float(similarities[i])
            ))
        return SearchResults(
            query_embedding=query_embedding.tolist(),
            results=top_results,
            model_used=EMBEDDING_MODEL_NAME
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during search: {str(e)}")

if __name__ == "__main__":
    print("Run this file with: uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload")

