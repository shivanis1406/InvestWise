from transformers import BertTokenizer, BertModel
import torch
import requests
import json, os
from serpapi import GoogleSearch
from dotenv import load_dotenv
from newspaper import Article

load_dotenv()

#from bs4 import BeautifulSoup
import concurrent.futures
from typing import Dict, List

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained("bert-base-uncased")

def tuples_to_list(file_path, N=3):  
    with open(file_path, 'r') as file:
        # Reading all lines from the file
        lines = file.readlines()
        
        # Create a list to store the tuples
        tuple_list = []
        elements = []
        temp_ele = ""
        # Iterate through each line and convert it into a tuple
        for line in lines:
            # Strip the newline character and split by the comma
            raw_elements = line.strip().strip('()').split('", "')
            elements = []
            temp_ele = ""
            for i in range(0, len(raw_elements)):
                if i < 2:
                    elements.append(raw_elements[i].strip('"').strip("'"))
                else:
                    temp_ele += raw_elements[i].strip('"').strip("'")
                    if i == len(raw_elements) - 1:
                        elements.append(temp_ele)
                    else:
                        temp_ele += " "

            if len(elements) > 0 and elements != ['']:
                tuple_list.append(tuple(elements))
        
        return list(set(sorted(tuple_list)))

def generate_embeddings(text):
    global model
    global tokenizer
    encoded_input = tokenizer(text, return_tensors='pt')
    #output = model(**encoded_input)
    with torch.no_grad():
        outputs = model(**encoded_input)
        last_hidden_states = outputs.last_hidden_state  # Shape: [batch_size, sequence_length, hidden_size]

        sentence_embedding = last_hidden_states.mean(dim=1)  # Shape: [1, hidden_size]
        return sentence_embedding

def calc_cosine_similarity(text: str, term: str) -> bool:
    # Placeholder function for calculating cosine similarity.
    # Replace with your actual implementation.
    return True  # Assuming all texts are relevant for demonstration purposes.

def extract_texts_concurrently(titles_links: Dict[str, Dict[str, str]]) -> Dict[str, Dict[str, Dict[str, str]]]:
    def extract_article_text_newspaper3k(url: str) -> tuple:
        print(f"Processing URL: {url}")
        article = Article(url)
        try:
            article.download()
        except Exception as e:
            print(f"Error during download: {e}")
            return (url, "")
        try:
            article.parse()
        except Exception as e:
            print(f"Error during parsing: {e}")
            return (url, "")
        article_text = article.text
        return (url, article_text)

    results = {}

    for term, links in titles_links.items():
        print(f"Processing term: {term}")
        term_results = {}

        # Use ThreadPoolExecutor for concurrent text extraction
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Create futures for each URL
            futures = {
                executor.submit(extract_article_text_newspaper3k, url): title 
                for title, url in links.items()
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(futures):
                title = futures[future]
                try:
                    url, text = future.result()
                    text_is_relevant = calc_cosine_similarity(text, term)
                    if text_is_relevant:
                        term_results[title] = {url: text}
                except Exception as e:
                    print(f"Error processing {title}: {e}")

        results[term] = term_results
    print(f"type of results.values() is {type(list(results.values())[0])}")
    return list(results.values())[0]

def isValidNews(url):
    if "livemint.com" in url or "outlookbusiness.com" in url or "businesstoday.com" in url or "financialexpress.com" in url or "reuters.com" in url or "indiatoday.in" in url or "economictimes.indiatimes.com" in url or "techcrunch.com" in url:
        return True
    else:
        return False 
    
def extract_titles_links(news_list, term):
    titles_links = {}
    for item in news_list:
        if "stories" in item:
            for story in item["stories"]:
                if isValidNews(story["link"]):
                    titles_links.update({story["title"] : story["link"]})
        else:
            if isValidNews(item["link"]):
                titles_links.update({item["title"] : item["link"]})
    return {term : titles_links}

def search_news(search_terms):
    titles_links = {}

    for term in search_terms:
        print(f"Extracting Links for {term}")

        params = {
        "q": term,
        "api_key": os.getenv("SERP_API_KEY"),
        "engine": "google_news",
        "gl": "in",
        "hl": "en",
        "num": 5
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        print(f"keys for results : {results}")
        
        try:
            news_results = results["news_results"]
        except Exception as err:
            print(f"Error while extracting news : {err}")
            continue

        # Check if the request was successful
        titles_links.update(extract_titles_links(news_results, term))

    return titles_links

if __name__ == "__main__":
    titles_links = search_news("zomato")
    print(f"Titles & Links")
    for k, v in titles_links.items():
        print(f"{k} : {v}")

    # Extract texts
    extracted_texts = extract_texts_concurrently(titles_links)
    # Print results
    for title, url_text in extracted_texts.items():
        print(f"Title: {title}")
        print(f"URL: {list(url_text.keys())[0]}")
        print(f"Text: {list(url_text.values())[0][:500]}...\n")  # Print first 500 characters
