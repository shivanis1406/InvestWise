import requests
import json, os
from serpapi import GoogleSearch
from dotenv import load_dotenv

load_dotenv()

from bs4 import BeautifulSoup
import concurrent.futures
from typing import Dict, List

def extract_texts_concurrently(titles_links: Dict[str, str]) -> Dict[str, str]:
    def extract_article_text(title: str, url: str) -> tuple:
        try:
            # Set a user agent to mimic a browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Fetch the webpage
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse the HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text (you might need to adjust selectors based on specific website structures)
            paragraphs = soup.find_all(['p', 'article', 'div'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['content', 'article', 'body', 'text']))
            
            # Combine extracted text
            article_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            return (title, url, article_text)
        
        except Exception as e:
            return (title, f"Error extracting text from {url}: {str(e)}")

    # Use ThreadPoolExecutor for concurrent text extraction
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Create futures for each URL
        futures = {
            executor.submit(extract_article_text, title, url): title 
            for title, url in titles_links.items()
        }
        
        # Collect results as they complete
        for future in concurrent.futures.as_completed(futures):
            title, url, text = future.result()
            results[title] = {url:text}
    
    return results

def isValidNews(url):
    if "livemint.com" in url or "outlookbusiness.com" in url or "businesstoday.com" in url or "financialexpress.com" in url or "reuters.com" in url or "indiatoday.in" in url or "economictimes.indiatimes.com" in url or "techcrunch.com" in url:
        return True
    else:
        return False 
    
def extract_titles_links(news_list):
    titles_links = {}
    for item in news_list:
        if "stories" in item:
            for story in item["stories"]:
                if isValidNews(story["link"]):
                    titles_links.update({story["title"] : story["link"]})
        else:
            if isValidNews(item["link"]):
                titles_links.update({item["title"] : item["link"]})
    return titles_links

def search_news(company_name):

    params = {
    "q": company_name,
    "tbm": "nws",
    "location": "India",
    "api_key": os.getenv("SERP_API_KEY")
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    news_results = results["news_results"]

    # Check if the request was successful
    titles_links = extract_titles_links(news_results)
    return titles_links

if __name__ == "__main__":
    titles_links = search_news("zomato")

    # Extract texts
    extracted_texts = extract_texts_concurrently(titles_links)

    # Print results
    for title, url_text in extracted_texts.items():
        print(f"Title: {title}")
        print(f"Text: {list(url_text.values())[0][:500]}...\n")  # Print first 500 characters

    #for key, value in titles_links.items():
    #    print(f"{key} : {value}")
