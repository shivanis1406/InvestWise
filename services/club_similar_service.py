import json
from collections import defaultdict

class ClubSimilarService:
    def __init__(self, file_path):
        """
        Initialize the service by loading the JSON file.

        Args:
            file_path (str): Path to the JSON file to read.
        """
        self.file_path = file_path
        self.data = self._load_json()

    def _load_json(self):
        """
        Load JSON data from the file.

        Returns:
            dict: Parsed JSON data.
        """
        try:
            with open(self.file_path, 'r') as file:
                return json.load(file)
        except FileNotFoundError:
            print(f"Error: File not found at {self.file_path}")
            return {}
        except json.JSONDecodeError:
            print("Error: Invalid JSON format.")
            return {}

    def club_texts_by_page(self):
        """
        Club texts for each key by `page_number` with a maximum of 3 texts per group.

        Returns:
            dict: Updated data with texts clubbed by `page_number`.
        """
        result = {}

        for key, entries in self.data.items():
            page_grouped = defaultdict(list)

            # Group texts by `page_number`
            for entry in entries:
                page_grouped[entry['page_number']].append(entry['text'])

            # Combine texts for each page_number with a maximum of 3 texts per group
            combined_entries = []
            for page_number, texts in page_grouped.items():
                for i in range(0, len(texts), 3):
                    combined_entries.append({
                        "page_number": page_number,
                        "text": " ".join(texts[i:i+3])
                    })

            result[key] = combined_entries

        return result

    def save_result(self, output_path, result):
        """
        Save the result to a JSON file.

        Args:
            output_path (str): Path to save the output JSON file.
            result (dict): The processed result to save.
        """
        try:
            with open(output_path, 'w') as file:
                json.dump(result, file, indent=4)
                print(f"Result saved to {output_path}")
        except IOError:
            print(f"Error: Unable to save file to {output_path}")

# Usage example
if __name__ == "__main__":
    input_file = "zomato_earnings_call_q2_fy25.json"
    output_file = "zomato_earnings_call_q2_fy25_new.json"

    service = ClubSimilarService(input_file)
    processed_data = service.club_texts_by_page()
    service.save_result(output_file, processed_data)
