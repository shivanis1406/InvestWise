import requests
import json, os
from serpapi import GoogleSearch
from dotenv import load_dotenv
from newspaper import Article

load_dotenv()

#from bs4 import BeautifulSoup
import concurrent.futures
from typing import Dict, List

def extract_texts_concurrently(titles_links: Dict[str, str]) -> Dict[str, str]:
    def extract_article_text_bs(title: str, url: str) -> tuple:
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
            # Economic times <article> -> <div with class = artText>
            # Reuters.com <div class="article-body__content__17Yit">
            # retail.economictimes.com <div class="article-section__body__news">
            # financialexpress.com <div class="article-section">
            # outlookbusiness.com <div class=".ob-article" id="articleBody">
            # Extract text (you might need to adjust selectors based on specific website structures)
            paragraphs = soup.find_all(['p', 'ul', 'li'], class_=lambda x: x and any(keyword in x.lower() for keyword in ['content', 'article', 'body', 'text']))
            
            # Combine extracted text
            article_text = ' '.join([p.get_text(strip=True) for p in paragraphs])
            
            return (title, url, article_text)
        
        except Exception as e:
            return (title, f"Error extracting text from {url}: {str(e)}")
    
    def extract_article_text_newspaper3k(url: str, title: str) -> tuple:
        article = Article(url)
        article.download()
        article.parse()
        article_text = article.text
        print(f"Text is {article_text}")
        #title = article.title

        # Explore these later
        #article.nlp()
        #article.keywords
        #article.summary
        return (title, url, article_text)

    # Use ThreadPoolExecutor for concurrent text extraction
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Create futures for each URL
        futures = {
            executor.submit(extract_article_text_newspaper3k, title, url): title 
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
    #extracted_texts = {
#"Zomato Share Price Highlights : Zomato closed today at ₹295.9, up 0.22% from yesterday's ₹295.25 | Stock Market News" : {"https://www.livemint.com/market/live-blog/zomato-share-price-today-latest-live-updates-on-10-dec-2024-11733797852910.html" : ""},
#"Zomato raises $1B in first major fundraise since 2021 listing" : {"https://techcrunch.com/2024/11/28/zomato-raises-1-billion-in-first-major-fundraise-since-2021-listing/" : ""},
#"Zomato launches ‘Recommendations from Friends’ feature for personalised food discovery" : {"https://www.financialexpress.com/business/brandwagon-zomato-launches-recommendations-from-friends-feature-for-personalised-food-discovery-3688479/" : ""},
#"India's Zomato expects food delivery business to grow 30% annually over 5 years, exec says" : {"https://www.reuters.com/business/retail-consumer/indias-zomato-expects-food-delivery-business-grow-30-annually-over-5-years-exec-2024-11-19/" : ""},
#"Zomato Shines Amidst E-commerce Boom: Market Growth and Strong Financial Performance in 2024" : {"https://www.outlookbusiness.com/ampstories/news/zomato-shines-amidst-e-commerce-boom-market-growth-and-strong-financial-performance-in-2024" : ""},
#"Zomato founder 'kicked out' of Shark Tank India 4 due to Swiggy? Makers respond" : {"https://www.indiatoday.in/television/reality-tv/story/deepinder-goyal-out-of-shark-tank-4-after-swiggy-sponsorship-sharks-makers-clarify-2647772-2024-12-10" : ""}
#}
    print(f"Inside main : {extracted_texts}")
    # Print results
    for title, url_text in extracted_texts.items():
        print(f"Title: {title}")
        print(f"URL: {list(url_text.keys())[0]}")
        print(f"Text: {list(url_text.values())[0][:500]}...\n")  # Print first 500 characters

    #for key, value in titles_links.items():
    #    print(f"{key} : {value}")
