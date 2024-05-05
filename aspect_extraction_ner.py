# -*- coding: utf-8 -*-
"""Aspect_Extraction_NER.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1gspvLTA08D_dgIKBaO_X2YscRL78nMN0

**Aspect Extraction ----NER**
"""

#Aspect extraction
import numpy as np
import spacy

nlp = spacy.load("en_core_web_sm")

def extract_aspect_terms(text):
    if isinstance(text, float) and np.isnan(text):
        return []
    doc = nlp(str(text))
    aspect_terms = []
    for token in doc:
        if token.pos_ in ["NOUN", "PROPN"]:
            aspect_terms.append(token.text)
        elif token.pos_ == "ADJ" and token.head.pos_ in ["NOUN", "PROPN"]:
            aspect_terms.append(token.head.text + " " + token.text)
            print(aspect_terms)
    return aspect_terms[:5]

pr_data['Aspect Terms'] = pr_data['Cleaned_content'].apply(extract_aspect_terms)
downlod_needed = pr_data
print(pr_data[['product_id','id', 'Cleaned_content','listing_id', 'Aspect Terms']])

unique_product_ids = pr_data['product_id'].unique()
print(unique_product_ids)

# Select
import ipywidgets as widgets
from IPython.display import display

def on_change(change):
    if change['type'] == 'change' and change['name'] == 'value':
        print("Selected Product ID:", change['new'])



# Create a dropdown widget
dropdown = widgets.Dropdown(options=unique_product_ids, description='Product ID:')
dropdown.observe(on_change)

# Display the dropdown
display(dropdown)

# filtering review based on the selection
filtered_df = pr_data[pr_data['product_id'] == dropdown.value]
filtered_df.reset_index(drop=True, inplace=True)
print(filtered_df)