import os
import requests
import xml.etree.ElementTree as ET
import mysql.connector
from mysql.connector import Error
from sentence_transformers import SentenceTransformer
import torch
import time
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
ARXIV_API_BASE_URL = "http://export.arxiv.org/api/query"
EMBEDDING_MODEL_NAME = 'all-MiniLM-L6-v2' # As per your PDF
ARXIV_API_RATE_LIMIT_DELAY = 3.5 # seconds, to respect arXiv's rate limits (approx 50 requests / 3s)

# MySQL Database Configuration (from environment variables)
DB_HOST = os.getenv("MYSQL_HOST")
DB_USER = os.getenv("MYSQL_USER")
DB_PASSWORD = os.getenv("MYSQL_PASSWORD")
DB_DATABASE = os.getenv("MYSQL_DATABASE")

# --- Database Functions ---

def create_db_connection():
    """Establishes and returns a MySQL database connection."""
    connection = None
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            passwd=DB_PASSWORD,
            database=DB_DATABASE
        )
        if connection.is_connected():
            print(f"Successfully connected to MySQL database: {DB_DATABASE}")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

def create_papers_table(connection):
    """Creates the 'papers' table if it doesn't exist."""
    cursor = connection.cursor()
    table_create_query = """
    CREATE TABLE IF NOT EXISTS papers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        arxiv_id VARCHAR(255) UNIQUE NOT NULL,
        title TEXT NOT NULL,
        abstract TEXT NOT NULL,
        authors TEXT,
        primary_category VARCHAR(255),
        published_date DATETIME,
        embedding BLOB
    )
    """
    try:
        cursor.execute(table_create_query)
        connection.commit()
        print("Table 'papers' ensured to exist.")
    except Error as e:
        print(f"Error creating table: {e}")
    finally:
        cursor.close()

def insert_paper_data(connection, paper: Dict[str, Any]):
    """Inserts or updates paper metadata into the 'papers' table."""
    cursor = connection.cursor()
    # Check if paper already exists
    check_query = "SELECT arxiv_id FROM papers WHERE arxiv_id = %s"
    cursor.execute(check_query, (paper['arxiv_id'],))
    result = cursor.fetchone()

    if result:
        print(f"Paper {paper['arxiv_id']} already exists. Skipping insertion.")
        return # Skip insertion if it exists, for a simple run. Could update if needed.

    insert_query = """
    INSERT INTO papers (arxiv_id, title, abstract, authors, primary_category, published_date)
    VALUES (%s, %s, %s, %s, %s, %s)
    """
    try:
        cursor.execute(insert_query, (
            paper['arxiv_id'],
            paper['title'],
            paper['abstract'],
            paper['authors'],
            paper['primary_category'],
            paper['published_date']
        ))
        connection.commit()
        print(f"Inserted paper: {paper['arxiv_id']}")
    except Error as e:
        print(f"Error inserting paper {paper['arxiv_id']}: {e}")
    finally:
        cursor.close()

def update_paper_embedding(connection, arxiv_id: str, embedding: List[float]):
    """Updates the embedding for a paper in the 'papers' table."""
    cursor = connection.cursor()
    # Convert list of floats to bytes for BLOB storage
    embedding_bytes = torch.tensor(embedding).numpy().tobytes()

    update_query = "UPDATE papers SET embedding = %s WHERE arxiv_id = %s"
    try:
        cursor.execute(update_query, (embedding_bytes, arxiv_id))
        connection.commit()
        print(f"Updated embedding for paper: {arxiv_id}")
    except Error as e:
        print(f"Error updating embedding for paper {arxiv_id}: {e}")
    finally:
        cursor.close()

def fetch_papers_for_embedding(connection) -> List[Dict[str, Any]]:
    """Fetches papers from the database that do not yet have an embedding."""
    cursor = connection.cursor(dictionary=True) # Return rows as dictionaries
    select_query = "SELECT arxiv_id, abstract FROM papers WHERE embedding IS NULL"
    papers = []
    try:
        cursor.execute(select_query)
        papers = cursor.fetchall()
        print(f"Found {len(papers)} papers without embeddings.")
    except Error as e:
        print(f"Error fetching papers for embedding: {e}")
    finally:
        cursor.close()
    return papers


# --- ArXiv API Functions ---

def fetch_papers_from_arxiv(search_query: str, start_index: int = 0, max_results: int = 100) -> Optional[str]:
    """
    Fetches papers from arXiv API based on a search query.
    Returns XML response string.
    """
    params = {
        "search_query": search_query,
        "start": start_index,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }
    print(f"Fetching papers from arXiv with query: {search_query} (start={start_index}, max_results={max_results})")
    try:
        response = requests.get(ARXIV_API_BASE_URL, params=params)
        response.raise_for_status() # Raise an HTTPError for bad responses (4xx or 5xx)
        time.sleep(ARXIV_API_RATE_LIMIT_DELAY) # Respect rate limits
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from arXiv API: {e}")
        return None

