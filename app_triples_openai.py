import streamlit as st
from openai import OpenAI
import json, os
import requests, time
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

#Used the @st.cache_resource decorator on this function. 
#This Streamlit decorator ensures that the function is only executed once and its result (the OpenAI client) is cached. 
#Subsequent calls to this function will return the cached client, avoiding unnecessary recreation.

@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

client = get_openai_client()

# Initialize assistants and vector stores
# Function to initialize vector stores and assistants
@st.cache_resource
def initialize_assistants_and_vector_stores():
    #Processing Level
    global client
    assistant1 = client.beta.assistants.create(
      name="Processing Level",
      instructions="You are an expert financial analyst. Use you knowledge base to answer questions about any company.",
      model="gpt-4o-mini",
      tools=[{"type": "file_search"}],
      temperature=0,
      top_p = 0.85
      )
    
    # Create a vector store
    vector_store1 = client.beta.vector_stores.create(name="Knowledeg Graph")
    
    # Ready the files for upload to OpenAI
    file_paths = ["tuples.txt"]
    file_streams = [open(path, "rb") for path in file_paths]
    
    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    file_batch1 = client.beta.vector_stores.file_batches.upload_and_poll(
      vector_store_id=vector_store1.id, files=file_streams
    )
    
    # You can print the status and the file counts of the batch to see the result of this operation.
    #print(file_batch1.status)
    #print(file_batch1.file_counts)
    
    
    #Processing Level
    assistant1 = client.beta.assistants.update(
      assistant_id=assistant1.id,
      tool_resources={"file_search": {"vector_store_ids": [vector_store1.id]}},
    )

    return assistant1

assistant1 = initialize_assistants_and_vector_stores()
    
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

        f = open("triples_sorted.docx", "w")
        for triple in list(set(sorted(tuple_list))):
            print(f"Writing to file {triple}.....")
            f.write(str(triple)+"\n")
        f.close()


def parse_response(raw_response):    
    # Example raw response as a string
    #raw_response = "[[\"entity1\", \"entity2\", \"entity3\"], [\"entity4\", \"entity5\", \"entity6\"]]"
    
    # Step 1: Parse the raw_response string into a Python list
    entity_sequences = json.loads(raw_response)
    
    # Step 2: Build a cause-effect map by creating a progression for each sequence
    cause_effect_map = []
    for sequence in entity_sequences:
        sequence_map = []
        for i in range(len(sequence) - 1):
            # Define a step-by-step cause-effect relationship
            cause = sequence[i]
            effect = sequence[i + 1]
            sequence_map.append(f"{cause} leads to {effect}")
        cause_effect_map.append(sequence_map)
    
    # Step 3: Display the cause-effect map
    parsed_response = ""
    start = 1
    for i, sequence_map in enumerate(cause_effect_map, start=1):
        print(f"Sequence {i}:")
        parsed_response += f"\nSequence {i} : "
        start = 1
        for step in sequence_map:
            if start == 0:
                print("  ->", step)
                parsed_response += f" -> {step}"
            else:
                print(step)
                parsed_response += step 
                start = 0
        parsed_response += "\n"
                
    return parsed_response

def analyze_company_information(company_name, assistant_id, user_query):
    global client
    thread = client.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": f"""Use you knowledge base to answer question : {user_query} about company {company_name}. 
Refine and answer questions about financial statements using structured, ordered lists of entities. Follow these output requirements:

Output Requirements:
        1. Format: Return a deterministically ordered list of lists
        2. Structure: [["entity1", "entity2", "entity3"], ["entity4", "entity5", "entity6"]]
        3. Rules:
            - Inner List Size: Each inner list must contain exactly between 3 to 5 entities. No inner list should have fewer than 3 or more than 5 items.
            - Coherence Within Inner Lists: Each entity within an inner list must logically lead to the next entity, forming a clear, step-by-step progression that builds a coherent sequence. Entity1 should naturally lead to entity2, which should lead to entity3, and so on. The entities should represent distinct yet connected ideas relevant to the question.
            - Independence of Outer Lists: Each outer list should represent a separate, self-contained line of reasoning or sequence of ideas related to the question, so that each list offers a distinct path for exploring the topic.
        4. Entity Guidelines:
            - Each entity should be concise and specific, using a short phrase that conveys a clear concept or idea directly tied to the question.
            - Avoid generic or vague terms; each entity should clearly reflect a step in the logical progression of the list.
            - No Connecting Words Within Entities: Refrain from using connectors like "because," "therefore," or "leads to." Each cause-effect relationship should be broken down into separate entities within the list.
        
        Return only the structured list without additional text.""",
            }
        ]
    )
    
    run = client.beta.threads.runs.create_and_poll(
        thread_id=thread.id,
        assistant_id=assistant_id
    )
    
    # Polling loop to wait for a response in the thread
    messages = []
    max_retries = 10  # You can set a maximum retry limit
    retries = 0
    wait_time = 2  # Seconds to wait between retries

    while retries < max_retries:
        messages = list(client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
        if messages:  # If we receive any messages, break the loop
            break
        retries += 1
        time.sleep(wait_time)

    # Check if we got the message content
    if not messages:
        raise TimeoutError("No messages were returned after polling.")

    message_content = messages[0].content[0].text
    annotations = message_content.annotations
    #citations = []
    for index, annotation in enumerate(annotations):
        message_content.value = message_content.value.replace(annotation.text, "")
        #if file_citation := getattr(annotation, "file_citation", None):
        #    cited_file = client.files.retrieve(file_citation.file_id)
        #    citations.append(f"[{index}] {cited_file.filename}")

    return message_content.value

def main():
    st.title("Company Information Analyzer")

    company_name = st.text_input("Enter the company name:", placeholder = "Reliance")
    user_query = st.text_area("Enter your query:", placeholder = "Reliance in healthcare")

    if st.button("Analyze"):
        global assistant1
        raw_response = analyze_company_information(company_name, assistant1.id, user_query)
        response = parse_response(raw_response)
        st.text_area("Response", response, height=400)

if __name__ == "__main__":
    tuples_to_list("tuples.txt", N=3)
    main()
