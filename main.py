# Read contents of each file
with open('Libraries and keys.txt', 'r') as file1:
    imports = file1.read()

with open('data_loading&data_cleaning.py', 'r') as file2:
    data_preparation = file2.read()

with open('Aspect_Extraction_NER.py', 'r') as file3:
    Aspect_Extraction = file3.read()

with open('embedding.py', 'r') as file4:
    Embedding = file4.read()

with open('vector_database_creation.py', 'r') as file5:
    Vector_database = file5.read()

with open('Review_Retrieval.py', 'r') as file6:
    Review_retrieval = file6.read()

with open('Reranking.py', 'r') as file7:
    Reranking = file7.read()

with open('llm.py', 'r') as file8:
    LLM = file8.read()

# Concatenate all contents
final_content = imports + '\n\n' + data_preparation + '\n\n' + Aspect_Extraction + '\n\n' + Embedding + '\n\n' + Vector_database + '\n\n' + Review_retrieval + '\n\n' + Reranking + '\n\n' + LLM

# Execute the concatenated code
exec(final_content)
