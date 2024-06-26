# -*- coding: utf-8 -*-
"""Info5731_Group4_Project.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1enQEnluqNsLEvmIYLHnNZHAJbjpGRj4J
"""

!pip install  numpy
!pip install faiss-cpu
!pip install sentence_transformers
!pip install langchain
!pip install llama-index
!pip install llama-index-llms-openai
!pip install llama-index-embeddings-jinaai
!pip install llama-index-llms-huggingface
!pip install "huggingface_hub[inference]"

# required keys
Japi_key = "jina_003279306e15431eb5d5d8f9d63f0621Xfl_KnauOYejyQ4WwVMzdpAja5RK"
huggingface_api_key: str = "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"

"""## Data loading"""

# loading product review data
import pandas as pd
pr_data = pd.read_csv('/content/Product_reviews_description_data.csv')
pr_data.describe()

pr_data.head()

"""## Data Cleansing"""

# Data Cleansing
pr_data.isnull().sum()

pr_data.fillna('', inplace=True)
pr_data.isnull().sum()

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

# Embedding
import numpy as np
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('jinaai/jina-embedding-s-en-v1')
def generate_embeddings(input_df):
    all_embeddings = []

    for t in input_df.Cleaned_content:
        review_embeddings = []
        all_embeddings.append(np.array(model.encode(t)))

    input_df["embeddings"] = all_embeddings
    return input_df

enhanced_dataframe = generate_embeddings(filtered_df)

enhanced_dataframe.head()

# vector database creation
import faiss
import numpy as np

if 'embeddings' not in enhanced_dataframe.columns:
    print("Error: 'embeddings' column not found in DataFrame")
else:
    dim = len(enhanced_dataframe['embeddings'].iloc[0])
    index = faiss.IndexFlatIP(dim)
    embeddings_array = np.vstack(enhanced_dataframe['embeddings'])
    faiss.normalize_L2(embeddings_array)
    index.add(embeddings_array)

expected_indexes = range(len(filtered_df))
# Find missing indexes
missing_indexes = [index for index in expected_indexes if index not in filtered_df.index or index == -1]

# Retriving top 20 results
def find_similar_texts(query, n=21):
    query_embedding = model.encode(query)
    query_embedding = np.ascontiguousarray(
        np.array(query_embedding, dtype="float32").reshape(1, -1)
    )
    faiss.normalize_L2(query_embedding)
    similarities, indices = index.search(query_embedding, n)
    results = []
    num_valid_indices = min(n, len(enhanced_dataframe))
    for i in range(num_valid_indices):
        similarity = similarities[0][i]
        index_id = indices[0][i]
        while index_id < 0 or index_id >= len(enhanced_dataframe):
            i += 1
            if i >= num_valid_indices:
                break
            index_id = indices[0][i]
        if index_id < 0 or index_id >= len(enhanced_dataframe):
            continue
        result_text = enhanced_dataframe.loc[index_id, "Cleaned_content"]
        results.append(result_text)
    return results[:n]

query = "cost"
search_results = find_similar_texts(query)
print(np.array(search_results))

# reranking  and getting top 5 reviews
from sentence_transformers import CrossEncoder

jina_reranking_model = CrossEncoder("jinaai/jina-reranker-v1-tiny-en", trust_remote_code=True)

results = jina_reranking_model.rank(query, search_results, return_documents=True, top_k=5)

all_reviews = [item['text'] for item in results]
print(np.array(all_reviews))

# model_name: str = "mistralai/Mixtral-8x7B-Instruct-v0.1"
# api_key: str = hf_inference_api_key
# context_window: int = 4096
# num_output: int = 512

#load reviews
from typing import List
from llama_index.core.readers import StringIterableReader
from llama_index.core.schema import Document
all_reviews.insert(0, "Below are the top 5 reviews of " + dropdown.value + " product")
def load_context_data(context_data: List[str]) -> List[Document]:
    ret: List[Document] = []
    buff: str = ""
    for text in context_data:
        buff += text + "\n\n"
        ret.append(buff)
        buff = ""
    return StringIterableReader().load_data(ret)
tokens = load_context_data(all_reviews)

from langchain.chains import RetrievalQA
from llama_index.core import VectorStoreIndex, ServiceContext
from llama_index.core import PromptTemplate
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core import get_response_synthesizer
from llama_index.llms.huggingface import HuggingFaceInferenceAPI

# load mistralai LLm model
mixtral_llm = HuggingFaceInferenceAPI(
    model_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
    token=huggingface_api_key
)
from llama_index.embeddings.jinaai import JinaEmbedding
jina_embedding_model = JinaEmbedding(
    api_key=Japi_key,
    model="jina-embeddings-v2-base-en",
)

service_context = ServiceContext.from_defaults(
    llm=mixtral_llm, embed_model=jina_embedding_model
)
index = VectorStoreIndex.from_documents(
    documents=tokens, service_context=service_context
)
qa_prompt_tmpl = (
    "Context information is below.\n"
    "---------------------\n"
    "{context_str}\n"
    "---------------------\n"
    "answer the query. Please be brief, concise, and complete.\n"
    "Answer: "
)
qa_prompt = PromptTemplate(qa_prompt_tmpl)

# configure retriever
retriever = VectorIndexRetriever(
    index=index,
    similarity_top_k=2,
)

# configure response synthesizer
response_synthesizer = get_response_synthesizer(
    service_context=service_context,
    text_qa_template=qa_prompt,
    response_mode="compact",
)

# assemble query engine
query_engine = RetrieverQueryEngine(
    retriever=retriever,
    response_synthesizer=response_synthesizer,
)

result = query_engine.query("text summary")
#print(result.response)

import textwrap
wrapped_text = textwrap.fill(result.response, width=110)
print(wrapped_text)