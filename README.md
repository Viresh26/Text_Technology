# 📚 arXiv Research Paper Search Engine  
**Efficient Academic Paper Discovery with Advanced Document Embeddings and Semantic Search**  

**By:** Rustom Bhesania & Viresh Kashetti  
**Course:** Text Technology Summer 25  

---

## 🧰 Tech Stack Used

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-Built--in-lightgrey.svg)](https://www.sqlite.org/)
[![arXiv API](https://img.shields.io/badge/arXiv-API-orange.svg)](https://arxiv.org/help/api)

- **Python 3.8+** – Core programming language for scripts and backend logic  
- **FastAPI** – Planned integration for building a high-performance REST API  
- **SQLite** – Lightweight relational database for local storage of parsed arXiv papers  
- **arXiv API** – Used to fetch academic paper metadata (title, abstract, authors, etc.)  
- **SentenceTransformers** – For generating semantic embeddings from paper abstracts

---

## 🎯 Problem Statement  

Current academic research discovery faces several challenges:

- **Time-Intensive Literature Review:** Manually sifting through numerous papers is time-consuming.  
- **Limited Search Capabilities:** Traditional keyword searches often miss semantically related papers.  
- **Lack of Semantic Understanding:** Current tools struggle to understand the context and meaning of research papers.  
- **No Similarity Analysis:** Difficulty in identifying truly similar papers based on content, not just keywords.  

---

## 💡 Proposed Solution  

This project proposes a local database of arXiv papers with advanced similarity evaluation using:

- **Document Embeddings (BERT-based):** Leveraging pre-trained models to create meaningful numerical representations of paper abstracts.  
- **XML Parsing of arXiv Responses:** Efficiently extracting structured data from arXiv's API.  
- **Multi-modal Search Capabilities:** Enabling searches beyond simple keywords.  
- **FastAPI Interface for Real-Time Semantic Search:** *(Planned for future integration)*  

---

## 🏗️ System Architecture  

```mermaid
graph TD
    A[arXiv API] --> B[XML Response]
    B --> C[XML Processing]
    C --> D[SQLite Database]
    D --> E[Abstract Extraction]
    E --> F[Document Embeddings]
    F --> G[Similarity Comparison]
    G --> H[Similar Papers Output]

    I[User Query] --> J[FastAPI Search Interface]
    J --> G
````

---

## 📁 Repository Structure

* `paperScraper.py`: Fetches paper metadata from the arXiv API based on keywords and categories.
* `xmlparser.py`: Parses XML responses, extracts metadata, generates sentence embeddings, and stores data into SQLite.
* `similarity_score.py`: Retrieves embeddings and calculates cosine similarity to find the most similar papers.
* `arxiv_corpus.db`: SQLite database storing parsed metadata and embeddings.
* `arxiv_papers_response.xml`: Sample XML file for parsing/testing.
* `response.xml`: Temporarily generated file used for printing and inspecting arXiv API responses during testing.  
* `README.md`: Comprehensive project guide.

---

## 🚀 Getting Started

### Prerequisites

* Python 3.8+
* `pip` (Python package installer)

### Installation

Clone the repository:

```bash
git clone https://github.com/Viresh26/Text_Technology.git
cd Text_Technology
```

Install dependencies:

```bash
pip install requests sentence-transformers numpy
```

> ⚠️ The `sentence-transformers` library will automatically download the `'all-MiniLM-L6-v2'` model on first use.

---

## ⚙️ How It Works

### 1. Fetching Data (`paperScraper.py`)

* Defines a list of Computer Science subcategories (`cs.AI`, `cs.CL`, `cs.HC`, `cs.LG`, `cs.MA`)
* Builds an arXiv API query using a user-provided keyword
* Sends HTTP GET request to the arXiv API
* Returns XML content

### 2. Parsing and Storing Data (`xmlparser.py`)

* **Database Creation:** Initializes `arxiv_corpus.db` and creates a table with fields for metadata and embeddings
* **XML Parsing:** Uses `ElementTree` to parse response and extract paper entries
* **Embedding Generation:** Generates embeddings for paper summaries using `all-MiniLM-L6-v2`
* **Data Insertion:** Stores paper data and embeddings into the database

### 3. Finding Similar Papers (`similarity_score.py`)

* **arXiv ID Extraction:** Gets the ID from a given arXiv link
* **Paper Fetching:** Fetches metadata using the arXiv API
* **Embedding:** Generates a new abstract embedding
* **Database Query:** Retrieves stored paper embeddings
* **Cosine Similarity:** Compares new embedding to database entries
* **Result:** Returns the most similar paper

---

## 🏃 Usage Examples

### 1. Initialize the Database and Populate with Papers

```bash
python xmlparser.py
```

> Enter a keyword (e.g., "voice", "GPT 3.5", "machine learning"). Fetches 5 papers and stores them.

### 2. Find Similar Papers

```bash
python similarity_score.py
```

> Enter an arXiv link (e.g., `https://arxiv.org/pdf/2304.11079v1`). Returns the most similar paper from the database.

---

## 🧪 Testing

### Test individual components:

```bash
# Test the paper scraper (prints XML)
python paperScraper.py

# Test XML parser and database population
python xmlparser.py

# Test similarity score calculation
python similarity_score.py
```

---



## 📚 References

* [arXiv API Documentation](https://info.arxiv.org/help/api/index.html)
* [Sentence-BERT Paper](https://arxiv.org/abs/1908.10084)
* [FastAPI Documentation](https://fastapi.tiangolo.com/)
* Reimers & Gurevych, 2019 – Sentence-BERT
* Cer et al., 2018 – Universal Sentence Encoder

---

## 📄 License

Licensed under the MIT License. See the `LICENSE` file for details.

---

## 👥 Authors

* **Rustom Bhesania** – Co-developer
* **Viresh Kashetti** – Co-developer

> *Text Technology Summer 25*

---


