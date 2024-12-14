import streamlit as st
import requests
import os, json
import networkx as nx
import matplotlib.pyplot as plt
from utils import extract_texts_concurrently, search_news
from openai import OpenAI

class EffectMapGenerator:
    def __init__(self):
        pass

    def analyze_news_impact(self, client, company_name, news_items):
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
                            "content": f"Analyze the following news event and provide:\n1. Whether the impact is positive or negative on company {company_name}(use 😊 or 😔).\n2. Short and crisp answer for How this event impacts the company {company_name}.\n3. Short and crisp answer for Why this event impacts the company {company_name}.\nEvent Title: {title}\nEvent Summary: {text}"
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

            if "Error" not in raw_response and raw_response:
                impacts.append({
                    "event": title,
                    "emoji": raw_response["emoji"],
                    "how": raw_response["how"],
                    "why": raw_response["why"]
                })
        
        return impacts

    def create_effect_map(self, impacts):
        """
        Create a network graph representing impact relationships
        """
        G = nx.DiGraph()
        
        # Add nodes and edges
        for impact in impacts:
            G.add_node(impact['event'], 
                       sentiment=impact['emoji'], 
                       how=impact['how'], 
                       why=impact['why'])
        
        # Create visualization
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(G, k=0.5)
        nx.draw_networkx_nodes(G, pos, node_color=['green' if '😊' in node[1]['sentiment'] else 'red' for node in G.nodes(data=True)], 
                                node_size=500, alpha=0.8)
        nx.draw_networkx_edges(G, pos)
        nx.draw_networkx_labels(G, pos, font_size=8, font_weight="bold")
        
        plt.title(f"Effect Map")
        plt.axis('off')
        
        return plt

def main():
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    st.title("Company Effect Map Generator 📊")

    # Company input
    company_name = st.text_input("Enter Company Name", placeholder="e.g., Apple, Tesla")
    
    if st.button("Generate Effect Map") and company_name:
        with st.spinner("Generating Effect Map..."):
            
            zomato_indirect_search_terms = [
            # Macro-Economic & Societal Trends
            "Millennial eating habits",
            "Gen Z dining preferences", 
            "Work from home food consumption",
            "Urban migration patterns",
            "Middle-class disposable income trends",
            "Startup employee lifestyle",

            # Technology & Ecosystem
            "Hyperlocal delivery innovations",
            "Gig economy worker satisfaction", 
            "Smartphone penetration rural India",
            "Digital payment adoption",
            "UPI transaction growth",
            "Electric two-wheeler delivery",
            "Battery swapping infrastructure",

            # Geopolitical & Regulatory
            "Startup visa regulations",
            "Foreign investment in Indian startups",
            "Cryptocurrency impact on digital transactions",
            "Cross-border payment regulations", 
            "Data localization laws",

            # Climate & Sustainability
            "Food packaging sustainability",
            "Carbon footprint delivery services",
            "Plant-based meat alternatives",
            "Urban farming trends", 
            "Cold chain logistics innovation",

            # Consumer Psychology
            "Social media food trends",
            "Influencer dining recommendations",
            "Hygiene perception restaurant delivery",
            "Mental health workplace eating habits",
            "Personalized nutrition trends",

            # Infrastructure & Connectivity
            "5G impact on delivery services",
            "Internet penetration tier-2 cities", 
            "Smart city digital infrastructure",
            "Rural broadband expansion",

            # Demographic Shifts
            "Nuclear family growth",
            "Single professional lifestyle",
            "Women workforce participation", 
            "Young professional migration",

            # Health & Wellness
            "Immunity-boosting food trends",
            "Personalized diet plans",
            "Mental health nutrition", 
            "Fitness tracking food choices",

            # Entertainment & Lifestyle
            "OTT platform viewing habits",
            "Gaming community food preferences",
            "Weekend entertainment spending", 
            "Co-living space meal patterns",

            # Global Trend Crossovers
            "K-pop food culture",
            "International cuisine popularity", 
            "Global food delivery models",
            "Fusion cuisine trends"
        ]

            titles_links = search_news(zomato_indirect_search_terms)
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
            impacts = generator.analyze_news_impact(client, company_name, extracted_texts)
            
            # Display impacts
            st.subheader("News Impacts")
            for impact in impacts:
                st.markdown(f"**{impact['emoji']} {impact['event']}**")
                st.markdown(f"- How: {impact['how']}")
                st.markdown(f"- Why: {impact['why']}")
                st.markdown("---")
            
            # Create and display effect map
            effect_map = generator.create_effect_map(impacts)
            st.pyplot(effect_map)

if __name__ == "__main__":
    main()