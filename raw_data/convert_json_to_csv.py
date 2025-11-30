import pandas as pd
import json
import os

def convert_json_to_csv(input_filename, output_filename):
    """
    Reads data from a Json file, handles potential nested structures,
    and writes the result to a CSV file using pandas.
    """
    if not os.path.exists(input_filename):
        print(f"Error: Input file not found at '{input_filename}'")
        return
    
    print(f"Reading data from: {input_filename}...")
    
    #Read the JSON file
    data = []
    try:
        with open(input_filename, 'r', encoding='utf-8') as f:
            for line in f:
                #Each line is a single JSON object
                data.append(json.loads(line))
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON in file at line: {e.lineno}")
        return
    if not data:
        print("Input file is empty or contained no valid data")
        return
    
    if not data:
        print("Input file is empty or contained no valid data.")
        return
    
    #Create a DataFrame
    df = pd.DataFrame(data)
    
    #Write the DataFrame to a CSV file
    try:
        df.to_csv(output_filename, index=False, encoding = 'utf-8')
        print(f"\nSuccessfully converted {len(df)} items.")
        print(f"Output saved to: {output_filename}")
        print("Done!")
    except Exception as e:
        print(f"An error occurred while writing to CSV file: {e}")
    
#------Execution----
#Define input and output filenames
INPUT_FILE = 'samawa_raw_data.jsonl'
OUTPUT_FILE = 'samawa_converted_data.csv'

if __name__ == "__main__":
    convert_json_to_csv(INPUT_FILE, OUTPUT_FILE)