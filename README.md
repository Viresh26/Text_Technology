# arXiv Linguistic Analysis Project 🚀

A comprehensive natural language processing system for analyzing and exploring academic papers from arXiv, with advanced features for entity recognition, topic modeling, citation analysis, and interactive visualization.

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Components](#core-components)


## 🎯 Overview

This project goes beyond basic arXiv paper analysis by implementing cutting-edge NLP techniques to extract meaningful insights from academic literature. It combines multiple machine learning approaches to provide researchers with powerful tools for literature discovery, trend analysis, and citation network exploration.

### Key Objectives
- **Intelligent Paper Discovery**: Advanced search and recommendation systems
- **Trend Analysis**: Temporal analysis of research directions and emerging topics
- **Network Analysis**: Citation graphs and author influence metrics
- **Interactive Exploration**: User-friendly web interface with real-time insights
- **Automated Processing**: Self-updating system with scheduled data ingestion

## ✨ Features

### Core Features
- **Multi-source Data Integration**: arXiv API + Semantic Scholar enrichment
- **Advanced Text Processing**: NER, topic modeling, sentiment analysis
- **Real-time Search**: Semantic search with transformer-based embeddings
- **Citation Network Analysis**: Interactive graph visualization
- **Temporal Trend Detection**: Time-series analysis of research patterns
- **Author Influence Ranking**: Comprehensive contributor analysis

### Advanced Add-ons
- **Named Entity Recognition (NER)** with scientific entity extraction
- **Topic Modeling** using LDA and advanced clustering
- **Citation Graph Analysis** with network centrality metrics
- **Interactive Web Interface** with search and exploration tools
- **Multilingual Support** with automatic language detection
- **Question Answering System** for natural language queries
- **Auto-updating Pipeline** with scheduled data refresh

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Processing    │    │   Applications  │
│                 │    │     Pipeline    │    │                 │
│ • arXiv API     │────│ • NLP Engine    │────│ • Web Interface │
│ • Semantic      │    │ • ML Models     │    │ • REST API      │
│   Scholar       │    │ • Graph Builder │    │ • Visualizations│
│ • Manual Feeds  │    │ • Topic Models  │    │ • Export Tools  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────│   Data Storage  │──────────────┘
                        │                 │
                        │ • PostgreSQL    │
                        │ • Vector DB     │
                        │ • File Storage  │
                        │ • Cache Layer   │
                        └─────────────────┘
```

## 🚀 Installation

### Prerequisites
- Python 3.8+
- PostgreSQL 13+
- Redis (for caching)
- Node.js 16+ (for web interface)
- Docker (optional, for containerized deployment)

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/arxiv-linguistic-analysis.git
cd arxiv-linguistic-analysis

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install spaCy models
python -m spacy download en_core_web_sm
python -m spacy download en_core_web_lg

# Install Node.js dependencies for web interface
cd frontend
npm install
cd ..
```

### Database Setup

```bash
# Create PostgreSQL database
createdb arxiv_analysis

# Run migrations
python manage.py migrate

# Create vector extension (for similarity search)
psql arxiv_analysis -c "CREATE EXTENSION IF NOT EXISTS vector;"
```

### Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Required environment variables:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/arxiv_analysis
REDIS_URL=redis://localhost:6379/0

# API Keys
SEMANTIC_SCHOLAR_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here  # Optional, for advanced features

# Application Settings
DEBUG=True
SECRET_KEY=your_secret_key_here
ALLOWED_HOSTS=localhost,127.0.0.1

# Processing Settings
MAX_PAPERS_PER_BATCH=1000
UPDATE_FREQUENCY_HOURS=24
```

## 🏃‍♂️ Quick Start

### 1. Initial Data Collection

```bash
# Download initial dataset
python scripts/fetch_arxiv_data.py --categories "cs.CL,cs.AI" --max-papers 10000

# Process papers through NLP pipeline
python scripts/process_papers.py --batch-size 100

# Build citation network
python scripts/build_citation_graph.py
```

### 2. Start the Services

```bash
# Start the web server
python manage.py runserver

# Start background workers (in separate terminals)
celery -A arxiv_analysis worker -l info
celery -A arxiv_analysis beat -l info

# Start frontend development server
cd frontend
npm run dev
```

### 3. Access the Application

- **Web Interface**: http://localhost:3000
- **API Documentation**: http://localhost:8000/docs
- **Admin Panel**: http://localhost:8000/admin

## 🧩 Core Components

### 1. Data Ingestion (`src/ingestion/`)

**arXiv Fetcher** (`arxiv_fetcher.py`)
```python
class ArxivFetcher:
    def __init__(self, categories=None, max_results=1000):
        self.categories = categories or ['cs.CL', 'cs.AI']
        self.max_results = max_results
    
    def fetch_papers(self, start_date=None, end_date=None):
        """Fetch papers from arXiv API with filtering"""
        
    def enrich_with_semantic_scholar(self, papers):
        """Add citation data from Semantic Scholar"""
```

**Data Models** (`models.py`)
```python
class Paper(models.Model):
    arxiv_id = models.CharField(max_length=50, unique=True)
    title = models.TextField()
    abstract = models.TextField()
    authors = models.JSONField()
    categories = models.JSONField()
    published_date = models.DateTimeField()
    citation_count = models.IntegerField(default=0)
    embedding = VectorField(dimensions=768)
    
class Author(models.Model):
    name = models.CharField(max_length=200)
    institution = models.CharField(max_length=300, blank=True)
    h_index = models.IntegerField(default=0)
    paper_count = models.IntegerField(default=0)
    
class Citation(models.Model):
    citing_paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    cited_paper = models.ForeignKey(Paper, on_delete=models.CASCADE)
    context = models.TextField(blank=True)
```

### 2. NLP Processing (`src/nlp/`)

**Named Entity Recognition** (`ner_processor.py`)
```python
import spacy
from flair.data import Sentence
from flair.models import SequenceTagger

class ScientificNER:
    def __init__(self):
        self.spacy_model = spacy.load("en_core_web_lg")
        self.flair_tagger = SequenceTagger.load("ner-ontonotes-fast")
    
    def extract_entities(self, text):
        """Extract scientific entities from text"""
        entities = {
            'methods': [],
            'datasets': [],
            'metrics': [],
            'organizations': [],
            'locations': []
        }
        
        # SpaCy processing
        doc = self.spacy_model(text)
        for ent in doc.ents:
            if ent.label_ in ['ORG', 'GPE']:
                entities['organizations'].append({
                    'text': ent.text,
                    'label': ent.label_,
                    'confidence': ent._.confidence if hasattr(ent._, 'confidence') else 1.0
                })
        
        # Flair processing for specialized entities
        sentence = Sentence(text)
        self.flair_tagger.predict(sentence)
        
        return entities
```

**Topic Modeling** (`topic_modeler.py`)
```python
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

class TopicModeler:
    def __init__(self, n_topics=20, random_state=42):
        self.n_topics = n_topics
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.lda_model = LatentDirichletAllocation(
            n_components=n_topics,
            random_state=random_state,
            learning_method='batch'
        )
    
    def fit_transform(self, documents):
        """Fit topic model and return document-topic matrix"""
        tfidf_matrix = self.vectorizer.fit_transform(documents)
        doc_topic_matrix = self.lda_model.fit_transform(tfidf_matrix)
        return doc_topic_matrix
    
    def get_topic_words(self, n_words=10):
        """Get top words for each topic"""
        feature_names = self.vectorizer.get_feature_names_out()
        topics = []
        
        for topic_idx, topic in enumerate(self.lda_model.components_):
            top_words_idx = topic.argsort()[-n_words:][::-1]
            top_words = [feature_names[i] for i in top_words_idx]
            topics.append({
                'id': topic_idx,
                'words': top_words,
                'weights': topic[top_words_idx].tolist()
            })
        
        return topics
```

### 3. Citation Network Analysis (`src/network/`)

**Graph Builder** (`citation_graph.py`)
```python
import networkx as nx
from community import community_louvain

class CitationNetworkAnalyzer:
    def __init__(self):
        self.graph = nx.DiGraph()
    
    def build_graph(self, papers, citations):
        """Build citation network from paper and citation data"""
        # Add nodes (papers)
        for paper in papers:
            self.graph.add_node(
                paper.arxiv_id,
                title=paper.title,
                year=paper.published_date.year,
                citation_count=paper.citation_count
            )
        
        # Add edges (citations)
        for citation in citations:
            self.graph.add_edge(
                citation.citing_paper.arxiv_id,
                citation.cited_paper.arxiv_id
            )
    
    def calculate_centrality_metrics(self):
        """Calculate various centrality measures"""
        metrics = {}
        
        # PageRank (paper importance)
        pagerank = nx.pagerank(self.graph)
        
        # Betweenness centrality (bridging papers)
        betweenness = nx.betweenness_centrality(self.graph)
        
        # In-degree (citation count)
        in_degree = dict(self.graph.in_degree())
        
        for node in self.graph.nodes():
            metrics[node] = {
                'pagerank': pagerank.get(node, 0),
                'betweenness': betweenness.get(node, 0),
                'in_degree': in_degree.get(node, 0),
                'out_degree': self.graph.out_degree(node)
            }
        
        return metrics
    
    def detect_communities(self):
        """Detect research communities using Louvain algorithm"""
        undirected_graph = self.graph.to_undirected()
        communities = community_louvain.best_partition(undirected_graph)
        return communities
```
