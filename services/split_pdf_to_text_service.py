import json
import os

class SplitPdfToTextService:
    def __init__(self, input_file, output_dir):
        """
        Initialize the service with the input JSON file path and output directory.

        :param input_file: Path to the input JSON file
        :param output_dir: Path to the directory where text files will be saved
        """
        self.input_file = input_file
        self.output_dir = output_dir

    def load_json(self):
        """Load data from the input JSON file."""
        try:
            with open(self.input_file, 'r') as file:
                data = json.load(file)
            return data
        except Exception as e:
            raise RuntimeError(f"Failed to load JSON file: {e}")

    def write_text_files(self, data):
        """
        Write text content from JSON data into separate .txt files.

        :param data: Dictionary containing JSON data
        """
        os.makedirs(self.output_dir, exist_ok=True)
        file_counter = 0

        for key, items in data.items():
            for entry in items:
                file_path = os.path.join(self.output_dir, f"{file_counter}.txt")
                with open(file_path, "w") as file:
                    file.write(entry["text"])
                file_counter += 1
        return file_counter

    def execute(self):
        """Main method to execute the file splitting process."""
        data = self.load_json()
        created_files_count = self.write_text_files(data)
        return os.listdir(self.output_dir), created_files_count

# Usage Example
if __name__ == "__main__":
    service = SplitPdfToTextService(
        input_file="zomato_titles_and_texts_new.json",
        output_dir="zomato_texts"
    )
    try:
        files, count = service.execute()
        print(f"Created {count} files: {files}")
    except Exception as e:
        print(f"Error: {e}")
