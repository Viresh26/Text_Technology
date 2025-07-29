
# 📚 arXiv Research Paper Search Engine

> Efficient Academic Paper Discovery with Advanced XML Querying and Document Embeddings

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-blue.svg)](https://www.mysql.com/)
[![arXiv API](https://img.shields.io/badge/arXiv-API-orange.svg)](https://arxiv.org/help/api)

**By: Rustom Bhesania & Viresh Kashetti**  
*Text Technology Summer 25*

---

## 🎯 Problem Statement

Current academic research discovery faces several challenges:

- **Time-Intensive Literature Review**
- **Limited Search Capabilities**
- **Lack of Semantic Understanding**
- **No Similarity Analysis**

---

## 💡 Proposed Solution

A **local database of arXiv papers** with advanced similarity evaluation using:

- Document Embeddings (e.g., BERT)
- XPath/XQuery-based XML parsing
- Multi-modal Search Capabilities
- FastAPI Interface for Real-Time Semantic Search

---

## 🏗️ System Architecture

```mermaid
graph TD
    A[arXiv API] --> B[XML Response]
    B --> C[XPath/XQuery Processing]
    C --> D[MySQL Database]
    D --> E[Abstract Extraction]
    E --> F[Document Embeddings]
    F --> G[Similarity Comparison]
    G --> H[Similar Papers Output]

    I[User Query] --> J[Multi-Modal Search Engine]
    J --> D
    J --> F

    style A fill:#ff9800
    style D fill:#4caf50
    style F fill:#2196f3
    style H fill:#9c27b0
````

---

## 🔄 Workflow

### 1. Data Collection

* arXiv API fetch by category/author/keyword
* XML response with abstract and metadata
* Batch download and XML parsing
* MySQL storage and deduplication

### 2. Data Processing

```
XML → XPath/XQuery → MySQL → BERT Embedding → Semantic Index
```

### 3. Search & Discovery

* Input a reference paper
* Compute embedding
* Compare with database
* Return ranked similar papers

---

## 🚀 Key Features

### 📌 Core

* Multi-Modal Search
* XML-based structured querying
* Semantic ranking
* Real-time FastAPI access

### 🧠 Technical

* Sentence-BERT: all-MiniLM-L6-v2
* Embedding batch processing
* MySQL backend with BLOB storage
* Swagger UI for API testing
* Rate limit aware fetch pipeline

---

## 🛠️ Tech Stack

| Component          | Technology                  |
| ------------------ | --------------------------- |
| **Backend**        | FastAPI, Python             |
| **Database**       | MySQL                       |
| **Embeddings**     | Sentence-BERT, Transformers |
| **XML Processing** | XPath, XQuery, lxml         |
| **Infra**          | Docker (optional)           |
| **Data Source**    | arXiv, Semantic Scholar     |

---

## 📦 Installation & Setup

### Prerequisites

* Python 3.8+
* MySQL 8.0+
* Docker (optional)
* Git

### Step-by-Step

```bash
# 1. Clone Repo
git clone https://github.com/Viresh26/Text_Technology.git
cd Text_Technology

# 2. Virtual Env
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install Deps
pip install -r requirements.txt

# 4. MySQL Setup
mysql -u root -p
CREATE DATABASE arxiv_papers;
CREATE USER 'arxiv_app_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON arxiv_papers.* TO 'arxiv_app_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 5. Add .env
echo "MYSQL_HOST=localhost
MYSQL_USER=arxiv_app_user
MYSQL_PASSWORD=your_secure_password
MYSQL_DATABASE=arxiv_papers" > .env

# 6. Init Schema
python scripts/init_database.py

# 7. Run Pipeline
python arxiv_pipeline.py

# 8. Start API
uvicorn fastapi_app:app --host 0.0.0.0 --port 8000 --reload
```

---

## 📡 API Documentation

Access via: [http://localhost:8000/docs](http://localhost:8000/docs)

### /health (GET)

```json
{
  "status": "ok",
  "model_loaded": true
}
```

### /embed (POST)

```json
{
  "text": "This paper proposes a new algorithm..."
}
```

Returns:

```json
{
  "embedding": [...],
  "model_used": "all-MiniLM-L6-v2"
}
```

### /embed\_batch (POST)

```json
{
  "texts": ["Doc 1 text", "Doc 2 text"]
}
```

Returns:

```json
{
  "embeddings": [[...], [...]],
  "model_used": "all-MiniLM-L6-v2"
}
```

---

## 🧪 Usage Examples

```python
# Search papers
res = requests.get("http://localhost:8000/search", params={
    "query": "machine learning",
    "category": "cs.AI",
    "max_results": 20
})

# Similarity analysis
res = requests.post("http://localhost:8000/similarity", json={
    "reference_paper_id": "2103.00020",
    "similarity_threshold": 0.7
})

# XML Query
res = requests.post("http://localhost:8000/xml-query", json={
    "xpath": "//entry[contains(summary, 'neural network')]",
    "limit": 50
})
```

---

## 🧱 Project Structure

```
Text_Technology/
├── main.py               # FastAPI entry point
├── fastapi_app.py        # Embedding API
├── arxiv_pipeline.py     # Ingestion pipeline
├── .env                  # DB credentials
├── requirements.txt
├── scripts/
│   └── init_database.py
├── api/
│   ├── search.py
│   ├── similarity.py
│   └── xml_query.py
├── core/
│   ├── arxiv_client.py
│   ├── xml_processor.py
│   ├── embeddings.py
│   └── similarity.py
├── database/
│   ├── models.py
│   ├── connection.py
│   └── repositories.py
├── tests/
└── README.md
```

---

## 🚧 Challenges

| Challenge         | Solution                         |
| ----------------- | -------------------------------- |
| arXiv Rate Limits | Smart batching and delays        |
| Missing Metadata  | Semantic Scholar fallback        |
| Embedding Cost    | Batch processing + caching       |
| Scaling Search    | Indexed similarity (e.g., FAISS) |

---

## 🔮 Roadmap

### Phase 1 – Core

* Personalized Paper Recommendations
* Citation Graph / Impact Analysis

### Phase 2 – Productization

* Public API
* Browser Plugin
* Frontend UI (React or Streamlit)

### Phase 3 – Collaboration

* Shared Libraries
* Annotations & Comments
* Research Network Tools

---

## 🧪 Testing

```bash
pytest tests/ -v
pytest tests/ --cov=core --cov-report=html
```

---

## 🤝 Contributing

1. Fork the repo
2. Create a branch: `git checkout -b feature-name`
3. Add your feature + tests
4. Push and open a PR

---

## 📚 References

* [arXiv API Docs](https://info.arxiv.org/help/api/index.html)
* [Sentence-BERT](https://www.sbert.net/)
* [Semantic Scholar API](https://api.semanticscholar.org/)
* Reimers & Gurevych, 2019
* Cer et al., 2018 (USE)

---

## 📄 License

Licensed under the **MIT License**. See the [LICENSE](LICENSE) file.

---

## 👥 Authors

* **Rustom Bhesania**
* **Viresh Kashetti**

*Text Technology Summer 25*

---

## 🆘 Support

* [GitHub Issues](https://github.com/Viresh26/Text_Technology/issues)
* [GitHub Repo](https://github.com/Viresh26/Text_Technology)

---

**⭐ Found it helpful? Star the repo to show your support!**

```

---

Let me know if you'd like:

- A clean `Dockerfile`
- A `.gitignore` template
- A deployment guide (Heroku, Render, EC2, etc.)
- Or integration with frontend tools like Streamlit or React

I'm happy to help streamline the next phase.
```
