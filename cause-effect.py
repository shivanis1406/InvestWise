import streamlit as st
import requests
import os, json
import networkx as nx
import matplotlib.pyplot as plt
from utils import extract_texts_concurrently, search_news
from openai import OpenAI
from dotenv import load_dotenv
import plotly.express as px

load_dotenv()

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


def main():
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
        options=["Zomato", "Swiggy", "Zepto", "BigBasket"],
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
    elif company_name.lower() == "zepto":
        company_info = "Zepto is a relatively new entrant in the quick commerce market, founded in 2021. It specializes in delivering groceries and essentials within a rapid timeframe, typically under 10 minutes. Zepto operates through a network of dark stores strategically located to optimize delivery efficiency. Despite being smaller than Zomato and Swiggy, Zepto has quickly gained market share by focusing on speed and convenience. The company aims to expand its store count significantly in the coming years to enhance its service capabilities."
    elif company_name.lower() == "bigbasket":
        company_info = "BigBasket is a leading online grocery delivery service in India, established in 2011. It operates an e-commerce platform that connects consumers with a vast network of local and regional grocery suppliers. Customers can browse and purchase a wide range of products, including fresh produce, dairy, and packaged goods, through its user-friendly website and mobile app. BigBasket has also introduced subscription models like BB Star for loyal customers, offering benefits such as free delivery and exclusive discounts. The company emphasizes efficient supply chain management and technology to ensure timely deliveries, including express options that promise delivery within 90 minutes in major cities, thus reshaping the grocery shopping experience in India."
    else:
        pass
        
    if st.button("Generate Effect Map") and company_info != "" and company_name:
        with st.spinner("Generating Effect Map..."):
    
            titles_links = search_news(selected_terms)
            #print(f"Titles & Links")
            #for k, v in titles_links.items():
            #    print(f"{k} : {v}")

            # Extract texts
            extracted_texts = extract_texts_concurrently(titles_links)
            # Print results
            for title, url_text in extracted_texts.items():
                print(f"Title: {title}")
                print(f"URL: {list(url_text.keys())[0]}")
                print(f"Text: {list(url_text.values())[0][:500]}...\n")  # Print first 500 characters

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
    main()
