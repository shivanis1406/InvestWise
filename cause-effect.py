import streamlit as st
import requests
import os, json
import networkx as nx
import matplotlib.pyplot as plt
from utils import extract_texts_concurrently, search_news
from openai import OpenAI
from dotenv import load_dotenv
import plotly.express as px
import time
from pymongo import MongoClient

load_dotenv()
username = os.getenv('MONGODB_USERNAME')
password = os.getenv('MONGODB_PASSWORD')

# MongoDB connection URI
MONGO_URI = f"mongodb+srv://{username}:{password}@cluster0.bkywn.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Connect to MongoDB
client = MongoClient(MONGO_URI)
# Check connection
try:
    client.server_info()  # Will raise an exception if unable to connect
    print("Connection successful!")
except Exception as err:
    print(f"Connection failed to {MONGO_URI}: {err}")
    
db = client['news_database']  # Database name
collection = db['titles_links']  # Collection name


# Function to save to MongoDB
def save_to_mongodb(titles_links):
    # Replace the existing document with a new one
    collection.replace_one(
        {"_id": "titles_links_time"},  # Identify the document by _id
        {"_id": "titles_links_time", "titles_links": titles_links, "time": time.time()},  # New document
        upsert=True  # Ensure the document is created if it doesn't exist
    )

# Function to read from MongoDB
def read_from_mongodb():
    document = collection.find_one({"_id": "titles_links_time"})
    print(f"Document read of db is {document}")
    return document
    
class EffectMapGenerator:
    def __init__(self):
        pass

    def analyze_news_impact(self, client, company_name, company_info, news_items):
        """
        Analyze news items and generate impact assessments
        Note: This is a simplified version. In real-world, 
        you'd want more sophisticated NLP/ML for impact analysis
        """
        impacts = []
        raw_response = {}
        texts = ""

        for title, url_text in news_items.items():
            text = list(url_text.values())[0]
            if text == "":
                continue
        
            response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system", 
                            "content": "You analyze news events and return JSON data with impact analysis."
                        },
                        {
                            "role": "user", 
                            "content": f"Analyze the following news event and provide the impact on company {company_name} :\n1. Whether the impact is positive, negative, or neutral (use 😊, 😔, or 😐).\n2. Short and crisp answer for How this event impacts the company.\n3. Short and crisp answer for Why this event impacts the company.\nLeave 'how' and 'why' blank if sentiment is neutral.\nEvent Title: {title}\nEvent Summary: {text}. Few lines about the {company_name} - {company_info}"
                        }
                    ],
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "impact_analysis",
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "emoji": {
                                        "description": "Whether the impact is positive or negative",
                                        "type": "string"
                                    },
                                    "how": {
                                        "description": "Short and crisp answer for how the event impacts the company",
                                        "type": "string"
                                    },
                                    "why": {
                                        "description": "Short and crisp answer for why the event impacts the company",
                                        "type": "string"
                                    }
                                },
                                "additionalProperties": False
                            }
                        }
                    }
                )
            
            try:
                raw_response = json.loads(response.choices[0].message.content)
            except Exception as e:
                raw_response = {"Error" : e}

            print(f"raw_response : {raw_response}")

            if "Error" not in raw_response and raw_response["emoji"] != "😐":
                impacts.append({
                    "event": title,
                    "emoji": raw_response["emoji"],
                    "how": raw_response["how"],
                    "why": raw_response["why"]
                })
        
        return impacts

    def create_impact_summary(self, impacts):
            # Count number of positive, negative, and neutral impacts
            sentiment_counts = {
                "Positive": sum(1 for impact in impacts if impact['emoji'] == '😊'),
                "Negative": sum(1 for impact in impacts if impact['emoji'] == '😔'),
            }
            
            # Plot the sentiment distribution
            fig = px.pie(names=list(sentiment_counts.keys()), values=list(sentiment_counts.values()), 
                         title="Sentiment Distribution of News Events")
            st.plotly_chart(fig)