def parse_arxiv_xml(xml_string: str) -> List[Dict[str, Any]]:
    """
    Parses arXiv XML response and extracts relevant paper data.
    """
    papers_data = []
    # Register arXiv namespaces for correct parsing
    namespaces = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    root = ET.fromstring(xml_string)

    for entry in root.findall('atom:entry', namespaces):
        try:
            arxiv_id = entry.find('atom:id', namespaces).text.split('/')[-1]
            title = entry.find('atom:title', namespaces).text.strip()
            abstract = entry.find('atom:summary', namespaces).text.strip()
            published_str = entry.find('atom:published', namespaces).text
            # ArXiv dates are typically ISO 8601, direct conversion to DATETIME
            published_date = published_str.split('T')[0] + ' ' + published_str.split('T')[1].split('Z')[0]

            authors_list = [author.find('atom:name', namespaces).text for author in entry.findall('atom:author', namespaces)]
            authors = ", ".join(authors_list)

            primary_category = entry.find('arxiv:primary_category', namespaces).get('term')

            papers_data.append({
                'arxiv_id': arxiv_id,
                'title': title,
                'abstract': abstract,
                'authors': authors,
                'primary_category': primary_category,
                'published_date': published_date
            })
        except AttributeError as e:
            print(f"Skipping entry due to missing data: {e} in {entry.find('atom:id', namespaces).text if entry.find('atom:id', namespaces) is not None else 'Unknown ID'}")
            continue
    return papers_data

# --- Embedding Model Loading ---

def load_embedding_model():
    """Loads the Sentence-BERT embedding model."""
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
        print(f"Successfully loaded embedding model '{EMBEDDING_MODEL_NAME}' on device: {device}")
        return model
    except Exception as e:
        print(f"Error loading embedding model '{EMBEDDING_MODEL_NAME}': {e}")
        return None

# --- Main Execution Flow ---

def run_pipeline(search_category: str = "cat:cs.AI", max_papers_to_fetch: int = 200, batch_size: int = 100):
    """
    Runs the complete pipeline: fetches papers, stores metadata, and generates/stores embeddings.
    """
    connection = None
    embedding_model = None
    try:
        # 1. Establish Database Connection and Create Table
        connection = create_db_connection()
        if not connection:
            print("Failed to establish database connection. Exiting.")
            return

        create_papers_table(connection)

        # 2. Load Embedding Model
        embedding_model = load_embedding_model()
        if not embedding_model:
            print("Failed to load embedding model. Cannot generate embeddings. Exiting.")
            return

        # 3. Fetch Papers from arXiv and Store Metadata
        print("\n--- Starting Data Collection and Storage ---")
        fetched_count = 0
        while fetched_count < max_papers_to_fetch:
            xml_response = fetch_papers_from_arxiv(
                search_query=search_category,
                start_index=fetched_count,
                max_results=batch_size
            )
            if xml_response:
                papers = parse_arxiv_xml(xml_response)
                if not papers:
                    print("No more papers found in this range or parsing error. Breaking loop.")
                    break
                for paper in papers:
                    insert_paper_data(connection, paper)
                fetched_count += len(papers)
                print(f"Processed {len(papers)} papers. Total fetched so far: {fetched_count}")
            else:
                print("Failed to fetch papers. Stopping data collection.")
                break
            # Add a small delay even between batches to be extra cautious with rate limits
            time.sleep(1)

        print("\n--- Starting Embedding Generation ---")
        # 4. Fetch Papers from DB that need embeddings and Generate/Store them
        papers_to_embed = fetch_papers_for_embedding(connection)
        if not papers_to_embed:
            print("No new papers to embed or all papers already have embeddings.")
        else:
            abstracts = [paper['abstract'] for paper in papers_to_embed]
            arxiv_ids = [paper['arxiv_id'] for paper in papers_to_embed]

            print(f"Generating embeddings for {len(abstracts)} abstracts...")
            # Generate embeddings in a batch for efficiency
            embeddings = embedding_model.encode(abstracts).tolist()

            # Update embeddings in the database
            for i, arxiv_id in enumerate(arxiv_ids):
                update_paper_embedding(connection, arxiv_id, embeddings[i])

        print("\nPipeline execution complete.")

    finally:
        if connection and connection.is_connected():
            connection.close()
            print("MySQL connection closed.")

if __name__ == "__main__":
    # Example usage: Fetch 200 papers from the 'cs.AI' category in batches of 100
    run_pipeline(search_category="cat:cs.AI", max_papers_to_fetch=200, batch_size=100)
    # You can change the category or max_papers_to_fetch as needed
    # Example: run_pipeline(search_category="au:Y. Lecun", max_papers_to_fetch=50)
