from sqlalchemy.orm import Session
from .models import Document, DocumentChunk
import uuid

def get_document(db: Session, document_id: str):
    return db.query(Document).filter(Document.id == document_id).first()

def create_document(db: Session, filename: str, file_path: str):
    db_document = Document(id=str(uuid.uuid4()), filename=filename, file_path=file_path)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document

def update_document_status(db: Session, document_id: str, status: str):
    db_document = db.query(Document).filter(Document.id == document_id).first()
    if db_document:
        db_document.status = status
        db.commit()
        db.refresh(db_document)
    return db_document

def create_document_chunk(db: Session, document_id: str, chunk_text: str, chunk_order: int, embedding_id: str):
    db_chunk = DocumentChunk(id=str(uuid.uuid4()), document_id=document_id, chunk_text=chunk_text, chunk_order=chunk_order, embedding_id=embedding_id)
    db.add(db_chunk)
    db.commit()
    db.refresh(db_chunk)
    return db_chunk

def get_document_chunks(db: Session, document_id: str):
    return db.query(DocumentChunk).filter(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_order).all()