def main(scrape_news):
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    # Title of the application
    st.title("SectorPulse 📈📰💼")
    
    # Tagline with formatting
    st.markdown(
        """
        **Your compass to sector trends and company impacts!**
        """,
        unsafe_allow_html=True
    )
    # Company input
    #company_name = st.text_input("Enter Company Name", placeholder="e.g., Zomato, Swiggy")
    # Company selection dropdown
    company_name = st.selectbox(
        "Select a Company:",
        options=["Zomato", "Swiggy"],
        index=0
    )
    
    zomato_indirect_search_terms = [
    "urbanization impact on food delivery",
    "disposable income food delivery trends",
    "smartphone adoption food delivery",
    "internet penetration food delivery growth",
    "food delivery promotional campaigns",
    "tier 2 city food delivery expansion",
    "sustainable packaging food delivery",
    "logistics technology advancements food delivery",
    "cloud kitchen business model",
    "healthy food demand delivery",
    "local store partnerships quick commerce",
    "10-minute delivery model",
    "fuel prices food delivery costs",
    "food delivery market competition",
    "food safety regulations delivery",
    "gig worker protests food delivery",
    "economic slowdown food delivery impact",
    "environmental concerns food delivery",
    "delivery delays customer complaints",
    "adverse weather food delivery disruptions",
    "discount wars food delivery profitability",
    "curfews impact food delivery services",
    "social media trends food delivery",
    "last-mile delivery innovations in food delivery",
    "impact of AI on food delivery services",
    "food delivery competition among startups",
    "growth of dark kitchens in food delivery",
    "delivery management software for food delivery",
    "consumer preferences in food delivery services",
    "food delivery pricing models",
    "food delivery subscription services",
    "impact of subscription models in grocery delivery",
    "mobile app usage trends in food delivery",
    "delivery tracking technology food industry",
    "consumer behavior changes in grocery delivery",
    "food delivery logistics optimization",
    "supply chain challenges in food delivery",
    "sustainability in food delivery packaging",
    "grocery delivery market trends",
    "e-commerce impact on grocery delivery services",
    "delivery efficiency in quick-commerce",
    "grocery delivery in rural areas",
    "crowdsourced delivery for grocery services",
    "on-demand grocery delivery model",
    "grocery delivery service regulations",
    "cloud-based solutions for grocery delivery",
    "AI-powered recommendations in grocery delivery",
    "environmental impact of grocery delivery services",
    "delivery service fees in food delivery",
    "partnering with local grocery stores for quick-commerce",
    "consumer adoption of 10-minute grocery delivery",
    "food delivery services during holidays",
    "impact of food delivery on traditional retail",
    "smart packaging in grocery deliveries",
    "predictive analytics in grocery delivery",
    "supply chain innovations in quick-commerce",
    "cross-border food delivery trends",
    "crowdshipping for food delivery",
    "impact of vehicle electrification on food delivery",
    "changing demographics of food delivery customers",
    "driverless delivery technology in quick-commerce"
]
    #zomato_indirect_search_terms = ["driverless delivery technology in quick-commerce"]
                                    
    # Multiple-selection menu for search terms
    selected_terms = st.multiselect(
        "Select key indicators for analysis:", 
        options=zomato_indirect_search_terms,
        default=zomato_indirect_search_terms[:3]  # Pre-select a few terms
    )
    company_info = ""
    
    if company_name.lower() == "zomato":
        company_info = "Zomato is an Indian multinational restaurant aggregator and food delivery service founded in 2008. It provides users with information about restaurants, including menus and user reviews, while facilitating food delivery from partner restaurants across over 1,000 cities. Zomato operates several business models, including an aggregator model that lists restaurants, a delivery service for partners, and a subscription service called Zomato Gold that offers exclusive deals to users. Recently, Zomato has expanded into quick commerce with its acquisition of Blinkit, aiming to deliver groceries and essentials rapidly through a network of dark stores."
    elif company_name.lower() == "swiggy":
        company_info = "Swiggy is another leading food delivery platform in India, launched in 2014. It offers a wide range of services including food delivery from local restaurants, grocery delivery through its Instamart service, and a cloud kitchen model that allows restaurants to operate without physical dining spaces. Swiggy has focused on enhancing user experience through features like real-time tracking of orders and a diverse menu selection. The company has also ventured into quick commerce, competing closely with Zomato's Blinkit by leveraging its extensive logistics network to ensure fast deliveries."
    else:
        pass
        
    if st.button("Generate Effect Map") and company_info != "" and company_name:
        with st.spinner("Generating Effect Map..."):
            # Main logic
            titles_links = {}
            start_time = 0
            try:
                # Read from MongoDB
                document = read_from_mongodb()
                if document:
                    start_time = document["time"]
                    titles_links = document["titles_links"]
                else:
                    start_time = 0
                    titles_links = {}
            except Exception as e:
                print(f"Error reading from MongoDB: {e}")
                start_time = 0
                titles_links = {}
        
            if time.time() - start_time > 4 * 60 * 60 or start_time == 0 or scrape_news == 1:  # 4 hours
                st.write("📰 Stay updated with the latest news! This app scrapes fresh news every 4 hours. ⏳ Since it's been more than 4 hours since the last update, we're fetching the newest headlines for you now! 🚀")
                # Find the latest news
                titles_links = search_news(zomato_indirect_search_terms)
                
                # Save to MongoDB
                save_to_mongodb(titles_links)
                print(f"Data saved to MongoDB : {titles_links}")
            else:
                print(f"Time elapsed: {time.time() - start_time} secs")
                print("Using cached data from MongoDB.")
                print("Titles and links:", titles_links)

            selected_titles_links = {}
            for topic in selected_terms:
                selected_titles_links.update({topic : titles_links[topic]})
            
            # Extract texts
            extracted_texts = extract_texts_concurrently(selected_titles_links)
            
            # Print results
            for title, url_text in extracted_texts.items():
                print(f"Title: {title}")
                print(f"URL: {list(url_text.keys())[0]}")
                #print(f"Text: {list(url_text.values())[0][:500]}...\n")  # Print first 500 characters

            if not extracted_texts:
                st.warning("No news found. Try a different company name.")
                return
            
            # Analyze news impacts
            generator = EffectMapGenerator()
            impacts = generator.analyze_news_impact(client, company_name, company_info, extracted_texts)
            
            # Display impacts
            st.subheader("News Impacts")
            for impact in impacts:
                st.markdown(f"**{impact['emoji']} {impact['event']}**")
                st.markdown(f"- How: {impact['how']}")
                st.markdown(f"- Why: {impact['why']}")
                st.markdown("---")
            
            # Create and display effect map
            effect_map = generator.create_impact_summary(impacts)

if __name__ == "__main__":
    scrape_news = 1
    main(scrape_news)
