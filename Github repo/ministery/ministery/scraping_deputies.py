import pandas as pd
from transformers import MarianMTModel, MarianTokenizer

# Load the Excel file (replace 'yourfile.xlsx' with your file path)
df = pd.read_excel("opendata-liste-dep-v2.xlsx")

# Load the MarianMT model for Arabic to French translation
model_name = 'Helsinki-NLP/opus-mt-ar-fr'
model = MarianMTModel.from_pretrained(model_name)
tokenizer = MarianTokenizer.from_pretrained(model_name)


# Function to translate Arabic text to French
def translate_text(text):
    try:
        if pd.notna(text):
            # Tokenize and translate
            translated = model.generate(**tokenizer(text, return_tensors="pt", padding=True))
            return tokenizer.decode(translated[0], skip_special_tokens=True)
        return text
    except Exception as e:
        print(f"Error translating {text}: {e}")
        return text

# Apply the translation function to each cell in the DataFrame
df_translated = df.applymap(translate_text)

# Save the translated DataFrame to a new Excel file
df_translated.to_excel('translated_file.xlsx', index=False)

print("Translation complete! File saved as 'translated_file.xlsx'.")
