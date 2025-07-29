import requests
import xml.etree.ElementTree as ET
from sentence_transformers import SentenceTransformer
import sqlite3
import numpy as np
import json

embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_arxiv_id_from_link(link):
    # Example: http://arxiv.org/abs/2304.11079v1 -> 2304.11079v1
    return link.rstrip('/').split('/')[-1]

def fetch_arxiv_paper(arxiv_id):
    api_url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}"
    response = requests.get(api_url)
    response.raise_for_status()
    xml_content = response.text

    namespaces = {
        'atom': 'http://www.w3.org/2005/Atom',
        'arxiv': 'http://arxiv.org/schemas/atom'
    }
    root = ET.fromstring(xml_content)
    entry = root.find('atom:entry', namespaces)
    if entry is None:
        return None

    paper = {
        'id': entry.find('atom:id', namespaces).text if entry.find('atom:id', namespaces) is not None else 'N/A',
        'title': entry.find('atom:title', namespaces).text if entry.find('atom:title', namespaces) is not None else 'N/A',
        'summary': entry.find('atom:summary', namespaces).text if entry.find('atom:summary', namespaces) is not None else 'N/A',
        'published': entry.find('atom:published', namespaces).text if entry.find('atom:published', namespaces) is not None else 'N/A',
        'updated': entry.find('atom:updated', namespaces).text if entry.find('atom:updated', namespaces) is not None else 'N/A',
        'authors': ", ".join([author.find('atom:name', namespaces).text for author in entry.findall('atom:author', namespaces) if author.find('atom:name', namespaces) is not None]),
        'primary_category': entry.find('arxiv:primary_category', namespaces).get('term') if entry.find('arxiv:primary_category', namespaces) is not None else 'N/A'
    }
    return paper

def fetch_all_embeddings_from_db(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, summary, embedding FROM arxiv_papers WHERE embedding IS NOT NULL")
    results = cursor.fetchall()
    conn.close()
    papers = []
    for row in results:
        paper_id, title, summary, embedding_str = row
        try:
            embedding = np.array(json.loads(embedding_str), dtype=np.float32)
        except Exception:
            continue
        papers.append({
            'id': paper_id,
            'title': title,
            'summary': summary,
            'embedding': embedding
        })
    return papers

def find_most_similar(new_embedding, papers):
    similarities = []
    for paper in papers:
        db_embedding = paper['embedding']
        # Cosine similarity
        sim = np.dot(new_embedding, db_embedding) / (np.linalg.norm(new_embedding) * np.linalg.norm(db_embedding))
        similarities.append(sim)
    if not similarities:
        return None, None
    max_idx = int(np.argmax(similarities))
    return papers[max_idx], similarities[max_idx]

if __name__ == "__main__":
    db_path = "arxiv_corpus.db"  # Adjust path if needed
    arxiv_link = input("Enter the arXiv paper link (e.g., https://arxiv.org/pdf/2507.21046): ")
    arxiv_id = get_arxiv_id_from_link(arxiv_link)
    paper = fetch_arxiv_paper(arxiv_id)
    if paper:
        print("\nPaper attributes from arXiv:")
        for k, v in paper.items():
            print(f"{k}: {v}")
        # Generate embedding for the abstract/summary
        new_embedding = embedding_model.encode(paper['summary'], convert_to_tensor=True).cpu().numpy()
        print("\nFinding most similar paper in the database...")
        db_papers = fetch_all_embeddings_from_db(db_path)
        most_similar_paper, similarity = find_most_similar(new_embedding, db_papers)
        if most_similar_paper:
            print(f"\nMost similar paper in DB (cosine similarity={similarity:.4f}):")
            print(f"ID: {most_similar_paper['id']}")
            print(f"Title: {most_similar_paper['title']}")
            print(f"Summary: {most_similar_paper['summary']}")
        else:
            print("No embeddings found in the database.")
    else:
        print("Paper not found on arXiv.")