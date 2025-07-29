import logging
import requests
import os
import urllib.parse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_arxiv_cs_papers_by_keyword(keyword: str, num_results: int = 5) -> list:
    
    base_url = "https://export.arxiv.org/api/query"

    cs_subcategories = [
        "cs.AI",  # Artificial Intelligence
        "cs.CL",  # Computation and Language
        "cs.HC",  # Human-Computer Interaction
        "cs.LG",  # Machine Learning
        "cs.MA"   # Multiagent Systems
    ]

    # Construct the search query.
    category_parts = [f"cat:{subcat}" for subcat in cs_subcategories]
    category_filter_encoded = " OR ".join(category_parts)

    full_query = f"({category_filter_encoded}) AND {keyword}"
    encoded_full_query = urllib.parse.quote_plus(full_query)

    # Construct the full API URL
    params = {
        "search_query": encoded_full_query,
        "max_results": num_results,
        "sortBy": "relevance", # Sort results by relevance
        "sortOrder": "descending" # Descending order means most relevant first
    }
    api_url = f"{base_url}?search_query={params['search_query']}&sortBy={params['sortBy']}&sortOrder={params['sortOrder']}&max_results={params['max_results']}"

    logging.info(f"Constructed API URL: {api_url}")
    print(f"Fetching raw XML from arXiv for keyword '{keyword}' (top {num_results} results)...")

    try:
        # # Use requests library to make the HTTP GET request
        # # Adding a User-Agent header is good practice for web requests
        # headers = {
        #     "User-Agent": "MyArXivCrawler/1.0 (contact: kashettivir@gmail.com)" # Placeholder email
        # }
        print(api_url)
        response = requests.get(api_url)

        # Raise an exception for HTTP errors (4xx or 5xx)
        response.raise_for_status()

        # Return the raw text content of the response, which is the XML feed
        return response.text

    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP Request failed: {e}", exc_info=True)
        print(f"Failed to fetch XML from arXiv: {e}")
        return ""
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)
        print(f"An unexpected error occurred: {e}")
        return ""
    
def save_xml(xml_content: str, filename: str = "arxiv_papers.xml"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(xml_content)
        print(f"XML response successfully saved to '{os.path.abspath(filename)}'")
    except IOError as e:
        logging.error(f"Failed to save XML to file '{filename}': {e}", exc_info=True)
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    user_keyword = input("Enter the keyword you want to search for in arXiv Computer Science papers: ")

    num_papers_to_fetch = 5

    found_papers = get_arxiv_cs_papers_by_keyword(user_keyword, num_papers_to_fetch)

    # Display the results
    if found_papers:
        print(f"\n--- Top {len(found_papers)} Computer Science Papers related to '{user_keyword}' ---")
        with open("Text_Technology/response.xml", 'w', encoding='utf-8') as f:
            f.write(found_papers)
    else:
        print(f"\nNo papers found in the 'Computer Science' category for the keyword '{user_keyword}'.")
        print("Consider trying a different keyword or broadening your search.")