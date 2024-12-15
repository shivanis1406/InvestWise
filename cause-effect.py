import streamlit as st
import requests
import os, json
import networkx as nx
import matplotlib.pyplot as plt
from utils import extract_texts_concurrently, search_news
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

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
                            "content": f"Analyze the following news event and provide:\n1. Whether the impact is positive, negative, or neutral on company {company_name} (use 😊, 😔, or 😐).\n2. Short and crisp answer for How this event impacts the company {company_name}.\n3. Short and crisp answer for Why this event impacts the company {company_name}.\nLeave 'how' and 'why' blank if sentiment is neutral.\nEvent Title: {title}\nEvent Summary: {text}"
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

    def create_effect_map(self, impacts):
        G = nx.DiGraph()
        
        # Add nodes with more sophisticated attributes
        for impact in impacts:
            node_color = 'green' if '😊' in impact['emoji'] else 'red' if '😔' in impact['emoji'] else 'gray'
            node_size = 1000 if '😊' in impact['emoji'] or '😔' in impact['emoji'] else 500
            
            G.add_node(impact['event'], 
                       sentiment=impact['emoji'], 
                       how=impact['how'], 
                       why=impact['why'],
                       color=node_color,
                       size=node_size)
        
        plt.figure(figsize=(15, 10))
        pos = nx.kamada_kawai_layout(G)  # More aesthetically pleasing layout
        
        # Draw nodes with variable size and color
        nx.draw_networkx_nodes(G, pos, 
                               node_color=[node[1]['color'] for node in G.nodes(data=True)],
                               node_size=[node[1]['size'] for node in G.nodes(data=True)],
                               alpha=0.8)
        nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True)
        nx.draw_networkx_labels(G, pos, font_size=8, font_weight="bold")
        
        plt.title("Comprehensive Effect Map", fontsize=15, fontweight='bold')
        plt.axis('off')
        
        return plt

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
    company_name = st.text_input("Enter Company Name", placeholder="e.g., Apple, Tesla")
                
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
    "pandemic restrictions food delivery",
    "discount wars food delivery profitability",
    "curfews impact food delivery services",
    "social media trends food delivery"
    ]

    # Multiple-selection menu for search terms
    selected_terms = st.multiselect(
        "Select search terms for news analysis:", 
        options=zomato_indirect_search_terms,
        default=zomato_indirect_search_terms[:3]  # Pre-select a few terms
    )
    
    if st.button("Generate Effect Map") and company_name:
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
