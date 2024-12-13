from unstructured.partition.pdf import partition_pdf
import json

class PDFProcessor:
    def __init__(self, filename):
        self.filename = filename
        self.title_to_texts = {}

    def parse_pdf(self):
        # Parse the PDF into elements
        elements = partition_pdf(filename=self.filename)
        current_title = None

        # Iterate through the elements and process titles, narrative texts, and page numbers
        for element in elements:
            # Convert the element to a dictionary for easier processing
            new_element = element.to_dict()

            # Extract the page number (if available) from the metadata
            page_number = new_element.get('metadata', {}).get('page_number', 'Unknown')

            # Check if the element is a title
            if new_element['type'] == 'Title':
                current_title = new_element['text'].strip()  # Set the current title as the key
                if current_title not in self.title_to_texts:
                    self.title_to_texts[current_title] = []  # Initialize the list for this title

            # Check if the element is narrative text
            elif new_element['type'] == 'NarrativeText' and current_title:
                # Append the narrative text and page number to the list of the current title
                self.title_to_texts[current_title].append({
                    "text": new_element['text'].strip(),
                    "page_number": page_number
                })

    def remove_empty_titles(self):
        self.title_to_texts = {title: texts for title, texts in self.title_to_texts.items() if texts}

    @staticmethod
    def remove_duplicates(texts):
        seen = set()
        unique_texts = []
        for text_entry in texts:
            text_tuple = (text_entry['text'], text_entry['page_number'])
            if text_tuple not in seen:
                seen.add(text_tuple)
                unique_texts.append(text_entry)
        return unique_texts

    @staticmethod
    def remove_invalid_entries(texts):
        valid_texts = []
        for text_entry in texts:
            text = text_entry['text']
            # Check for patterns like "character space character"
            if not all(len(word) == 1 or len(word) == 2 or len(word) == 3 for word in text.split()):
                valid_texts.append(text_entry)
        return valid_texts

    def clean_data(self):
        self.title_to_texts = {
            title: self.remove_invalid_entries(self.remove_duplicates(texts))
            for title, texts in self.title_to_texts.items()
        }
        self.remove_empty_titles()

    def save_to_json(self, output_file):
        # Store the result in JSON format
        with open(output_file, "w", encoding="utf-8") as json_file:
            json.dump(self.title_to_texts, json_file, ensure_ascii=False, indent=4)
        print(f"Data extracted and saved to {output_file}.")

# Example usage
if __name__ == "__main__":
    processor = PDFProcessor(filename="Downloads/zomato.pdf")
    processor.parse_pdf()
    processor.clean_data()
    processor.save_to_json(output_file="zomato_titles_and_texts.json")
