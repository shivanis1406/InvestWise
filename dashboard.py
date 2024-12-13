import streamlit as st
import pdfplumber
import os
import glob
import re
from typing import List, Dict

# Move page config to the top
st.set_page_config(
    page_title="Insights & Resources Hub", 
    page_icon="🔍", 
    layout="wide"
)

# Custom CSS for enhanced styling
def local_css():
    st.markdown("""
    <style>
    /* Global Styling */
    body {
        color: #333;
        background-color: #f4f6f9;
        font-family: 'Inter', sans-serif;
    }
    
    /* Header Styling */
    .stMarkdown h1 {
        color: #2c3e50;
        font-weight: 700;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Search Input Styling */
    .stTextInput > div > div > input {
        background-color: white;
        border: 2px solid #3498db;
        border-radius: 10px;
        padding: 10px;
        color: #2c3e50;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #2980b9;
        box-shadow: 0 0 10px rgba(52, 152, 219, 0.2);
    }
    
    /* Button Styling */
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 10px 20px;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #2980b9;
        transform: scale(1.05);
    }
    
    /* Expander Styling */
    .stExpander {
        border: 1px solid #e0e4e8;
        border-radius: 10px;
        margin-bottom: 10px;
    }
    
    /* Highlight Styling */
    mark {
        background-color: #ffd700;
        color: #333;
        padding: 2px 4px;
        border-radius: 3px;
    }
    
    /* Statistics Styling */
    .stats-container {
        background-color: #3498db;
        color: white;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        font-size: 16px;
    }
    .stats-container h3 {
        margin-top: 0;
        color: #fff;
        font-weight: bold;
    }
    .stats-container p {
        margin: 5px 0;
    }
    
    /* Welcome Message Styling */
    .welcome-message {
        background-color: #ffffff;
        border-left: 6px solid #3498db;
        padding: 10px 15px;
        border-radius: 10px;
        margin: 20px 0;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

class PDFSearchApp:
    def __init__(self, pdf_directory_pattern: str):
        """
        Initialize the PDF search application with recursive file discovery
        
        :param pdf_directory_pattern: Glob pattern to find PDFs recursively
        """
        # Use glob to find all PDFs recursively
        self.pdf_files = glob.glob(pdf_directory_pattern, recursive=True)
        
        # Validate PDF files found
        if not self.pdf_files:
            st.warning(f"No PDFs found in {pdf_directory_pattern}")
    
    def search_pdf(self, pdf_path: str, search_term: str) -> List[Dict[str, str]]:
        """
        Search a single PDF file for the given search term
        
        :param pdf_path: Full path to the PDF file
        :param search_term: Term to search for in the PDF
        :return: List of dictionaries containing matching passages
        """
        results = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                # Search through each page
                for page_num, page in enumerate(pdf.pages, 1):
                    text = page.extract_text().lower() if page.extract_text() else ''
                    search_term_lower = search_term.lower()
                    
                    # Find all occurrences of the search term
                    if search_term_lower in text:
                        # Extract context around the search term
                        lines = text.split('\n')
                        matching_lines = [
                            line.strip() for line in lines 
                            if search_term_lower in line.lower()
                        ]
                        
                        for match in matching_lines:
                            results.append({
                                'page': str(page_num),
                                'context': match,
                                'file': os.path.relpath(pdf_path),
                                'full_path': pdf_path  # Add full path for preview
                            })
        
        except Exception as e:
            st.error(f"Error searching {pdf_path}: {e}")
        
        return results
    
    def search_all_pdfs(self, search_term: str) -> List[Dict[str, str]]:
        """
        Search through all PDFs found recursively
        
        :param search_term: Term to search for
        :return: Consolidated search results across all PDFs
        """
        all_results = []
        
        for pdf_file in self.pdf_files:
            pdf_results = self.search_pdf(pdf_file, search_term)
            all_results.extend(pdf_results)
        
        return all_results
    
    def generate_preview(self, pdf_path: str, search_term: str, preview_page_count: int = 1) -> str:
        """
        Generate a highlighted preview of PDF pages
        
        :param pdf_path: Full path to the PDF file
        :param search_term: Term to highlight
        :param preview_page_count: Number of pages to preview
        :return: HTML string with highlighted text
        """
        try:
            with pdfplumber.open(pdf_path) as pdf:
                preview_text = ""
                for page_num in range(min(preview_page_count, len(pdf.pages))):
                    page = pdf.pages[page_num]
                    text = page.extract_text() if page.extract_text() else ''
                    
                    # Highlight all occurrences of search term
                    highlighted_text = re.sub(
                        f'({re.escape(search_term)})', 
                        r'<mark style="background-color: #ffd700; color: #333;">\1</mark>', 
                        text, 
                        flags=re.IGNORECASE
                    )
                    
                    preview_text += f"Page {page_num + 1}:\n{highlighted_text}\n\n"
                
                return preview_text
        except Exception as e:
            st.error(f"Error generating preview for {pdf_path}: {e}")
            return "Preview unavailable"

def main():
    # Apply custom CSS
    local_css()
    
    # PDF directory pattern for recursive search
    PDF_DIRECTORY = "../docs/earnings_call/*"
    
    # Title with gradient effect
    st.markdown("""
    <h1 style="
        background: linear-gradient(to right, #3498db, #2980b9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 20px;
    ">Insights & Resources Hub</h1>
    """, unsafe_allow_html=True)
    
    # Create two columns
    left_column, right_column = st.columns([1, 3])
    
    with left_column:
        # Sidebar-like configuration in left column
        st.header("🔍 Search Configuration")
        
        # Search input with icon
        search_term = st.text_input(
            "Search Term", 
            placeholder="Enter search term...",
            help="Find keywords across multiple document types"
        )
        
        # Search button
        search_clicked = st.button("🚀 Search")
        
        # Document Categories with Icons
        st.markdown("### 📚 Resources")
        st.markdown("""
        - 📊 Company Docs
        - 📰 News & Trends
        - 💬 Expert Interviews
        """)
    
    # Right column for results
    with right_column:
        # Main content area for search results
        pdf_search_app = PDFSearchApp(PDF_DIRECTORY)
        
        if search_term and search_clicked:
            try:
                # Perform search
                search_results = pdf_search_app.search_all_pdfs(search_term)
                
                # Display results
                st.markdown(f"## 🔎 Search Results for '{search_term}'")
                
                if search_results:
                    # Statistics container
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"""
                        <div class="stats-container">
                        <h3>📊 Search Statistics</h3>
                        <p><strong>Total Matches:</strong> {len(search_results)}</p>
                        <p><strong>Files Matched:</strong> {len(set(result['file'] for result in search_results))}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    # Detailed results
                    st.markdown("### 📄 Detailed Matches")
                    for result in search_results:
                        with st.expander(f"{result['file']} - Page {result['page']}"):
                            # Display context with highlighted term
                            highlighted_context = re.sub(
                                f'({re.escape(search_term)})', 
                                r'<mark>\1</mark>', 
                                result['context'], 
                                flags=re.IGNORECASE
                            )
                            st.markdown(highlighted_context, unsafe_allow_html=True)
                    
                    # PDF Previews
                    st.markdown("### 🖼️ PDF Previews")
                    for file in set(result['file'] for result in search_results):
                        # Find a result from this file to get the full path
                        file_result = next(r for r in search_results if r['file'] == file)
                        preview = pdf_search_app.generate_preview(file_result['full_path'], search_term)
                        
                        with st.expander(f"Preview: {file}"):
                            st.markdown(preview, unsafe_allow_html=True)
                else:
                    st.warning("No matches found in the PDFs.")
            
            except Exception as e:
                st.error(f"An error occurred: {e}")
        else:
            # Initial state with welcome message
            st.markdown("""
            <div class="welcome-message" style="color: #2c3e50;">
            🔍 Enter a search term and click 'Search Documents' to begin
            </div>
            """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
