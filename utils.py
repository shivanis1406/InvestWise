from transformers import BertTokenizer, BertModel
import torch

tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
model = BertModel.from_pretrained("bert-base-uncased")

def tuples_to_list(file_path, N=3):  
    with open(file_path, 'r') as file:
        # Reading all lines from the file
        lines = file.readlines()
        
        # Create a list to store the tuples
        tuple_list = []
        elements = []
        temp_ele = ""
        # Iterate through each line and convert it into a tuple
        for line in lines:
            # Strip the newline character and split by the comma
            raw_elements = line.strip().strip('()').split('", "')
            elements = []
            temp_ele = ""
            for i in range(0, len(raw_elements)):
                if i < 2:
                    elements.append(raw_elements[i].strip('"').strip("'"))
                else:
                    temp_ele += raw_elements[i].strip('"').strip("'")
                    if i == len(raw_elements) - 1:
                        elements.append(temp_ele)
                    else:
                        temp_ele += " "

            if len(elements) > 0 and elements != ['']:
                tuple_list.append(tuple(elements))
        
        return list(set(sorted(tuple_list)))

def generate_embeddings(text):
    global model
    global tokenizer
    encoded_input = tokenizer(text, return_tensors='pt')
    #output = model(**encoded_input)
    with torch.no_grad():
        outputs = model(**encoded_input)
        last_hidden_states = outputs.last_hidden_state  # Shape: [batch_size, sequence_length, hidden_size]

        sentence_embedding = last_hidden_states.mean(dim=1)  # Shape: [1, hidden_size]
        return sentence_embedding

