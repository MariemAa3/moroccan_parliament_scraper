import json

def are_json_files_equal(file1, file2):
    """
    Compares two JSON files for equality.

    Args:
        file1 (str): Path to the first JSON file.
        file2 (str): Path to the second JSON file.

    Returns:
        bool: True if the files are equal, False otherwise.
    """
    try:
        # Load the contents of the first file
        with open(file1, "r", encoding="utf-8") as f1:
            data1 = json.load(f1)

        # Load the contents of the second file
        with open(file2, "r", encoding="utf-8") as f2:
            data2 = json.load(f2)

        # Compare the data
        return data1 == data2

    except Exception as e:
        print(f"Error while comparing JSON files: {e}")
        return False

# Example usage
if __name__ == "__main__":
    file1 = "parliamentarians_arabic_2011_2016.json"
    file2 = "parliamentarians_arabic_2016_2021.json"
    if are_json_files_equal(file1, file2):
        print("The two JSON files are equal.")
    else:
        print("The two JSON files are not equal.")
