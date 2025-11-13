import os
import shutil
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid # Import uuid for generating unique IDs

from .models import SessionLocal, create_db_tables, Document, DocumentChunk
from .services.document_processing import process_document_and_store_embeddings, retrieve_relevant_rules
from .services.llm_service import get_compliance_suggestions, ComplianceFinding

# Load environment variables
load_dotenv()

print(f"CHROMADB_PATH: {os.getenv('CHROMADB_PATH')}")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")

# FastAPI App
app = FastAPI()

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Database Setup (SQLite) ---
# This will be further defined in models.py and crud.py
# For now, we'll just have a placeholder for the DB session.
# In a real app, you'd use SQLAlchemy to manage database interactions.

# --- ChromaDB Setup ---
# This will be further defined in services/document_processing.py
# For now, we'll initialize a simple client
import chromadb
CHROMA_DB_PATH = os.getenv("CHROMADB_PATH", "./data/embeddings")
if not os.path.exists(CHROMA_DB_PATH):
    os.makedirs(CHROMA_DB_PATH)
chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
# You might want to get or create a collection here
# collection = chroma_client.get_or_create_collection(name="compliance_documents")


# --- Pydantic Models for API Responses ---
class DocumentAnalysisResult(BaseModel):
    document_id: str
    filename: str
    status: str
    findings: List[ComplianceFinding] = []

# --- Endpoints ---

@app.on_event("startup")
async def startup_event():
    create_db_tables()

@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document (PDF/DOCX) for compliance analysis.
    """
    db = SessionLocal() # Get a database session
    try:
        documents_dir = "data/documents"
        os.makedirs(documents_dir, exist_ok=True)
        file_location = os.path.join(documents_dir, file.filename)
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        document_id = str(uuid.uuid4()) # Generate a unique ID for the document
        new_document = Document(id=document_id, filename=file.filename, file_path=file_location, status="processing")
        db.add(new_document)
        db.commit()
        db.refresh(new_document)

        try:
            process_document_and_store_embeddings(file_location, file.filename)
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error processing document {file.filename}: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Failed to process document: {e}")

        return {"message": f"Document {file.filename} uploaded successfully. Analysis pending.", "document_id": document_id, "filename": file.filename}
    except Exception as e:
        import traceback
        traceback.print_exc()
        db.rollback() # Rollback changes if an error occurs
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {e}")
    finally:
        db.close() # Close the database session


@app.get("/list-documents")
async def list_documents():
    """
    List all uploaded documents.
    """
    db = SessionLocal()
    documents = db.query(Document).all()
    return {"documents": [{"id": doc.id, "filename": doc.filename, "status": doc.status} for doc in documents]}


@app.get("/compliance-findings/{document_id}", response_model=DocumentAnalysisResult)
async def get_compliance_findings(document_id: str):
    """
    Retrieve compliance findings for a given document.
    """
    db = SessionLocal()
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Assuming `document.content` or `document.title` holds relevant info for the query
    # For this example, I'll use a placeholder query.
    query = f"Compliance rules for {document.filename}"

    relevant_rules = retrieve_relevant_rules(query)

    findings = get_compliance_suggestions(document.file_path, relevant_rules)

    document.status = "completed"  # Update document status to completed
    db.add(document)
    db.commit()
    db.refresh(document)

    return DocumentAnalysisResult(
        document_id=document.id,
        filename=document.filename,
        status=document.status,
        findings=findings
    )

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
