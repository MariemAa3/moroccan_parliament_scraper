import json
import os

def add_term_as_attribute(filename, start_year="2011", end_year="2016"):
    """
    Adds a new attribute 'term' (e.g., '2016-2021') to each entry in the JSON file.

    Args:
        filename (str): The path to the JSON file to modify.
        start_year (str): The starting year to use in the term.
        end_year (str): The ending year to use in the term.
    """
    try:
        # Check if the file exists
        if not os.path.exists(filename):
            print(f"Error: File '{filename}' does not exist.")
            return
        
        # Read the JSON file
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Add the new attribute 'term' to each entry
        term = f"{start_year}-{end_year}"
        for entry in data:
            entry["term"] = term
        
        # Save the updated data back to the file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully added 'term' attribute to {len(data)} entries in '{filename}'.")
    
    except Exception as e:
        print(f"Error while processing the file: {e}")

# Example usage
if __name__ == "__main__":
    add_term_as_attribute("parliamentarians_arabic.json")
