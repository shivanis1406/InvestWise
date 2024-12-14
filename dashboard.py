import streamlit as st
import pdfplumber
import os, io
import glob
import re
from typing import List, Dict
import urllib.parse
import requests
import tempfile, shutil
from urllib.parse import quote

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
    /* PDF Viewer Styling */
    .pdf-viewer {
        width: 100%;
        height: 800px;
        border: 1px solid #e0e4e8;
        border-radius: 10px;
    }

    /* Scrollable lists */
    .scrollable-list {
        max-height: 400px;
        overflow-y: auto;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 10px;
        margin-top: 10px;
    }

    /* Category list styling */
    .category-container {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin-top: 10px;
        margin-bottom: 20px;
    }

    .category-item {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 16px;
    }

    /* Hover effects for list items */
    .list-item:hover {
        background-color: #f0f0f0;
        cursor: pointer;
    }
    </style>
    """, unsafe_allow_html=True)

class PDFSearchApp:
    def __init__(self, pdf_directory: list):
        """
        Initialize the PDF search application with recursive file discovery
        
        :param pdf_directory_pattern: Glob pattern to find PDFs recursively
        """
        # Use glob to find all PDFs recursively
        self.pdf_files = [os.path.join(root, file)
                          for root, _, files in os.walk(pdf_directory)
                          for file in files if file.endswith('.pdf')]

        print(f"pdf files are {self.pdf_files}")
        # Validate PDF files found
        if not self.pdf_files:
            st.warning(f"No PDFs found in {pdf_directory}")
    
    def search_pdf(self, pdf_path: str, search_term: str) -> List[Dict[str, str]]:
        """
        Search a single PDF file for the given search term
        
        :param pdf_path: path  to the PDF file
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
                                'file': pdf_path,
                                'full_path': pdf_path  # Add full path for preview
                            })
                        print(f"results : {results}")
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
        
        for pdf_path in self.pdf_files:
            pdf_results = self.search_pdf(pdf_path, search_term)
            if pdf_results:
                all_results.extend(pdf_results)
        
        return all_results

    def render_pdf_with_highlight(self, pdf_path: str, search_term: str, highlight_text: str) -> None:
        try:

            file_url = None

            # Create a temporary file URL for the PDF
            with open(pdf_path, 'rb') as file:
                temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                temp_pdf.write(file.read())
                shutil.copyfileobj(file, temp_pdf)
                temp_pdf_path = temp_pdf.name
                temp_pdf.close()
                file_url = f"file://{quote(temp_pdf_path)}"

                print(f"PDF Temp File Path: {temp_pdf_path}")

            
            # Generate a unique identifier for the PDF viewer
            pdf_viewer_id = f"pdf_viewer_{hash(pdf_path)}"
            
            # Use PDF.js for rendering
            pdf_viewer_html = f"""
            <html>
            <head>
                <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.11.338/pdf_viewer.min.css">
                <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.11.338/pdf.min.js"></script>
                <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.11.338/pdf_viewer.min.js"></script>
                <style>
                    body {{ margin: 0; }}
                    #container {{ position: relative; }}
                    #viewerContainer {{ width: 100%; height: 800px; }}
                    .highlight {{ background-color: yellow; }}
                </style>
            </head>
            <body>
                <div id="container">
                    <div id="viewerContainer">
                        <div id="{pdf_viewer_id}" class="pdfViewer"></div>
                    </div>
                </div>
                <script>
                    pdfjsLib.getDocument('{file_url}').promise.then(function(pdfDocument) {{
                        var pdfViewer = new pdfjsViewer.PDFViewer({{
                            container: document.getElementById('viewerContainer'),
                            viewer: document.getElementById('{pdf_viewer_id}')
                        }});
                        
                        pdfViewer.setDocument(pdfDocument);
                        
                        // Function to find and highlight search term
                        function findAndHighlightText(searchTerm) {{
                            console.log('Searching for:', searchTerm);
                        }}
                        
                        findAndHighlightText('{highlight_text}');
                    }});
                </script>
            </body>
            </html>
            """
            
            # Render the PDF viewer
            st.components.v1.html(pdf_viewer_html, height=850, scrolling=True)
        
        except Exception as e:
            st.error(f"Error rendering PDF {pdf_path}: {e}")


def main():
    # Apply custom CSS
    local_css()
    
    # Initialize session state for search results and selected PDF
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'selected_pdf' not in st.session_state:
        st.session_state.selected_pdf = None
    if 'selected_text_chunk' not in st.session_state:
        st.session_state.selected_text_chunk = None
    
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
    
    # Search input centered at the top
    st.markdown('<div style="display: flex; justify-content: center;">', unsafe_allow_html=True)
    search_term = st.text_input(
        "Search Term", 
        placeholder="Enter search term...",
        help="Find keywords across multiple document types",
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Horizontal Category Display
    st.markdown("""
    <div class="category-container">
        <div class="category-item">📊 Company Docs</div>
        <div class="category-item">📰 News & Trends</div>
        <div class="category-item">💬 Expert Interviews</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Search button centered
    st.markdown('<div style="display: flex; justify-content: center;">', unsafe_allow_html=True)
    search_clicked = st.button("🚀 Search")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Create three columns for the three panels
    panel_a, panel_b, panel_c = st.columns(3)
    
    # Main content area for search results
    pdf_search_app = PDFSearchApp('../docs/quarterly_rpts/')
    
    # Handle search and PDF selection
    if search_term and search_clicked:
        try:
            # Perform search with a spinner to indicate loading
            with st.spinner(f"Searching for '{search_term}'..."):
                st.session_state.search_results = pdf_search_app.search_all_pdfs(search_term)
        
        except Exception as e:
            st.error(f"An error occurred: {e}")
    
    # Panel A: List of PDFs
    with panel_a:
        if st.session_state.search_results:
            st.markdown(f"## 📄 Docs with '{search_term}'")
            pdf_files = list(set(result['file'] for result in st.session_state.search_results))
            for pdf in pdf_files:
                if st.button(pdf, key=f"pdf_{pdf}"):
                    st.session_state.selected_pdf = pdf
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Panel B: List of text chunks for the selected PDF
    with panel_b:
        if st.session_state.selected_pdf:
            st.markdown(f"## 📄 {st.session_state.selected_pdf.split('/')[-1]}")
            chunks = [result['context'] for result in st.session_state.search_results if result['file'] == st.session_state.selected_pdf]
            for chunk in chunks:
                if st.button(chunk, key=f"chunk_{chunk}"):
                    st.session_state.selected_text_chunk = chunk
            st.markdown('</div>', unsafe_allow_html=True)
    
    # Panel C: Render selected PDF
    with panel_c:
        if st.session_state.selected_text_chunk:
            st.markdown(f"## 📄 Full PDF View")
            pdf_search_app.render_pdf_with_highlight(st.session_state.selected_pdf, search_term, st.session_state.selected_text_chunk)

if __name__ == "__main__":
    main()
