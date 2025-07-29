import paperScraper
import os
import xml.etree.ElementTree as ET
import sqlite3
import logging
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')  # Load the embedding model

# Configure logging for better debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_arxiv_xml(xml_content: str) -> list:
    papers_data = []
    if not xml_content:
        logging.warning("No XML content provided for parsing.")
        return papers_data

    try:
        root = ET.fromstring(xml_content)

        namespaces = {
            'atom': 'http://www.w3.org/2005/Atom',
            'arxiv': 'http://arxiv.org/schemas/atom'
        }

        # Iterate over each 'entry' element in the XML feed
        for entry in root.findall('atom:entry', namespaces):
            paper = {}
            # Extract basic fields and handling potential None values
            paper['id'] = entry.find('atom:id', namespaces).text if entry.find('atom:id', namespaces) is not None else 'N/A'
            paper['title'] = entry.find('atom:title', namespaces).text if entry.find('atom:title', namespaces) is not None else 'N/A'
            paper['summary'] = entry.find('atom:summary', namespaces).text if entry.find('atom:summary', namespaces) is not None else 'N/A'
            paper['published'] = entry.find('atom:published', namespaces).text if entry.find('atom:published', namespaces) is not None else 'N/A'
            paper['updated'] = entry.find('atom:updated', namespaces).text if entry.find('atom:updated', namespaces) is not None else 'N/A'

            # Extract authors
            authors = [author.find('atom:name', namespaces).text for author in entry.findall('atom:author', namespaces) if author.find('atom:name', namespaces) is not None]
            paper['authors'] = ", ".join(authors) if authors else 'N/A'

            # Extract primary category (using the arXiv namespace)
            primary_category_element = entry.find('arxiv:primary_category', namespaces)
            paper['primary_category'] = primary_category_element.get('term') if primary_category_element is not None else 'N/A'

            papers_data.append(paper)
        logging.info(f"Successfully parsed {len(papers_data)} papers from XML.")
    except ET.ParseError as e:
        logging.error(f"XML parsing error: {e}", exc_info=True)
        print(f"Error parsing XML content: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred during XML parsing: {e}", exc_info=True)
        print(f"An unexpected error occurred during XML parsing: {e}")

    return papers_data

def create_database_and_table(db_name: str):
    # Try to create a database in case of 1st use
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS arxiv_papers (
                id TEXT PRIMARY KEY,
                title TEXT,
                summary TEXT,
                published TEXT,
                updated TEXT,
                authors TEXT,
                primary_category TEXT
            )
        ''')
        conn.commit()
        logging.info(f"Database '{db_name}' and table 'arxiv_papers' ensured to exist.")
    except sqlite3.Error as e:
        logging.error(f"SQLite error during table creation: {e}", exc_info=True)
        print(f"Error creating database table: {e}")
    finally:
        if conn:
            conn.close()

def insert_paper_data(db_name: str, paper_data: dict):
    conn = None
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO arxiv_papers (id, title, summary, published, updated, authors, primary_category)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            paper_data.get('id'),
            paper_data.get('title'),
            paper_data.get('summary'),
            paper_data.get('published'),
            paper_data.get('updated'),
            paper_data.get('authors'),
            paper_data.get('primary_category')
        ))
        conn.commit()
        logging.info(f"Inserted/Ignored paper: {paper_data.get('id')}")
    except sqlite3.Error as e:
        logging.error(f"SQLite error during data insertion for {paper_data.get('id')}: {e}", exc_info=True)
        print(f"Error inserting paper data for {paper_data.get('id')}: {e}")
    finally:
        if conn:
            conn.close()

def fetch_parse_and_save_to_db(keyword: str, num_papers: int = 5,
                                output_xml_filename: str = "arxiv_papers_response.xml",
                                database_name: str = "arxiv_corpus.db"):
    """
    Orchestrates fetching XML, parsing it, and saving the structured data to a database.

    Args:
        keyword (str): The keyword to search for in arXiv.
        num_papers (int): The maximum number of papers to fetch.
        output_xml_filename (str): The filename to save the raw XML response.
        database_name (str): The name of the SQLite database file.
    """
    output_dir = "Text_Technology"
    os.makedirs(output_dir, exist_ok=True)
    full_output_xml_path = os.path.join(output_dir, output_xml_filename)
    full_database_path = os.path.join(output_dir, database_name)

    print(f"--- Starting process for keyword: '{keyword}' ---")
    print(f"1. Fetching raw XML from arXiv...")
    xml_content = paperScraper.get_arxiv_cs_papers_by_keyword(keyword, num_papers)

    if xml_content:
        print(f"2. Saving raw XML to '{full_output_xml_path}'...")
        paperScraper.save_xml(xml_content, full_output_xml_path)

        print(f"3. Parsing XML content...")
        parsed_papers = parse_arxiv_xml(xml_content)

        if parsed_papers:
            print(f"Generating sentence embeddings for abstracts...")
            abstracts = [paper['summary'] for paper in parsed_papers]
            embeddings = embedding_model.encode(abstracts, convert_to_tensor=True)

            for paper, embedding in zip(parsed_papers, embeddings):
                paper['embedding'] = embedding.cpu().numpy().tolist()


            print(f"4. Creating/Connecting to database '{full_database_path}' and ensuring table exists...")
            create_database_and_table(full_database_path)

            print(f"5. Inserting parsed paper data into the database...")
            for paper in parsed_papers:
                insert_paper_data(full_database_path, paper)
            print(f"Successfully processed and saved {len(parsed_papers)} papers to the database.")
        else:
            print("No papers parsed from the XML content. Database insertion skipped.")
    else:
        print("Failed to fetch XML content. Skipping parsing and database insertion.")

    print(f"--- Process completed for keyword: '{keyword}' ---")

if __name__ == "__main__":
    user_keyword = input("Enter the keyword you want to search for in arXiv Computer Science papers: ")
    num_papers_to_fetch = 5 # You can adjust this number

    # Call the main orchestration function
    fetch_parse_and_save_to_db(user_keyword, num_papers_to_fetch)