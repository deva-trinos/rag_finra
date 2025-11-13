import os
import shutil
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
#from langchain_community.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document as LangchainDocument

# Retrieve CHROMADB_PATH from environment or use a default
CHROMA_DB_PATH = os.getenv("CHROMADB_PATH", "./data/embeddings")
if not os.path.exists(CHROMA_DB_PATH):
    os.makedirs(CHROMA_DB_PATH)

def process_document_and_store_embeddings(file_path: str, filename: str):
    # ... existing code ...

    # Modify the existing function to accept a file_path and filename directly
    # and assume the file is already saved in the data/documents directory
    # Or, if we want to handle UploadFile directly, we'd do it here.
    # For now, I'll adjust the main.py to save the file first.
    # I'll revert this to original if the user wants me to handle UploadFile directly
    
    loaded_documents = []
    if filename.endswith(".pdf"):
        loader = PyPDFLoader(file_path)
        loaded_documents.extend(loader.load())
    elif filename.endswith(".docx"):
        loader = Docx2txtLoader(file_path)
        loaded_documents.extend(loader.load())
    # Add other document types if needed

    if not loaded_documents:
        print(f"No documents found or loaded from '{file_path}'.")
        return

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunked_documents = text_splitter.split_documents(loaded_documents)

    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma.from_documents(chunked_documents, embeddings, persist_directory=CHROMA_DB_PATH)
    print(f"Processed {len(loaded_documents)} documents and stored {len(chunked_documents)} chunks in ChromaDB.")

def retrieve_relevant_rules(query: str):
    embeddings = OpenAIEmbeddings()
    vectorstore = Chroma(embedding_function=embeddings, persist_directory=CHROMA_DB_PATH)
    
    if not vectorstore._collection.count():
        print("ChromaDB is empty. Please process documents first.")
        return []

    relevant_docs = vectorstore.similarity_search(query, k=5)
    return [doc.page_content for doc in relevant_docs]
