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
#for l in tuples_list:
#    print(l)

#print(f"Length of list is {len(tuples_list)}")
